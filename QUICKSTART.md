# Quick Start Guide

Get up and running with Raspberry Pi Thermal Streaming in 5 minutes!

## Prerequisites

- Raspberry Pi 4 (or any system with Python 3.9+)
- Snowflake account
- Internet connection

## Step 1: Run Setup Script

```bash
cd RPIThermalStreaming
./quickstart.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Generate RSA key pair
- Create configuration file template

## Step 2: Register Public Key in Snowflake

The `generate_keys.sh` script outputs an SQL command. Copy it and run in Snowflake:

```sql
ALTER USER THERMAL_STREAMING_USER SET RSA_PUBLIC_KEY='MIIBIj...';
```

## Step 3: Setup Snowflake Objects

Run the SQL script in Snowflake:

```bash
# In Snowflake web UI or CLI, run:
# setup_snowflake.sql
```

This creates:
- User: `THERMAL_STREAMING_USER`
- Role: `THERMAL_STREAMING_ROLE`  
- Table: `DEMO.DEMO.THERMAL_SENSOR_DATA`
- Pipe: `DEMO.DEMO.THERMAL_SENSOR_PIPE`

## Step 4: Configure Application

Edit `snowflake_config.json`:

```json
{
  "account": "xy12345",              ← Your Snowflake account ID
  "database": "DEMO",
  "schema": "DEMO",
  "pipe": "THERMAL_SENSOR_PIPE"
}
```

**Find your account ID:**
- Look at your Snowflake URL: `https://xy12345.snowflakecomputing.com`
- Account ID is `xy12345`

## Step 5: Test Connection

```bash
python test_connection.py
```

Expected output:
```
✓ Configuration loaded successfully
✓ Private key loaded successfully
✓ JWT token generated
✓ Scoped token obtained
✓ Ingest host discovered
✓ Channel opened successfully
```

## Step 6: Run Application

**Simulation mode (no sensors required):**

```bash
python main.py --simulate
```

**With real sensors:**

```bash
python main.py
```

You should see:

```
--- Batch 1 ---
Reading 10 sensor samples...
Sample reading: Temp=27.1°C, Humidity=48.1%, CO2=988ppm, CPU=6.0%
✓ Successfully streamed 10 readings
```

## Step 7: Query Data in Snowflake

```sql
-- Count rows
SELECT COUNT(*) FROM DEMO.DEMO.THERMAL_SENSOR_DATA;

-- View latest readings
SELECT 
    hostname,
    temperature,
    humidity,
    co2,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY datetimestamp DESC
LIMIT 10;
```

## Troubleshooting

### "Failed to get scoped token"

**Issue:** Public key not registered or mismatch

**Fix:**
1. Run `./generate_keys.sh` again
2. Copy the ALTER USER command
3. Run it in Snowflake

### "Channel open failed"

**Issue:** Pipe doesn't exist or no privileges

**Fix:**
1. Run `setup_snowflake.sql` in Snowflake
2. Verify pipe exists: `SHOW PIPES;`
3. Check privileges on the role

### "Configuration file not found"

**Fix:**
```bash
cp snowflake_config.json.template snowflake_config.json
# Edit with your details
```

## Command Line Options

```bash
# Custom batch size and interval
python main.py --batch-size 20 --interval 10.0 --simulate

# Verbose logging
python main.py --verbose --simulate

# Help
python main.py --help
```

## What's Next?

- **Check sensors:** Run `python check_sensors.py` to verify sensor connections
- **Production deployment:** See README.md for systemd service setup
- **Real sensors:** Connect SCD4X, ICP10125, and SGP30 sensors via I2C
- **Monitoring:** Create Snowflake dashboards with the data
- **Alerts:** Set up alerts for high temperature thresholds

## Getting Help

- **Full documentation:** See `README.md`
- **Snowflake docs:** https://docs.snowflake.com/
- **Test connection:** `python test_connection.py`

---

**Need more help?** Check the troubleshooting section in `README.md`

