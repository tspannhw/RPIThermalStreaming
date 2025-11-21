#!/usr/bin/env python3
"""
Snowpipe Streaming v2 REST API Client for Raspberry Pi Thermal Sensor Data

This client uses the high-performance Snowpipe Streaming REST API to ingest
thermal sensor data from a Raspberry Pi into Snowflake in near real-time.

Based on Snowflake's Snowpipe Streaming v2 REST API:
https://docs.snowflake.com/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-rest-api
"""

import json
import logging
import time
import sys
from datetime import datetime, timezone
from typing import Dict, Optional, List
import requests
from pathlib import Path

# Import JWT authentication module
from snowflake_jwt_auth import SnowflakeJWTAuth

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


class SnowpipeStreamingClient:
    """
    Client for Snowpipe Streaming v2 REST API.
    Handles authentication, channel management, and data ingestion.
    """
    
    def __init__(self, config_file: str = 'snowflake_config.json'):
        """Initialize the streaming client."""
        self.config = self._load_config(config_file)
        self.jwt_auth = SnowflakeJWTAuth(self.config)
        
        # Streaming state
        self.control_host = None
        self.ingest_host = None
        self.channel_name = self.config.get('channel_name', 'thermal_channel_001')
        self.continuation_token = None
        self.offset_token = 0
        self.scoped_token = None
        self.token_expiry = None
        
        # Statistics
        self.stats = {
            'total_rows_sent': 0,
            'total_batches': 0,
            'total_bytes_sent': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        logger.info("SnowpipeStreamingClient initialized")
        logger.info(f"Database: {self.config['database']}")
        logger.info(f"Schema: {self.config['schema']}")
        logger.info(f"Pipe: {self.config['pipe']}")
        logger.info(f"Channel: {self.channel_name}")
    
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
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def _ensure_valid_token(self):
        """Ensure we have a valid scoped token."""
        if self.scoped_token is None or (self.token_expiry and time.time() >= self.token_expiry):
            logger.info("Obtaining new scoped token...")
            self.scoped_token = self.jwt_auth.get_scoped_token()
            # Tokens typically valid for 1 hour, refresh after 50 minutes
            self.token_expiry = time.time() + 3000
            logger.info("New scoped token obtained")
    
    def discover_ingest_host(self) -> str:
        """
        Discover the ingest host URL using the control plane.
        Step 2 in the REST API tutorial.
        """
        logger.info("Discovering ingest host...")
        
        # Construct control host URL
        account = self.config['account']
        self.control_host = f"https://{account}.snowflakecomputing.com"
        
        url = f"{self.control_host}/v2/streaming/control"
        
        self._ensure_valid_token()
        
        headers = {
            'Authorization': f'Bearer {self.scoped_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.ingest_host = data.get('ingest_host')
            
            if not self.ingest_host:
                raise ValueError("No ingest_host returned from control plane")
            
            logger.info(f"Ingest host discovered: {self.ingest_host}")
            return self.ingest_host
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to discover ingest host: {e}")
            raise
    
    def open_channel(self) -> Dict:
        """
        Open a streaming channel.
        Step 3 in the REST API tutorial.
        """
        logger.info(f"Opening channel: {self.channel_name}")
        
        if not self.ingest_host:
            self.discover_ingest_host()
        
        self._ensure_valid_token()
        
        db = self.config['database']
        schema = self.config['schema']
        pipe = self.config['pipe']
        
        url = (
            f"https://{self.ingest_host}/v2/streaming"
            f"/databases/{db}/schemas/{schema}/pipes/{pipe}/channels/{self.channel_name}:open"
        )
        
        headers = {
            'Authorization': f'Bearer {self.scoped_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'channel_name': self.channel_name,
            'write_mode': 'CLOUD_STORAGE'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract tokens
            self.continuation_token = data.get('next_continuation_token')
            channel_status = data.get('channel_status', {})
            self.offset_token = channel_status.get('last_committed_offset_token', 0)
            
            logger.info(f"Channel opened successfully")
            logger.info(f"Initial offset token: {self.offset_token}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to open channel: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def append_rows(self, rows: List[Dict]) -> Dict:
        """
        Append rows to the streaming channel.
        Step 4 in the REST API tutorial.
        
        Args:
            rows: List of dictionaries representing the data rows
            
        Returns:
            Response dictionary from the API
        """
        if not rows:
            logger.warning("No rows to append")
            return {}
        
        logger.info(f"Appending {len(rows)} rows...")
        
        if not self.ingest_host or not self.continuation_token:
            raise RuntimeError("Channel not opened. Call open_channel() first.")
        
        self._ensure_valid_token()
        
        # Increment offset for this batch
        new_offset = self.offset_token + 1
        
        db = self.config['database']
        schema = self.config['schema']
        pipe = self.config['pipe']
        
        url = (
            f"https://{self.ingest_host}/v2/streaming/data"
            f"/databases/{db}/schemas/{schema}/pipes/{pipe}/channels/{self.channel_name}/rows"
            f"?continuationToken={self.continuation_token}&offsetToken={new_offset}"
        )
        
        headers = {
            'Authorization': f'Bearer {self.scoped_token}',
            'Content-Type': 'application/x-ndjson'
        }
        
        # Convert rows to NDJSON format
        ndjson_data = '\n'.join(json.dumps(row) for row in rows)
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=ndjson_data.encode('utf-8'),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Update tokens for next append
            self.continuation_token = data.get('next_continuation_token')
            
            # Update offset token only after successful append
            self.offset_token = new_offset
            
            # Update statistics
            self.stats['total_rows_sent'] += len(rows)
            self.stats['total_batches'] += 1
            self.stats['total_bytes_sent'] += len(ndjson_data)
            
            logger.info(f"Successfully appended {len(rows)} rows")
            logger.debug(f"New offset token: {self.offset_token}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.stats['errors'] += 1
            logger.error(f"Failed to append rows: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_channel_status(self) -> Dict:
        """
        Get the current status of the channel.
        Step 4.4 in the REST API tutorial - Critical for verifying data persistence.
        """
        logger.debug(f"Getting channel status: {self.channel_name}")
        
        if not self.ingest_host:
            raise RuntimeError("Ingest host not discovered. Call discover_ingest_host() first.")
        
        self._ensure_valid_token()
        
        db = self.config['database']
        schema = self.config['schema']
        pipe = self.config['pipe']
        
        url = (
            f"https://{self.ingest_host}/v2/streaming"
            f"/databases/{db}/schemas/{schema}/pipes/{pipe}:bulk-channel-status"
        )
        
        headers = {
            'Authorization': f'Bearer {self.scoped_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'channel_names': [self.channel_name]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            channel_statuses = data.get('channel_statuses', {})
            channel_status = channel_statuses.get(self.channel_name, {})
            
            committed_offset = channel_status.get('committed_offset_token', 0)
            logger.debug(f"Channel committed offset: {committed_offset}")
            
            return channel_status
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get channel status: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def wait_for_commit(self, expected_offset: int, timeout: int = 60, poll_interval: int = 2) -> bool:
        """
        Wait for data to be committed to Snowflake.
        
        Args:
            expected_offset: The offset we're waiting to be committed
            timeout: Maximum time to wait in seconds
            poll_interval: How often to poll for status in seconds
            
        Returns:
            True if committed, False if timeout
        """
        logger.info(f"Waiting for offset {expected_offset} to be committed...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                status = self.get_channel_status()
                committed_offset = status.get('committed_offset_token', 0)
                
                if committed_offset >= expected_offset:
                    logger.info(f"Data committed! Offset: {committed_offset}")
                    return True
                
                logger.debug(f"Waiting... committed={committed_offset}, expected={expected_offset}")
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.warning(f"Error checking status: {e}")
                time.sleep(poll_interval)
        
        logger.warning(f"Timeout waiting for commit after {timeout}s")
        return False
    
    def close_channel(self):
        """Close the streaming channel (optional - channels auto-close after inactivity)."""
        logger.info(f"Closing channel: {self.channel_name}")
        # Note: The REST API doesn't have an explicit close endpoint
        # Channels automatically close after period of inactivity
        logger.info("Channel will auto-close after inactivity period")
    
    def print_statistics(self):
        """Print ingestion statistics."""
        elapsed_time = time.time() - self.stats['start_time']
        
        logger.info("=" * 60)
        logger.info("INGESTION STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total rows sent: {self.stats['total_rows_sent']}")
        logger.info(f"Total batches: {self.stats['total_batches']}")
        logger.info(f"Total bytes sent: {self.stats['total_bytes_sent']:,}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
        
        if self.stats['total_rows_sent'] > 0:
            rows_per_sec = self.stats['total_rows_sent'] / elapsed_time
            logger.info(f"Average throughput: {rows_per_sec:.2f} rows/sec")
        
        logger.info(f"Current offset token: {self.offset_token}")
        logger.info("=" * 60)


def main():
    """Main entry point for testing."""
    logger.info("Starting Thermal Streaming Client Test")
    
    try:
        # Initialize client
        client = SnowpipeStreamingClient('snowflake_config.json')
        
        # Discover ingest host
        client.discover_ingest_host()
        
        # Open channel
        client.open_channel()
        
        # Sample thermal data (simulating your sensor)
        sample_data = {
            "uuid": "thrml_lgu_20250721181107",
            "ipaddress": "192.168.1.175",
            "cputempf": 126,
            "runtime": 0,
            "host": "thermal",
            "hostname": "thermal",
            "macaddress": "e4:5f:01:7c:3f:34",
            "endtime": "1753121467.469562",
            "te": "0.0008215904235839844",
            "cpu": 6.0,
            "diskusage": "92358.2 MB",
            "memory": 10.0,
            "rowid": "20250721181107_aaa0541d-135c-4156-9ad4-5de877f84d5c",
            "systemtime": "07/21/2025 14:11:08",
            "ts": int(time.time()),
            "starttime": datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M:%S"),
            "datetimestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": 27.1031,
            "humidity": 48.05,
            "co2": 988.0,
            "equivalentco2ppm": 65535.0,
            "totalvocppb": 0.0,
            "pressure": 100770.23,
            "temperatureicp": 84.0
        }
        
        # Append rows
        rows = [sample_data]
        client.append_rows(rows)
        
        # Wait for commit
        client.wait_for_commit(client.offset_token, timeout=30)
        
        # Print statistics
        client.print_statistics()
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

