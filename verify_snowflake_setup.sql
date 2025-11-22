-- Verify Snowflake Setup for Snowpipe Streaming
-- Run these queries in Snowflake to verify your setup

-- 1. Check if the role exists and is active
SELECT CURRENT_ROLE();
SHOW ROLES LIKE 'THERMAL_STREAMING_ROLE';

-- 2. Check if the user exists
SHOW USERS LIKE 'THERMAL_STREAMING_USER';

-- 3. Check if the database exists
SHOW DATABASES LIKE 'DEMO';

-- 4. Use the correct database and schema
USE ROLE THERMAL_STREAMING_ROLE;
USE DATABASE DEMO;
USE SCHEMA DEMO;

-- 5. Check if the table exists
SHOW TABLES LIKE 'THERMAL_SENSOR_DATA';

-- 6. Check if the pipe exists
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';

-- 7. Describe the pipe to see its configuration
DESCRIBE PIPE THERMAL_SENSOR_PIPE;

-- 8. Check grants on the pipe
SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;

-- 9. Check what privileges the role has
SHOW GRANTS TO ROLE THERMAL_STREAMING_ROLE;

-- 10. Check what roles the user has
SHOW GRANTS TO USER THERMAL_STREAMING_USER;

-- 11. Verify the user can operate the pipe
-- The user needs OPERATE privilege on the pipe
GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE THERMAL_STREAMING_ROLE;

-- 12. Also ensure the role has necessary database and schema usage
GRANT USAGE ON DATABASE DEMO TO ROLE THERMAL_STREAMING_ROLE;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE THERMAL_STREAMING_ROLE;
GRANT INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE THERMAL_STREAMING_ROLE;

-- 13. Verify the role is the default for the user
ALTER USER THERMAL_STREAMING_USER SET DEFAULT_ROLE = THERMAL_STREAMING_ROLE;

-- 14. Check if Snowpipe Streaming is enabled
-- Note: This feature may need to be enabled by Snowflake support
SELECT SYSTEM$GET_SNOWPIPE_STREAMING_STATUS();

