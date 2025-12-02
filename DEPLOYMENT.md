# Deployment Guide - Mac to Raspberry Pi

## Quick Fix for Current Error

The error you're seeing:
```
TypeError: ThermalSensor.read_batch() got an unexpected keyword argument 'fast_mode'
```

**Cause**: Your Raspberry Pi has an old version of `thermal_sensor.py` without the `fast_mode` parameter.

**Solution**: Deploy the updated files to your Raspberry Pi.

---

## Easy Deployment - Using Script

### Step 1: Run the deployment script

```bash
cd /Users/tspann/Downloads/code/cursorai/RPIThermalStreaming
./deploy_to_pi.sh pi@thermal
```

This will automatically copy:
- `thermal_sensor.py` (with fast_mode support)
- `thermal_streaming_client.py`
- `main.py`
- `snowflake_config.json`

### Step 2: SSH into Raspberry Pi and restart

```bash
ssh pi@thermal
cd /opt/demo/rpisnow
python3 main.py --batch-size 100 --interval 10.0 --fast
```

---

## Manual Deployment - Using SCP

If you prefer to copy files manually:

```bash
# From your Mac terminal
cd /Users/tspann/Downloads/code/cursorai/RPIThermalStreaming

# Copy updated Python files
scp thermal_sensor.py pi@thermal:/opt/demo/rpisnow/
scp thermal_streaming_client.py pi@thermal:/opt/demo/rpisnow/
scp main.py pi@thermal:/opt/demo/rpisnow/

# Verify files were copied
ssh pi@thermal "ls -lh /opt/demo/rpisnow/*.py"
```

---

## Verify Deployment

### Check file timestamps on Raspberry Pi

```bash
ssh pi@thermal "ls -lh /opt/demo/rpisnow/thermal_sensor.py"
```

You should see a recent timestamp (today's date).

### Check for fast_mode parameter

```bash
ssh pi@thermal "grep -n 'fast_mode' /opt/demo/rpisnow/thermal_sensor.py"
```

Expected output:
```
346:            fast_mode: If True, collect readings as fast as possible with minimal delay
354:        actual_interval = 0.05 if fast_mode else interval  # 50ms in fast mode
```

---

## Troubleshooting

### Issue: Permission Denied

```bash
# Add execute permission to deployment script
chmod +x deploy_to_pi.sh

# Or manually copy files with sudo on Raspberry Pi
ssh pi@thermal
sudo cp ~/thermal_sensor.py /opt/demo/rpisnow/
sudo chown pi:pi /opt/demo/rpisnow/thermal_sensor.py
```

### Issue: Connection Refused

```bash
# Test SSH connection first
ssh pi@thermal

# If this fails, check:
# 1. Raspberry Pi is powered on
# 2. Network connection is working
# 3. SSH is enabled on Raspberry Pi
```

### Issue: File Not Found on Raspberry Pi

```bash
# Create directory if it doesn't exist
ssh pi@thermal "sudo mkdir -p /opt/demo/rpisnow"
ssh pi@thermal "sudo chown -R pi:pi /opt/demo/rpisnow"
```

---

## Files to Keep Synchronized

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| `thermal_sensor.py` | Sensor reading logic | When adding features |
| `thermal_streaming_client.py` | Snowflake API client | When API changes |
| `main.py` | Application entry point | When changing behavior |
| `snowflake_config.json` | Credentials | Rarely (keep secure!) |

---

## Best Practices

### 1. Test Locally First (Mac)

```bash
# On Mac - test with simulation
python3 main.py --batch-size 10 --interval 5.0 --fast
```

### 2. Deploy to Raspberry Pi

```bash
./deploy_to_pi.sh
```

### 3. Test on Raspberry Pi

```bash
ssh pi@thermal
cd /opt/demo/rpisnow
python3 main.py --batch-size 100 --interval 10.0 --fast
```

### 4. Monitor Performance

Check Snowflake for data arrival:
```sql
SELECT 
    local_hostname,
    COUNT(*) as row_count,
    MAX(datetimestamp) as latest
FROM DEMO.DEMO.THERMAL_DATA
WHERE datetimestamp >= DATEADD(minute, -5, CURRENT_TIMESTAMP())
GROUP BY local_hostname;
```

---

## Using Git for Deployment (Optional)

If you want to use Git for version control:

### Initial Setup on Raspberry Pi

```bash
ssh pi@thermal
cd /opt/demo
sudo rm -rf rpisnow  # Backup first if needed!
sudo git clone https://github.com/YOUR_USERNAME/RPIThermalStreaming.git rpisnow
cd rpisnow
```

### Future Updates

```bash
# On Mac - commit and push changes
cd /Users/tspann/Downloads/code/cursorai/RPIThermalStreaming
git add .
git commit -m "Added fast_mode support"
git push origin main

# On Raspberry Pi - pull changes
ssh pi@thermal
cd /opt/demo/rpisnow
git pull origin main
python3 main.py --batch-size 100 --interval 10.0 --fast
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `./deploy_to_pi.sh` | Deploy all files to Raspberry Pi |
| `ssh pi@thermal` | Connect to Raspberry Pi |
| `cd /opt/demo/rpisnow` | Navigate to app directory |
| `python3 main.py --fast` | Run with fast mode |
| `Ctrl+C` | Stop the application |

---

## Next Steps After Deployment

1. ✅ Deploy updated files to Raspberry Pi
2. ✅ Start application with `--fast` flag
3. ✅ Monitor performance (should see 20+ rows/sec)
4. ✅ Check Snowflake for data arrival
5. ✅ Verify `local_hostname` field shows "thermal"

**Expected Performance After Fix:**
- Throughput: **20+ rows/sec** (instead of 0.21)
- Batch size: 100 readings
- Interval: 10 seconds
- Local hostname: "thermal"

