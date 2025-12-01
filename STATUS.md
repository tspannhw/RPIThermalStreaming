# Current Status - Snowpipe Streaming v2 REST API

## Summary

The application has been configured to use Snowpipe Streaming v2 REST API exclusively, but we've encountered a blocking issue with the REST API implementation.

## What Works ✅

1. **PAT Authentication** - Successfully authenticating with Programmatic Access Tokens
2. **Ingest Host Discovery** - `/v2/streaming/hostname` endpoint works correctly
3. **Channel Registration** - `/v2/streaming/databases/{db}/schemas/{schema}/pipes/{pipe}/channels/{channel}:register` returns success and continuation token
4. **Sensor Reading** - Simulated and real sensor data collection works
5. **Application Structure** - Main loop, batching, error handling all functional
6. **Permissions** - OPERATE privilege granted on pipe

## What Doesn't Work ❌

### Core Issue: Data Append Fails

**Error:** `ERR_CHANNEL_DOES_NOT_EXIST_OR_IS_NOT_AUTHORIZED`

**Endpoint:** `POST https://{ingest_host}/v2/streaming/data/databases/{db}/schemas/{schema}/pipes/{pipe}/channels/{channel}/rows`

**Symptoms:**
- Channel registration succeeds (status 200, returns continuation token)
- Immediately after registration, data append fails (status 400)
- Error persists even with:
  - Unique channel names (timestamp-based)
  - Fresh continuation tokens  
  - Correct authentication headers
  - Valid offsetToken incrementing

**Testing Done:**
1. Tried `:open` suffix → Got back channel named `"TH_CHNL:open"` (wrong)
2. Tried `:register` suffix → Channel registers but data append fails
3. Tried POST method → 405 Method Not Allowed
4. Tried PUT method → Works for registration, fails for append
5. Tried unique channel names → Same error
6. Tried different continuation tokens → Same error

## Root Cause Analysis

### Hypothesis 1: REST API Not Fully Released
The Snowpipe Streaming v2 REST API appears to be documented but may not be fully implemented or available on all Snowflake accounts. Evidence:
- `snowflake-ingest` SDK only has v1.0.12 (v2 doesn't exist)
- Channel registration works but data plane doesn't recognize channels
- No official Python examples using pure REST API (all use SDK)

### Hypothesis 2: Missing Configuration/Setup
There may be account-level settings or additional setup steps required:
- Special feature flags that need to be enabled
- Additional grants beyond OPERATE on pipe
- Specific account configuration for REST API access

### Hypothesis 3: API Documentation Incomplete
The public documentation may not include all required steps or parameters:
- Missing headers or payload fields
- Undocumented channel activation step
- Different endpoint structure than documented

## Recommendations

### Option 1: Contact Snowflake Support ⭐ RECOMMENDED
**Action:** Open a support case to ask about Snowpipe Streaming v2 REST API availability

**Questions to Ask:**
1. Is the Snowpipe Streaming v2 REST API fully available on our account type?
2. Are there additional account-level settings or feature flags needed?
3. Why does channel registration succeed but data appends fail with `ERR_CHANNEL_DOES_NOT_EXIST_OR_IS_NOT_AUTHORIZED`?
4. Can you provide working Python examples using the REST API (not SDK)?
5. What's the status of the `snowflake-ingest` v2 SDK?

**Include in Support Case:**
- Account: `SFSENORTHAMERICA-TSPANN-AWS1`
- Error logs from this application
- Confirmation that OPERATE privilege is granted
- Confirmation that PAT authentication works

### Option 2: Wait for SDK v2 Release
**Pros:**
- SDK handles all complexity
- Official support and examples
- Better error handling

**Cons:**
- No ETA on release
- Can't proceed with project

### Option 3: Use Direct SQL INSERT (Temporary Workaround)
**Status:** Previously working, removed per user request

**Pros:**
- Works immediately
- Simple implementation
- Proven reliable

**Cons:**
- Higher latency (15-30s vs 5-10s)
- Requires running warehouse (compute costs)
- Not the intended streaming approach

**To Re-enable:**
1. Restore `thermal_direct_insert.py` from git history
2. Update `main.py` to import `SnowflakeDirectClient`
3. Run application

### Option 4: Continue REST API Debugging
**Next Steps to Try:**
1. Add more verbose logging to see full HTTP requests/responses
2. Try different pipe configurations
3. Test with a minimal example (single row, simple data)
4. Check if there's a Snowflake community forum post about this
5. Review Snowflake's GitHub repositories for examples

## Technical Details

### Working Authentication Flow
```
1. GET /v2/streaming/hostname
   → Returns: LXB29530.ingest.iadaax.snowflakecomputing.com
   
2. PUT /v2/streaming/databases/DEMO/schemas/DEMO/pipes/THERMAL_SENSOR_PIPE/channels/{channel}:register
   Headers: Authorization: Bearer {PAT}
   Payload: {"write_mode": "CLOUD_STORAGE", "role": "ACCOUNTADMIN"}
   → Returns: {"next_continuation_token": "0_1", "channel_status": {...}}
```

### Failing Data Append
```
3. POST /v2/streaming/data/databases/DEMO/schemas/DEMO/pipes/THERMAL_SENSOR_PIPE/channels/{channel}/rows
   Params: continuationToken=0_1, offsetToken=1
   Headers: Authorization: Bearer {PAT}, Content-Type: application/x-ndjson
   Body: {JSON}\n{JSON}\n...
   → Returns: 400 {"code":"ERR_CHANNEL_DOES_NOT_EXIST_OR_IS_NOT_AUTHORIZED","message":""}
```

## Files Status

### Core Files
- ✅ `thermal_sensor.py` - Sensor reading (working)
- ✅ `snowflake_jwt_auth.py` - PAT authentication (working)
- ⚠️  `thermal_streaming_client.py` - REST API client (partial - registration works, append fails)
- ✅ `main.py` - Application orchestration (working, waiting for append to work)
- ❌ `thermal_direct_insert.py` - Deleted per user request (was working)

### Configuration
- ✅ `snowflake_config.json` - PAT configured
- ✅ `FINAL_FIX.sql` - Permissions granted
- ✅ `requirements.txt` - Dependencies installed

### Documentation
- ✅ `README.md` - Complete documentation
- ✅ `MIGRATION_TO_REST_API.md` - Migration notes
- ✅ `QUICK_START.md` - Setup guide
- ✅ `GRANT_PERMISSIONS.sql` - Permission fixes
- 📄 `STATUS.md` - This file

## Next Steps

**Immediate:** Contact Snowflake Support with the questions above

**Meanwhile:** Consider temporarily re-enabling direct insert so the project can proceed

**Long-term:** Once REST API issue is resolved or SDK v2 is released, switch to proper streaming approach

## Contact Info for Support Case

- **Account ID:** SFSENORTHAMERICA-TSPANN-AWS1
- **User:** THERMAL_STREAMING_USER
- **Role:** ACCOUNTADMIN
- **Pipe:** DEMO.DEMO.THERMAL_SENSOR_PIPE
- **Authentication:** Programmatic Access Token (PAT)
- **Issue:** REST API channel registration succeeds but data append returns ERR_CHANNEL_DOES_NOT_EXIST_OR_IS_NOT_AUTHORIZED

---

**Last Updated:** 2025-11-26
**Status:** ⚠️ Blocked on Snowflake REST API issue

