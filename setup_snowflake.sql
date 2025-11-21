-- ============================================================================
-- Snowflake Setup Script for Raspberry Pi Thermal Sensor Streaming
-- ============================================================================
-- This script creates the necessary Snowflake objects for streaming 
-- thermal sensor data from Raspberry Pi using Snowpipe Streaming v2 REST API.
--
-- Prerequisites:
-- 1. Run with a highly-privileged role (e.g., ACCOUNTADMIN or USERADMIN)
-- 2. Have generated key pair using OpenSSL (see README.md)
-- ============================================================================

-- Step 1: Create a dedicated role and user
CREATE OR REPLACE USER THERMAL_STREAMING_USER;
CREATE ROLE IF NOT EXISTS THERMAL_STREAMING_ROLE;
GRANT ROLE THERMAL_STREAMING_ROLE TO USER THERMAL_STREAMING_USER;

-- Step 2: Set the public key for key-pair authentication
-- IMPORTANT: Replace 'YOUR_FORMATTED_PUBLIC_KEY' with the output from:
--   cat ./rsa_key.pub | grep -v KEY- | tr -d '\012'
ALTER USER THERMAL_STREAMING_USER SET RSA_PUBLIC_KEY='YOUR_FORMATTED_PUBLIC_KEY';

-- Step 3: Set the default role
ALTER USER THERMAL_STREAMING_USER SET DEFAULT_ROLE=THERMAL_STREAMING_ROLE;

-- Step 4: Switch to the new role
USE ROLE THERMAL_STREAMING_ROLE;

-- Create or use existing warehouse
-- CREATE WAREHOUSE IF NOT EXISTS STREAMING_WH 
--   WAREHOUSE_SIZE = 'XSMALL' 
--   AUTO_SUSPEND = 60 
--   AUTO_RESUME = TRUE;
-- USE WAREHOUSE STREAMING_WH;

-- Create database and schema (or use existing DEMO)
-- CREATE OR REPLACE DATABASE DEMO;
-- CREATE OR REPLACE SCHEMA DEMO;

USE DATABASE DEMO;
USE SCHEMA DEMO;

