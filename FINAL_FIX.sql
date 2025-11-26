-- ==============================================================================
-- FINAL FIX FOR ERR_ROLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED
-- ==============================================================================
-- COPY THIS ENTIRE FILE INTO SNOWFLAKE AND RUN IT LINE BY LINE
-- ==============================================================================

-- IMPORTANT: You must be logged in as a user with ACCOUNTADMIN privileges
-- Switch to ACCOUNTADMIN role first
USE ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 1: Create user if it doesn't exist
-- ==============================================================================

CREATE USER IF NOT EXISTS THERMAL_STREAMING_USER
  PASSWORD = 'TempPassword123!'  -- You can change this
  DEFAULT_ROLE = ACCOUNTADMIN
  DEFAULT_WAREHOUSE = COMPUTE_WH
  MUST_CHANGE_PASSWORD = FALSE;

-- ==============================================================================
-- STEP 2: Grant ACCOUNTADMIN role to the user
-- ==============================================================================

GRANT ROLE ACCOUNTADMIN TO USER THERMAL_STREAMING_USER;

-- ==============================================================================
-- STEP 3: Enable PAT for the user (if not already enabled)
-- ==============================================================================

ALTER USER THERMAL_STREAMING_USER 
  SET PROGRAMMATIC_ACCESS_TOKEN 
  ENABLED = TRUE 
  EXPIRES_IN = 90;

-- COPY THE PAT SECRET FROM THE OUTPUT ABOVE!
-- Update snowflake_config.json with the new PAT if it changed

-- ==============================================================================
-- STEP 4: Set up database, schema, and table
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS DEMO;
CREATE SCHEMA IF NOT EXISTS DEMO.DEMO;

USE DATABASE DEMO;
USE SCHEMA DEMO;

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
    te STRING,
    ingestion_timestamp TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ==============================================================================
-- STEP 5: Create the pipe
-- ==============================================================================

CREATE OR REPLACE PIPE THERMAL_SENSOR_PIPE
  AS COPY INTO THERMAL_SENSOR_DATA
  FROM (
    SELECT 
      $1 as raw_data,
      $1:uuid::STRING as uuid,
      $1:rowid::STRING as rowid,
      $1:hostname::STRING as hostname,
      $1:host::STRING as host,
      $1:ipaddress::STRING as ipaddress,
      $1:macaddress::STRING as macaddress,
      $1:temperature::FLOAT as temperature,
      $1:humidity::FLOAT as humidity,
      $1:co2::FLOAT as co2,
      $1:equivalentco2ppm::FLOAT as equivalentco2ppm,
      $1:totalvocppb::FLOAT as totalvocppb,
      $1:pressure::FLOAT as pressure,
      $1:cputempf::INTEGER as cputempf,
      $1:temperatureicp::FLOAT as temperatureicp,
      $1:cpu::FLOAT as cpu,
      $1:memory::FLOAT as memory,
      $1:diskusage::STRING as diskusage,
      $1:runtime::INTEGER as runtime,
      $1:ts::BIGINT as ts,
      $1:systemtime::STRING as systemtime,
      $1:starttime::STRING as starttime,
      $1:endtime::STRING as endtime,
      $1:datetimestamp::TIMESTAMP_NTZ as datetimestamp,
      $1:te::STRING as te
  )
  FILE_FORMAT = (TYPE = JSON);

-- ==============================================================================
-- STEP 6: Grant ALL necessary privileges on database and schema
-- ==============================================================================

GRANT USAGE ON DATABASE DEMO TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 7: Grant privileges on table
-- ==============================================================================

GRANT INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;
GRANT SELECT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 8: Grant OPERATE on pipe (THIS IS THE CRITICAL ONE!)
-- ==============================================================================

GRANT OPERATE ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 9: Grant MONITOR privilege (optional but helpful)
-- ==============================================================================

GRANT MONITOR ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 10: Verify everything is set up correctly
-- ==============================================================================

-- Should show the pipe
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';

-- Should show OPERATE privilege
SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;

-- Should show ACCOUNTADMIN role granted to user
SHOW GRANTS TO USER THERMAL_STREAMING_USER;

-- Should show table
SHOW TABLES LIKE 'THERMAL_SENSOR_DATA';

-- ==============================================================================
-- EXPECTED OUTPUT FROM SHOW GRANTS ON PIPE:
-- ==============================================================================
-- You MUST see this line:
--   privilege: OPERATE
--   granted_on: PIPE
--   name: THERMAL_SENSOR_PIPE
--   granted_to: ROLE
--   grantee_name: ACCOUNTADMIN
--
-- If you don't see "OPERATE" privilege, the grants didn't work!
-- ==============================================================================

-- ==============================================================================
-- TROUBLESHOOTING: If grants still don't work
-- ==============================================================================

-- Try granting to PUBLIC role as well (not recommended for production)
-- GRANT OPERATE ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE PUBLIC;

-- Or check if there are ownership issues
SELECT * FROM TABLE(INFORMATION_SCHEMA.OBJECT_PRIVILEGES(
  'DEMO.DEMO.THERMAL_SENSOR_PIPE'
));

-- ==============================================================================
-- AFTER RUNNING THIS, TEST WITH:
-- ==============================================================================
-- python test_connection.py
-- ==============================================================================

