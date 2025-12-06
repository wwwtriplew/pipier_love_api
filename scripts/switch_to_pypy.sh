#!/bin/bash

echo "==========================================="
echo "Converting VPS to Use PyPy"
echo "==========================================="
echo ""

# Step 1: Check if PyPy is available
echo "Step 1: Locating PyPy..."
echo "-------------------------------------------"

PYPY_EXEC=""

if command -v pypy3 &> /dev/null; then
    PYPY_EXEC="pypy3"
    echo "✓ Using system PyPy: $(which pypy3)"
elif [ -f "pypy/bin/pypy3" ]; then
    PYPY_EXEC="$(pwd)/pypy/bin/pypy3"
    echo "✓ Using local PyPy: $PYPY_EXEC"
elif [ -f "pypy/pypy3" ]; then
    PYPY_EXEC="$(pwd)/pypy/pypy3"
    echo "✓ Using local PyPy: $PYPY_EXEC"
else
    echo "✗ PyPy not found!"
    echo ""
    echo "Installing PyPy3 from apt..."
    sudo apt update
    sudo apt install -y pypy3
    
    if command -v pypy3 &> /dev/null; then
        PYPY_EXEC="pypy3"
        echo "✓ PyPy installed: $(which pypy3)"
    else
        echo "✗ Failed to install PyPy"
        exit 1
    fi
fi

echo ""
$PYPY_EXEC --version 2>&1
echo ""

# Step 2: Update systemd service
echo "Step 2: Updating systemd service..."
echo "-------------------------------------------"

SERVICE_FILE="/etc/systemd/system/piperlove.service"

if [ ! -f "$SERVICE_FILE" ]; then
    echo "✗ Service file not found: $SERVICE_FILE"
    exit 1
fi

# Backup current service file
sudo cp "$SERVICE_FILE" "${SERVICE_FILE}.backup"
echo "✓ Backed up service file to ${SERVICE_FILE}.backup"

# Update ExecStart to use PyPy
sudo sed -i "s|ExecStart=python3 |ExecStart=$PYPY_EXEC |g" "$SERVICE_FILE"
sudo sed -i "s|ExecStart=/usr/bin/python3 |ExecStart=$PYPY_EXEC |g" "$SERVICE_FILE"

echo "✓ Updated service file"
echo ""
echo "New ExecStart line:"
grep "ExecStart" "$SERVICE_FILE"

echo ""

# Step 3: Reload systemd
echo "Step 3: Reloading systemd..."
echo "-------------------------------------------"

sudo systemctl daemon-reload
echo "✓ Systemd reloaded"

echo ""

# Step 4: Restart service
echo "Step 4: Restarting piperlove service..."
echo "-------------------------------------------"

sudo systemctl restart piperlove.service
sleep 2

echo "✓ Service restarted"
echo ""

# Step 5: Check status
echo "Step 5: Checking service status..."
echo "-------------------------------------------"

systemctl status piperlove.service --no-pager | head -20

echo ""

# Step 6: Check if it's using PyPy
echo "Step 6: Verifying PyPy is running..."
echo "-------------------------------------------"

sleep 2

if ps aux | grep -v grep | grep pypy | grep main.py > /dev/null; then
    echo "✓ Service is running with PyPy!"
    echo ""
    ps aux | grep -v grep | grep pypy | grep main.py
elif ps aux | grep -v grep | grep python | grep main.py > /dev/null; then
    echo "⚠️  Service is running but with Python, not PyPy"
    echo ""
    ps aux | grep -v grep | grep python | grep main.py
else
    echo "✗ Service doesn't appear to be running"
fi

echo ""
echo "==========================================="
echo "Conversion complete!"
echo "==========================================="
echo ""
echo "To check logs:"
echo "  journalctl -u piperlove.service -f"
echo ""
echo "To check performance:"
echo "  bash check_vps_pypy.sh"
echo ""
