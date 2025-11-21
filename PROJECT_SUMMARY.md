# Project Summary: Raspberry Pi Thermal Streaming to Snowflake

## Overview

This project implements a complete **Snowpipe Streaming v2 REST API** application in Python for streaming thermal and environmental sensor data from a Raspberry Pi 4 to Snowflake in near real-time.

**Key Features:**
- ✅ Snowpipe Streaming v2 High-Performance Architecture (REST API)
- ✅ JWT-based key-pair authentication
- ✅ Support for real sensors (BME680, SGP30) and simulation mode
- ✅ Configurable batching and polling intervals
- ✅ Comprehensive logging and error handling
- ✅ Production-ready with graceful shutdown

## Project Structure

```
RPIThermalStreaming/
│
├── Core Application Files
│   ├── main.py                          # Main application entry point
│   ├── thermal_streaming_client.py      # Snowpipe Streaming REST API client
│   ├── snowflake_jwt_auth.py            # JWT authentication module
│   └── thermal_sensor.py                # Sensor data reader (real & simulated)
│
├── Configuration Files
│   ├── snowflake_config.json.template   # Snowflake configuration template
│   └── requirements.txt                 # Python dependencies
│
├── Setup Scripts
│   ├── setup_snowflake.sql              # Creates Snowflake objects
│   ├── generate_keys.sh                 # Generates RSA key pair
│   └── quickstart.sh                    # Automated setup script
│
├── Testing & Utilities
│   ├── test_connection.py               # Connection test script
│   └── example_queries.sql              # SQL query examples
│
├── Documentation
│   ├── README.md                        # Complete documentation
│   ├── QUICKSTART.md                    # Quick start guide
│   ├── PROJECT_SUMMARY.md               # This file
│   └── .gitignore                       # Git ignore rules
│
└── Generated Files (not in repo)
    ├── rsa_key.p8                       # Private key (DO NOT COMMIT)
    ├── rsa_key.pub                      # Public key
    ├── snowflake_config.json            # Your configuration
    └── thermal_streaming.log            # Application logs
```

## Components

### 1. Main Application (`main.py`)
The entry point that orchestrates the entire streaming process:
- Initializes sensor reader and streaming client
- Continuously reads sensor data in batches
- Streams data to Snowflake via REST API
- Handles graceful shutdown and statistics

**Command-line options:**
```bash
python main.py [OPTIONS]
  --config FILE         Configuration file path
  --batch-size N        Readings per batch (default: 10)
  --interval SECONDS    Seconds between batches (default: 5.0)
  --simulate            Use simulated sensor data
  --verbose             Enable debug logging
```

### 2. Streaming Client (`thermal_streaming_client.py`)
Implements the Snowpipe Streaming v2 REST API client:
- **Authentication:** Manages JWT tokens and scoped tokens
- **Host discovery:** Finds the correct ingest endpoint
- **Channel management:** Opens and manages streaming channels
- **Data ingestion:** Appends rows in NDJSON format
- **Status monitoring:** Checks commit status and offsets
- **Statistics tracking:** Monitors throughput and errors

**Key Methods:**
- `discover_ingest_host()` - Discovers the ingest endpoint
- `open_channel()` - Opens a streaming channel
- `append_rows(rows)` - Sends data to Snowflake
- `get_channel_status()` - Checks data commit status
- `wait_for_commit(offset)` - Waits for data persistence

### 3. JWT Authentication (`snowflake_jwt_auth.py`)
Handles Snowflake authentication using key-pair authentication:
- Loads private key from PEM file
- Generates JWT tokens with proper claims
- Exchanges JWT for scoped OAuth tokens
- Manages token expiration and refresh

**Authentication Flow:**
1. Load private RSA key
2. Generate JWT token signed with private key
3. Exchange JWT for scoped access token via OAuth endpoint
4. Use scoped token for API requests

### 4. Sensor Reader (`thermal_sensor.py`)
Reads thermal and environmental data:
- **Environmental sensors:** Temperature, humidity, pressure, CO2, VOC
- **System metrics:** CPU temp, CPU usage, memory, disk
- **Metadata:** Hostname, IP, MAC address, timestamps
- **Simulation mode:** Generates realistic test data

**Supported Hardware:**
- **SCD4X** (I2C @ 0x62) - CO2, Temperature, Humidity
- **ICP10125** (I2C @ 0x63) - Pressure, Temperature
- **SGP30** (I2C @ 0x58) - eCO2, TVOC
- System sensors - CPU, memory, disk

