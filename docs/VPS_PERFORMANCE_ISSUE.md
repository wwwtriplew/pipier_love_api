# VPS Performance Issue Analysis

## Current Status

Your VPS is running PyPy successfully, but the performance is CRITICALLY SLOW.

### Evidence from Logs:
```
info depth 7 score cp -30 nodes 66580 nps 12049 time 5525
```

**Analysis:**
- Depth: 7 plies
- Nodes: 66,580 positions
- Time: 5.5 seconds
- **NPS: 12,049** ← EXTREMELY SLOW!

### Expected Performance

**With PyPy (properly optimized):**
- Depth 7: Should search 5-10 MILLION nodes
- NPS: 500,000 - 2,000,000
- Time: 5-10 seconds for 10M nodes

**Your actual:**
- NPS: 12,049 (50-150x slower than expected!)
- Nodes: 66k (150x fewer than expected!)

## Why So Slow?

### Possible Causes:

1. **PyPy Not Actually Running Engine Code** ❌
   - Service shows: `/root/venv/bin/pypy3 /root/venv/bin/uvicorn`
   - This means uvicorn is running with PyPy
   - BUT: The chess engine code might still be using CPython modules!

2. **Virtual Environment Issue** ⚠️
   - You're using `/root/venv/bin/pypy3`
   - The venv might not have PyPy-compatible packages
   - Or it's mixing PyPy and CPython somehow

3. **Import Issues** ⚠️
   - If any C-extension modules are imported, PyPy falls back to slow mode
   - Check if you're importing numpy, scipy, or other C extensions

4. **No JIT Warmup** (Unlikely after 20 hours) ❌
   - PyPy needs warmup, but you've been running 20 hours
   - Should be fully warmed up by now

5. **Slow Search Algorithm** ⚠️
   - Your search might be doing extra work
   - Check for debug logging, expensive operations

## Quick Diagnostic Commands

Run these on your VPS:

### 1. Check what's imported
```bash
# Check service logs for import errors
journalctl -u piperlove.service | grep -i import

# Check for C extensions
pypy3 -c "import sys; print(sys.modules.keys())" | grep numpy
```

### 2. Test perft performance directly
```bash
cd /root/pipier_love_api

# Once you pull the fixed scripts:
bash check_vps_pypy.sh
```

### 3. Check venv Python version
```bash
/root/venv/bin/python3 --version
# Should show PyPy, not CPython!
```

### 4. Verify PyPy venv setup
```bash
ls -la /root/venv/bin/ | grep python
# Should see pypy3 symlinks
```

## Recommended Fix

### Option 1: Recreate venv with PyPy
```bash
cd /root/pipier_love_api

# Remove old venv
rm -rf venv

# Create new venv with PyPy
pypy3 -m venv venv

# Install requirements
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart piperlove.service
```

### Option 2: Use system PyPy directly
```bash
# Edit service file
sudo nano /etc/systemd/system/piperlove.service

# Change ExecStart to use system PyPy:
ExecStart=/usr/bin/pypy3 -m uvicorn main:app --host 127.0.0.1 --port 8000

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart piperlove.service
```

## Expected After Fix

Once PyPy is properly running your engine code:

**Perft(4) benchmark:**
- CPython: ~5s (40k NPS)
- PyPy: ~0.2s (1M NPS)
- **Speedup: 25x**

**Browser gameplay (12-second search):**
- Before: 100k-150k nodes (depth 5-6)
- After: 6-24M nodes (depth 7-8)
- **Strength: Much stronger!**

## Action Items

1. ✅ Pull the fixed diagnostic scripts: `git pull`
2. ✅ Run diagnostic: `bash check_vps_pypy.sh`
3. ⚠️ Check if perft shows good speed (should be 1M NPS)
4. ⚠️ If perft is fast but search is slow, there's a search issue
5. ⚠️ If perft is ALSO slow, PyPy isn't running engine code properly

## Next Steps

After you run the diagnostic, let me know:
1. What's the perft NPS?
2. Is there any error in the perft test?
3. What does `/root/venv/bin/python3 --version` show?

Then we can pinpoint the exact issue!
