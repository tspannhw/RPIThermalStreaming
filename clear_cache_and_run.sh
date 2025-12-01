#!/bin/bash
# Clear Python cache and run the thermal streaming application
# PRODUCTION MODE: Real sensors + Snowpipe Streaming REST API only

echo "========================================================================"
echo "PRODUCTION MODE: Real Sensors + Snowpipe Streaming REST API ONLY"
echo "========================================================================"
echo ""
echo "Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "Python cache cleared."
echo ""
echo "Verifying Snowpipe Streaming client..."
python3 -c "from thermal_streaming_client import SnowpipeStreamingClient; print('[OK] SnowpipeStreamingClient loaded'); print('[OK] insert_rows method exists:', hasattr(SnowpipeStreamingClient, 'insert_rows'))"
echo ""
echo "Starting PRODUCTION application (real sensors only)..."
python3 main.py "$@"