### 5. Configuration (`snowflake_config.json`)
JSON configuration file with Snowflake connection details:
```json
{
  "user": "THERMAL_STREAMING_USER",
  "account": "xy12345",
  "url": "https://xy12345.snowflakecomputing.com:443",
  "private_key_file": "rsa_key.p8",
  "role": "THERMAL_STREAMING_ROLE",
  "database": "DEMO",
  "schema": "DEMO",
  "pipe": "THERMAL_SENSOR_PIPE",
  "channel_name": "thermal_channel_001"
}
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. SENSOR READING (thermal_sensor.py)                               │
│    - Read from BME680/SGP30 sensors (or simulate)                   │
│    - Collect system metrics (CPU, memory)                           │
│    - Format as JSON with timestamps and metadata                    │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. BATCHING (main.py)                                               │
│    - Collect N readings (configurable batch size)                   │
│    - Add ingestion metadata                                         │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. AUTHENTICATION (snowflake_jwt_auth.py)                           │
│    - Generate JWT token with private key                            │
│    - Exchange for scoped OAuth token                                │
│    - Token valid for ~1 hour                                        │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. STREAMING (thermal_streaming_client.py)                          │
│    Step 1: Discover ingest host                                     │
│            POST /v2/streaming/control                               │
│    Step 2: Open channel                                             │
│            POST /v2/streaming/.../channels/{name}:open              │
│    Step 3: Append rows (NDJSON format)                              │
│            POST /v2/streaming/.../channels/{name}/rows              │
│    Step 4: Verify commit                                            │
│            POST /v2/streaming/.../:bulk-channel-status              │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. SNOWFLAKE INGESTION                                              │
│    - Data buffered in Snowpipe Streaming service                    │
│    - Transformed by PIPE object (COPY INTO syntax)                  │
│    - Committed to table (5-10 second latency)                       │
│    - Available for querying                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Snowflake Objects Created

### Table: THERMAL_SENSOR_DATA
Stores all thermal sensor readings with:
- **Raw data:** Original JSON payload
- **Environmental:** Temperature, humidity, CO2, pressure, VOC
- **System metrics:** CPU temp, CPU usage, memory, disk
- **Metadata:** Host info, IP address, MAC address
- **Timestamps:** Multiple timestamp formats
- **Ingestion metadata:** Ingestion timestamp

### Pipe: THERMAL_SENSOR_PIPE
Snowpipe Streaming v2 pipe that:
- Uses `DATA_SOURCE(TYPE => 'STREAMING')` for streaming data
- Extracts and transforms JSON fields using COPY INTO syntax
- Maps JSON fields to table columns
- Validates data types and formats

### User and Role
- **User:** `THERMAL_STREAMING_USER` - Service account with key-pair auth
- **Role:** `THERMAL_STREAMING_ROLE` - Minimal privileges (OPERATE, MONITOR on pipe)

## Setup Process

### Quick Setup (5 minutes)

```bash
# 1. Run automated setup
./quickstart.sh

# 2. Register public key in Snowflake
# (Copy ALTER USER command from generate_keys.sh output)

# 3. Run setup_snowflake.sql in Snowflake

# 4. Edit snowflake_config.json with your details

# 5. Test connection
python test_connection.py

# 6. Run application
python main.py --simulate
```

### Manual Setup

1. **Generate keys:** `./generate_keys.sh`
2. **Setup Snowflake:** Run `setup_snowflake.sql`
3. **Configure:** Edit `snowflake_config.json`
4. **Install deps:** `pip install -r requirements.txt`
5. **Test:** `python test_connection.py`
6. **Run:** `python main.py --simulate`

## Testing

### Test Connection Script (`test_connection.py`)
Comprehensive test suite that verifies:
1. ✓ Configuration file valid
2. ✓ Private key loads correctly
3. ✓ JWT token generation works
4. ✓ Scoped token obtained from Snowflake
5. ✓ Ingest host discovery succeeds
6. ✓ Channel opens successfully
7. ✓ Sensor data reads correctly

Run: `python test_connection.py`

## Monitoring

### Application Logs
- **Console output:** Real-time status
- **Log file:** `thermal_streaming.log`
- **Statistics:** Printed every 10 batches

### Snowflake Monitoring
```sql
-- Channel history
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWPIPE_STREAMING_CHANNEL_HISTORY
WHERE PIPE_NAME = 'THERMAL_SENSOR_PIPE';

