# PRODUCTION MODE - Configuration Guide

## Overview

This application runs in **PRODUCTION MODE ONLY**, with the following strict requirements:

### ✅ PRODUCTION REQUIREMENTS

1. **Real Physical Sensors ONLY**
   - No simulation mode
   - Physical sensors must be connected and working
   - Application will fail if sensors are not available

2. **Snowpipe Streaming v2 REST API ONLY**
   - High-performance streaming via REST endpoints
   - NO direct INSERT statements
   - NO Snowflake Connector for batch inserts
   - NO COPY INTO or stage-based loading

### 🚫 WHAT IS NOT USED

- ❌ Simulated sensor data
- ❌ Direct SQL INSERT statements
- ❌ Snowflake Connector Python library for inserts
- ❌ Batch loading via COPY INTO
- ❌ Stage-based ingestion
- ❌ Snowpipe (classic) - Only Snowpipe Streaming v2

## Required Physical Sensors

The following I2C sensors must be connected to your Raspberry Pi:

| Sensor | Purpose | Required |
|--------|---------|----------|
| **SCD4X** | CO2, Temperature, Humidity | Yes (primary) |
| **ICP10125** | Atmospheric Pressure, Temperature | Yes (primary) |
| **SGP30** | eCO2, TVOC (Volatile Organic Compounds) | Recommended |

### Installation

```bash
pip3 install scd4x icp10125 sgp30
```

## Snowpipe Streaming Configuration

### What This Application Uses

The application **EXCLUSIVELY** uses these Snowpipe Streaming v2 REST API endpoints:

1. **Hostname Discovery**
   ```
   GET /v2/streaming/hostname
   ```
   Discovers the ingest host for your Snowflake account

2. **Channel Management**
   ```
   PUT /v2/streaming/databases/{db}/schemas/{schema}/pipes/{pipe}/channels/{channel}
   ```
   Opens a streaming channel

3. **Data Ingestion (High-Speed)**
   ```
   POST /v2/streaming/data/databases/{db}/schemas/{schema}/pipes/{pipe}/channels/{channel}/rows
   ```
   Streams data in NDJSON format over HTTP

4. **Status Monitoring**
   ```
   POST /v2/streaming/databases/{db}/schemas/{schema}/pipes/{pipe}:bulk-channel-status
   ```
   Checks channel commit status

### Authentication

Supported authentication methods:
- **PAT (Programmatic Access Token)** - Recommended for production
- **JWT (JSON Web Token)** - Key pair authentication

## Starting the Application

### Option 1: Production Startup Script (Recommended)

```bash
./start_production.sh
```

With options:
```bash
./start_production.sh --batch-size 20 --interval 10.0 --verbose
```

### Option 2: Direct Python

```bash
python3 main.py
```

With options:
```bash
python3 main.py --batch-size 10 --interval 5.0 --verbose
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config FILE` | Snowflake configuration file | `snowflake_config.json` |
| `--batch-size N` | Number of readings per batch | 10 |
| `--interval N` | Seconds between batches | 5.0 |
| `--verbose` | Enable detailed logging | Off |

**Note:** The `--simulate` flag has been **REMOVED** in production mode.

## Verification

### Pre-Flight Check

Before starting, run verification:

```bash
python3 quick_verify.py
```

This will verify:
- ✅ Snowpipe Streaming client is loaded
- ✅ Required methods exist (insert_rows, append_rows, etc.)
- ✅ Configuration file is valid

### Runtime Monitoring

The application logs to:
- **Console** (stdout)
- **File**: `thermal_streaming.log`

Watch logs:
```bash
tail -f thermal_streaming.log
```

## Production Checklist

Before deploying to production:

- [ ] Physical sensors connected and tested
- [ ] Sensor libraries installed (scd4x, icp10125, sgp30)
- [ ] `snowflake_config.json` configured with PAT or JWT
- [ ] Snowflake pipe created and configured
- [ ] Network connectivity to Snowflake verified
- [ ] Appropriate Snowflake permissions granted
- [ ] Log monitoring configured
- [ ] Application tested with real sensor data

## Troubleshooting

### Error: "Physical sensor libraries not available"

**Cause:** Sensor Python packages not installed

**Fix:**
```bash
pip3 install scd4x icp10125 sgp30
```

### Error: "No sensors initialized"

**Cause:** Sensors not connected or I2C not enabled

**Fix:**
1. Enable I2C on Raspberry Pi:
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   ```
2. Check sensor connections
3. Verify sensors with `i2cdetect -y 1`

### Error: "Failed to discover ingest host"

**Cause:** Network or authentication issue

**Fix:**
1. Check network connectivity
2. Verify Snowflake credentials in config
3. Ensure PAT/JWT token is valid

### Error: "'SnowpipeStreamingClient' object has no attribute 'insert_rows'"

**Cause:** Python cache with old code

**Fix:**
```bash
./start_production.sh
# Or manually:
find . -type d -name __pycache__ -exec rm -rf {} +
python3 main.py
```

## Performance Tuning

### Batch Size

- **Small batches (5-10)**: Lower latency, more frequent commits
- **Large batches (50-100)**: Higher throughput, less overhead

### Interval

- **Short (1-5s)**: Near real-time streaming
- **Long (30-60s)**: Reduced API calls, batch optimization

### Recommended Production Settings

```bash
./start_production.sh --batch-size 20 --interval 10.0
```

This provides a good balance of:
- 20 readings per batch
- 10 second intervals
- ~2 readings/second sustained throughput

## Architecture

```
┌─────────────────────┐
│  Physical Sensors   │
│  (I2C connected)    │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Thermal Sensor    │
│   Reader Module     │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│    Main Loop        │
│  (Batch readings)   │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ Snowpipe Streaming  │
│   Client (REST)     │
└──────────┬──────────┘
           │
           ↓ HTTPS/NDJSON
┌─────────────────────┐
│   Snowflake         │
│   Ingest Host       │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Snowflake Table   │
│  (Real-time data)   │
└─────────────────────┘
```

## Security

- **Authentication**: PAT or JWT tokens only (no username/password)
- **Transport**: HTTPS only (TLS 1.2+)
- **Credentials**: Stored in `snowflake_config.json` (should be secured)
- **Permissions**: Minimal required (OPERATE on pipe, INSERT on table)

## Compliance

This production configuration ensures:

✅ **No Simulation**: Only real sensor data  
✅ **High Performance**: Snowpipe Streaming v2 REST API only  
✅ **No Direct Inserts**: No SQL INSERT statements  
✅ **Proper Authentication**: PAT or JWT tokens  
✅ **Error Handling**: Fail-fast on missing sensors  
✅ **Logging**: Complete audit trail  

## Support

For issues or questions:
1. Check `thermal_streaming.log`
2. Review `TROUBLESHOOTING.md`
3. Verify configuration with `quick_verify.py`
4. Check Snowflake pipe status in Snowsight

