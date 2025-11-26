-- ==============================================================================
-- GRANT PERMISSIONS FOR SNOWPIPE STREAMING
-- ==============================================================================
-- This script grants the necessary permissions for the thermal streaming app
-- to use the Snowpipe Streaming v2 REST API.
--
-- THE CRITICAL PERMISSION: OPERATE ON PIPE
-- Without this, you'll get: ERR_ROLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED
--
-- Run this script as ACCOUNTADMIN in Snowflake.
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE DEMO;
USE SCHEMA DEMO;

-- ==============================================================================
-- STEP 1: Verify Pipe Exists
-- ==============================================================================

SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';

-- If the pipe doesn't exist, you need to run setup_snowflake.sql first!

-- ==============================================================================
-- STEP 2: Grant OPERATE Privilege (REQUIRED for Snowpipe Streaming REST API)
-- ==============================================================================

GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;

-- This is THE critical permission. Without OPERATE privilege, the REST API
-- will return: ERR_ROLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED

-- ==============================================================================
-- STEP 3: Grant INSERT Privilege (Required for data ingestion)
-- ==============================================================================

GRANT INSERT ON TABLE THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 4: Grant MONITOR Privilege (Optional but recommended)
-- ==============================================================================

GRANT MONITOR ON PIPE THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;

-- This allows you to query SNOWPIPE_STREAMING_CHANNEL_HISTORY

-- ==============================================================================
-- STEP 5: Verify Permissions
-- ==============================================================================

-- Check pipe privileges
SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;

-- Check table privileges
SHOW GRANTS ON TABLE THERMAL_SENSOR_DATA;

-- Check user privileges
SHOW GRANTS TO USER THERMAL_STREAMING_USER;

-- ==============================================================================
-- VERIFICATION QUERIES
-- ==============================================================================

-- View pipe details
DESC PIPE THERMAL_SENSOR_PIPE;

-- Check if user can access the pipe
SELECT SYSTEM$PIPE_STATUS('THERMAL_SENSOR_PIPE');

-- ==============================================================================
-- EXPECTED RESULTS
-- ==============================================================================
-- After running these grants, you should see:
--   SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;
--   -> OPERATE | ACCOUNTADMIN
--
-- Now run: python test_connection.py
-- It should succeed and show: [OK] Channel opened: TH_CHNL
-- ==============================================================================

-- ==============================================================================
-- TROUBLESHOOTING
-- ==============================================================================

-- If you still get permission errors:

-- 1. Check if role is correct in config file
SELECT CURRENT_ROLE();  -- Should match role in snowflake_config.json

-- 2. Check if user has the role
SHOW GRANTS TO USER THERMAL_STREAMING_USER;

-- 3. Check if role has privileges on the pipe
SHOW GRANTS TO ROLE ACCOUNTADMIN;

-- 4. If using a custom role (not ACCOUNTADMIN), grant to that role:
-- GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE YOUR_CUSTOM_ROLE;
-- GRANT INSERT ON TABLE THERMAL_SENSOR_DATA TO ROLE YOUR_CUSTOM_ROLE;

-- ==============================================================================
-- ADDITIONAL PERMISSIONS FOR PRODUCTION
-- ==============================================================================

-- If you want to use a dedicated role (recommended for production):

-- Create dedicated role
CREATE ROLE IF NOT EXISTS THERMAL_STREAMING_ROLE;

-- Grant privileges
GRANT USAGE ON DATABASE DEMO TO ROLE THERMAL_STREAMING_ROLE;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE THERMAL_STREAMING_ROLE;
GRANT INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE THERMAL_STREAMING_ROLE;
GRANT OPERATE ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE THERMAL_STREAMING_ROLE;
GRANT MONITOR ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE THERMAL_STREAMING_ROLE;

-- Grant role to user
GRANT ROLE THERMAL_STREAMING_ROLE TO USER THERMAL_STREAMING_USER;

-- Set as default role for user
ALTER USER THERMAL_STREAMING_USER SET DEFAULT_ROLE = THERMAL_STREAMING_ROLE;

-- Update snowflake_config.json to use "role": "THERMAL_STREAMING_ROLE"

-- ==============================================================================

