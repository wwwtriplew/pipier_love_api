# Switch from PyPy to CPython

## Why Switch?

PyPy's JIT is not helping this codebase:
- **Current PyPy performance:** 2,600-8,000 NPS
- **Expected CPython performance:** 50,000-100,000+ NPS
- PyPy JIT overhead is slowing down the engine
- CPython's predictable performance is better for chess

## VPS Deployment Steps

### 1. Check Current Setup

```bash
cd /root/pipier_love_api

# Check what's running
sudo systemctl status piperlove

# Check current Python
/root/venv/bin/python --version
/root/venv/bin/python -c "try: import __pypy__; print('PyPy'); except: print('CPython')"
```

### 2. Install CPython (if needed)

```bash
# Ubuntu 24.04 comes with Python 3.12
python3 --version  # Should show Python 3.12.x

# Install pip and venv if missing
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev
```

### 3. Create New CPython Virtual Environment

```bash
cd /root/pipier_love_api

# Stop the service
sudo systemctl stop piperlove

# Backup old venv (if it exists)
mv venv venv-old 2>/dev/null || true

# Create new CPython venv
python3 -m venv venv

# Activate and install dependencies

pip install --upgrade pip
pip install -r requirements.txt

# Verify CPython
python --version
python -c "try: import __pypy__; print('ERROR: Still PyPy!'); except: print('✓ CPython')"
```

### 4. Update Systemd Service

```bash
# Edit service file
sudo nano /etc/systemd/system/piperlove.service
```

**Update to:**

```ini
[Unit]
Description=PiperLove Chess Engine API (CPython)
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/pipier_love_api
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/pipier_love_api/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=3
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

**Key changes:**
- Updated description to mention CPython
- Changed ExecStart to use new venv path
- Set `--workers 1` (single worker is fine for chess engine)

### 5. Restart Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start piperlove

# Check status
sudo systemctl status piperlove

# Watch logs
sudo journalctl -u piperlove -f
```

**Expected startup logs:**
```
📚 Initializing opening book...
Loading opening book: 120 entries
✓ Loaded opening book: openingbook/piperlove_black.bin
✓ Opening book loaded successfully
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**No PyPy warmup messages should appear!**

### 6. Test Performance

```bash
# Test from VPS
curl -X POST "http://localhost:8000/move" \
  -H "Content-Type: application/json" \
  -d '{
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "ai_thinking_ms": 5000
  }'
```

**Expected results:**
- **NPS:** 50,000-100,000+ (not 2,000-8,000)
- **Depth:** 5-7 in 5 seconds
- **Nodes:** 250K-500K in 5 seconds

### 7. Verify from Frontend

Play a game at https://wwwtriplew.github.io/piperlove/play.html

**Check console logs:**
- Move 1 (book): `Depth: 0, Nodes: 0, Time: <50ms` ✓
- Move 2+ (search): `Depth: 5-7, Nodes: 100K+, NPS: 50K+` ✓

### 8. Cleanup (Optional)

```bash
# Remove old PyPy venv
rm -rf /root/venv-old
rm -rf /root/venv-pypy 2>/dev/null

# Remove PyPy if no longer needed
# (only if you're not using it for other projects)
# sudo apt remove pypy3 pypy3-dev
```

## Performance Comparison

### Before (PyPy):
```
Depth: 4, Nodes: 38K, Time: 14s, NPS: 2,724
Depth: 5, Nodes: 18K, Time: 7s, NPS: 2,660
```

### After (CPython):
```
Depth: 6-7, Nodes: 300K+, Time: 5-10s, NPS: 50K-100K+
```

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u piperlove -n 50 --no-pager

# Common issues:
# - Port 8000 already in use
# - Python dependencies missing
# - Wrong venv path
```

### Still showing low NPS

```bash
# Verify CPython is being used
ps aux | grep uvicorn
# Should show: /root/pipier_love_api/venv/bin/python

# Check Python version in running process
sudo ls -la /proc/$(pgrep -f uvicorn)/exe
```

### Import errors

```bash
# Reinstall dependencies
cd /root/pipier_love_api
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

## Rollback (if needed)

```bash
# Stop service
sudo systemctl stop piperlove

# Restore old venv
rm -rf venv
mv venv-old venv

# Edit service to use old path
sudo nano /etc/systemd/system/piperlove.service

# Restart
sudo systemctl daemon-reload
sudo systemctl start piperlove
```

## Summary

**Steps:**
1. ✅ Create CPython venv
2. ✅ Install dependencies
3. ✅ Update systemd service
4. ✅ Restart and verify
5. ✅ Test performance
6. ✅ Cleanup old PyPy venv

**Expected improvement:** **20-40x faster** (2.7K → 50-100K NPS)
