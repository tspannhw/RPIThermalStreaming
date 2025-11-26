-- ==============================================================================
-- COMPLETE FIX: ERR_ROLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED
-- ==============================================================================
-- Run these commands in Snowflake as ACCOUNTADMIN
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE DEMO;
USE SCHEMA DEMO;

-- ==============================================================================
-- STEP 1: Verify the pipe exists
-- ==============================================================================

SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';

-- If you see "No results", the pipe doesn't exist. Run setup_snowflake.sql first!

-- ==============================================================================
-- STEP 2: Grant ACCOUNTADMIN role to user (if not already granted)
-- ==============================================================================

GRANT ROLE ACCOUNTADMIN TO USER THERMAL_STREAMING_USER;

-- ==============================================================================
-- STEP 3: Grant OPERATE privilege on pipe (CRITICAL!)
-- ==============================================================================

GRANT OPERATE ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 4: Grant INSERT privilege on table
-- ==============================================================================

GRANT INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 5: Grant USAGE on database and schema (required for access)
-- ==============================================================================

GRANT USAGE ON DATABASE DEMO TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 6: Verify all grants
-- ==============================================================================

-- Check pipe grants
SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;

-- Check table grants
SHOW GRANTS ON TABLE THERMAL_SENSOR_DATA;

-- Check user's roles
SHOW GRANTS TO USER THERMAL_STREAMING_USER;

-- ==============================================================================
-- EXPECTED OUTPUT:
-- ==============================================================================
-- SHOW GRANTS ON PIPE should include:
--   OPERATE | PIPE | THERMAL_SENSOR_PIPE | ROLE | ACCOUNTADMIN
--
-- SHOW GRANTS TO USER should include:
--   ACCOUNTADMIN | ROLE | | USER | THERMAL_STREAMING_USER
-- ==============================================================================

-- ==============================================================================
-- NOW RUN: python test_connection.py
-- ==============================================================================
