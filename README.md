# Raspberry Pi Thermal Sensor Streaming to Snowflake

A Python application that streams thermal and environmental sensor data from a Raspberry Pi 4 to Snowflake using the **Snowpipe Streaming v2 REST API** (high-performance architecture).

## Overview

This application continuously reads data from sensors connected to a Raspberry Pi and streams it in near real-time to Snowflake. It supports:

- ✅ **Snowpipe Streaming v2 REST API** - High-performance architecture
- ✅ **JWT-based authentication** - Secure key-pair authentication
- ✅ **Real sensor support** - BME680, SGP30 environmental sensors
- ✅ **Simulation mode** - Test without physical hardware
- ✅ **Automatic batching** - Configurable batch sizes and intervals
- ✅ **Graceful shutdown** - Ensures data commit before exit
- ✅ **Comprehensive logging** - Detailed logging to file and console

## Architecture

```
┌─────────────────────────────────────────────┐
│         Raspberry Pi 4                      │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Environmental Sensors              │    │
│  │  - BME680: Temp, Humidity, Pressure │    │
│  │  - SGP30: CO2, VOC                  │    │
│  │  - System: CPU, Memory, Disk        │    │
│  └────────────┬────────────────────────┘    │
│               │                             │
│  ┌────────────▼────────────────────────┐    │
│  │  Python Application                 │    │
│  │  - thermal_sensor.py                │    │
│  │  - thermal_streaming_client.py      │    │
│  │  - snowflake_jwt_auth.py            │    │
│  └────────────┬────────────────────────┘    │
└───────────────┼─────────────────────────────┘
                │ REST API (HTTPS)
                │ JWT Authentication
                ▼
┌───────────────────────────────────────────┐
│         Snowflake Cloud                   │
│                                           │
│  Snowpipe Streaming v2 (REST API)         │
│         ↓                                 │
│  THERMAL_SENSOR_PIPE                      │
│         ↓                                 │
│  THERMAL_SENSOR_DATA (Table)              │
│                                           │
│  Near real-time ingestion (5-10s latency) │
└───────────────────────────────────────────┘
```

## Features

### Sensor Data Collected

The application collects comprehensive environmental and system metrics:

**Environmental Sensors:**
- **SCD4X:** Temperature (°C), Humidity (%), CO2 levels (ppm)
- **ICP10125:** Atmospheric Pressure (Pa), Temperature (°C)
- **SGP30:** Equivalent CO2 (ppm), Total VOC (ppb)

**System Metrics:**
- CPU Temperature (°F and °C)
- CPU Usage (%)
- Memory Usage (%)
- Disk Usage (MB)

**Metadata:**
- UUID and Row ID
- Hostname and IP Address
- MAC Address
- Timestamps (multiple formats)

## Prerequisites

### Hardware
- **Raspberry Pi 4** (or Pi 3 Model B+)
- **Sensors (I2C connected):**
  - **SCD4X** - CO2, Temperature, Humidity sensor
  - **ICP10125** - Pressure and Temperature sensor
  - **SGP30** - eCO2 and TVOC sensor
- Internet connection

### Software
- **Python 3.9+**
- **Snowflake account** with appropriate privileges
- Network access to Snowflake

## Quick Start

### Step 1: Clone and Setup

```bash
# Clone or copy the project
cd RPIThermalStreaming

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Choose Authentication Method

This application supports two authentication methods:

**OPTION A: Programmatic Access Token (PAT) - Recommended - Easier**

Generate a PAT in Snowflake:
```sql
-- Generate PAT for user (valid 15 days by default)
ALTER USER THERMAL_STREAMING_USER 
  ADD PROGRAMMATIC ACCESS TOKEN 
  NAME = 'thermal_pat'
  EXPIRES_IN = 90;
