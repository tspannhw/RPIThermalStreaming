#!/usr/bin/env python3
"""
Test script to verify Snowflake connection and authentication.

This script tests:
1. Configuration file loading
2. Private key loading
3. JWT token generation
4. Scoped token acquisition
5. Control plane connection
6. Ingest host discovery

Usage:
    python test_connection.py [--config snowflake_config.json]
"""

import sys
import os
import logging
import argparse
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_configuration(config_file: str) -> bool:
    """Test configuration file loading."""
    logger.info("=" * 70)
    logger.info("TEST 1: Configuration File")
    logger.info("=" * 70)
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        required_fields = ['user', 'account', 'private_key_file', 'role', 
                          'database', 'schema', 'pipe']
        
        missing_fields = [f for f in required_fields if f not in config]
        
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return False
        
        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  User: {config['user']}")
        logger.info(f"  Account: {config['account']}")
        logger.info(f"  Database: {config['database']}")
        logger.info(f"  Schema: {config['schema']}")
        logger.info(f"  Pipe: {config['pipe']}")
        logger.info(f"  Private key file: {config['private_key_file']}")
        
        return True
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        logger.error("Run: cp snowflake_config.json.template snowflake_config.json")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return False


def test_private_key(config: dict) -> bool:
    """Test private key loading."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Private Key")
    logger.info("=" * 70)
    
    private_key_file = config['private_key_file']
    
    if not Path(private_key_file).exists():
        logger.error(f"Private key file not found: {private_key_file}")
        logger.error("Run: ./generate_keys.sh")
        return False
    
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        
        with open(private_key_file, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        
        logger.info(f"✓ Private key loaded successfully")
        logger.info(f"  File: {private_key_file}")
        logger.info(f"  Key type: {type(private_key).__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading private key: {e}")
        return False


def test_jwt_auth(config: dict) -> bool:
    """Test JWT token generation and scoped token acquisition."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: JWT Authentication")
    logger.info("=" * 70)
    
    try:
        from snowflake_jwt_auth import SnowflakeJWTAuth
        
        auth = SnowflakeJWTAuth(config)
        
        # Generate JWT token
        jwt_token = auth.generate_jwt_token()
        logger.info(f"✓ JWT token generated")
        logger.info(f"  Token length: {len(jwt_token)} characters")
        
        # Get scoped token
        logger.info("Requesting scoped token from Snowflake...")
        scoped_token = auth.get_scoped_token()
        logger.info(f"✓ Scoped token obtained")
        logger.info(f"  Token length: {len(scoped_token)} characters")
        logger.info(f"  Token prefix: {scoped_token[:50]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        logger.error("\nPossible issues:")
        logger.error("1. Public key not registered in Snowflake")
        logger.error("2. User or account identifier incorrect")
        logger.error("3. Network connectivity issues")
        return False


def test_streaming_client(config: dict) -> bool:
    """Test streaming client initialization and host discovery."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Streaming Client")
    logger.info("=" * 70)
    
    try:
        from thermal_streaming_client import SnowpipeStreamingClient
        
        # Initialize client
        client = SnowpipeStreamingClient(config_file='snowflake_config.json')
        logger.info(f"✓ Client initialized")
        
        # Discover ingest host
        logger.info("Discovering ingest host...")
        ingest_host = client.discover_ingest_host()
        logger.info(f"✓ Ingest host discovered: {ingest_host}")
        
        # Open channel
        logger.info(f"Opening channel: {client.channel_name}...")
        result = client.open_channel()
        logger.info(f"✓ Channel opened successfully")
        logger.info(f"  Channel: {client.channel_name}")
        logger.info(f"  Initial offset: {client.offset_token}")
        
        # Get channel status
        logger.info("Getting channel status...")
        status = client.get_channel_status()
        logger.info(f"✓ Channel status retrieved")
        
        committed_offset = status.get('committed_offset_token', 0)
        logger.info(f"  Committed offset: {committed_offset}")
        
        return True
        
    except Exception as e:
        logger.error(f"Streaming client test failed: {e}", exc_info=True)
        logger.error("\nPossible issues:")
        logger.error("1. Pipe does not exist in Snowflake")
        logger.error("2. User lacks OPERATE privilege on pipe")
        logger.error("3. Database/schema/pipe names incorrect")
        return False


def test_sensor() -> bool:
    """Test sensor data reading."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Sensor Data Reading")
    logger.info("=" * 70)
    
    try:
        from thermal_sensor import ThermalSensor
        
        # Initialize sensor (will auto-detect or simulate)
        sensor = ThermalSensor()
        
        if sensor.simulate:
            logger.info("Running in SIMULATION mode (no physical sensors)")
        else:
            logger.info("Physical sensors detected")
        
        # Read sample data
        logger.info("Reading sensor data...")
        data = sensor.read_sensor_data()
        
        logger.info(f"✓ Sensor data read successfully")
        logger.info(f"  Temperature: {data['temperature']:.2f}°C")
        logger.info(f"  Humidity: {data['humidity']:.1f}%")
        logger.info(f"  CO2: {data['co2']:.0f} ppm")
        logger.info(f"  Pressure: {data['pressure']:.1f} Pa")
        logger.info(f"  CPU Temp: {data['cputempf']:.1f}°F")
        logger.info(f"  CPU Usage: {data['cpu']:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"Sensor test failed: {e}", exc_info=True)
        return False


def main():
    """Main test routine."""
    parser = argparse.ArgumentParser(
        description='Test Snowflake Streaming connection and configuration'
    )
    parser.add_argument(
        '--config',
        default='snowflake_config.json',
        help='Path to Snowflake configuration file'
    )
    
    args = parser.parse_args()
    
    logger.info("\n" + "=" * 70)
    logger.info("SNOWFLAKE STREAMING CONNECTION TEST")
    logger.info("=" * 70)
    
    results = {}
    
    # Test 1: Configuration
    with open(args.config, 'r') as f:
        config = json.load(f)
    results['configuration'] = test_configuration(args.config)
    
    if not results['configuration']:
        logger.error("\n❌ Configuration test failed. Fix configuration before proceeding.")
        return 1
    
    # Test 2: Private Key
    results['private_key'] = test_private_key(config)
    
    if not results['private_key']:
        logger.error("\n❌ Private key test failed. Generate keys before proceeding.")
        return 1
    
    # Test 3: JWT Authentication
    results['jwt_auth'] = test_jwt_auth(config)
    
    if not results['jwt_auth']:
        logger.error("\n❌ Authentication test failed. Check Snowflake setup.")
        return 1
    
    # Test 4: Streaming Client
    results['streaming_client'] = test_streaming_client(config)
    
    if not results['streaming_client']:
        logger.error("\n❌ Streaming client test failed. Check Snowflake pipe setup.")
        return 1
    
    # Test 5: Sensor
    results['sensor'] = test_sensor()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n" + "=" * 70)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 70)
        logger.info("\nYou're ready to run the application:")
        logger.info("  python main.py --simulate")
        logger.info("=" * 70)
        return 0
    else:
        logger.error("\n" + "=" * 70)
        logger.error("✗ SOME TESTS FAILED")
        logger.error("=" * 70)
        logger.error("\nPlease fix the issues above before running the application.")
        logger.error("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())

