-- Check Snowpipe Streaming Availability
-- Run this in Snowflake to verify if Snowpipe Streaming v2 is available

-- 1. Check if THERMAL_SENSOR_PIPE exists
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE' IN SCHEMA DEMO.DEMO;

-- 2. Describe the pipe to see its definition
DESC PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE;

-- 3. Check pipe status
SELECT SYSTEM$PIPE_STATUS('DEMO.DEMO.THERMAL_SENSOR_PIPE');

-- 4. Check your Snowflake edition
SELECT CURRENT_VERSION();
SELECT CURRENT_REGION();
SELECT CURRENT_ACCOUNT();

-- 5. Check for Snowpipe Streaming features
SHOW PARAMETERS LIKE '%STREAMING%' IN ACCOUNT;

-- 6. Verify user has correct privileges
SHOW GRANTS TO ROLE ACCOUNTADMIN;

-- 7. Check if user can access the pipe
SHOW GRANTS ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE;

