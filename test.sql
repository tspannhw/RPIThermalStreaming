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
COMMENT ON COLUMN THERMAL_SENSOR_DATA.temperatureicp IS 'Temperature in Celsius from ICP10125 sensor';
COMMENT ON COLUMN THERMAL_SENSOR_DATA.cputempf IS 'CPU temperature in Fahrenheit';

GRANT ROLE ACCOUNTADMIN TO USER THERMAL_STREAMING_USER;

-- Step 6: Create PIPE object for streaming ingestion
-- This PIPE uses Snowpipe Streaming v2 high-performance architecture
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


SELECT  PARSE_JSON('{"uuid": "thrml_the_20251122030001", "ipaddress": "192.168.1.175", "cputempf": 140, "runtime": 3, "host": "thermal", "hostname": "thermal", "macaddress": "e4:5f:01:7c:3f:34", "endtime": "1763780403.801484", "te": "2.5594329833984375", "cpu": 28.5, "diskusage": "91379.3 MB", "memory": 13.5, "rowid": "20251122030001_d0814b01-95be-45e2-b545-7e440f353495", "systemtime": "11/22/2025 03:00:01", "ts": 1763780401, "starttime": "11/22/2025 03:00:01", "datetimestamp": "2025-11-22T03:00:01.242053+00:00", "temperature": 31.8776, "humidity": 23.89, "co2": 898, "equivalentco2ppm": 65535.0, "totalvocppb": 0.0, "pressure": 100929.72, "temperatureicp": 89.28}') ;


-- Step 7: Grant necessary privileges
GRANT USAGE ON DATABASE DEMO TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA DEMO.DEMO TO ROLE ACCOUNTADMIN;
GRANT SELECT, INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;
GRANT OPERATE, MONITOR ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE SYSADMIN;
GRANT OPERATE, MONITOR ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE SYSADMIN;

-- This is THE critical permission for Snowpipe Streaming
GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;
GRANT INSERT ON TABLE THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;

GRANT SELECT, INSERT ON TABLE DEMO.DEMO.THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;
GRANT OPERATE, MONITOR ON PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;



-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify the pipe was created
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE' IN SCHEMA DEMO.DEMO;

-- Describe the pipe
DESC PIPE DEMO.DEMO.THERMAL_SENSOR_PIPE;

SELECT
  PIPE_ID,
  CHANNEL_ID,
  STREAM_OFFSET,
  LAG(STREAM_OFFSET) OVER (
    PARTITION BY PIPE_ID, CHANNEL_ID
    ORDER BY STREAM_OFFSET
  ) AS previous_offset,
  (LAG(STREAM_OFFSET) OVER (
    PARTITION BY PIPE_ID, CHANNEL_ID
    ORDER BY STREAM_OFFSET
  ) + 1) AS expected_next
FROM DEMO.DEMO.THERMAL_SENSOR_PIPE
QUALIFY STREAM_OFFSET != previous_offset + 1;


-- ============================================================================
-- Monitoring Queries (Run after data is flowing)
-- ============================================================================

-- Check row count
SELECT COUNT(*) FROM DEMO.DEMO.THERMAL_SENSOR_DATA;

-- View recent readings
 SELECT * FROM DEMO.DEMO.THERMAL_SENSOR_DATA 
 ORDER BY ingestion_timestamp DESC 
 LIMIT 100;

-- View temperature trends
 SELECT 
     hostname,
     datetimestamp,
     temperature,
     humidity,
     co2,
     cputempf
 FROM DEMO.DEMO.THERMAL_SENSOR_DATA
 ORDER BY datetimestamp DESC
LIMIT 50;

-- Check ingestion latency
 SELECT 
     hostname,
     datetimestamp as sensor_time,
     ingestion_timestamp,
     DATEDIFF('second', datetimestamp, ingestion_timestamp) as latency_seconds
 FROM DEMO.DEMO.THERMAL_SENSOR_DATA
 ORDER BY ingestion_timestamp DESC
 LIMIT 100;

-- Average temperature by hour
 SELECT 
     DATE_TRUNC('hour', datetimestamp) as hour,
     hostname,
     AVG(temperature) as avg_temp_c,
     AVG(humidity) as avg_humidity,
     AVG(co2) as avg_co2,
     AVG(cputempf) as avg_cpu_temp_f,
     COUNT(*) as reading_count
 FROM DEMO.DEMO.THERMAL_SENSOR_DATA
 GROUP BY 1, 2
 ORDER BY 1 DESC;

