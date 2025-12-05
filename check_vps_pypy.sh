#!/bin/bash

echo "==========================================="
echo "PyPy VPS Diagnostic Script"
echo "==========================================="
echo ""

# Check if PyPy is installed
echo "1. Checking PyPy installation..."
echo "-------------------------------------------"

if command -v pypy3 &> /dev/null; then
    echo "✓ PyPy3 found in PATH"
    echo "  Location: $(which pypy3)"
    echo "  Version: $(pypy3 --version 2>&1)"
else
    echo "✗ PyPy3 NOT found in PATH"
fi

echo ""

# Check the pypy directory
echo "2. Checking local pypy directory..."
echo "-------------------------------------------"

if [ -d "pypy" ]; then
    echo "✓ pypy directory exists"
    ls -lh pypy/ | head -20
    
    # Check if there's a pypy3 executable
    if [ -f "pypy/bin/pypy3" ]; then
        echo ""
        echo "✓ Found pypy/bin/pypy3"
        pypy/bin/pypy3 --version 2>&1
    elif [ -f "pypy/pypy3" ]; then
        echo ""
        echo "✓ Found pypy/pypy3"
        pypy/pypy3 --version 2>&1
    else
        echo ""
        echo "Searching for pypy3 executable in pypy directory..."
        find pypy -name "pypy3*" -type f 2>/dev/null | head -5
    fi
else
    echo "✗ pypy directory not found"
fi

echo ""

# Check systemd service
echo "3. Checking systemd service..."
echo "-------------------------------------------"

if [ -f "/etc/systemd/system/piperlove.service" ]; then
    echo "✓ Service file exists"
    echo ""
    echo "Service configuration:"
    grep "ExecStart" /etc/systemd/system/piperlove.service
    echo ""
    
    echo "Current service status:"
    systemctl status piperlove.service --no-pager | head -15
else
    echo "✗ Service file not found at /etc/systemd/system/piperlove.service"
fi

echo ""

# Check current process
echo "4. Checking running process..."
echo "-------------------------------------------"

if pgrep -f "main.py" > /dev/null; then
    echo "✓ main.py process is running"
    echo ""
    ps aux | grep "main.py" | grep -v grep
else
    echo "✗ main.py process not found"
fi

echo ""

# Check performance with CPython
echo "5. Quick performance test with CPython..."
echo "-------------------------------------------"

python3 -c "
import sys
import time
sys.path.insert(0, 'src')
from board_state import BoardState

board = BoardState()
board.perft(2)  # Warmup

start = time.time()
nodes = board.perft(3)
elapsed = time.time() - start
nps = int(nodes / elapsed) if elapsed > 0 else 0

print(f'CPython: {nodes:,} nodes in {elapsed:.3f}s = {nps:,} NPS')
" 2>&1

echo ""

# Check if we can test with PyPy
echo "6. Testing with PyPy (if available)..."
echo "-------------------------------------------"

PYPY_EXEC=""

if command -v pypy3 &> /dev/null; then
    PYPY_EXEC="pypy3"
elif [ -f "pypy/bin/pypy3" ]; then
    PYPY_EXEC="pypy/bin/pypy3"
elif [ -f "pypy/pypy3" ]; then
    PYPY_EXEC="pypy/pypy3"
fi

if [ -n "$PYPY_EXEC" ]; then
    echo "Testing with: $PYPY_EXEC"
    echo ""
    
    $PYPY_EXEC -c "
import sys
import time
sys.path.insert(0, 'src')
from board_state import BoardState

board = BoardState()
board.perft(2)  # Warmup

start = time.time()
nodes = board.perft(3)
elapsed = time.time() - start
nps = int(nodes / elapsed) if elapsed > 0 else 0

print(f'PyPy: {nodes:,} nodes in {elapsed:.3f}s = {nps:,} NPS')
" 2>&1
else
    echo "✗ No PyPy executable found for testing"
fi

echo ""
echo "==========================================="
echo "Diagnostic complete!"
echo "==========================================="
