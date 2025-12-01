#!/usr/bin/env python3
"""
Main Application: Raspberry Pi Thermal Sensor to Snowflake Streaming

Continuously reads thermal sensor data from Raspberry Pi and streams it
to Snowflake using Snowpipe Streaming v2 REST API.


Usage:
    python main.py [--config CONFIG_FILE] [--batch-size SIZE] [--interval SECONDS]
"""

import argparse
import logging
import time
import sys
import os
import signal
from datetime import datetime
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thermal_sensor import ThermalSensor
from thermal_streaming_client import SnowpipeStreamingClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('thermal_streaming.log')
    ]
)
logger = logging.getLogger(__name__)


class ThermalStreamingApp:
    """Main application for streaming thermal sensor data to Snowflake."""
    
    def __init__(self, config_file: str = 'snowflake_config.json',
                 batch_size: int = 10, interval: float = 5.0):
        """
        Initialize the application.
        
        
        Args:
            config_file: Path to Snowflake configuration file
            batch_size: Number of readings per batch
            interval: Seconds between batches
        
        Note: PRODUCTION MODE ONLY - No simulation. Requires physical sensors.
        """
        self.config_file = config_file
        self.batch_size = batch_size
        self.interval = interval
        self.running = False
        
        logger.info("=" * 70)
        logger.info("Thermal Sensor Streaming Application - PRODUCTION MODE")
        logger.info("Raspberry Pi → Snowflake via Snowpipe Streaming v2 REST API")
        logger.info("=" * 70)
        logger.info("PRODUCTION CONFIGURATION:")
        logger.info("  - Real sensor data ONLY (no simulation)")
        logger.info("  - Snowpipe Streaming high-speed REST API ONLY")
        logger.info("=" * 70)
        
        # Initialize components - PRODUCTION MODE ONLY
        logger.info("Initializing REAL physical sensors...")
        self.sensor = ThermalSensor(simulate=False, require_real_sensors=True)
        
        logger.info("Initializing Snowpipe Streaming REST API client...")
        self.client = SnowpipeStreamingClient(config_file)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Initialization complete")
        logger.info(f"Batch size: {batch_size} readings")
        logger.info(f"Batch interval: {interval} seconds")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
    
    def initialize(self):
        """Initialize the Snowpipe Streaming connection."""
        logger.info("Setting up Snowpipe Streaming connection...")
        
        try:
            # Discover ingest host
            logger.info("Discovering ingest host...")
            ingest_host = self.client.discover_ingest_host()
            logger.info(f"[OK] Ingest host: {ingest_host}")
            
            # Open channel
            logger.info("Opening streaming channel...")
            self.client.open_channel()
            logger.info("[OK] Channel opened successfully")
            
            logger.info("Snowpipe Streaming connection ready!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize streaming: {e}", exc_info=True)
            return False
    
    def run(self):
        """Main application loop."""
        if not self.initialize():
            logger.error("Initialization failed, exiting")
            return 1
        
        self.running = True
        batch_count = 0
        last_commit_check = time.time()
        
        logger.info("=" * 70)
        logger.info("Starting data collection and streaming...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
        
        try:
            while self.running:
                batch_count += 1
                batch_start = time.time()
                
                logger.info(f"\n--- Batch {batch_count} ---")
                
                # Read sensor data
                logger.info(f"Reading {self.batch_size} sensor samples...")
                readings = self.sensor.read_batch(
                    count=self.batch_size,
                    interval=max(0.5, self.interval / self.batch_size)
                )
                
                # Log sample data
                if readings:
                    sample = readings[0]
                    logger.info(f"Sample reading: Temp={sample['temperature']:.1f}°C, "
                               f"Humidity={sample['humidity']:.1f}%, "
                               f"CO2={sample['co2']:.0f}ppm, "
                               f"CPU={sample['cpu']:.1f}%")
                
                # Insert to Snowflake via Snowpipe Streaming
                try:
                    row_count = self.client.insert_rows(readings)
                    logger.info(f"[OK] Successfully sent {row_count} readings to Snowpipe Streaming")
                    
                except Exception as e:
                    logger.error(f"Failed to insert batch: {e}")
                    # Continue to next batch even if this one fails
                
                # Print statistics every 10 batches
                if batch_count % 10 == 0:
                    self.client.print_statistics()
                
                # Calculate sleep time to maintain interval
                batch_elapsed = time.time() - batch_start
                sleep_time = max(0, self.interval - batch_elapsed)
                
                if sleep_time > 0 and self.running:
                    logger.info(f"Waiting {sleep_time:.1f}s until next batch...")
                    time.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            return 1
        
        finally:
            self.shutdown()
        
        return 0
    
    def shutdown(self):
        """Graceful shutdown."""
        logger.info("\n" + "=" * 70)
        logger.info("Shutting down...")
        logger.info("=" * 70)
        
        try:
            # Print final statistics
            self.client.print_statistics()
            
            # Close streaming channel
            logger.info("Closing streaming channel...")
            self.client.close_channel()
            logger.info("[OK] Channel closed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Stream Raspberry Pi thermal sensor data to Snowflake'
    )
    parser.add_argument(
        '--config',
        default='snowflake_config.json',
        help='Path to Snowflake configuration file (default: snowflake_config.json)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of readings per batch (default: 10)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=5.0,
        help='Seconds between batches (default: 5.0)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Adjust logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # PRODUCTION MODE: Verify Snowpipe Streaming is configured
    logger.info("PRODUCTION MODE: Real sensors + Snowpipe Streaming REST API only")
    
    # Create and run application
    app = ThermalStreamingApp(
        config_file=args.config,
        batch_size=args.batch_size,
        interval=args.interval
    )
    
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()