```

**Copy the secret from the output immediately** - you cannot view it again!

Add the PAT to `snowflake_config.json` (see Step 4).

See [Snowflake PAT Documentation](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens) for details.

**OPTION B: JWT Key-Pair Authentication**

Generate RSA key pair:
```bash
chmod +x generate_keys.sh
./generate_keys.sh
```

This creates `rsa_key.p8` (private key) and displays the SQL command to register the public key.

**See [AUTHENTICATION.md](AUTHENTICATION.md) for detailed instructions.**

### Step 3: Setup Snowflake

1. Run the SQL script in Snowflake:

```bash
# Copy the ALTER USER command from generate_keys.sh output
# Then run setup_snowflake.sql in Snowflake
```

The script creates:
- User: `THERMAL_STREAMING_USER`
- Role: `THERMAL_STREAMING_ROLE`
- Database: `DEMO`
- Schema: `DEMO`
- Table: `THERMAL_SENSOR_DATA`
- Pipe: `THERMAL_SENSOR_PIPE`

2. Verify the pipe was created:

```sql
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE' IN SCHEMA DEMO.DEMO;
DESC PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE;
```

### Step 4: Configure Application

Create your configuration file from the template:

```bash
cp snowflake_config.json.template snowflake_config.json
```

Edit `snowflake_config.json`:

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

Replace `xy12345` with your Snowflake account identifier.

### Step 5: Check Your Sensors (Optional)

If you have physical sensors connected, verify they're working:

```bash
python check_sensors.py
```

This will detect and test all connected sensors.

### Step 6: Run the Application

**With Physical Sensors:**

```bash
python main.py
```

**Simulation Mode (no hardware required):**

```bash
python main.py --simulate
```

**Custom Configuration:**

```bash
python main.py \
  --config snowflake_config.json \
  --batch-size 20 \
  --interval 10.0 \
  --simulate
```

### Step 7: Verify Data in Snowflake

Query your data:

```sql
-- Check row count
SELECT COUNT(*) FROM DEMO.DEMO.THERMAL_SENSOR_DATA;

-- View recent readings
SELECT * FROM DEMO.DEMO.THERMAL_SENSOR_DATA 
ORDER BY ingestion_timestamp DESC 
LIMIT 100;

-- Temperature trends
SELECT 
    hostname,
    datetimestamp,
    temperature,
    humidity,
    co2,
    cputempf
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY datetimestamp DESC
LIMIT 50;
```

## Command Line Options

```
python main.py [OPTIONS]

Options:
  --config FILE       Path to Snowflake config (default: snowflake_config.json)
  --batch-size N      Readings per batch (default: 10)
  --interval SECONDS  Seconds between batches (default: 5.0)
  --simulate          Use simulated sensor data
  --verbose           Enable debug logging
  -h, --help          Show help message
```

## Project Structure

```
RPIThermalStreaming/
├── main.py                          # Main application entry point
├── thermal_streaming_client.py      # Snowpipe Streaming REST API client
├── snowflake_jwt_auth.py            # JWT authentication for Snowflake
├── thermal_sensor.py                # Sensor data reader (real & simulated)
├── requirements.txt                 # Python dependencies
├── setup_snowflake.sql              # Snowflake setup script
├── snowflake_config.json.template   # Configuration template
├── generate_keys.sh                 # Key pair generation script
├── .gitignore                       # Git ignore file
└── README.md                        # This file
```

## Configuration

### Batch Size and Interval

Adjust based on your needs:

- **High frequency, low latency:** `--batch-size 5 --interval 2.0`
- **Balanced (default):** `--batch-size 10 --interval 5.0`
- **Lower frequency:** `--batch-size 20 --interval 15.0`

### Sensor Configuration

The application automatically detects sensors. If not found, it falls back to simulation mode.

**Supported sensors:**
- **SCD4X** - CO2, Temperature, Humidity (I2C address: 0x62)
- **ICP10125** - Pressure, Temperature (I2C address: 0x63)
- **SGP30** - eCO2, TVOC (I2C address: 0x58)

**Enabling sensors:**
Uncomment the sensor libraries in `requirements.txt` and install:
```bash
pip install python-scd4x icp10125 sgp30 smbus2
```

## Monitoring

### Application Logs

Logs are written to:
- **Console** (stdout)
- **File:** `thermal_streaming.log`

Statistics are printed every 10 batches:

```
===== INGESTION STATISTICS =====
Total rows sent: 150
Total batches: 15
Total bytes sent: 45,234
Errors: 0
Elapsed time: 75.23 seconds
Average throughput: 1.99 rows/sec
Current offset token: 15
================================
```

### Snowflake Monitoring

Check channel status:

```sql
-- View channel history
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWPIPE_STREAMING_CHANNEL_HISTORY
WHERE PIPE_NAME = 'THERMAL_SENSOR_PIPE'
ORDER BY START_TIME DESC;

-- Check ingestion latency
SELECT 
    hostname,
    datetimestamp as sensor_time,
    ingestion_timestamp,
    DATEDIFF('second', datetimestamp, ingestion_timestamp) as latency_seconds
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY ingestion_timestamp DESC
LIMIT 100;
```

## Example Queries

### Latest Reading per Host

```sql
SELECT 
    hostname,
    temperature,
    humidity,
    co2,
    pressure,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
