# URGENT FIX: PyPy Trace Limit Too High

## Problem Identified

The `trace_limit=200000` in the diagnostic was **TOO HIGH** for your PyPy version and caused a `TraceLimitTooHigh` SystemError. This likely disabled JIT compilation entirely, explaining the terrible performance.

## Solution

### Option 1: Use the Fixed Diagnostic (Recommended)

```bash
# Pull the updated diagnostic
git pull origin main

# Run it - it will now try progressively lower trace limits
python diagnose_pypy_jit.py
```

### Option 2: Use the Startup Script

```bash
# Use the new startup script that auto-configures JIT
python start_with_jit.py
```

### Option 3: Manual Fix in Your Systemd Service

Edit your systemd service file to configure JIT properly:

```bash
sudo nano /etc/systemd/system/pipier-api.service
```

Add this BEFORE the ExecStart line:

```ini
[Service]
# Configure PyPy JIT before starting
ExecStartPre=/root/pipier_love_api/venv/bin/python -c "import pypyjit; pypyjit.set_param('trace_limit=20000')"
ExecStart=/root/pipier_love_api/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart pipier-api
```

## What Happened

1. **Default PyPy trace limit**: ~6,000-10,000 operations
2. **Your diagnostic tried**: 200,000 operations (20x default!)
3. **Result**: `TraceLimitTooHigh` exception → JIT likely disabled entirely
4. **Effect**: Running in interpreter mode only → 30k NPS instead of 300k+

## Expected Results After Fix

- **With trace_limit=20000**: Should see 200k-300k NPS
- **With trace_limit=50000**: May see 300k-400k NPS (if accepted)
- **With default (~6000)**: Should still see 150k-250k NPS

The key is that the JIT needs to be ENABLED and not crashed by too-high limits.

## Verification

After applying the fix, run:

```bash
python critical_tests.py
```

You should see:
- ✅ TEST 2 (perft): **200,000+ NPS** (currently 26k)
- ✅ TEST 3 (search): **100,000+ NPS** (currently 1.1k)

## Root Cause

The `pypyjit.set_param('trace_limit=200000')` call in the diagnostic crashed and likely put PyPy into a degraded state. This is why removing python-chess didn't improve performance - the JIT was effectively disabled by the trace limit exception.
