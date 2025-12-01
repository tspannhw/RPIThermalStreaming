# 🚀 Production Mode - Quick Start

## Status: ✅ PRODUCTION MODE ENFORCED

Your application is now configured for **PRODUCTION MODE ONLY**:

- ✅ **Real physical sensors REQUIRED** - No simulation fallback
- ✅ **Snowpipe Streaming v2 REST API ONLY** - No direct inserts
- ✅ **Fail-fast error handling** - Clear errors when requirements not met

---

## Quick Start (3 Steps)

### Step 1: Verify Configuration

```bash
python3 quick_verify.py
```

Expected output:
```
[SUCCESS] All checks passed!
PRODUCTION MODE READY
```

### Step 2: Start Application

```bash
./start_production.sh
```

Or with custom settings:
```bash
./start_production.sh --batch-size 20 --interval 10.0 --verbose
```

### Step 3: Monitor Logs

```bash
tail -f thermal_streaming.log
```

---

## ⚠️ IMPORTANT CHANGES

### What's Different Now

| Before | After (Production) |
|--------|-------------------|
| `python main.py --simulate` | ❌ **REMOVED** - No simulation allowed |
| Falls back to simulation | ❌ **FAILS FAST** - Clear error message |
| Can run without sensors | ❌ **REQUIRES SENSORS** - Must be connected |

### What Stays the Same

- ✅ Snowpipe Streaming v2 REST API (always was, now enforced)
- ✅ Authentication via PAT or JWT
- ✅ Real-time streaming to Snowflake
- ✅ NDJSON data format

---

## Required Hardware

### Physical Sensors (Must be connected)

- **SCD4X** - CO2, Temperature, Humidity
- **ICP10125** - Atmospheric Pressure, Temperature  
- **SGP30** - eCO2, TVOC (Recommended)

### Installation

```bash
pip3 install scd4x icp10125 sgp30
```

---

## Troubleshooting

### Error: "Physical sensor libraries not available"

```bash
pip3 install scd4x icp10125 sgp30
```

### Error: "No sensors initialized"

1. Enable I2C: `sudo raspi-config` → Interface Options → I2C
2. Check connections: `i2cdetect -y 1`
3. Test sensors: `python3 thermal_sensor.py`

### Error: "'SnowpipeStreamingClient' object has no attribute 'insert_rows'"

```bash
./start_production.sh  # Automatically clears cache
```

---

## Files You Need

| File | Purpose | Status |
|------|---------|--------|
| `snowflake_config.json` | Snowflake credentials | **REQUIRED** |
| `main.py` | Main application | Production mode ✅ |
| `thermal_sensor.py` | Sensor reader | Production mode ✅ |
| `thermal_streaming_client.py` | Snowpipe client | Production mode ✅ |
| `start_production.sh` | Startup script | **RECOMMENDED** |
| `quick_verify.py` | Pre-flight check | **USE BEFORE START** |

---

## Command Reference

### Start Application
```bash
# Recommended (with validation)
./start_production.sh

# Direct
python3 main.py

# With options
./start_production.sh --batch-size 20 --interval 10.0 --verbose
```

### Verify Setup
```bash
# Quick verification
python3 quick_verify.py

# Full verification with startup
python3 verify_and_run.py
```

### Test Components
```bash
# Test sensors
python3 thermal_sensor.py

# Test Snowflake connection
python3 test_connection.py

# Check I2C devices
i2cdetect -y 1
```

---

## Performance Settings

### Low Latency (Near Real-Time)
```bash
./start_production.sh --batch-size 5 --interval 1.0
```

### Balanced (Recommended)
```bash
./start_production.sh --batch-size 20 --interval 10.0
```

### High Throughput
```bash
./start_production.sh --batch-size 50 --interval 30.0
```

---

## Architecture

```
┌──────────────────┐
│ Physical Sensors │  ← SCD4X, ICP10125, SGP30
│   (I2C Bus)      │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Thermal Sensor  │  ← Production Mode (require_real_sensors=True)
│     Reader       │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ Main Application │  ← No --simulate flag
│ (Production Mode)│
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│   Snowpipe       │  ← REST API ONLY (no direct inserts)
│ Streaming Client │
└────────┬─────────┘
         │
         ↓ HTTPS/NDJSON
┌──────────────────┐
│    Snowflake     │
│   Ingest Host    │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Snowflake Table │  ← Real-time data
└──────────────────┘
```

---

## Validation Checklist

Before production deployment:

- [ ] Run `python3 quick_verify.py` - passes all checks
- [ ] Physical sensors connected and detected
- [ ] `snowflake_config.json` configured with PAT or JWT
- [ ] Snowflake pipe created and accessible
- [ ] Network connectivity to Snowflake verified
- [ ] Test run with `./start_production.sh --verbose`
- [ ] Log monitoring configured
- [ ] No simulation mode in any logs

---

## Documentation

| Document | Description |
|----------|-------------|
| `PRODUCTION_MODE.md` | Complete production guide |
| `PRODUCTION_CHANGES.md` | Detailed change log |
| `README_PRODUCTION.md` | This quick start guide |
| `TROUBLESHOOTING.md` | Troubleshooting guide |

---

## Support Commands

```bash
# View logs
tail -f thermal_streaming.log

# Check running processes
ps aux | grep main.py

# Stop application
pkill -f main.py

# Clear cache and restart
./start_production.sh

# Full verification
python3 quick_verify.py && python3 test_connection.py
```

---

## Key Points

1. **No Simulation** - Application will fail if sensors unavailable
2. **REST API Only** - No direct database inserts ever
3. **Fail Fast** - Clear error messages for missing requirements
4. **Production Ready** - Enforced best practices
5. **Well Documented** - Complete guides available

---

## Success Indicators

When running correctly, you should see:

```
======================================================================
PRODUCTION MODE: Real Sensors + Snowpipe Streaming REST API ONLY
======================================================================
PRODUCTION MODE: Real sensors required and enforced
Physical sensors initialized successfully
[OK] Sensor verification passed - physical sensors available
SNOWPIPE STREAMING CLIENT - PRODUCTION MODE
Using ONLY Snowpipe Streaming v2 REST API
NO direct inserts - HIGH-PERFORMANCE STREAMING ONLY
[OK] Channel opened successfully
Starting data collection and streaming...
```

---

## Questions?

1. Check logs: `thermal_streaming.log`
2. Run verification: `python3 quick_verify.py`
3. Review docs: `PRODUCTION_MODE.md`
4. Test connection: `python3 test_connection.py`

---

**🎯 Ready for Production!**

Your application is now configured to run in production mode with real sensors and Snowpipe Streaming v2 REST API only.

