#!/bin/bash
# ============================================================================
# Quick Start Script for Raspberry Pi Thermal Streaming
# ============================================================================
# This script helps you set up the application quickly.
#
# Usage: ./quickstart.sh
# ============================================================================

set -e

echo "============================================================================"
echo "Raspberry Pi Thermal Sensor Streaming to Snowflake"
echo "Quick Start Setup"
echo "============================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check if Python 3.9+
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "ERROR: Python 3.9 or later is required!"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version OK"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Generate keys if they don't exist
if [ ! -f "rsa_key.p8" ]; then
    echo "RSA keys not found. Generating keys..."
    chmod +x generate_keys.sh
    ./generate_keys.sh
    echo ""
else
    echo "✓ RSA keys already exist"
    echo ""
fi

# Create config file if it doesn't exist
if [ ! -f "snowflake_config.json" ]; then
    echo "Creating configuration file from template..."
    cp snowflake_config.json.template snowflake_config.json
    echo "✓ Configuration file created"
    echo ""
    echo "IMPORTANT: Edit snowflake_config.json with your Snowflake details!"
    echo ""
else
    echo "✓ Configuration file already exists"
    echo ""
fi

# Summary
echo "============================================================================"
echo "Setup Complete!"
echo "============================================================================"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Register public key in Snowflake:"
echo "   - Copy the ALTER USER command from generate_keys.sh output"
echo "   - Run it in Snowflake"
echo ""
echo "2. Run setup_snowflake.sql in Snowflake to create:"
echo "   - User, role, database, schema"
echo "   - Table and pipe"
echo ""
echo "3. Edit snowflake_config.json with your Snowflake details:"
echo "   - account: Your Snowflake account identifier"
echo "   - database, schema, pipe: Names from setup script"
echo ""
echo "4. Test the connection:"
echo "   python test_connection.py"
echo ""
echo "5. Run the application:"
echo "   python main.py --simulate"
echo ""
echo "For more information, see README.md"
echo "============================================================================"

