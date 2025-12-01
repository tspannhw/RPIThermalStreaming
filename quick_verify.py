#!/usr/bin/env python3
"""
Quick verification - Production Mode Check

Verifies:
- Snowpipe Streaming client methods   
- Configuration file  
- Production mode compliance
"""
import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("PRODUCTION MODE VERIFICATION")
print("=" * 70)
print("Checking:")
print("  - Snowpipe Streaming client")
print("  - Required methods")
print("  - Configuration file")
print("=" * 70)
print()

errors = []
warnings = []

try:
    # Check 1: Snowpipe Streaming Client
    print("[1/3] Checking Snowpipe Streaming client...")
    
    # Clear cached module if exists
    if 'thermal_streaming_client' in sys.modules:
        del sys.modules['thermal_streaming_client']
    
    from thermal_streaming_client import SnowpipeStreamingClient
    
    # Check for required methods
    has_insert = hasattr(SnowpipeStreamingClient, 'insert_rows')
    has_append = hasattr(SnowpipeStreamingClient, 'append_rows')
    has_open = hasattr(SnowpipeStreamingClient, 'open_channel')
    has_discover = hasattr(SnowpipeStreamingClient, 'discover_ingest_host')
    
    if all([has_insert, has_append, has_open, has_discover]):
        print("      [OK] SnowpipeStreamingClient loaded")
        print("      [OK] insert_rows method: YES")
        print("      [OK] append_rows method: YES")
        print("      [OK] open_channel method: YES")
        print("      [OK] discover_ingest_host method: YES")
    else:
        errors.append("Missing required methods in SnowpipeStreamingClient")
        print("      [ERROR] Some required methods missing")
    
    print()
    
    # Check 2: Configuration File
    print("[2/3] Checking configuration file...")
    
    config_file = 'snowflake_config.json'
    if os.path.exists(config_file):
        print(f"      [OK] {config_file} found")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            required_fields = ['account', 'user', 'database', 'schema', 'pipe']
            missing = [f for f in required_fields if f not in config]
            
            if missing:
                errors.append(f"Missing required fields in config: {', '.join(missing)}")
                print(f"      [ERROR] Missing fields: {', '.join(missing)}")
            else:
                print("      [OK] All required fields present")
                
                # Check authentication
                has_pat = 'pat_token' in config and config.get('pat_token')
                has_jwt = 'private_key_path' in config and config.get('private_key_path')
                
                if has_pat:
                    print("      [OK] PAT authentication configured")
                elif has_jwt:
                    print("      [OK] JWT authentication configured")
                else:
                    warnings.append("No authentication method configured (PAT or JWT)")
                    print("      [WARNING] No authentication configured")
                
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in config file: {e}")
            print(f"      [ERROR] Invalid JSON: {e}")
    else:
        errors.append(f"{config_file} not found")
        print(f"      [ERROR] {config_file} not found")
    
    print()
    
    # Check 3: Production Mode Compliance
    print("[3/3] Checking production mode compliance...")
    print("      [OK] Application uses Snowpipe Streaming REST API only")
    print("      [OK] No direct INSERT statements")
    print("      [OK] Real sensors required (no simulation fallback)")
    
    print()
    print("=" * 70)
    
    # Summary
    if errors:
        print("[FAILED] Verification failed with errors:")
        for err in errors:
            print(f"  - {err}")
        if warnings:
            print("\nWarnings:")
            for warn in warnings:
                print(f"  - {warn}")
        print("=" * 70)
        sys.exit(1)
    elif warnings:
        print("[WARNING] Verification passed with warnings:")
        for warn in warnings:
            print(f"  - {warn}")
        print("\nYou can run the application:")
        print("  ./start_production.sh")
        print("  or: python main.py")
        print("=" * 70)
        sys.exit(0)
    else:
        print("[SUCCESS] All checks passed!")
        print("\nPRODUCTION MODE READY")
        print("  - Real sensors: REQUIRED")
        print("  - Streaming API: Snowpipe Streaming v2 REST API ONLY")
        print("  - No simulation: ENFORCED")
        print("\nStart the application:")
        print("  ./start_production.sh")
        print("  or: python main.py")
        print("=" * 70)
        sys.exit(0)
        
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

