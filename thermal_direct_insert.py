#!/usr/bin/env python3
"""
Direct Insert Client for Raspberry Pi Thermal Sensor Data

Uses Snowflake Python Connector with PAT authentication
to insert data directly into Snowflake table.

This is simpler and more widely supported than REST API.
"""

import json
import logging
import sys
import os
from typing import Dict, List
import snowflake.connector
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


class SnowflakeDirectClient:
    """Client for direct insertion to Snowflake using Python connector."""
    
    def __init__(self, config_file: str = 'snowflake_config.json'):
        """Initialize the client."""
        self.config = self._load_config(config_file)
        self.conn = None
        self.cursor = None
        
        # Statistics
        self.stats = {
            'total_rows_inserted': 0,
            'total_batches': 0,
            'errors': 0,
            'start_time': None
        }
        
        logger.info("Direct insert client initialized")
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
    
    def connect(self):
        """Connect to Snowflake using PAT."""
        logger.info("Connecting to Snowflake...")
        
        try:
            # PAT can be used as a password replacement
            self.conn = snowflake.connector.connect(
                user=self.config['user'],
                account=self.config['account'],
                password=self.config['pat'],  # Use PAT as password
                database=self.config['database'],
                schema=self.config['schema'],
                warehouse='COMPUTE_WH'  # Default warehouse
            )
            
            self.cursor = self.conn.cursor()
            
            logger.info("✓ Connected to Snowflake")
            logger.info(f"  Database: {self.config['database']}")
            logger.info(f"  Schema: {self.config['schema']}")
            
            # Verify connection
            self.cursor.execute("SELECT CURRENT_VERSION(), CURRENT_WAREHOUSE()")
            version, warehouse = self.cursor.fetchone()
            logger.info(f"  Snowflake version: {version}")
            logger.info(f"  Warehouse: {warehouse}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def insert_rows(self, rows: List[Dict]) -> int:
        """
        Insert rows directly into Snowflake table.
        
        Args:
            rows: List of dictionaries representing sensor data
            
        Returns:
            Number of rows inserted
        """
        if not rows:
            logger.warning("No rows to insert")
            return 0
        
        if not self.conn or not self.cursor:
            raise RuntimeError("Not connected. Call connect() first.")
        
        logger.info(f"Inserting {len(rows)} rows...")
        
        try:
            # Prepare INSERT statement with VALUES
            # Cast JSON string to VARIANT using TO_VARIANT
            insert_sql = """
            INSERT INTO THERMAL_SENSOR_DATA (
                raw_data, uuid, rowid, hostname, host, ipaddress, macaddress,
                temperature, humidity, co2, equivalentco2ppm, totalvocppb, pressure,
                cputempf, temperatureicp, cpu, memory, diskusage, runtime,
                ts, systemtime, starttime, endtime, datetimestamp, te
            ) VALUES (
                TO_VARIANT(PARSE_JSON(%s)), %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            """
            
            # Prepare data tuples
            data_tuples = []
            for row in rows:
                data_tuple = (
                    json.dumps(row),  # raw_data as JSON string (will be auto-converted to VARIANT)
                    row.get('uuid'),
                    row.get('rowid'),
                    row.get('hostname'),
                    row.get('host'),
                    row.get('ipaddress'),
                    row.get('macaddress'),
                    row.get('temperature'),
                    row.get('humidity'),
                    row.get('co2'),
                    row.get('equivalentco2ppm'),
                    row.get('totalvocppb'),
                    row.get('pressure'),
                    row.get('cputempf'),
                    row.get('temperatureicp'),
                    row.get('cpu'),
                    row.get('memory'),
                    row.get('diskusage'),
                    row.get('runtime'),
                    row.get('ts'),
                    row.get('systemtime'),
                    row.get('starttime'),
                    row.get('endtime'),
                    row.get('datetimestamp'),  # Already in correct format
                    row.get('te')
                )
                data_tuples.append(data_tuple)
            
            # Execute batch insert
            self.cursor.executemany(insert_sql, data_tuples)
            self.conn.commit()
            
            # Update statistics
            rows_inserted = len(rows)
            self.stats['total_rows_inserted'] += rows_inserted
            self.stats['total_batches'] += 1
            
            logger.info(f"✓ Inserted {rows_inserted} rows successfully")
            
            return rows_inserted
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Failed to insert rows: {e}")
            self.conn.rollback()
            raise
    
    def close(self):
        """Close connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Connection closed")
    
    def print_statistics(self):
        """Print insertion statistics."""
        logger.info("=" * 70)
        logger.info("INGESTION STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total rows inserted: {self.stats['total_rows_inserted']}")
        logger.info(f"Total batches: {self.stats['total_batches']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 70)


def main():
    """Test the direct insert client."""
    import time
    from thermal_sensor import ThermalSensor
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    
    logger.info("Testing Direct Insert Client")
    
    try:
        # Initialize client
        client = SnowflakeDirectClient('snowflake_config.json')
        
        # Connect
        client.connect()
        
        # Initialize sensor
        sensor = ThermalSensor(simulate=True)
        
        # Read some data
        logger.info("Reading sensor data...")
        rows = sensor.read_batch(count=5, interval=1.0)
        
        # Insert to Snowflake
        client.insert_rows(rows)
        
        # Print statistics
        client.print_statistics()
        
        # Close connection
        client.close()
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

