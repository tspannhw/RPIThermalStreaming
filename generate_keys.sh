#!/bin/bash
# ============================================================================
# Generate RSA Key Pair for Snowflake Authentication
# ============================================================================
# This script generates a private/public key pair for authenticating with
# Snowflake using key-pair authentication.
#
# Usage: ./generate_keys.sh
# ============================================================================

set -e

echo "Generating RSA key pair for Snowflake authentication..."
echo ""

# Check if keys already exist
if [ -f "rsa_key.p8" ]; then
    echo "WARNING: rsa_key.p8 already exists!"
    read -p "Do you want to overwrite it? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        echo "Aborted. Existing keys preserved."
        exit 0
    fi
fi

# Generate private key (PKCS#8 format, unencrypted)
echo "Step 1: Generating private key (rsa_key.p8)..."
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
echo "Step 2: Generating public key (rsa_key.pub)..."
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Format public key for Snowflake
echo ""
echo "Step 3: Formatting public key for Snowflake..."
PUBK=$(cat ./rsa_key.pub | grep -v KEY- | tr -d '\012')

echo ""
echo "✓ Keys generated successfully!"
echo ""
echo "============================================================================"
echo "NEXT STEPS:"
echo "============================================================================"
echo ""
echo "1. Copy the following SQL command and run it in Snowflake:"
echo ""
echo "   ALTER USER THERMAL_STREAMING_USER SET RSA_PUBLIC_KEY='${PUBK}';"
echo ""
echo "2. Update your snowflake_config.json with:"
echo "   - Your Snowflake account identifier"
echo "   - Database, schema, and pipe names"
echo "   - Ensure private_key_file points to: rsa_key.p8"
echo ""
echo "3. IMPORTANT: Keep rsa_key.p8 secure and never commit it to version control!"
echo ""
echo "============================================================================"
echo ""

# Set secure permissions on private key
chmod 600 rsa_key.p8
echo "Private key permissions set to 600 (owner read/write only)"
echo ""

