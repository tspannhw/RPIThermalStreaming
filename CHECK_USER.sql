-- ==============================================================================
-- DIAGNOSTIC: Check THERMAL_STREAMING_USER
-- ==============================================================================
-- Run these commands in Snowflake to diagnose the issue
-- ==============================================================================

USE ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 1: Check if user exists
-- ==============================================================================

SHOW USERS LIKE 'THERMAL_STREAMING_USER';

-- If you see "No results", the user doesn't exist!

-- ==============================================================================
-- STEP 2: Check what roles the user has
-- ==============================================================================

SHOW GRANTS TO USER THERMAL_STREAMING_USER;

-- This will show all roles granted to the user

-- ==============================================================================
-- STEP 3: Check current role and user
-- ==============================================================================

SELECT CURRENT_USER();
SELECT CURRENT_ROLE();

-- ==============================================================================
-- STEP 4: Check pipe ownership and grants
-- ==============================================================================

USE DATABASE DEMO;
USE SCHEMA DEMO;

SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';

SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;

-- ==============================================================================
-- IF USER DOESN'T EXIST - CREATE IT:
-- ==============================================================================

-- Uncomment and run if user doesn't exist:

-- CREATE USER IF NOT EXISTS THERMAL_STREAMING_USER
--   PASSWORD = 'YourSecurePassword123!'
--   DEFAULT_ROLE = ACCOUNTADMIN
--   DEFAULT_WAREHOUSE = COMPUTE_WH;

-- GRANT ROLE ACCOUNTADMIN TO USER THERMAL_STREAMING_USER;

-- -- Enable PAT for user
-- ALTER USER THERMAL_STREAMING_USER 
--   SET PROGRAMMATIC_ACCESS_TOKEN 
--   ENABLED = TRUE 
--   EXPIRES_IN = 90;

-- -- IMPORTANT: Copy the PAT secret from the output!

-- ==============================================================================
-- IF USER EXISTS BUT DOESN'T HAVE ACCOUNTADMIN:
-- ==============================================================================

GRANT ROLE ACCOUNTADMIN TO USER THERMAL_STREAMING_USER;

-- ==============================================================================
-- GRANT OPERATE ON PIPE (CRITICAL!)
-- ==============================================================================

GRANT OPERATE ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;
GRANT INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;
GRANT USAGE ON DATABASE DEMO TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- VERIFY
-- ==============================================================================

SHOW GRANTS TO USER THERMAL_STREAMING_USER;
SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;

-- ==============================================================================
-- Expected output:
-- ==============================================================================
-- SHOW GRANTS TO USER should show:
--   ACCOUNTADMIN | ROLE | | USER | THERMAL_STREAMING_USER
--
-- SHOW GRANTS ON PIPE should show:
--   OPERATE | PIPE | THERMAL_SENSOR_PIPE | ROLE | ACCOUNTADMIN
-- ==============================================================================