-- Step 5: Create target table for thermal sensor data
CREATE OR REPLACE TABLE THERMAL_SENSOR_DATA (
    -- Raw JSON data
    raw_data VARIANT,
    
    -- Identifiers and metadata
    uuid VARCHAR(100),
    rowid VARCHAR(100),
    hostname VARCHAR(100),
    host VARCHAR(100),
    ipaddress VARCHAR(50),
    macaddress VARCHAR(50),
    
    -- Environmental sensor readings
    temperature DECIMAL(10, 4),
    humidity DECIMAL(10, 2),
    co2 DECIMAL(10, 1),
    equivalentco2ppm DECIMAL(10, 1),
    totalvocppb DECIMAL(10, 1),
    pressure DECIMAL(10, 2),
    
    -- System metrics
    cputempf INTEGER,
    temperatureicp DECIMAL(10, 1),
    cpu DECIMAL(5, 1),
    memory DECIMAL(5, 1),
    diskusage VARCHAR(50),
    runtime INTEGER,
    
    -- Timestamps
    ts BIGINT,
    systemtime VARCHAR(50),
    starttime VARCHAR(50),
    endtime VARCHAR(50),
    datetimestamp TIMESTAMP_NTZ,
    te VARCHAR(50),
    
    -- Ingestion metadata
    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Add comments
COMMENT ON TABLE THERMAL_SENSOR_DATA IS 
'Real-time thermal and environmental sensor data from Raspberry Pi, ingested via Snowpipe Streaming v2 REST API';

COMMENT ON COLUMN THERMAL_SENSOR_DATA.temperature IS 'Temperature in Celsius from SCD4X sensor';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.humidity IS 'Relative humidity percentage from SCD4X sensor';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.co2 IS 'CO2 level in ppm from SCD4X sensor';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.equivalentco2ppm IS 'Equivalent CO2 in ppm from SGP30 sensor';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.totalvocppb IS 'Total VOC in ppb from SGP30 sensor';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.pressure IS 'Atmospheric pressure in Pascals from ICP10125 sensor';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.temperatureicp IS 'Temperature in Fahrenheit from ICP10125 sensor';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.cputempf IS 'CPU temperature in Fahrenheit';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.diskusage IS 'Disk free space in MB';

-- Step 6: Create PIPE object for streaming ingestion
-- This PIPE uses Snowpipe Streaming v2 high-performance architecture
-- Note: AUTO_INGEST is NOT used with Snowpipe Streaming (only for file-based Snowpipe)
CREATE OR REPLACE PIPE THERMAL_SENSOR_PIPE
COMMENT = 'Snowpipe Streaming v2 pipe for Raspberry Pi thermal sensor data'
AS 
COPY INTO THERMAL_SENSOR_DATA (
    raw_data,
    uuid,
    rowid,
    hostname,
    host,
    ipaddress,
    macaddress,
    temperature,
    humidity,
    co2,
    equivalentco2ppm,
    totalvocppb,
    pressure,
    cputempf,
    temperatureicp,
    cpu,
    memory,
    diskusage,
    runtime,
    ts,
    systemtime,
    starttime,
    endtime,
    datetimestamp,
    te
)
FROM (
    SELECT 
        $1 as raw_data,
        $1:uuid::VARCHAR as uuid,
        $1:rowid::VARCHAR as rowid,
        $1:hostname::VARCHAR as hostname,
        $1:host::VARCHAR as host,
        $1:ipaddress::VARCHAR as ipaddress,
        $1:macaddress::VARCHAR as macaddress,
        $1:temperature::DECIMAL(10,4) as temperature,
        $1:humidity::DECIMAL(10,2) as humidity,
        $1:co2::DECIMAL(10,1) as co2,
        $1:equivalentco2ppm::DECIMAL(10,1) as equivalentco2ppm,
        $1:totalvocppb::DECIMAL(10,1) as totalvocppb,
        $1:pressure::DECIMAL(10,2) as pressure,
        $1:cputempf::INTEGER as cputempf,
        $1:temperatureicp::DECIMAL(10,1) as temperatureicp,
        $1:cpu::DECIMAL(5,1) as cpu,
        $1:memory::DECIMAL(5,1) as memory,
        $1:diskusage::VARCHAR as diskusage,
        $1:runtime::INTEGER as runtime,
        $1:ts::BIGINT as ts,
        $1:systemtime::VARCHAR as systemtime,
        $1:starttime::VARCHAR as starttime,
        $1:endtime::VARCHAR as endtime,
        TO_TIMESTAMP_NTZ($1:datetimestamp) as datetimestamp,
        $1:te::VARCHAR as te
    FROM TABLE(DATA_SOURCE(TYPE => 'STREAMING'))
);

-- Step 7: Grant necessary privileges
GRANT USAGE ON DATABASE DEMO TO ROLE THERMAL_STREAMING_ROLE;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE THERMAL_STREAMING_ROLE;
GRANT SELECT, INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE THERMAL_STREAMING_ROLE;
GRANT OPERATE, MONITOR ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE THERMAL_STREAMING_ROLE;

-- Step 8 (Optional): Create authentication policy
CREATE OR REPLACE AUTHENTICATION POLICY thermal_streaming_auth_policy
    AUTHENTICATION_METHODS = ('KEYPAIR')
    CLIENT_TYPES = ('DRIVERS');

ALTER USER THERMAL_STREAMING_USER SET AUTHENTICATION POLICY thermal_streaming_auth_policy;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify the pipe was created
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE' IN SCHEMA DEMO.DEMO;

-- Describe the pipe
DESC PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE;

-- ============================================================================
-- Monitoring Queries (Run after data is flowing)
-- ============================================================================

-- Check row count
-- SELECT COUNT(*) FROM DEMO.DEMO.THERMAL_SENSOR_DATA;

-- View recent readings
-- SELECT * FROM DEMO.DEMO.THERMAL_SENSOR_DATA 
-- ORDER BY ingestion_timestamp DESC 
-- LIMIT 100;

-- View temperature trends
-- SELECT 
--     hostname,
--     datetimestamp,
--     temperature,
--     humidity,
--     co2,
--     cputempf
-- FROM DEMO.DEMO.THERMAL_SENSOR_DATA
-- ORDER BY datetimestamp DESC
-- LIMIT 50;

-- Check ingestion latency
-- SELECT 
--     hostname,
--     datetimestamp as sensor_time,
--     ingestion_timestamp,
--     DATEDIFF('second', datetimestamp, ingestion_timestamp) as latency_seconds
-- FROM DEMO.DEMO.THERMAL_SENSOR_DATA
-- ORDER BY ingestion_timestamp DESC
-- LIMIT 100;

-- Average temperature by hour
-- SELECT 
--     DATE_TRUNC('hour', datetimestamp) as hour,
--     hostname,
--     AVG(temperature) as avg_temp_c,
--     AVG(humidity) as avg_humidity,
--     AVG(co2) as avg_co2,
--     AVG(cputempf) as avg_cpu_temp_f,
--     COUNT(*) as reading_count
-- FROM DEMO.DEMO.THERMAL_SENSOR_DATA
-- GROUP BY 1, 2
-- ORDER BY 1 DESC;

-- High temperature alerts (>30°C)
-- SELECT 
--     hostname,
--     datetimestamp,
--     temperature,
--     cputempf
-- FROM DEMO.DEMO.THERMAL_SENSOR_DATA
-- WHERE temperature > 30
-- ORDER BY datetimestamp DESC;

-- System health overview
-- SELECT 
--     hostname,
--     MAX(datetimestamp) as last_reading,
--     AVG(temperature) as avg_temp,
--     MAX(temperature) as max_temp,
--     AVG(cpu) as avg_cpu_usage,
--     AVG(memory) as avg_memory_usage,
--     COUNT(*) as reading_count
-- FROM DEMO.DEMO.THERMAL_SENSOR_DATA
-- WHERE datetimestamp >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
-- GROUP BY hostname;

-- ============================================================================
-- Optional: Create views for easier querying
-- ============================================================================

-- CREATE OR REPLACE VIEW THERMAL_SENSOR_LATEST AS
-- SELECT 
--     hostname,
--     temperature,
--     humidity,
--     co2,
--     pressure,
--     cputempf,
--     cpu as cpu_usage_pct,
--     memory as memory_usage_pct,
--     datetimestamp,
--     ingestion_timestamp
-- FROM DEMO.DEMO.THERMAL_SENSOR_DATA
-- QUALIFY ROW_NUMBER() OVER (PARTITION BY hostname ORDER BY datetimestamp DESC) = 1;

-- CREATE OR REPLACE VIEW THERMAL_SENSOR_HOURLY_STATS AS
-- SELECT 
--     DATE_TRUNC('hour', datetimestamp) as hour,
--     hostname,
--     AVG(temperature) as avg_temperature_c,
--     MIN(temperature) as min_temperature_c,
--     MAX(temperature) as max_temperature_c,
--     AVG(humidity) as avg_humidity_pct,
--     AVG(co2) as avg_co2_ppm,
--     AVG(pressure) as avg_pressure_pa,
--     AVG(cpu) as avg_cpu_usage_pct,
--     AVG(memory) as avg_memory_usage_pct,
--     COUNT(*) as reading_count
-- FROM DEMO.DEMO.THERMAL_SENSOR_DATA
-- GROUP BY 1, 2;

-- ============================================================================
-- Cleanup (Use with caution!)
-- ============================================================================

-- To remove all objects (DESTRUCTIVE - USE WITH CAUTION):
-- DROP PIPE IF EXISTS DEMO.DEMO.THERMAL_SENSOR_PIPE;
-- DROP TABLE IF EXISTS DEMO.DEMO.THERMAL_SENSOR_DATA;
-- DROP AUTHENTICATION POLICY IF EXISTS thermal_streaming_auth_policy;
-- DROP USER IF EXISTS THERMAL_STREAMING_USER;
-- DROP ROLE IF EXISTS THERMAL_STREAMING_ROLE;

