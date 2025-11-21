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

