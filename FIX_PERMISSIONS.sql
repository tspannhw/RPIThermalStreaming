-- ======================================================================
-- FIX SNOWPIPE STREAMING PERMISSIONS
-- Run these commands in Snowflake to fix the ERR_ROLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED error
-- ======================================================================

-- Step 1: Switch to ACCOUNTADMIN role (or your admin role)
USE ROLE ACCOUNTADMIN;

-- Step 2: Verify the database and schema exist
USE DATABASE DEMO;
USE SCHEMA DEMO;

-- Step 3: Check if the table exists
SHOW TABLES LIKE 'THERMAL_SENSOR_DATA';

-- Step 4: If table doesn't exist, create it
CREATE TABLE IF NOT EXISTS THERMAL_SENSOR_DATA (
    raw_data VARIANT,
    uuid STRING,
    rowid STRING,
    hostname STRING,
    host STRING,
    ipaddress STRING,
    macaddress STRING,
    temperature FLOAT,
    humidity FLOAT,
    co2 FLOAT,
    equivalentco2ppm FLOAT,
    totalvocppb FLOAT,
    pressure FLOAT,
    cputempf INTEGER,
    temperatureicp FLOAT,
    cpu FLOAT,
    memory FLOAT,
    diskusage STRING,
    runtime INTEGER,
    ts BIGINT,
    systemtime STRING,
    starttime STRING,
    endtime STRING,
    datetimestamp TIMESTAMP_NTZ,
    te STRING
);

-- Step 5: Check if the pipe exists
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';

-- Step 6: If pipe doesn't exist, create it
-- Note: For Snowpipe Streaming, we create a pipe WITHOUT AUTO_INGEST
CREATE PIPE IF NOT EXISTS THERMAL_SENSOR_PIPE
  AS COPY INTO THERMAL_SENSOR_DATA
  FROM @~/staged
  FILE_FORMAT = (TYPE = JSON);

-- Step 7: Grant CRITICAL permissions to ACCOUNTADMIN role
-- This is the KEY permission needed for Snowpipe Streaming
GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;

-- Step 8: Grant other necessary permissions
GRANT USAGE ON DATABASE DEMO TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE ACCOUNTADMIN;
GRANT INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;
GRANT SELECT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;

-- Step 9: Verify the user exists and has the role
SHOW USERS LIKE 'THERMAL_STREAMING_USER';
SHOW GRANTS TO USER THERMAL_STREAMING_USER;

-- Step 10: Grant ACCOUNTADMIN role to user if not already granted
GRANT ROLE ACCOUNTADMIN TO USER THERMAL_STREAMING_USER;

-- Step 11: Set default role for the user
ALTER USER THERMAL_STREAMING_USER SET DEFAULT_ROLE = ACCOUNTADMIN;

-- Step 12: Verify all grants are in place
SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;
SHOW GRANTS TO ROLE ACCOUNTADMIN;

-- ======================================================================
-- VERIFICATION
-- ======================================================================

-- Run these to verify everything is set up correctly:

SELECT 'Database check' as test, COUNT(*) as exists FROM INFORMATION_SCHEMA.DATABASES WHERE DATABASE_NAME = 'DEMO';
SELECT 'Schema check' as test, COUNT(*) as exists FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'DEMO';
SELECT 'Table check' as test, COUNT(*) as exists FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'THERMAL_SENSOR_DATA';

-- Check pipe status
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';

-- ======================================================================
-- AFTER RUNNING THIS, TEST WITH:
-- ======================================================================
-- python test_connection.py
-- 
-- You should now see:
-- ✓ Ingest host discovered
-- ✓ Channel opened successfully
-- ======================================================================

