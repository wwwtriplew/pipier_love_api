#!/bin/bash
# Test PyPy JIT Optimizations
# Run this on VPS to verify refactored code works and improves performance

set -e

cd /root/pipier_love_api

echo "=========================================="
echo "TESTING PYPY JIT OPTIMIZATIONS"
echo "=========================================="
echo ""

echo "1. Testing perft correctness..."
/root/venv/bin/pypy3 -c "
from src.board_state import Position
import time

p = Position()
print('Testing perft(3)...')
start = time.time()
nodes = p.perft(3)
elapsed = time.time() - start

print(f'Perft(3): {nodes:,} nodes in {elapsed:.3f}s = {int(nodes/elapsed):,} NPS')
print('Expected: 8,902 nodes')
if nodes == 8902:
    print('✓ PASS - Perft results correct')
else:
    print(f'✗ FAIL - Expected 8902, got {nodes}')
    exit(1)
"

echo ""
echo "2. Testing move generation correctness..."
/root/venv/bin/pypy3 -c "
from src.board_state import Position

p = Position()
moves = p.get_legal_moves()
print(f'Starting position: {len(moves)} legal moves')
print('Expected: 20 legal moves')
if len(moves) == 20:
    print('✓ PASS - Move generation correct')
else:
    print(f'✗ FAIL - Expected 20, got {len(moves)}')
    exit(1)
"

echo ""
echo "3. Running perft with JIT logging to check trace aborts..."
PYPYLOG=jit-summary:/tmp/jit_summary.log /root/venv/bin/pypy3 -c "
from src.board_state import Position
import time

p = Position()

# Warmup for JIT
for _ in range(3):
    p.perft(2)

# Actual test
start = time.time()
nodes = p.perft(4)
elapsed = time.time() - start

print(f'Perft(4): {nodes:,} nodes in {elapsed:.3f}s = {int(nodes/elapsed):,} NPS')
" 2>&1

echo ""
echo "4. Analyzing JIT trace aborts..."
if [ -f /tmp/jit_summary.log ]; then
    echo "JIT Summary:"
    grep -E "Tracing:|Backend:|abort:" /tmp/jit_summary.log | head -20
    
    ABORT_COUNT=$(grep -c "abort: trace too long" /tmp/jit_summary.log || echo "0")
    echo ""
    echo "Trace Too Long Aborts: $ABORT_COUNT"
    
    if [ "$ABORT_COUNT" -eq 0 ]; then
        echo "✓ SUCCESS - No trace aborts! PyPy JIT can compile all hot loops"
    elif [ "$ABORT_COUNT" -lt 3 ]; then
        echo "⚠ IMPROVED - Reduced from 6 aborts to $ABORT_COUNT"
    else:
        echo "⚠ STILL ISSUES - $ABORT_COUNT traces still too long"
    fi
else
    echo "Warning: No JIT log generated"
fi

echo ""
echo "5. Performance comparison (CPython vs PyPy)..."
echo ""
echo "CPython baseline:"
python3 -c "
from src.board_state import Position
import time

p = Position()
start = time.time()
nodes = p.perft(3)
elapsed = time.time() - start
print(f'CPython: {int(nodes/elapsed):,} NPS')
"

echo ""
echo "PyPy optimized:"
/root/venv/bin/pypy3 -c "
from src.board_state import Position
import time

p = Position()
# Warmup
for _ in range(5):
    p.perft(2)

start = time.time()
nodes = p.perft(3)
elapsed = time.time() - start
print(f'PyPy: {int(nodes/elapsed):,} NPS')
"

echo ""
echo "=========================================="
echo "TEST COMPLETE"
echo "=========================================="
echo ""
echo "Expected results after optimization:"
echo "- Perft correctness: PASS"
echo "- Trace aborts: 0-2 (down from 6)"
echo "- PyPy NPS: 50k-200k+ (was 6k)"
echo ""
