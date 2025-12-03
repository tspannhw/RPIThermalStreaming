#!/usr/bin/env python3
"""
Performance Test Script
Demonstrates the dramatic performance improvement from caching system metrics.
"""

import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thermal_sensor import ThermalSensor

def test_reading_speed(sensor, num_readings=50):
    """Test how fast we can read sensor data."""
    print(f"\nTesting {num_readings} sensor readings...")
    print("=" * 60)
    
    start_time = time.time()
    
    for i in range(num_readings):
        data = sensor.read_sensor_data()
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            print(f"  [{i+1:3d}/{num_readings}] {rate:.2f} rows/sec | "
                  f"Temp={data['temperature']:.1f}°C | "
                  f"CPU={data['cpu']:.1f}%")
    
    end_time = time.time()
    elapsed = end_time - start_time
    rate = num_readings / elapsed
    
    print("=" * 60)
    print(f"[OK] Completed {num_readings} readings in {elapsed:.2f} seconds")
    print(f"[OK] Average rate: {rate:.2f} rows/sec")
    print(f"[OK] Average time per reading: {elapsed/num_readings*1000:.0f}ms")
    print("=" * 60)
    
    return rate

def main():
    print("=" * 60)
    print("PERFORMANCE TEST - Thermal Sensor Reading Speed")
    print("=" * 60)
    print("\nThis test demonstrates the performance improvements from:")
    print("  [OK] Non-blocking CPU monitoring (was blocking 1000ms!)")
    print("  [OK] System metrics caching (60-second cache)")
    print("  [OK] Network info cached at startup")
    print()
    
    # Initialize sensor (will use simulation if no real sensors)
    print("Initializing sensor...")
    sensor = ThermalSensor(simulate=False, require_real_sensors=False)
    print(f"Sensor mode: {'REAL SENSORS' if not sensor.simulate else 'SIMULATION'}")
    print(f"Hostname: {sensor.hostname}")
    print(f"IP Address: {sensor.ip_address}")
    
    # Test 1: Small batch
    print("\n" + "=" * 60)
    print("TEST 1: Small batch (10 readings)")
    print("=" * 60)
    rate1 = test_reading_speed(sensor, 10)
    
    # Test 2: Medium batch
    print("\n" + "=" * 60)
    print("TEST 2: Medium batch (50 readings)")
    print("=" * 60)
    rate2 = test_reading_speed(sensor, 50)
    
    # Test 3: Large batch
    print("\n" + "=" * 60)
    print("TEST 3: Large batch (100 readings)")
    print("=" * 60)
    rate3 = test_reading_speed(sensor, 100)
    
    # Summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Small batch (10):   {rate1:.2f} rows/sec")
    print(f"Medium batch (50):  {rate2:.2f} rows/sec")
    print(f"Large batch (100):  {rate3:.2f} rows/sec")
    print()
    print("Expected results:")
    print("  [OLD] OLD CODE: 0.21 rows/sec (blocked by CPU monitoring)")
    print("  [NEW] NEW CODE: 2-10 rows/sec (15-50x faster!)")
    print()
    
    if rate3 > 1.0:
        improvement = rate3 / 0.21
        print(f"*** SUCCESS! You're now {improvement:.1f}x faster than before! ***")
        print(f"    (was 0.21 rows/sec, now {rate3:.2f} rows/sec)")
    else:
        print("WARNING: Performance lower than expected.")
        print("         Check sensor read times and network latency.")
    
    print("=" * 60)

if __name__ == '__main__':
    main()

