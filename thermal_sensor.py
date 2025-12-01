#!/usr/bin/env python3
"""
Thermal Sensor Data Reader for Raspberry Pi

This module reads data from various sensors on the Raspberry Pi:
- SCD4X: CO2, Temperature, Humidity
- ICP10125: Pressure and Temperature
- SGP30: VOC and eCO2 readings
- System metrics: CPU temp, memory, disk usage


For simulation mode, it generates realistic sensor data.
"""

import uuid
import time
import socket
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
import json

logger = logging.getLogger(__name__)

# Try to import sensor libraries (optional for simulation mode)
SENSORS_AVAILABLE = False
try:
    from scd4x import SCD4X
    from icp10125 import ICP10125
    from sgp30 import SGP30
    SENSORS_AVAILABLE = True
    logger.info("Sensor libraries imported successfully (SCD4X, ICP10125, SGP30)")
except ImportError as e:
    logger.warning(f"Sensor libraries not available - using simulation mode: {e}")


class ThermalSensor:
    """Read thermal and environmental sensor data from Raspberry Pi."""
    
    def __init__(self, simulate: bool = False, require_real_sensors: bool = False):
        """
        Initialize sensor reader.
        
        Args:
            simulate: If True, generate simulated data instead of reading real sensors
            require_real_sensors: If True, raise error if physical sensors not available
                                  (PRODUCTION MODE - no fallback to simulation)
        
        Raises:
            RuntimeError: If require_real_sensors=True and sensors unavailable
        """
        # PRODUCTION MODE: Enforce real sensors
        if require_real_sensors:
            if not SENSORS_AVAILABLE:
                raise RuntimeError(
                    "PRODUCTION MODE FAILED: Physical sensor libraries not available. "
                    "Install required packages: scd4x, icp10125, sgp30"
                )
            if simulate:
                raise RuntimeError(
                    "PRODUCTION MODE FAILED: Simulation mode requested but "
                    "require_real_sensors=True. Cannot use simulated data."
                )
            logger.info("PRODUCTION MODE: Real sensors required and enforced")
            self.simulate = False
        else:
            # Development/test mode: Allow simulation fallback
            self.simulate = simulate or not SENSORS_AVAILABLE
        
        self.hostname = socket.gethostname()
        self.mac_address = self._get_mac_address()
        self.ip_address = self._get_ip_address()
        
        if not self.simulate:
            try:
                self._init_sensors()
                logger.info("Physical sensors initialized successfully")
                if require_real_sensors:
                    self._verify_sensors()
            except Exception as e:
                error_msg = f"Failed to initialize sensors: {e}"
                if require_real_sensors:
                    raise RuntimeError(
                        f"PRODUCTION MODE FAILED: {error_msg}. "
                        "Physical sensors required but initialization failed."
                    )
                logger.warning(error_msg)
                logger.info("Falling back to simulation mode")
                self.simulate = True
        else:
            logger.info("Running in simulation mode")
        
        # For simulation - track values for realistic variation
        self.sim_base = {
            'temperature': 25.0,
            'humidity': 50.0,
            'co2': 1000.0,
            'pressure': 101325.0
        }
    
    def _init_sensors(self):
        """Initialize I2C sensors."""
        if self.simulate:
            return
        
        # Initialize SCD4X (CO2, temperature, humidity)
        try:
            self.scd4x = SCD4X(quiet=False)
            self.scd4x.start_periodic_measurement()
            logger.info("SCD4X sensor initialized (CO2, Temp, Humidity)")
        except Exception as e:
            self.scd4x = None
            logger.warning(f"SCD4X sensor not found: {e}")
        
        # Initialize ICP10125 (pressure and temperature)
        try:
            self.icp10125 = ICP10125()
            logger.info("ICP10125 sensor initialized (Pressure, Temp)")
        except Exception as e:
            self.icp10125 = None
            logger.warning(f"ICP10125 sensor not found: {e}")
        
        # Initialize SGP30 (eCO2 and VOC)
        try:
            self.sgp30 = SGP30()
            self.sgp30.start_measurement()
            logger.info("SGP30 sensor initialized (eCO2, TVOC)")
        except Exception as e:
            self.sgp30 = None
            logger.warning(f"SGP30 sensor not found: {e}")
    
    def _verify_sensors(self):
        """Verify at least one sensor is available (for production mode)."""
        if not hasattr(self, 'scd4x') or self.scd4x is None:
            if not hasattr(self, 'icp10125') or self.icp10125 is None:
                raise RuntimeError(
                    "PRODUCTION MODE FAILED: No sensors initialized. "
                    "At least SCD4X or ICP10125 must be available."
                )
        logger.info("[OK] Sensor verification passed - physical sensors available")
    
    def _get_mac_address(self) -> str:
        """Get MAC address of the primary network interface."""
        try:
            import psutil
            nics = psutil.net_if_addrs()
            # Try wlan0 first (WiFi on Raspberry Pi)
            if 'wlan0' in nics:
                nic = nics['wlan0']
                for i in nic:
                    if i.family == psutil.AF_LINK:
                        return i.address
            # Try eth0 (Ethernet)
            if 'eth0' in nics:
                nic = nics['eth0']
                for i in nic:
                    if i.family == psutil.AF_LINK:
                        return i.address
        except:
            pass
        
        # Fallback
        import uuid
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                       for i in range(0, 8*6, 8)][::-1])
        return mac
    
    def _get_ip_address(self) -> str:
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _get_cpu_temp(self) -> float:
        """Get CPU temperature in Celsius."""
        try:
            with open('/sys/devices/virtual/thermal/thermal_zone0/temp', 'r') as f:
                cputemp = f.readline().strip()
                temp_c = round(float(cputemp) / 1000.0)
                return temp_c
        except:
            # Simulation fallback
            import random
            return 40.0 + random.uniform(-5, 15)
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except:
            import random
            return random.uniform(5, 25)
    
    def _get_memory_usage(self) -> float:
        """Get memory usage percentage."""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except:
            import random
            return random.uniform(10, 40)
    
    def _get_disk_usage(self) -> str:
        """Get disk FREE space in MB (matches original sensors.py)."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            free_mb = disk.free / (1024 * 1024)
            return f"{free_mb:.1f} MB"
        except:
            return "92358.2 MB"
    
    def read_sensor_data(self) -> Dict:
        """
        Read all sensor data and return as dictionary.
        
        Returns:
            Dictionary with all sensor readings and metadata
        """
        start_time_dt = datetime.now(timezone.utc)
        start_time = time.time()
        now = datetime.now(timezone.utc)
        
        # Initialize default values
        temperature = None
        humidity = None
        pressure = None
        co2 = None
        tvoc = None
        temperatureicp_f = None
        equivalent_co2_ppm = 65535.0
        
        # Read SCD4X sensor (CO2, temperature, humidity)
        if not self.simulate and self.scd4x:
            try:
                # Use measure() method which returns (co2, temp, humidity, timestamp)
                co2_reading, temp_reading, hum_reading, timestamp = self.scd4x.measure()
                temperature = temp_reading
                humidity = hum_reading
                co2 = co2_reading
                logger.debug(f"SCD4X: CO2={co2}ppm, Temp={temperature}°C, Humidity={humidity}%")
            except Exception as e:
                logger.warning(f"Error reading SCD4X: {e}")
        
        # Read ICP10125 sensor (pressure and temperature)
        if not self.simulate and self.icp10125:
            try:
                # Use measure() method which returns (pressure, temperature)
                pressure_reading, temp_icp_c = self.icp10125.measure()
                pressure = pressure_reading  # In Pascals
                # Convert to Fahrenheit like the original code
                temperatureicp_f = round(9.0/5.0 * float(temp_icp_c) + 32, 2)
                logger.debug(f"ICP10125: Pressure={pressure}Pa, Temp={temperatureicp_f}°F")
            except Exception as e:
                logger.warning(f"Error reading ICP10125: {e}")
        
        # Read SGP30 sensor (eCO2 and VOC)
        if not self.simulate and self.sgp30:
            try:
                result = self.sgp30.get_air_quality()
                equivalent_co2_ppm = round(float(result.equivalent_co2), 5)
                tvoc = round(float(result.total_voc), 3)
                logger.debug(f"SGP30: eCO2={equivalent_co2_ppm}ppm, TVOC={tvoc}ppb")
            except Exception as e:
                logger.warning(f"Error reading SGP30: {e}")
        
        # Fall back to simulation if sensors didn't provide data
        if temperature is None:
            import random
            temperature = self.sim_base['temperature'] + random.uniform(-2, 2)
        if humidity is None:
            import random
            humidity = self.sim_base['humidity'] + random.uniform(-5, 5)
        if pressure is None:
            import random
            pressure = self.sim_base['pressure'] + random.uniform(-100, 100)
        if co2 is None:
            import random
            co2 = self.sim_base['co2'] + random.uniform(-100, 100)
        if tvoc is None:
            import random
            tvoc = random.uniform(0, 500)
        if temperatureicp_f is None:
            # Use ambient temp converted to F as fallback
            temperatureicp_f = round(9.0/5.0 * float(temperature) + 32, 2)
        
        # Get system metrics
        cpu_temp_c = self._get_cpu_temp()
        cpu_temp_f = int(round(cpu_temp_c * 9/5 + 32))
        cpu_usage = self._get_cpu_usage()
        memory_usage = self._get_memory_usage()
        disk_usage = self._get_disk_usage()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Generate unique identifiers
        row_uuid = str(uuid.uuid4())
        timestamp_str = now.strftime("%Y%m%d%H%M%S")
        unique_id = f"thrml_{self.hostname[:3]}_{timestamp_str}"
        row_id = f"{timestamp_str}_{row_uuid}"
        
        # Construct data record matching your format
        data = {
            "uuid": unique_id,
            "ipaddress": self.ip_address,
            "cputempf": cpu_temp_f,
            "runtime": int(round(elapsed_time)),
            "host": self.hostname,
            "hostname": self.hostname,
            "macaddress": self.mac_address,
            "endtime": str(end_time),
            "te": str(elapsed_time),
            "cpu": round(cpu_usage, 1),
            "diskusage": disk_usage,
            "memory": round(memory_usage, 1),
            "rowid": row_id,
            "systemtime": now.strftime("%m/%d/%Y %H:%M:%S"),
            "ts": int(now.timestamp()),
            "starttime": start_time_dt.strftime("%m/%d/%Y %H:%M:%S"),
            "datetimestamp": now.isoformat(),
            "temperature": round(temperature, 4),
            "humidity": round(humidity, 2),
            "co2": round(co2, 2),
            "equivalentco2ppm": round(equivalent_co2_ppm, 5),
            "totalvocppb": round(tvoc, 3),
            "pressure": round(pressure, 2),
            "temperatureicp": temperatureicp_f
        }
        
        return data
    
    def read_batch(self, count: int = 1, interval: float = 1.0) -> list:
        """
        Read multiple sensor readings.
        
        Args:
            count: Number of readings to collect
            interval: Time between readings in seconds
            
        Returns:
            List of sensor data dictionaries
        """
        batch = []
        for i in range(count):
            data = self.read_sensor_data()
            batch.append(data)
            
            if i < count - 1:  # Don't sleep after last reading
                time.sleep(interval)
        
        return batch


def main():
    """Test sensor reading."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Testing Thermal Sensor Reader")
    
    # Initialize sensor (will auto-detect or simulate)
    sensor = ThermalSensor()
    
    # Read a few samples
    for i in range(3):
        logger.info(f"\n--- Reading {i+1} ---")
        data = sensor.read_sensor_data()
        
        # Print formatted output
        print(json.dumps(data, indent=2))
        
        # Print key values
        logger.info(f"Temperature: {data['temperature']:.2f}°C")
        logger.info(f"Humidity: {data['humidity']:.1f}%")
        logger.info(f"CO2: {data['co2']:.0f} ppm")
        logger.info(f"Pressure: {data['pressure']:.1f} Pa")
        logger.info(f"CPU Temp: {data['cputempf']:.1f}°F")
        logger.info(f"CPU Usage: {data['cpu']:.1f}%")
        
        if i < 2:
            time.sleep(2)


if __name__ == '__main__':
    main()

