#!/usr/bin/env python3
"""
Quick verification script to ensure all methods exist before running the app.
   
PRODUCTION MODE: Real sensors + Snowpipe Streaming REST API only
"""
import sys
import os

# Clear any cached modules
if 'thermal_streaming_client' in sys.modules:
    del sys.modules['thermal_streaming_client']

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and verify
try:
    from thermal_streaming_client import SnowpipeStreamingClient
    
    print("=" * 70)
    print("PRODUCTION MODE VERIFICATION")
    print("=" * 70)
    print("Configuration:")
    print("  - Real physical sensors REQUIRED")
    print("  - Snowpipe Streaming REST API ONLY (no direct inserts)")
    print("=" * 70)
    
    # Check for insert_rows method
    if hasattr(SnowpipeStreamingClient, 'insert_rows'):
        print("[OK] insert_rows method exists")
    else:
        print("[ERROR] insert_rows method NOT FOUND")
        print("  Available methods:", [m for m in dir(SnowpipeStreamingClient) if not m.startswith('_')])
        sys.exit(1)
    
    # Check for other critical methods
    required_methods = ['append_rows', 'open_channel', 'discover_ingest_host']
    for method in required_methods:
        if hasattr(SnowpipeStreamingClient, method):
            print(f"[OK] {method} method exists")
        else:
            print(f"[ERROR] {method} method NOT FOUND")
            sys.exit(1)
    
    print("\n" + "=" * 70)
    print("ALL CHECKS PASSED - Starting application...")
    print("=" * 70 + "\n")
    
    # Import and run main
    from main import main
    main()
    
except ImportError as e:
    print(f"[ERROR] Failed to import module: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

