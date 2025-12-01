#!/bin/bash
################################################################################
# PRODUCTION STARTUP SCRIPT
# Raspberry Pi Thermal Sensor → Snowflake Streaming
################################################################################
#
# PRODUCTION MODE REQUIREMENTS:
#   1. Physical sensors MUST be connected and working (SCD4X, ICP10125, SGP30)
#   2. ONLY Snowpipe Streaming v2 REST API is used (no direct inserts)
#   3. Valid Snowflake configuration with PAT or JWT authentication
#
# This script will:
#   - Verify configuration
#   - Clear Python cache
#   - Check Snowpipe Streaming client
#   - Start application in PRODUCTION mode
#
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================================================"
echo -e "${BLUE}PRODUCTION STARTUP - Thermal Sensor Streaming${NC}"
echo "========================================================================"
echo ""
echo -e "${YELLOW}PRODUCTION MODE:${NC}"
echo "  - Real physical sensors REQUIRED (no simulation)"
echo "  - Snowpipe Streaming v2 REST API ONLY (no direct inserts)"
echo "  - High-performance streaming to Snowflake"
echo ""
echo "========================================================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo -e "${YELLOW}[WARNING]${NC} Not running on Raspberry Pi"
    echo "Continuing anyway, but sensors may not be available..."
    echo ""
fi

# Check if config file exists
if [ ! -f "snowflake_config.json" ]; then
    echo -e "${RED}[ERROR]${NC} snowflake_config.json not found!"
    echo "Please create configuration file first."
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Configuration file found"
echo ""

# Clear Python cache
echo "Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}[OK]${NC} Python cache cleared"
echo ""

# Verify Python modules
echo "Verifying Snowpipe Streaming client..."
python3 -c "
import sys
sys.path.insert(0, '.')
from thermal_streaming_client import SnowpipeStreamingClient
print('[OK] SnowpipeStreamingClient loaded')
assert hasattr(SnowpipeStreamingClient, 'insert_rows'), 'insert_rows method missing'
assert hasattr(SnowpipeStreamingClient, 'append_rows'), 'append_rows method missing'
print('[OK] All required methods available')
" || {
    echo -e "${RED}[ERROR]${NC} Failed to verify Snowpipe Streaming client"
    exit 1
}
echo ""

# Parse command line arguments
BATCH_SIZE=10
INTERVAL=5.0
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --batch-size N    Number of readings per batch (default: 10)"
            echo "  --interval N      Seconds between batches (default: 5.0)"
            echo "  --verbose         Enable verbose logging"
            echo "  --help            Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "========================================================================"
echo -e "${GREEN}Starting PRODUCTION application...${NC}"
echo "========================================================================"
echo "Configuration:"
echo "  - Batch size: $BATCH_SIZE readings"
echo "  - Interval: $INTERVAL seconds"
echo "  - Mode: PRODUCTION (real sensors only)"
echo "========================================================================"
echo ""

# Start the application
python3 main.py \
    --batch-size "$BATCH_SIZE" \
    --interval "$INTERVAL" \
    $VERBOSE

# Capture exit code
EXIT_CODE=$?

echo ""
echo "========================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}Application exited successfully${NC}"
else
    echo -e "${RED}Application exited with error code: $EXIT_CODE${NC}"
fi
echo "========================================================================"

exit $EXIT_CODE