-- Ingestion latency
SELECT 
    DATEDIFF('second', datetimestamp, ingestion_timestamp) as latency_sec
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY ingestion_timestamp DESC;
```

## Performance

### Expected Performance
- **Ingestion latency:** 5-10 seconds (end-to-end)
- **Throughput:** Limited by batch size and interval
- **API overhead:** ~100-200ms per REST call
- **Snowflake limit:** Up to 10 GB/s per table

### Tuning Options

**High frequency, low latency:**
```bash
python main.py --batch-size 5 --interval 2.0
```

**Balanced (default):**
```bash
python main.py --batch-size 10 --interval 5.0
```

**Lower frequency, lower cost:**
```bash
python main.py --batch-size 20 --interval 15.0
```

## Security

### Best Practices Implemented
1. ✅ Private key never committed (in `.gitignore`)
2. ✅ Key file permissions set to 600
3. ✅ Dedicated service account with minimal privileges
4. ✅ Key-pair authentication (no passwords)
5. ✅ Token expiration and refresh
6. ✅ HTTPS for all API calls

### Key Management
- **Generate keys:** `./generate_keys.sh`
- **Store securely:** Private key should be protected
- **Rotate regularly:** Generate new keys periodically
- **Never share:** Private key is secret

## Example Queries

See `example_queries.sql` for comprehensive query examples:
- Latest readings per host
- Hourly/daily aggregates
- Temperature trends and alerts
- CO2 monitoring
- System health metrics
- Ingestion monitoring
- Anomaly detection
- Correlation analysis

## Production Deployment

### Systemd Service (Auto-start)
```bash
# Create service file
sudo nano /etc/systemd/system/thermal-streaming.service

# Enable and start
sudo systemctl enable thermal-streaming
sudo systemctl start thermal-streaming
```

### Monitoring & Alerts
- Monitor application logs
- Set up Snowflake alerts for high temperature
- Track ingestion latency
- Monitor system resource usage

## Dependencies

### Python Packages
```
requests>=2.31.0      # HTTP client for REST API
PyJWT>=2.8.0          # JWT token generation
cryptography>=41.0.0  # RSA key handling
psutil>=5.9.0         # System metrics
```

### Optional (for real sensors)
```
adafruit-circuitpython-bme680  # Temperature/humidity/pressure sensor
adafruit-circuitpython-sgp30   # CO2/VOC sensor
```

## Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| "Private key file not found" | Keys not generated | Run `./generate_keys.sh` |
| "Failed to get scoped token" | Public key not registered | Run ALTER USER command in Snowflake |
| "Channel open failed" | Pipe doesn't exist | Run `setup_snowflake.sql` |
| "No ingest_host returned" | Network or config issue | Check account identifier |
| "Sensor libraries not found" | Missing dependencies | Use `--simulate` flag |

See `README.md` for detailed troubleshooting steps.

## References

### Documentation Used
1. [Snowpipe Streaming High-Performance Architecture](https://docs.snowflake.com/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview)
2. [Snowpipe Streaming REST API Tutorial](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-rest-tutorial)
3. [REST API Endpoints](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-rest-api)
4. [Key-Pair Authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
5. [Best Practices](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-best-practices)

### Hardware References
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
- [BME680 Sensor Guide](https://learn.adafruit.com/adafruit-bme680-humidity-temperature-barometic-pressure-voc-gas)
- [SGP30 Sensor Guide](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor)

## Next Steps

1. **Test the application:**
   ```bash
   python test_connection.py
   python main.py --simulate
   ```

2. **Connect real sensors** (optional):
   - Wire BME680 to I2C
   - Wire SGP30 to I2C
   - Enable I2C on Raspberry Pi
   - Remove `--simulate` flag

3. **Production deployment:**
   - Set up systemd service
   - Configure log rotation
   - Set up monitoring alerts
   - Create Snowflake dashboards

4. **Explore the data:**
   - Run queries from `example_queries.sql`
   - Create visualizations
   - Set up alerts for thresholds
   - Analyze trends over time

## Support

- **Full documentation:** `README.md`
- **Quick start:** `QUICKSTART.md`
- **Test suite:** `python test_connection.py`
- **Example queries:** `example_queries.sql`
- **Snowflake docs:** https://docs.snowflake.com/

---

**Project Status:** ✅ Complete and ready to use!

**License:** Provided as-is for demonstration purposes

**Last Updated:** November 2025

