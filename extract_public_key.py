#!/usr/bin/env python3
"""
Simple script to extract public key from private key and generate SQL.
"""

import sys
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Your configuration
PRIVATE_KEY_FILE = '/Users/tspann/.snowflake/keys/snowflake_private_key.p8'
USERNAME = 'KAFKAGUY'

print("=" * 70)
print("EXTRACTING PUBLIC KEY")
print("=" * 70)

try:
    # Load private key
    print(f"\nReading private key from: {PRIVATE_KEY_FILE}")
    with open(PRIVATE_KEY_FILE, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    print("[OK] Private key loaded")
    
    # Extract public key
    public_key = private_key.public_key()
    
    # Get public key in PEM format
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    # Remove header/footer and newlines for Snowflake format
    public_key_lines = [
        line for line in public_key_pem.split('\n')
        if line and not line.startswith('-----')
    ]
    public_key_formatted = ''.join(public_key_lines)
    
    print("[OK] Public key extracted")
    
    # Generate SQL
    sql_command = f"ALTER USER {USERNAME} SET RSA_PUBLIC_KEY='{public_key_formatted}';"
    
    print("\n" + "=" * 70)
    print("COPY AND RUN THIS SQL COMMAND IN SNOWFLAKE:")
    print("=" * 70)
    print()
    print(sql_command)
    print()
    print("=" * 70)
    print("THEN VERIFY:")
    print("=" * 70)
    print()
    print(f"DESC USER {USERNAME};")
    print("-- Check that RSA_PUBLIC_KEY_FP is set")
    print()
    print("=" * 70)
    
    # Save to file
    output_file = 'set_public_key.sql'
    with open(output_file, 'w') as f:
        f.write(f"-- Set public key for user {USERNAME}\n\n")
        f.write(sql_command + "\n\n")
        f.write(f"-- Verify:\n")
        f.write(f"DESC USER {USERNAME};\n")
    
    print(f"\n[OK] SQL saved to: {output_file}")
    print("\nNext steps:")
    print("1. Copy the SQL command above")
    print("2. Run it in Snowflake (Snowsight or CLI)")
    print("3. Run: python test_connection.py")
    print("=" * 70)
    
except FileNotFoundError:
    print(f"\n[ERROR] Private key file not found: {PRIVATE_KEY_FILE}")
    print("\nCheck the path in your snowflake_config.json")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] {e}")
    sys.exit(1)

