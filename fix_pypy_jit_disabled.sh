#!/bin/bash
# Fix PyPy JIT Disabled Issue
# Root cause identified: PyPy JIT is not enabled, causing 7.6k NPS instead of 200k+

set -e

echo "=========================================="
echo "FIXING PYPY JIT DISABLED ISSUE"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Step 1: Diagnose WHY JIT is disabled"
echo "=========================================="
echo ""

echo "Checking environment variables..."
if [ -n "$PYPYLOG" ]; then
    echo "⚠ WARNING: PYPYLOG is set: $PYPYLOG"
    echo "This might interfere with JIT"
fi

if [ -n "$PYPY_GC_MAX" ]; then
    echo "PyPy GC max: $PYPY_GC_MAX"
fi

env | grep -i pypy || echo "No PyPy-specific env vars"

echo ""
echo "Checking service configuration..."
systemctl cat piperlove.service | grep -A5 ExecStart || echo "Could not read service file"

echo ""
echo "Checking PyPy build info..."
/root/venv/bin/pypy3 --info 2>&1 | grep -i jit || echo "JIT info not available"

echo ""
echo "Checking available memory..."
free -h
echo ""
AVAILABLE_MB=$(free -m | awk '/^Mem:/{print $7}')
echo "Available memory: ${AVAILABLE_MB}MB"
if [ "$AVAILABLE_MB" -lt 500 ]; then
    echo "⚠ WARNING: Low memory! PyPy JIT needs ~500MB to run efficiently"
fi

echo ""
echo ""
echo "Step 2: Test JIT with explicit warmup"
echo "=========================================="
echo ""

/root/venv/bin/pypy3 -c "
import __pypy__
import gc

print('Testing JIT enablement...')
print(f'PyPy version: {__pypy__.pypyver}')

# Try to check JIT status
try:
    jit_enabled = __pypy__.jit_enabled()
    print(f'JIT enabled: {jit_enabled}')
except AttributeError:
    print('JIT status method not available')

# Try to get JIT parameters
try:
    params = __pypy__.jit_parameters()
    print(f'JIT threshold: {params.get(\"threshold\", \"N/A\")}')
    print(f'JIT trace_limit: {params.get(\"trace_limit\", \"N/A\")}')
except:
    print('⚠ JIT parameters not accessible - JIT might be disabled!')

# Force garbage collection
gc.collect()

# Test with aggressive JIT warmup
from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb
import time

board = ChessBoard()

def direct_perft(board, depth):
    if depth == 0:
        return 1
    nodes = 0
    for from_sq, to_sq, promo in board.generate_moves():
        board.make_move(from_sq, to_sq, promo)
        king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])
        if not board.is_square_attacked(king_sq, board.side_to_move):
            nodes += direct_perft(board, depth - 1)
        board.unmake_move()
    return nodes

# Aggressive warmup - force JIT compilation
print('\\nWarming up JIT (30 iterations)...')
for i in range(30):
    direct_perft(board, 2)
    if i % 10 == 0:
        print(f'  Warmup {i}/30...')

print('\\nTesting after warmup:')
start = time.time()
nodes = direct_perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)
print(f'Perft(3) after warmup: {nps:,} NPS')

if nps < 15000:
    print('⚠ STILL SLOW - JIT not working!')
    print('  Expected: 50k-200k NPS with JIT')
    print('  Got: {nps:,} NPS (interpreter mode)')
elif nps < 50000:
    print('⚠ IMPROVED but still suboptimal')
    print('  JIT might be partially working')
else:
    print('✓ SUCCESS - JIT is working!')
" 2>&1

echo ""
echo ""
echo "Step 3: Possible fixes"
echo "=========================================="
echo ""

AVAILABLE_MB=$(free -m | awk '/^Mem:/{print $7}')

if [ "$AVAILABLE_MB" -lt 500 ]; then
    echo "FIX 1: Free up memory for JIT"
    echo "------------------------------"
    echo "PyPy JIT needs memory to compile code. Current available: ${AVAILABLE_MB}MB"
    echo ""
    echo "Options:"
    echo "  a) Reduce transposition table size in search.py"
    echo "  b) Restart service to clear memory:"
    echo "     sudo systemctl restart piperlove.service"
    echo "  c) Add swap space (if not already done)"
    echo "  d) Upgrade VPS to more memory"
    echo ""
fi

echo "FIX 2: Try reinstalling PyPy with JIT enabled"
echo "------------------------------"
echo "Current PyPy might be a JIT-disabled build"
echo ""
echo "Commands to try:"
echo "  # Download official PyPy with JIT"
echo "  cd /tmp"
echo "  wget https://downloads.python.org/pypy/pypy3.10-v7.3.16-linux64.tar.bz2"
echo "  tar xf pypy3.10-v7.3.16-linux64.tar.bz2"
echo "  cd /root"
echo "  python3 -m venv --copies venv-new"
echo "  ln -sf /tmp/pypy3.10-v7.3.16-linux64/bin/pypy3 venv-new/bin/pypy3"
echo "  venv-new/bin/pypy3 -m pip install -r pipier_love_api/requirements.txt"
echo "  # Update service to use venv-new"
echo ""

echo "FIX 3: Use PYPY_GC environment variables"
echo "------------------------------"
echo "Help PyPy manage memory better:"
echo ""
echo "Add to service file (/etc/systemd/system/piperlove.service):"
echo "  [Service]"
echo "  Environment=\"PYPY_GC_MAX=1024MB\""
echo "  Environment=\"PYPY_GC_MIN=512MB\""
echo ""

echo "FIX 4: If all else fails - use CPython"
echo "------------------------------"
echo "CPython gets 32k NPS which is 4x better than PyPy without JIT"
echo ""
echo "Update service to use CPython instead:"
echo "  # Edit /etc/systemd/system/piperlove.service"
echo "  # Change: /root/venv/bin/pypy3"
echo "  # To: /usr/bin/python3"
echo ""

echo ""
echo "=========================================="
echo "DIAGNOSIS COMPLETE"
echo "=========================================="
echo ""
echo "SUMMARY:"
echo "--------"
echo "Problem: PyPy JIT is disabled/not working"
echo "Impact: Running at 7.6k NPS instead of 200k+ NPS"
echo "Cause: Likely insufficient memory for JIT compilation"
echo ""
echo "Recommended action:"
echo "1. Try aggressive warmup (already tested above)"
echo "2. If still slow, restart service to free memory"
echo "3. If still slow, fall back to CPython (32k NPS)"
echo "4. If need speed, upgrade VPS RAM or optimize TT size"
echo ""
