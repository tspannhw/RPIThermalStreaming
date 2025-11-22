#!/usr/bin/env python3
"""
I2C Sensor Detection Script for Raspberry Pi

This script checks which I2C sensors are connected and provides
detailed information about their status.

Expected sensors:
- SCD4X (0x62) - CO2, Temperature, Humidity
- ICP10125 (0x63) - Pressure, Temperature
- SGP30 (0x58) - eCO2, TVOC

Usage:
    python check_sensors.py
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def check_i2c_devices():
    """Check which I2C devices are detected."""
    logger.info("Checking I2C bus for devices...")
    
    try:
        import smbus2
        bus = smbus2.SMBus(1)  # Raspberry Pi uses bus 1
        
        devices = []
        for addr in range(0x03, 0x78):
            try:
                bus.read_byte(addr)
                devices.append(addr)
            except:
                pass
        
        if devices:
            logger.info(f"[OK] Found {len(devices)} I2C device(s):")
            for addr in devices:
                logger.info(f"  - 0x{addr:02X}")
        else:
            logger.warning("No I2C devices found")
            logger.info("Make sure I2C is enabled: sudo raspi-config")
        
        return devices
        
    except ImportError:
        logger.error("smbus2 not installed. Install with: pip install smbus2")
        return []
    except Exception as e:
        logger.error(f"Error checking I2C bus: {e}")
        logger.info("Make sure I2C is enabled: sudo raspi-config")
        return []


def check_scd4x():
    """Check SCD4X sensor (0x62)."""
    logger.info("\nChecking SCD4X sensor (CO2, Temp, Humidity)...")
    
    try:
        from scd4x import SCD4X
        sensor = SCD4X(quiet=False)
        
        # Start periodic measurement
        sensor.start_periodic_measurement()
        
        logger.info("[OK] SCD4X sensor initialized successfully")
        logger.info("  Address: 0x62")
        logger.info("  Measures: CO2, Temperature, Humidity")
        
        # Try to read data using measure() method
        import time
        time.sleep(5)  # Wait for first measurement
        co2, temp, humidity, timestamp = sensor.measure()
        logger.info(f"  Sample reading: CO2={co2}ppm, Temp={temp:.1f}°C, Humidity={humidity:.1f}%")
        
        sensor.stop_periodic_measurement()
        return True
        
    except ImportError:
        logger.warning("[ERROR] SCD4X library not installed")
        logger.info("  Install with: pip install python-scd4x")
        return False
    except Exception as e:
        logger.error(f"[ERROR] SCD4X sensor error: {e}")
        return False


def check_icp10125():
    """Check ICP10125 sensor (0x63)."""
    logger.info("\nChecking ICP10125 sensor (Pressure, Temperature)...")
    
    try:
        from icp10125 import ICP10125
        sensor = ICP10125()
        
        logger.info("[OK] ICP10125 sensor initialized successfully")
        logger.info("  Address: 0x63")
        logger.info("  Measures: Pressure, Temperature")
        
        # Try to read data using measure() method
        pressure, temp = sensor.measure()
        temp_f = round(9.0/5.0 * float(temp) + 32, 2)
        logger.info(f"  Sample reading: Pressure={pressure:.1f}Pa, Temp={temp:.1f}°C ({temp_f:.1f}°F)")
        
        return True
        
    except ImportError:
        logger.warning("[ERROR] ICP10125 library not installed")
        logger.info("  Install with: pip install icp10125")
        return False
    except Exception as e:
        logger.error(f"[ERROR] ICP10125 sensor error: {e}")
        return False


def check_sgp30():
    """Check SGP30 sensor (0x58)."""
    logger.info("\nChecking SGP30 sensor (eCO2, TVOC)...")
    
    try:
        from sgp30 import SGP30
        sensor = SGP30()
        
        logger.info("[OK] SGP30 sensor initialized successfully")
        logger.info("  Address: 0x58")
        logger.info("  Measures: eCO2, TVOC")
        
        # Try to read data
        sensor.start_measurement()
        import time
        time.sleep(1)
        result = sensor.get_air_quality()
        logger.info(f"  Sample reading: eCO2={result.equivalent_co2}ppm, TVOC={result.total_voc}ppb")
        
        return True
        
    except ImportError:
        logger.warning("[ERROR] SGP30 library not installed")
        logger.info("  Install with: pip install sgp30")
        return False
    except Exception as e:
        logger.error(f"[ERROR] SGP30 sensor error: {e}")
        return False


def main():
    """Main sensor check routine."""
    logger.info("=" * 70)
    logger.info("RASPBERRY PI SENSOR CHECK")
    logger.info("=" * 70)
    
    # Check I2C devices
    devices = check_i2c_devices()
    
    expected_sensors = {
        0x58: "SGP30 (eCO2, TVOC)",
        0x62: "SCD4X (CO2, Temp, Humidity)",
        0x63: "ICP10125 (Pressure, Temp)"
    }
    
    if devices:
        logger.info("\nExpected sensor addresses:")
        for addr, name in expected_sensors.items():
            found = "[OK] FOUND" if addr in devices else "[MISSING]"
            logger.info(f"  0x{addr:02X} - {name}: {found}")
    
    # Check each sensor with its library
    results = {}
    results['scd4x'] = check_scd4x()
    results['icp10125'] = check_icp10125()
    results['sgp30'] = check_sgp30()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    working_sensors = sum(1 for v in results.values() if v)
    total_sensors = len(results)
    
    logger.info(f"Working sensors: {working_sensors}/{total_sensors}")
    
    for sensor_name, working in results.items():
        status = "[OK]" if working else "[NOT WORKING]"
        logger.info(f"  {sensor_name.upper()}: {status}")
    
    if working_sensors == total_sensors:
        logger.info("\n[OK] All sensors working! Ready to run the application.")
        logger.info("  Run: python main.py")
        return 0
    elif working_sensors > 0:
        logger.warning(f"\n⚠ Some sensors not working ({working_sensors}/{total_sensors})")
        logger.info("  You can still run in simulation mode: python main.py --simulate")
        return 1
    else:
        logger.error("\n[ERROR] No sensors working")
        logger.info("  Run in simulation mode: python main.py --simulate")
        logger.info("\nTroubleshooting:")
        logger.info("  1. Enable I2C: sudo raspi-config → Interface Options → I2C")
        logger.info("  2. Check wiring (SDA → GPIO2, SCL → GPIO3)")
        logger.info("  3. Install libraries: pip install python-scd4x icp10125 sgp30 smbus2")
        logger.info("  4. Reboot: sudo reboot")
        return 1


if __name__ == '__main__':
    sys.exit(main())

