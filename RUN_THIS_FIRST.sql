-- ==============================================================================
-- STEP 1: CREATE THE PIPE (if it doesn't exist)
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE DEMO;
USE SCHEMA DEMO;

-- Check if pipe exists
SHOW PIPES LIKE 'THERMAL_SENSOR_PIPE';

-- If pipe doesn't exist, create it:
CREATE PIPE IF NOT EXISTS THERMAL_SENSOR_PIPE
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
-- STEP 2: GRANT PERMISSIONS (CRITICAL!)
-- ==============================================================================

GRANT OPERATE ON PIPE THERMAL_SENSOR_PIPE TO ROLE ACCOUNTADMIN;
GRANT INSERT ON TABLE THERMAL_SENSOR_DATA TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- STEP 3: VERIFY
-- ==============================================================================

SHOW GRANTS ON PIPE THERMAL_SENSOR_PIPE;

-- You should see:
-- privilege | granted_on | name                  | granted_to | grantee_name
-- OPERATE   | PIPE       | THERMAL_SENSOR_PIPE   | ROLE       | ACCOUNTADMIN

-- ==============================================================================
-- NOW RUN: python test_connection.py
-- ==============================================================================