-- High temperature alerts (>30°C)
 SELECT 
     hostname,
     datetimestamp,
     temperature,
     cputempf
 FROM DEMO.DEMO.THERMAL_SENSOR_DATA
 WHERE temperature > 30
 ORDER BY datetimestamp DESC;

-- System health overview
 SELECT 
     hostname,
     MAX(datetimestamp) as last_reading,
     AVG(temperature) as avg_temp,
     MAX(temperature) as max_temp,
     AVG(cpu) as avg_cpu_usage,
     AVG(memory) as avg_memory_usage,
     COUNT(*) as reading_count
 FROM DEMO.DEMO.THERMAL_SENSOR_DATA
 WHERE datetimestamp >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
 GROUP BY hostname;

-- ============================================================================
-- Optional: Create views for easier querying
-- ============================================================================

 CREATE OR REPLACE VIEW THERMAL_SENSOR_LATEST AS
 SELECT 
     hostname,
     temperature,
     humidity,
     co2,
     pressure,
     cputempf,
     cpu as cpu_usage_pct,
     memory as memory_usage_pct,
     datetimestamp,
     ingestion_timestamp
 FROM DEMO.DEMO.THERMAL_SENSOR_DATA
 QUALIFY ROW_NUMBER() OVER (PARTITION BY hostname ORDER BY datetimestamp DESC) = 1;

 CREATE OR REPLACE VIEW THERMAL_SENSOR_HOURLY_STATS AS
 SELECT 
     DATE_TRUNC('hour', datetimestamp) as hour,
     hostname,
     AVG(temperature) as avg_temperature_c,
     MIN(temperature) as min_temperature_c,
     MAX(temperature) as max_temperature_c,
     AVG(humidity) as avg_humidity_pct,
     AVG(co2) as avg_co2_ppm,
     AVG(pressure) as avg_pressure_pa,
     AVG(cpu) as avg_cpu_usage_pct,
     AVG(memory) as avg_memory_usage_pct,
     COUNT(*) as reading_count
 FROM DEMO.DEMO.THERMAL_SENSOR_DATA
 GROUP BY 1, 2;

-- ============================================================================
-- Cleanup (Use with caution!)
-- ============================================================================

-- To remove all objects (DESTRUCTIVE - USE WITH CAUTION):
-- DROP PIPE IF EXISTS DEMO.DEMO.THERMAL_SENSOR_PIPE;
-- DROP TABLE IF EXISTS DEMO.DEMO.THERMAL_SENSOR_DATA;
-- DROP AUTHENTICATION POLICY IF EXISTS thermal_streaming_auth_policy;
-- DROP USER IF EXISTS THERMAL_STREAMING_USER;
-- DROP ROLE IF EXISTS THERMAL_STREAMING_ROLE;


-- ============================================================================
-- Example Queries for Raspberry Pi Thermal Sensor Data
-- ============================================================================
-- This file contains useful SQL queries for analyzing thermal sensor data
-- streamed from Raspberry Pi devices.
-- ============================================================================

-- ============================================================================
-- Basic Queries
-- ============================================================================

-- Count total readings
SELECT COUNT(*) as total_readings
FROM DEMO.DEMO.THERMAL_SENSOR_DATA;

-- View latest 100 readings
SELECT * 
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY datetimestamp DESC
LIMIT 100;

-- Check data freshness (latest reading per host)
SELECT 
    hostname,
    MAX(datetimestamp) as last_reading,
    DATEDIFF('minute', MAX(datetimestamp), CURRENT_TIMESTAMP()) as minutes_ago
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
GROUP BY hostname
ORDER BY last_reading DESC;

-- ============================================================================
-- Temperature Analysis
-- ============================================================================

-- Current temperature by host
SELECT 
    hostname,
    temperature as temp_celsius,
    humidity,
    co2,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
QUALIFY ROW_NUMBER() OVER (PARTITION BY hostname ORDER BY datetimestamp DESC) = 1;

-- Temperature trends (last 24 hours)
SELECT 
    DATE_TRUNC('hour', datetimestamp) as hour,
    hostname,
    AVG(temperature) as avg_temp_c,
    MIN(temperature) as min_temp_c,
    MAX(temperature) as max_temp_c,
    STDDEV(temperature) as temp_stddev,
    COUNT(*) as reading_count
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE datetimestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- High temperature alerts (>30°C)
SELECT 
    hostname,
    temperature,
    cputempf as cpu_temp_f,
    datetimestamp,
    DATEDIFF('minute', datetimestamp, CURRENT_TIMESTAMP()) as minutes_ago
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE temperature > 30
ORDER BY datetimestamp DESC;

