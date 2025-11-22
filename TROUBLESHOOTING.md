# Troubleshooting Guide

## Error: ERR_ROLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED

This error occurs when trying to open a streaming channel. It means either:
1. The pipe doesn't exist
2. The user doesn't have permission to operate the pipe
3. The role specified doesn't have the necessary grants

### Steps to Fix:

1. **Verify the pipe exists:**
```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE DEMO;
USE SCHEMA DEMO;
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';
```

2. **If the pipe doesn't exist, create it:**
```sql
-- Run the setup_snowflake.sql script
-- Or manually create the pipe:
CREATE OR REPLACE PIPE THERMAL_SENSOR_PIPE
  AS COPY INTO THERMAL_SENSOR_DATA
  FROM @~/staged
  FILE_FORMAT = (TYPE = JSON);
```

3. **Grant necessary privileges to your role:**
```sql
-- Replace ACCOUNTADMIN with your role from snowflake_config.json
GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;
GRANT USAGE ON DATABASE DEMO TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE ACCOUNTADMIN;
GRANT INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;
```

4. **Verify your user has the role:**
```sql
SHOW GRANTS TO USER THERMAL_STREAMING_USER;
-- Should show ACCOUNTADMIN role granted to user
```

5. **If the user doesn't have the role, grant it:**
```sql
USE ROLE ACCOUNTADMIN;
GRANT ROLE ACCOUNTADMIN TO USER THERMAL_STREAMING_USER;
ALTER USER THERMAL_STREAMING_USER SET DEFAULT_ROLE = ACCOUNTADMIN;
```

## Error: 404 Not Found on /v2/streaming/hostname

The Snowpipe Streaming v2 REST API endpoint was updated:
- Old: `/v2/streaming/control`
- New: `/v2/streaming/hostname`

This has been fixed in the code. If you still see this error, update to the latest version.

## Error: 405 Method Not Allowed

The HTTP method may be incorrect for the endpoint:
- `/v2/streaming/hostname` uses GET
- `/v2/streaming/databases/.../channels/...:open` uses PUT
- `/v2/streaming/databases/.../channels/...:insert` uses POST

These have been corrected in the latest version.

## Snowpipe Streaming Not Available

Some Snowflake accounts may not have Snowpipe Streaming v2 enabled. Check with:

```sql
SELECT SYSTEM$GET_SNOWPIPE_STREAMING_STATUS();
```

If not available, you can use the direct insert method instead:
- Edit `main.py` to use `ThermalDirectInsertClient` instead of `SnowpipeStreamingClient`
- This uses standard SQL INSERT statements via the Snowflake Python Connector
- Works on all Snowflake accounts
- Slightly higher latency but more compatible

## PAT (Programmatic Access Token) Issues

### PAT Expired
PATs have an expiration date. Generate a new one:
1. Log into Snowflake UI
2. Click your username → My Profile
3. Scroll to "Programmatic Access Tokens"
4. Click "Generate New Token"
5. Copy the token
6. Update `snowflake_config.json`

### PAT Permissions
Make sure the PAT was created by a user with the necessary role and privileges.

## Connection Issues

### Account Identifier
Make sure your account identifier is correct in `snowflake_config.json`:
- Format: `ORGNAME-ACCOUNTNAME` (e.g., `SFSENORTHAMERICA-TSPANN-AWS1`)
- You can find this in Snowflake UI → Admin → Accounts

### Network/Firewall
If running behind a firewall or proxy, you may need to configure network settings:
```python
# Add to your code if needed
import os
os.environ['HTTP_PROXY'] = 'http://proxy:port'
os.environ['HTTPS_PROXY'] = 'http://proxy:port'
```

## Sensor Issues

Run the sensor check script:
```bash
python check_sensors.py
```

This will verify:
- I2C is enabled
- Sensors are detected
- Sensor readings are working

### Enable I2C on Raspberry Pi:
```bash
sudo raspi-config
# Navigate to: Interfacing Options → I2C → Enable
sudo reboot
```

### Check I2C devices:
```bash
sudo i2cdetect -y 1
```

Should show sensors at addresses:
- `0x62` - SCD4X (CO2/temp/humidity)
- `0x63` - ICP10125 (pressure/temp)
- `0x58` - SGP30 (eCO2/TVOC)

## Debug Mode

Run with verbose logging:
```bash
export LOG_LEVEL=DEBUG
python main.py --simulate
```

Or in Python:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Still Having Issues?

1. Check the Snowflake query history for errors
2. Review the application logs
3. Run `verify_snowflake_setup.sql` queries to check permissions
4. Try the `test_connection.py` script for detailed diagnostics
5. Use `--simulate` mode to test without real sensors