QUALIFY ROW_NUMBER() OVER (PARTITION BY hostname ORDER BY datetimestamp DESC) = 1;
```

### Hourly Averages

```sql
SELECT 
    DATE_TRUNC('hour', datetimestamp) as hour,
    hostname,
    AVG(temperature) as avg_temp_c,
    AVG(humidity) as avg_humidity,
    AVG(co2) as avg_co2,
    COUNT(*) as reading_count
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
GROUP BY 1, 2
ORDER BY 1 DESC;
```

### High Temperature Alerts

```sql
SELECT 
    hostname,
    datetimestamp,
    temperature,
    cputempf
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE temperature > 30
ORDER BY datetimestamp DESC;
```

## Troubleshooting

### Issue: "Private key file not found"

**Solution:** Run `./generate_keys.sh` to generate the key pair.

### Issue: "Failed to get scoped token"

**Solution:**
1. Verify the public key is registered in Snowflake
2. Check that user and account identifiers are correct
3. Ensure the private key matches the public key

### Issue: "No ingest_host returned"

**Solution:**
1. Verify Snowflake account identifier is correct
2. Check network connectivity to Snowflake
3. Ensure the pipe exists and is properly configured

### Issue: "Channel open failed"

**Solution:**
1. Verify database, schema, and pipe names in config
2. Check user has OPERATE privilege on the pipe
3. Review Snowflake error message in logs

### Issue: Sensor libraries not importing

**Solution:**
1. Install sensor libraries: `pip install python-scd4x icp10125 sgp30 smbus2`
2. Enable I2C on Raspberry Pi: `sudo raspi-config` → Interface Options → I2C
3. Verify sensors are connected: `i2cdetect -y 1` (should show 0x58, 0x62, 0x63)
4. Or use simulation mode: `python main.py --simulate`

## Performance Tuning

### For Higher Throughput

1. Increase batch size: `--batch-size 50`
2. Reduce interval: `--interval 2.0`
3. Monitor Snowflake costs (charged by throughput)

### For Lower Costs

1. Decrease batch frequency: `--interval 15.0`
2. Reduce batch size: `--batch-size 5`

### Expected Performance

- **Ingestion latency:** 5-10 seconds (end-to-end)
- **Throughput:** Up to 10 GB/s per table (Snowflake limit)
- **API overhead:** ~100-200ms per REST call

## Security Best Practices

1. **Never commit credentials:**
   - `rsa_key.p8` and `rsa_key.pub` are in `.gitignore`
   - `snowflake_config.json` is also ignored

2. **Secure private key:**
   ```bash
   chmod 600 rsa_key.p8
   ```

3. **Use dedicated service account:**
   - Create a dedicated user with minimal privileges
   - Only grant OPERATE and MONITOR on the specific pipe

4. **Rotate keys regularly:**
   - Snowflake supports key rotation
   - Generate new keys and update public key in Snowflake

5. **Monitor access:**
   ```sql
   SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
   WHERE USER_NAME = 'THERMAL_STREAMING_USER'
   ORDER BY EVENT_TIMESTAMP DESC;
   ```

## Systemd Service (Auto-start on Boot)

Create a systemd service file to run the application automatically:

```bash
sudo nano /etc/systemd/system/thermal-streaming.service
```

```ini
[Unit]
Description=Thermal Sensor Streaming to Snowflake
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RPIThermalStreaming
Environment="PATH=/home/pi/RPIThermalStreaming/venv/bin"
ExecStart=/home/pi/RPIThermalStreaming/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable thermal-streaming
sudo systemctl start thermal-streaming
sudo systemctl status thermal-streaming
```

View logs:

```bash
sudo journalctl -u thermal-streaming -f
```

## References

- [Snowpipe Streaming High-Performance Architecture](https://docs.snowflake.com/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview)
- [Snowpipe Streaming REST API Tutorial](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-rest-tutorial)
- [Snowpipe Streaming REST API Reference](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-rest-api)
- [Key-Pair Authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [SCD4X Sensor](https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensor-scd4x/)
- [ICP10125 Sensor](https://www.invensense.com/products/pressure/icp-10125/)
- [SGP30 Sensor](https://www.sensirion.com/en/environmental-sensors/gas-sensors/sgp30/)

## License

This project is provided as-is for demonstration purposes.

## Support

For issues with:
- **Snowflake:** [Snowflake Documentation](https://docs.snowflake.com/)
- **Raspberry Pi Sensors:** [Adafruit Learning System](https://learn.adafruit.com/)
- **This Application:** Check logs and troubleshooting section above

---

**Built with ❄️ Snowflake and 🥧 Raspberry Pi**

