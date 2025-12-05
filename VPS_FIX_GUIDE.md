# URGENT: VPS Performance Problem Diagnosis

## Problem Summary

Your VPS shows PyPy is installed and running, BUT the chess engine is performing at only **12,000 NPS** - this is:
- **4x slower** than CPython should be (40k NPS)
- **100x slower** than PyPy should be (1M NPS)

## Root Cause (Suspected)

Your service file shows:
```
ExecStart=/root/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

The venv was probably created with **regular Python**, not PyPy!

Evidence:
- Service shows: `/root/venv/bin/pypy3 /root/venv/bin/uvicorn`
- But the venv itself might be a CPython venv with PyPy installed as a package
- This creates a mixed environment that runs SLOW

## Quick Diagnostic

Run this to check if venv is using PyPy:
```bash
cd /root/pipier_love_api
bash check_venv_python.sh
```

Look for:
```
3. Venv Python:
```

If it says `Python 3.x.x` (without PyPy), **that's the problem!**

## The Fix

### Option 1: Automated Fix (Recommended)
```bash
cd /root/pipier_love_api
bash fix_venv_pypy.sh
```

This will:
1. Backup your current venv
2. Create new venv with PyPy: `pypy3 -m venv venv`
3. Install requirements with PyPy pip
4. Restart service
5. Test performance

### Option 2: Manual Fix
```bash
cd /root/pipier_love_api

# Backup old venv
mv venv venv.old

# Create new venv with PyPy
pypy3 -m venv venv

# Activate and install
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Test
python --version  # Should show PyPy!

# Restart service
sudo systemctl restart piperlove.service
```

## Expected Results

### Before Fix:
```
info depth 7 nodes 66580 nps 12049
```
- 12k NPS (terrible!)
- Depth 7 with only 66k nodes

### After Fix:
```
info depth 7 nodes 5000000+ nps 800000+
```
- 800k+ NPS (good PyPy performance)
- Depth 7 with 5M+ nodes
- Much stronger gameplay!

## Verification

After applying the fix, watch the service logs:
```bash
journalctl -u piperlove.service -f
```

Play a move on the website and watch for:
```
info depth X score cp Y nodes ZZZZZ nps NNNNNN
```

The `nps NNNNNN` should show:
- ✅ **100,000+**: PyPy is working!
- ⚠️ **30,000-50,000**: CPython (not PyPy)
- ❌ **< 30,000**: Something is very wrong

## Why This Happened

When you created the venv initially, you probably used:
```bash
python3 -m venv venv  # ← This creates CPython venv!
```

Instead of:
```bash
pypy3 -m venv venv    # ← This creates PyPy venv!
```

Then when you ran `pip install` inside the CPython venv, it installed PyPy as a package, but the venv's Python interpreter is still CPython.

## Files to Help You

1. `check_venv_python.sh` - Check what Python your venv is using
2. `fix_venv_pypy.sh` - Automatically fix the venv to use PyPy
3. `check_vps_pypy.sh` - Test performance after fix

## Next Steps

1. Run: `bash check_venv_python.sh`
2. If venv shows CPython, run: `bash fix_venv_pypy.sh`
3. Verify logs show high NPS during gameplay
4. Enjoy 100x faster chess engine! 🚀
