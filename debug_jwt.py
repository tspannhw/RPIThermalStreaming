#!/usr/bin/env python3
"""
Debug JWT Token Generation

This script shows exactly what's in your JWT token
so we can verify it matches Snowflake's requirements.
"""

import sys
import os
import json
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from hashlib import sha256
import jwt as pyjwt

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Your configuration
PRIVATE_KEY_FILE = '/Users/tspann/.snowflake/keys/snowflake_private_key.p8'
ACCOUNT = 'SFSENORTHAMERICA-TSPANN-AWS1'
USER = 'KAFKAGUY'
ROLE = 'ACCOUNTADMIN'

print("=" * 70)
print("JWT TOKEN DEBUG")
print("=" * 70)

try:
    # Load private key
    print(f"\n1. Loading private key: {PRIVATE_KEY_FILE}")
    with open(PRIVATE_KEY_FILE, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    print("[OK] Private key loaded")
    
    # Extract public key fingerprint
    public_key_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    fingerprint = 'SHA256:' + sha256(public_key_bytes).hexdigest().upper()
    
    print(f"\n2. Public key fingerprint:")
    print(f"   {fingerprint}")
    
    # Construct qualified username
    account_upper = ACCOUNT.upper()
    user_upper = USER.upper()
    qualified_username = f"{account_upper}.{user_upper}"
    
    print(f"\n3. Qualified username:")
    print(f"   {qualified_username}")
    
    # Create JWT payload
    now = datetime.now(timezone.utc)
    iat = int(now.timestamp())
    exp = int((now + timedelta(hours=1)).timestamp())
    
    issuer = f"{qualified_username}.{fingerprint}"
    
    payload = {
        'iss': issuer,
        'sub': qualified_username,
        'iat': iat,
        'exp': exp
    }
    
    print(f"\n4. JWT Payload:")
    print(f"   iss: {issuer}")
    print(f"   sub: {qualified_username}")
    print(f"   iat: {iat} ({datetime.fromtimestamp(iat, timezone.utc)})")
    print(f"   exp: {exp} ({datetime.fromtimestamp(exp, timezone.utc)})")
    
    # Generate JWT
    token = pyjwt.encode(payload, private_key, algorithm='RS256')
    
    print(f"\n5. JWT Token generated:")
    print(f"   Length: {len(token)} characters")
    print(f"   First 50 chars: {token[:50]}...")
    print(f"   Last 50 chars: ...{token[-50:]}")
    
    # Decode JWT (without verification) to show what's inside
    decoded = pyjwt.decode(token, options={"verify_signature": False})
    print(f"\n6. JWT Token contents (decoded):")
    print(json.dumps(decoded, indent=2))
    
    # OAuth URL
    account_lower = ACCOUNT.lower()
    oauth_url = f"https://{account_lower}.snowflakecomputing.com/oauth/token"
    
    print(f"\n7. OAuth endpoint:")
    print(f"   {oauth_url}")
    
    print(f"\n8. OAuth request data:")
    print(f"   grant_type: urn:ietf:params:oauth:grant-type:jwt-bearer")
    print(f"   assertion: <JWT token>")
    print(f"   scope: session:role:{ROLE.upper()}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Verify the public key is registered in Snowflake:")
    print(f"   DESC USER {USER};")
    print(f"   -- Look for RSA_PUBLIC_KEY_FP")
    print(f"\n2. The fingerprint should match:")
    print(f"   {fingerprint}")
    print(f"\n3. If not matching, run:")
    print(f"   python extract_public_key.py")
    print(f"   -- Then run the SQL command it generates")
    print("\n4. Verify the account identifier is correct:")
    print(f"   Account in config: {ACCOUNT}")
    print(f"   Should match your Snowflake URL")
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