-- Temperature range by host
SELECT 
    hostname,
    MIN(temperature) as min_temp,
    AVG(temperature) as avg_temp,
    MAX(temperature) as max_temp,
    MAX(temperature) - MIN(temperature) as temp_range
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
GROUP BY hostname;

-- ============================================================================
-- Environmental Monitoring
-- ============================================================================

-- Current environmental conditions
SELECT 
    hostname,
    temperature || '°C' as temperature,
    humidity || '%' as humidity,
    co2 || ' ppm' as co2,
    pressure || ' Pa' as pressure,
    totalvocppb || ' ppb' as voc,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
QUALIFY ROW_NUMBER() OVER (PARTITION BY hostname ORDER BY datetimestamp DESC) = 1;

-- CO2 levels over time
SELECT 
    DATE_TRUNC('hour', datetimestamp) as hour,
    hostname,
    AVG(co2) as avg_co2,
    MIN(co2) as min_co2,
    MAX(co2) as max_co2
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE datetimestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1 DESC;

-- High CO2 alerts (>1200 ppm indicates poor ventilation)
SELECT 
    hostname,
    co2,
    temperature,
    humidity,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE co2 > 1200
ORDER BY datetimestamp DESC;

-- Humidity analysis
SELECT 
    DATE_TRUNC('day', datetimestamp) as day,
    hostname,
    AVG(humidity) as avg_humidity,
    MIN(humidity) as min_humidity,
    MAX(humidity) as max_humidity
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE datetimestamp >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1 DESC;

-- ============================================================================
-- System Health Monitoring
-- ============================================================================

-- Current system metrics
SELECT 
    hostname,
    cputempf as cpu_temp_f,
    cpu as cpu_usage_pct,
    memory as memory_usage_pct,
    diskusage,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
QUALIFY ROW_NUMBER() OVER (PARTITION BY hostname ORDER BY datetimestamp DESC) = 1;

-- CPU temperature vs ambient temperature
SELECT 
    hostname,
    temperature as ambient_temp_c,
    temperatureicp as cpu_temp_c,
    (temperatureicp - temperature) as temp_delta,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY datetimestamp DESC
LIMIT 100;

-- High CPU usage alerts (>80%)
SELECT 
    hostname,
    cpu as cpu_usage,
    cputempf as cpu_temp_f,
    memory as memory_usage,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE cpu > 80
ORDER BY datetimestamp DESC;

