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
        
        # Required fields for all auth methods
        required_fields = ['user', 'account', 'role', 'database', 'schema', 'pipe']
        
        missing_fields = [f for f in required_fields if f not in config]
        
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return False
        
        # Check for at least one authentication method
        has_pat = 'pat' in config and config.get('pat')
        has_jwt = 'private_key_file' in config and config.get('private_key_file')
        
        if not has_pat and not has_jwt:
            logger.error("No authentication method configured!")
            logger.error("Provide either 'pat' (Programmatic Access Token) or 'private_key_file' (JWT)")
            return False
        
        logger.info("[OK] Configuration loaded successfully")
        logger.info(f"  User: {config['user']}")
        logger.info(f"  Account: {config['account']}")
        logger.info(f"  Database: {config['database']}")
        logger.info(f"  Schema: {config['schema']}")
        logger.info(f"  Pipe: {config['pipe']}")
        
        if has_pat:
            logger.info(f"  Auth method: PAT (Programmatic Access Token)")
            logger.info(f"  PAT: {config['pat'][:20]}...") 
        elif has_jwt:
            logger.info(f"  Auth method: JWT Key-Pair")
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


def test_authentication_method(config: dict) -> bool:
    """Test authentication method (PAT or JWT)."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Authentication Method")
    logger.info("=" * 70)
    
    # Check for PAT
    if 'pat' in config and config.get('pat'):
        logger.info("[OK] Using PAT (Programmatic Access Token)")
        logger.info(f"  PAT length: {len(config['pat'])} characters")
        logger.info(f"  PAT starts with: {config['pat'][:15]}...")
        return True
    
    # Check for JWT
    if 'private_key_file' in config and config.get('private_key_file'):
        logger.info("Using JWT Key-Pair Authentication")
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
            
            logger.info(f"[OK] Private key loaded successfully")
            logger.info(f"  File: {private_key_file}")
            logger.info(f"  Key type: {type(private_key).__name__}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading private key: {e}")
            return False
    
    logger.error("No valid authentication method found")
    return False


def test_auth(config: dict) -> bool:
    """Test authentication (PAT or JWT)."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Authentication")
    logger.info("=" * 70)
    
    try:
        from snowflake_jwt_auth import SnowflakeJWTAuth
        
        auth = SnowflakeJWTAuth(config)
        
        if auth.auth_method == 'pat':
            # Using PAT
            logger.info("Using PAT authentication")
            token = auth.get_scoped_token()
            logger.info(f"[OK] PAT validated")
            logger.info(f"  Token length: {len(token)} characters")
        else:
            # Using JWT
            logger.info("Using JWT authentication")
            
            # Generate JWT token
            jwt_token = auth.generate_jwt_token()
            logger.info(f"[OK] JWT token generated")
            logger.info(f"  Token length: {len(jwt_token)} characters")
            
            # Get OAuth token
            logger.info("Requesting OAuth token from Snowflake...")
            token = auth.get_scoped_token()
            logger.info(f"[OK] OAuth token obtained")
            logger.info(f"  Token length: {len(token)} characters")
            logger.info(f"  Token prefix: {token[:50]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        
        if 'pat' in config and config.get('pat'):
            logger.error("\nTroubleshooting PAT authentication:")
            logger.error("1. Verify the PAT is valid (not expired or revoked)")
            logger.error("2. Check: SHOW USER PROGRAMMATIC ACCESS TOKENS FOR USER <user>;")
            logger.error("3. Generate new PAT: ALTER USER <user> ADD PROGRAMMATIC ACCESS TOKEN;")
        else:
            logger.error("\nTroubleshooting JWT authentication:")
            logger.error("1. Public key not registered in Snowflake")
            logger.error("2. User or account identifier incorrect")
            logger.error("3. Network connectivity issues")
            logger.error("\nOR switch to PAT (easier):")
            logger.error("  See GENERATE_PAT.md for instructions")
        
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
    
    # Test 2: Authentication Method
    results['auth_method'] = test_authentication_method(config)
    
    if not results['auth_method']:
        logger.error("\n[ERROR] Authentication method test failed.")
        logger.error("Add 'pat' to your config or generate JWT keys.")
        return 1
    
    # Test 3: Authentication
    results['authentication'] = test_auth(config)
    
    if not results['authentication']:
        logger.error("\n[ERROR] Authentication test failed. Check Snowflake setup.")
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
        logger.info("[SUCCESS] ALL TESTS PASSED!")
        logger.info("=" * 70)
        logger.info("\nYou're ready to run the application:")
        logger.info("  python main.py --simulate")
        logger.info("=" * 70)
        return 0
    else:
        logger.error("\n" + "=" * 70)
        logger.error("[FAILED] SOME TESTS FAILED")
        logger.error("=" * 70)
        logger.error("\nPlease fix the issues above before running the application.")
        logger.error("\nQuick fix: Use PAT authentication (easier)")
        logger.error("  See GENERATE_PAT.md for instructions")
        logger.error("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())

