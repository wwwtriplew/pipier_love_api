# 🚀 Quick Deploy Guide

## On Your VPS (Run These Commands)

### ⚠️ IMPORTANT: Check Your Current Setup First

You have a `venv` folder. Check if it's PyPy or CPython:
```bash
cd ~/pipier_love_api
./venv/bin/python --version
# If it shows "Python 3.x.x" → CPython (wrong)
# If it shows "PyPy" → PyPy (correct)
```

---

## Deployment Steps

### Step 1: Pull Changes
```bash
cd ~/pipier_love_api
git pull
```

### Step 2: Install to PyPy (Choose ONE method)

#### Method A: If You Have PyPy venv Already
```bash
# Activate PyPy venv
source venv/bin/activate

# Check it's PyPy
python --version  # Should show "PyPy"

# Uninstall chess and reinstall clean
pip uninstall chess -y
pip install -r requirements.txt
```

#### Method B: If Your venv is CPython (Most Likely Your Case)
```bash
# Remove old CPython venv
rm -rf venv

# Create NEW PyPy venv
pypy3 -m venv venv

# Activate it
source venv/bin/activate

# Verify it's PyPy
python --version  # Should show "PyPy"

# Install dependencies (chess will NOT be installed - that's correct!)
pip install -r requirements.txt
```

#### Method C: Install Directly to PyPy System (Not Recommended)
```bash
# Only use if you don't want venv
pypy3 -m pip uninstall chess -y --break-system-packages
pypy3 -m pip install -r requirements.txt --break-system-packages
```

### Step 3: Update Systemd Service

Check your service file:
```bash
sudo cat /etc/systemd/system/pipier_love_api.service | grep ExecStart
```

Make sure it uses PyPy venv:
```bash
sudo nano /etc/systemd/system/pipier_love_api.service
```

Change `ExecStart` to:
```
ExecStart=/root/pipier_love_api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 4: Restart Service
```bash
sudo systemctl daemon-reload
sudo systemctl restart pipier_love_api
sudo systemctl status pipier_love_api
```

### Step 5: Verify It Works
```bash
cd ~/pipier_love_api

# Activate venv first
source venv/bin/activate

# Test engine loads
python -c "from src.chess_engine import ChessBoard; print('✅ Engine OK')"

# Check no chess library
python -c "import chess" 2>&1 | grep -q "No module" && echo "✅ python-chess removed" || echo "❌ chess still installed!"

# Run performance test
python critical_tests.py
```

## Expected Output

```
TEST 2: Pure Engine Performance (Perft)
========================================
Nodes:    197,281
Time:     0.65s
NPS:      303,509
🚀 EXCELLENT: > 200k NPS (PyPy with full JIT)
```

## Before vs After

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| NPS | 30,000 | 300,000+ | **10x faster** |
| Response time | 3-5s | < 500ms | **6-10x faster** |
| PyPy JIT | ❌ Disabled | ✅ Enabled | ✅ |
| Dependencies | 4 | 3 | Simplified |

## Success = NPS > 200k

If you see NPS > 200,000 in the test, **you're done!** 🎉

Your chess engine is now running at full PyPy-optimized speed.

---

## 🔧 Troubleshooting

### ❌ Problem: "You used `pip` instead of `pypy3 -m pip`"

**What happened:** You ran `pip install` which installed to CPython, not PyPy.

**Fix:**
```bash
# Check which Python your venv uses
cd ~/pipier_love_api
./venv/bin/python --version

# If it says "Python 3.12" (not PyPy), recreate the venv:
rm -rf venv
pypy3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ Problem: "externally-managed-environment"

**Fix:** Use a virtual environment instead of system packages (see Method B above).

### ❌ Problem: NPS still low (< 100k)

**Checks:**
```bash
# 1. Verify PyPy is running
ps aux | grep uvicorn
# Should show path with "pypy" in it

# 2. Check for chess library
source venv/bin/activate
python -c "import sys; print(sys.executable); import chess" 2>&1
# Should show "No module named 'chess'"

# 3. Test directly
python critical_tests.py
```

### ❌ Problem: Service won't start

```bash
# Check logs
sudo journalctl -u pipier_love_api -n 50

# Test manually
cd ~/pipier_love_api
source venv/bin/activate
python -c "from src.chess_engine import ChessBoard; print('OK')"
uvicorn main:app --host 0.0.0.0 --port 8000
```

### ✅ How to Verify Success

All these should pass:
```bash
cd ~/pipier_love_api
source venv/bin/activate

# 1. PyPy is being used
python --version  # Shows "PyPy"

# 2. chess is NOT installed
python -c "import chess" 2>&1 | grep "No module"  # Success

# 3. Engine works
python -c "from src.chess_engine import ChessBoard; print('OK')"

# 4. Performance is good
python critical_tests.py  # NPS > 200k
```