-- System resource trends
SELECT 
    DATE_TRUNC('hour', datetimestamp) as hour,
    hostname,
    AVG(cpu) as avg_cpu_usage,
    AVG(memory) as avg_memory_usage,
    AVG(cputempf) as avg_cpu_temp_f
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE datetimestamp >= DATEADD('day', -1, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1 DESC;

-- ============================================================================
-- Ingestion Monitoring
-- ============================================================================

-- Check ingestion latency
SELECT 
    hostname,
    datetimestamp as sensor_time,
    ingestion_timestamp,
    DATEDIFF('second', datetimestamp, ingestion_timestamp) as latency_seconds
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY ingestion_timestamp DESC
LIMIT 100;

-- Average ingestion latency by hour
SELECT 
    DATE_TRUNC('hour', ingestion_timestamp) as hour,
    AVG(DATEDIFF('second', datetimestamp, ingestion_timestamp)) as avg_latency_sec,
    MIN(DATEDIFF('second', datetimestamp, ingestion_timestamp)) as min_latency_sec,
    MAX(DATEDIFF('second', datetimestamp, ingestion_timestamp)) as max_latency_sec,
    COUNT(*) as record_count
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE ingestion_timestamp >= DATEADD('day', -1, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 1 DESC;

-- Ingestion volume by hour
SELECT 
    DATE_TRUNC('hour', ingestion_timestamp) as hour,
    hostname,
    COUNT(*) as record_count,
    COUNT(DISTINCT uuid) as unique_readings
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- Data gaps (hours with no data)
WITH hourly_data AS (
    SELECT 
        DATE_TRUNC('hour', datetimestamp) as hour,
        hostname,
        COUNT(*) as record_count
    FROM DEMO.DEMO.THERMAL_SENSOR_DATA
    WHERE datetimestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
    GROUP BY 1, 2
)
SELECT * FROM hourly_data
WHERE record_count = 0
ORDER BY hour DESC;

-- ============================================================================
-- Advanced Analytics
-- ============================================================================

-- Correlation between temperature and CO2
SELECT 
    hostname,
    CORR(temperature, co2) as temp_co2_correlation,
    CORR(temperature, humidity) as temp_humidity_correlation,
    CORR(humidity, co2) as humidity_co2_correlation
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE datetimestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY hostname;

-- Moving average (24-hour window)
SELECT 
    hostname,
    datetimestamp,
    temperature,
    AVG(temperature) OVER (
        PARTITION BY hostname 
        ORDER BY datetimestamp 
        ROWS BETWEEN 24 PRECEDING AND CURRENT ROW
    ) as moving_avg_24h
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY hostname, datetimestamp DESC;

-- Anomaly detection (values outside 2 standard deviations)
WITH stats AS (
    SELECT 
        hostname,
        AVG(temperature) as avg_temp,
        STDDEV(temperature) as stddev_temp
    FROM DEMO.DEMO.THERMAL_SENSOR_DATA
    WHERE datetimestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
    GROUP BY hostname
)
SELECT 
    d.hostname,
    d.temperature,
    s.avg_temp,
    s.stddev_temp,
    ABS(d.temperature - s.avg_temp) / s.stddev_temp as std_deviations,
    d.datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA d
JOIN stats s ON d.hostname = s.hostname
WHERE ABS(d.temperature - s.avg_temp) > 2 * s.stddev_temp
ORDER BY d.datetimestamp DESC;

-- ============================================================================
-- Reporting Views
-- ============================================================================

-- Create view for latest readings
CREATE OR REPLACE VIEW THERMAL_SENSOR_LATEST AS
SELECT 
    hostname,
    temperature,
    humidity,
    co2,
    pressure,
    totalvocppb,
    cputempf,
    cpu,
    memory,
    diskusage,
    datetimestamp,
    ingestion_timestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
QUALIFY ROW_NUMBER() OVER (PARTITION BY hostname ORDER BY datetimestamp DESC) = 1;

-- Create view for hourly aggregates
CREATE OR REPLACE VIEW THERMAL_SENSOR_HOURLY AS
SELECT 
    DATE_TRUNC('hour', datetimestamp) as hour,
    hostname,
    AVG(temperature) as avg_temperature,
    MIN(temperature) as min_temperature,
    MAX(temperature) as max_temperature,
    AVG(humidity) as avg_humidity,
    AVG(co2) as avg_co2,
    AVG(pressure) as avg_pressure,
    AVG(cpu) as avg_cpu_usage,
    AVG(memory) as avg_memory_usage,
    COUNT(*) as reading_count
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
GROUP BY 1, 2;

-- Create view for daily summaries
CREATE OR REPLACE VIEW THERMAL_SENSOR_DAILY AS
SELECT 
    DATE_TRUNC('day', datetimestamp) as day,
    hostname,
    AVG(temperature) as avg_temperature,
    MIN(temperature) as min_temperature,
    MAX(temperature) as max_temperature,
    AVG(humidity) as avg_humidity,
    AVG(co2) as avg_co2,
    AVG(cpu) as avg_cpu_usage,
    COUNT(*) as reading_count
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
GROUP BY 1, 2;

-- ============================================================================
-- Query the views
-- ============================================================================

-- Latest readings for all hosts
SELECT * FROM THERMAL_SENSOR_LATEST;

-- Hourly trends for last 24 hours
SELECT * FROM THERMAL_SENSOR_HOURLY
WHERE hour >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
ORDER BY hour DESC;

-- Daily summary for last 30 days
SELECT * FROM THERMAL_SENSOR_DAILY
WHERE day >= DATEADD('day', -30, CURRENT_TIMESTAMP())
ORDER BY day DESC;



-- View channel history
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWPIPE_STREAMING_CHANNEL_HISTORY
WHERE PIPE_NAME = 'THERMAL_SENSOR_PIPE'
ORDER BY CREATED_ON DESC;

-- Check ingestion latency
SELECT 
    hostname,
    datetimestamp as sensor_time,
    ingestion_timestamp,
    DATEDIFF('second', datetimestamp, ingestion_timestamp) as latency_seconds
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
ORDER BY ingestion_timestamp DESC
LIMIT 100;


SELECT 
    hostname,
    temperature,
    humidity,
    co2,
    pressure,
    datetimestamp
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
QUALIFY ROW_NUMBER() OVER (PARTITION BY hostname ORDER BY datetimestamp DESC) = 1;



SELECT 
    DATE_TRUNC('hour', datetimestamp) as hour,
    hostname,
    AVG(temperature) as avg_temp_c,
    AVG(humidity) as avg_humidity,
    AVG(co2) as avg_co2,
    COUNT(*) as reading_count
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
GROUP BY 1, 2
ORDER BY 1 DESC;


SELECT 
    hostname,
    datetimestamp,
    temperature,
    cputempf
FROM DEMO.DEMO.THERMAL_SENSOR_DATA
WHERE temperature > 30
ORDER BY datetimestamp DESC;
