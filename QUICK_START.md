# Quick Start Guide

Get your Raspberry Pi thermal sensor data streaming to Snowflake in **5 minutes**.

## Prerequisites

- Python 3.8+
- Snowflake account with ACCOUNTADMIN access
- (Optional) Raspberry Pi 4 with sensors (or use simulation mode)

## Step 1: Clone and Install (1 min)

```bash
cd /path/to/your/project
pip install -r requirements.txt
```

## Step 2: Setup Snowflake (2 min)

Run this in your Snowflake SQL worksheet:

```sql
-- Create database, schema, table, and pipe
-- Copy from setup_snowflake.sql or run:
!source setup_snowflake.sql

-- Generate PAT token
ALTER USER THERMAL_STREAMING_USER 
  SET PROGRAMMATIC_ACCESS_TOKEN 
  ENABLED = TRUE 
  EXPIRES_IN = 90;

-- **COPY THE SECRET FROM OUTPUT** (you can't view it again!)

-- Grant permissions (CRITICAL!)
GRANT OPERATE ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;
GRANT INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;
```

## Step 3: Configure Application (1 min)

```bash
cp snowflake_config.json.template snowflake_config.json
nano snowflake_config.json
```

Update these fields:

```json
{
  "user": "THERMAL_STREAMING_USER",
  "account": "YOUR_ACCOUNT.YOUR_REGION",
  "role": "ACCOUNTADMIN",
  "database": "DEMO",
  "schema": "DEMO",
  "pipe": "THERMAL_SENSOR_PIPE",
  "channel_name": "TH_CHNL",
  "pat": "YOUR_PAT_TOKEN_HERE"
}
```

Find your account identifier:

```sql
-- In Snowflake, run:
SELECT CURRENT_ACCOUNT();
SELECT CURRENT_REGION();
-- Format: account_name.region (e.g., myaccount.us-east-1)
```

## Step 4: Test Connection (30 sec)

```bash
python test_connection.py
```

Expected output:

```
[OK] Configuration loaded
[OK] PAT validated
[OK] Ingest host discovered
[OK] Channel opened: TH_CHNL
[SUCCESS] ALL TESTS PASSED!
```

If you get `ERR_ROLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED`:
- **You forgot to grant OPERATE permission!**
- Run: `GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;`

## Step 5: Run Application (30 sec)

**Simulation mode (no hardware):**

```bash
python main.py --simulate --batch-size 5 --interval 3
```

**With real sensors:**

```bash
python main.py --batch-size 100 --interval 10
```

## Step 6: Verify Data in Snowflake

```sql
-- Check row count
SELECT COUNT(*) FROM DEMO.DEMO.THERMAL_SENSOR_DATA;

-- View latest readings
SELECT 
    hostname,
    datetimestamp,
    temperature,
    humidity,
    co2,
    cputempf
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY datetimestamp DESC
LIMIT 10;
```

## Done! 🎉

Your data is now streaming to Snowflake with **5-10 second latency**.

---

## Common Issues

### ❌ "ERR_ROLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED"

**Fix:** Run in Snowflake:

```sql
GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;
```

### ❌ "404 Not Found" for hostname endpoint

**Fix:** Check your account identifier format:

```sql
SELECT CURRENT_ACCOUNT(), CURRENT_REGION();
```

Update `snowflake_config.json` with: `account_name.region`

### ❌ "Sensor libraries not available"

**Fix:** Either:
1. Install sensors: `pip install python-scd4x icp10125 sgp30 smbus2`
2. Or use simulation: `python main.py --simulate`

### ❌ "Private key file not found"

**Fix:** You're using PAT authentication, so you **don't need keys**. Just make sure `pat` is in your config:

```json
{
  "pat": "YOUR_PAT_HERE"
}
```

---

## Next Steps

- **Production setup:** See `README.md` → Systemd Service
- **Performance tuning:** Adjust `--batch-size` and `--interval`
- **Security:** See `GENERATE_PAT.md` → PAT rotation
- **Monitoring:** See `README.md` → Snowflake Monitoring

---

## Architecture Overview

```
Raspberry Pi Sensors
        ↓
   (thermal_sensor.py)
        ↓
    main.py
        ↓
(thermal_streaming_client.py)
        ↓
  [REST API over HTTPS]
        ↓
Snowpipe Streaming v2
        ↓
  Snowflake Table
  (5-10 sec latency)
```

## Performance

- **Latency:** 5-10 seconds (end-to-end)
- **Throughput:** Up to 10 GB/s per table (Snowflake limit)
- **Cost:** Ingestion is free, only storage/query costs

## Support

- **Troubleshooting:** See `TROUBLESHOOTING.md`
- **Migration notes:** See `MIGRATION_TO_REST_API.md`
- **Authentication:** See `GENERATE_PAT.md`

---

**Ready to stream? Run:** `python main.py --simulate` 🚀

