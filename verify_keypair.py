#!/usr/bin/env python3
"""
Verify Key Pair and Generate SQL for Snowflake

This script:
1. Loads your private key
2. Derives the public key
3. Generates the SQL ALTER USER command
4. Shows the public key fingerprint

Usage:
    python verify_keypair.py [--key-file path/to/rsa_key.p8] [--user USERNAME]
"""

import sys
import argparse
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from hashlib import sha256


def main():
    parser = argparse.ArgumentParser(description='Verify RSA key pair and generate Snowflake SQL')
    parser.add_argument('--key-file', 
                       default='/Users/tspann/.snowflake/keys/snowflake_private_key.p8',
                       help='Path to private key file')
    parser.add_argument('--user',
                       default='kafkaguy',
                       help='Snowflake username')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("SNOWFLAKE KEY PAIR VERIFICATION")
    print("=" * 70)
    
    # Load private key
    print(f"\n1. Loading private key from: {args.key_file}")
    try:
        with open(args.key_file, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        print("[OK] Private key loaded successfully")
    except Exception as e:
        print(f"[ERROR] Error loading private key: {e}")
        return 1
    
    # Extract public key
    print("\n2. Extracting public key...")
    public_key = private_key.public_key()
    
    # Get public key in PEM format
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Get public key in DER format for fingerprint
    public_key_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Calculate fingerprint
    fingerprint = 'SHA256:' + sha256(public_key_der).hexdigest().upper()
    print(f"[OK] Public key fingerprint: {fingerprint}")
    
    # Format public key for Snowflake (remove headers and newlines)
    public_key_str = public_key_pem.decode('utf-8')
    public_key_formatted = ''.join([
        line for line in public_key_str.split('\n')
        if not line.startswith('-----')
    ])
    
    # Generate SQL command
    print("\n" + "=" * 70)
    print("SQL COMMAND TO RUN IN SNOWFLAKE")
    print("=" * 70)
    print(f"\nALTER USER {args.user.upper()} SET RSA_PUBLIC_KEY='{public_key_formatted}';")
    
    print("\n" + "=" * 70)
    print("VERIFICATION STEPS")
    print("=" * 70)
    print("\n1. Run the ALTER USER command above in Snowflake")
    print("\n2. Verify it was set:")
    print(f"   DESC USER {args.user.upper()};")
    print("   -- Look for RSA_PUBLIC_KEY_FP in the output")
    
    print("\n3. Expected fingerprint in Snowflake:")
    print(f"   {fingerprint}")
    
    print("\n4. Test the connection:")
    print("   python test_connection.py")
    
    print("\n" + "=" * 70)
    
    # Save to file
    output_file = 'set_public_key.sql'
    with open(output_file, 'w') as f:
        f.write(f"-- Generated public key SQL for user {args.user.upper()}\n")
        f.write(f"-- Fingerprint: {fingerprint}\n\n")
        f.write(f"ALTER USER {args.user.upper()} SET RSA_PUBLIC_KEY='{public_key_formatted}';\n\n")
        f.write(f"-- Verify:\n")
        f.write(f"DESC USER {args.user.upper()};\n")
    
    print(f"\n[OK] SQL saved to: {output_file}")
    print("\n" + "=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

