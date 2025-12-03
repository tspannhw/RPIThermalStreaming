#!/usr/bin/env python3
"""
Performance Diagnostic Script
Identifies where time is being spent during sensor reads.
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thermal_sensor import ThermalSensor

def time_function(name, func):
    """Time a function call and print result."""
    start = time.time()
    result = func()
    elapsed = (time.time() - start) * 1000  # Convert to milliseconds
    print(f"  {name:30s}: {elapsed:7.1f} ms")
    return result, elapsed

def diagnose_sensor_performance():
    """Diagnose where time is being spent in sensor reads."""
    print("=" * 70)
    print("PERFORMANCE DIAGNOSTIC - Timing Each Component")
    print("=" * 70)
    print()
    
    # Initialize sensor
    print("Initializing sensor...")
    sensor = ThermalSensor(simulate=False, require_real_sensors=False)
    print(f"Mode: {'REAL SENSORS' if not sensor.simulate else 'SIMULATION'}")
    print()
    
    # Wait for initial sensor update if using real sensors
    if not sensor.simulate:
        print("Waiting 2 seconds for background sensor thread to initialize...")
        time.sleep(2)
        print()
    
    # Test individual components
    print("=" * 70)
    print("Component Timing (10 iterations)")
    print("=" * 70)
    
    total_times = {}
    iterations = 10
    
    for i in range(iterations):
        print(f"\nIteration {i+1}/{iterations}:")
        
        # Time CPU temp
        _, t = time_function("CPU Temperature", sensor._get_cpu_temp)
        total_times.setdefault('cpu_temp', []).append(t)
        
        # Time CPU usage
        _, t = time_function("CPU Usage", sensor._get_cpu_usage)
        total_times.setdefault('cpu_usage', []).append(t)
        
        # Time Memory usage
        _, t = time_function("Memory Usage", sensor._get_memory_usage)
        total_times.setdefault('memory', []).append(t)
        
        # Time Disk usage
        _, t = time_function("Disk Usage", sensor._get_disk_usage)
        total_times.setdefault('disk', []).append(t)
        
        # Time full sensor read
        _, t = time_function("FULL SENSOR READ", sensor.read_sensor_data)
        total_times.setdefault('full_read', []).append(t)
    
    # Print averages
    print()
    print("=" * 70)
    print("AVERAGE TIMES (over 10 iterations)")
    print("=" * 70)
    for component, times in total_times.items():
        avg = sum(times) / len(times)
        print(f"  {component:30s}: {avg:7.1f} ms average")
    
    # Analysis
    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    avg_full = sum(total_times['full_read']) / len(total_times['full_read'])
    avg_cpu = sum(total_times['cpu_usage']) / len(total_times['cpu_usage'])
    
    print(f"Average time per sensor read: {avg_full:.1f} ms")
    print(f"Average CPU monitoring time:  {avg_cpu:.1f} ms")
    print()
    
    if avg_cpu > 100:
        print("[ERROR] CPU monitoring is taking > 100ms!")
        print("        This means psutil.cpu_percent(interval=1) is still being used.")
        print("        The updated code was NOT deployed to the Pi.")
        print()
        print("ACTION: Deploy the updated thermal_sensor.py to the Pi!")
    elif avg_cpu < 10:
        print("[OK] CPU monitoring is fast (< 10ms) - cache is working!")
        print()
        
        if avg_full > 500:
            print("[WARNING] Full sensor read is taking > 500ms")
            print("          With async sensor reading, this should be < 100ms")
            print("          The old SYNCHRONOUS code may still be deployed.")
            print()
            print("SOLUTIONS:")
            print("  1. Deploy the NEW asynchronous sensor reading code")
            print("  2. New code reads sensors in background thread every 5 seconds")
            print("  3. read_sensor_data() returns cached values instantly")
        elif avg_full < 100:
            print("[OK] Sensor reads are FAST (< 100ms)!")
            print("     Asynchronous sensor reading is working!")
            print("     Expected throughput: 5-20+ rows/sec")
        else:
            print("[OK] Sensor reads are reasonably fast (< 500ms)")
            print("     Expected throughput: 2-5 rows/sec")
    else:
        print("[WARNING] CPU monitoring taking 10-100ms")
        print("          Caching may not be working optimally.")
    
    # Check if code was deployed
    print()
    print("=" * 70)
    print("CODE VERSION CHECK")
    print("=" * 70)
    
    # Try to check the actual code
    import inspect
    source = inspect.getsource(sensor._update_system_metrics_cache)
    if 'interval=None' in source:
        print("[OK] Code has the performance fix (interval=None)")
    elif 'interval=1' in source:
        print("[ERROR] OLD CODE DETECTED! Still using interval=1")
        print("        You MUST deploy the updated code to your Pi!")
    else:
        print("[UNKNOWN] Cannot determine code version")
    
    print()
    print("=" * 70)
    
    # Cleanup
    print("Cleaning up...")
    sensor.cleanup()
    print("Done!")

if __name__ == '__main__':
    try:
        diagnose_sensor_performance()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

