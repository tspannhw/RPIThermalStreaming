#!/bin/bash
#
# Deploy updated files to Raspberry Pi
#
# Usage:
#   ./deploy_to_pi.sh [pi@thermal]
#

# Configuration
PI_HOST="${1:-pi@thermal}"
PI_DIR="/opt/demo/rpisnow"
LOCAL_DIR="/Users/tspann/Downloads/code/cursorai/RPIThermalStreaming"

echo "=========================================="
echo "Deploying to Raspberry Pi"
echo "=========================================="
echo "Host: $PI_HOST"
echo "Remote directory: $PI_DIR"
echo "Local directory: $LOCAL_DIR"
echo ""

# Files to deploy
FILES=(
    "thermal_sensor.py"
    "thermal_streaming_client.py"
    "main.py"
    "test_performance.py"
    "diagnose_performance.py"
    "snowflake_config.json"
)

# Deploy each file
for file in "${FILES[@]}"; do
    echo "Deploying $file..."
    scp "$LOCAL_DIR/$file" "$PI_HOST:$PI_DIR/$file"
    
    if [ $? -eq 0 ]; then
        echo "[OK] $file deployed successfully"
    else
        echo "[ERROR] Failed to deploy $file"
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "[OK] Deployment Complete!"
echo "=========================================="
echo ""
echo "To restart the application on Raspberry Pi:"
echo "  ssh $PI_HOST"
echo "  cd $PI_DIR"
echo "  python3 main.py --batch-size 100 --interval 10.0 --fast"
echo ""

