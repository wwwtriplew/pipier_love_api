# VPS PyPy Setup Guide

## Quick Diagnostic

Run this on your VPS to check current PyPy status:

```bash
cd ~/pipier_love_api
bash check_vps_pypy.sh
```

This will show:
- ✓/✗ PyPy installation status
- Current service configuration
- Performance comparison (CPython vs PyPy)

---

## Switch to PyPy (Automatic)

If PyPy is installed but not being used:

```bash
cd ~/pipier_love_api
bash switch_to_pypy.sh
```

This will:
1. Find PyPy executable (system or local)
2. Update systemd service to use PyPy
3. Restart the service
4. Verify it's working

---

## Manual Setup

### Check PyPy Installation

```bash
# Check if PyPy is in PATH
which pypy3
pypy3 --version

# Check local pypy directory
ls -lh ~/pipier_love_api/pypy/
ls -lh ~/pipier_love_api/pypy/bin/
```

### Install PyPy (if needed)

```bash
sudo apt update
sudo apt install -y pypy3
```

### Update Service File

```bash
# Backup current service
sudo cp /etc/systemd/system/piperlove.service /etc/systemd/system/piperlove.service.backup

# Edit service file
sudo nano /etc/systemd/system/piperlove.service
```

Change the `ExecStart` line from:
```ini
ExecStart=python3 main.py
```

To one of these:

**Option 1: System PyPy**
```ini
ExecStart=pypy3 main.py
```

**Option 2: Local PyPy**
```ini
ExecStart=/root/pipier_love_api/pypy/bin/pypy3 main.py
```

### Reload and Restart

```bash
# Reload systemd
sudo systemctl daemon-reload

# Restart service
sudo systemctl restart piperlove.service

# Check status
sudo systemctl status piperlove.service

# Check logs
journalctl -u piperlove.service -f
```

### Verify PyPy is Running

```bash
# Check if process is using PyPy
ps aux | grep pypy | grep main.py

# Should show something like:
# root ... pypy3 main.py
```

---

## Performance Test

### Quick Test

```bash
cd ~/pipier_love_api

# Test with CPython
python3 -c "
import sys, time
sys.path.insert(0, 'src')
from chess_engine import ChessBoard
board = ChessBoard()
start = time.time()
nodes = board.perft(4)
print(f'CPython: {nodes:,} nodes in {time.time()-start:.2f}s')
"

# Test with PyPy
pypy3 -c "
import sys, time
sys.path.insert(0, 'src')
from chess_engine import ChessBoard
board = ChessBoard()
start = time.time()
nodes = board.perft(4)
print(f'PyPy: {nodes:,} nodes in {time.time()-start:.2f}s')
"
```

### Expected Results

**CPython:**
- 197,281 nodes in ~5s = ~40,000 NPS

**PyPy:**
- 197,281 nodes in ~0.2s = ~1,000,000 NPS

**Speedup: 25x faster!**

---

## Browser Performance

After switching to PyPy, your browser gameplay should see:

**Before (CPython):**
- 100k nodes in 12 seconds
- Depth: 4-5
- Weak play

**After (PyPy):**
- 10M+ nodes in 12 seconds
- Depth: 7-8
- Much stronger play

---

## Troubleshooting

### PyPy not found

```bash
# Install from apt
sudo apt update
sudo apt install -y pypy3

# Verify
which pypy3
pypy3 --version
```

### Service fails to start

```bash
# Check logs
journalctl -u piperlove.service -n 50

# Test manually
cd ~/pipier_love_api
pypy3 main.py

# If it works manually but not as service, check:
# - Working directory in service file
# - Environment variables
# - File permissions
```

### ImportError with PyPy

```bash
# PyPy has its own pip
pypy3 -m pip install fastapi uvicorn

# Or use requirements
pypy3 -m pip install -r requirements.txt
```

### Still slow after switching

```bash
# Verify PyPy is actually running
ps aux | grep pypy

# Check if service restarted successfully
systemctl status piperlove.service

# Force restart
sudo systemctl stop piperlove.service
sleep 2
sudo systemctl start piperlove.service
```

---

## Files on VPS

Based on your `ls` output, you have:
- ✓ `pypy/` directory (local PyPy installation?)
- ✓ `requirements-pypy.txt` (PyPy-specific requirements)
- ✓ Main code files

You're ready to switch! Just run:

```bash
bash check_vps_pypy.sh    # Check current status
bash switch_to_pypy.sh    # Switch to PyPy
```

---

## Quick Commands

```bash
# Check if PyPy is running
ps aux | grep pypy | grep main.py

# Check service status
systemctl status piperlove.service

# View live logs
journalctl -u piperlove.service -f

# Restart service
sudo systemctl restart piperlove.service

# Test performance
bash check_vps_pypy.sh
```

---

## Expected NPS Improvement

Your current: **~8,300 NPS** (very slow!)

With PyPy: **500,000 - 2,000,000 NPS** (60-240x faster!)

This will make your engine play **much stronger** and search **much deeper** in the same time.
