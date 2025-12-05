#!/bin/bash
# Deep JIT Investigation - Why is warmup not working?

echo "=========================================="
echo "WHY ISN'T JIT WORKING?"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Test 1: Check if JIT is actually compiling traces"
echo "=================================================="
PYPYLOG=jit-summary:/tmp/jit_trace_test.log /root/venv/bin/python3 -c "
from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb
import time

board = ChessBoard()
def perft(b, d):
    if d == 0: return 1
    n = 0
    for f, t, p in b.generate_moves():
        b.make_move(f, t, p)
        k = get_lsb(b.pieces[1-b.side_to_move][5])
        if not b.is_square_attacked(k, b.side_to_move):
            n += perft(b, d-1)
        b.unmake_move()
    return n

# Heavy warmup
for i in range(50):
    perft(board, 2)

# Test
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
print(f'NPS after 50 warmups: {int(nodes/elapsed):,}')
" 2>&1

echo ""
echo "JIT Log Analysis:"
if [ -f /tmp/jit_trace_test.log ]; then
    echo "Total traces compiled:"
    grep -c "Tracing" /tmp/jit_trace_test.log || echo "0"
    echo ""
    echo "Trace aborts:"
    grep "abort:" /tmp/jit_trace_test.log | sort | uniq -c
    echo ""
    echo "Backend compilation:"
    grep -c "Backend" /tmp/jit_trace_test.log || echo "0"
else
    echo "No JIT log generated - JIT might not be running!"
fi

echo ""
echo ""
echo "Test 2: Check JIT parameters and threshold"
echo "=================================================="
/root/venv/bin/python3 -c "
import __pypy__

params = __pypy__.jit_parameters()
print('JIT Parameters:')
print(f'  threshold: {params[\"threshold\"]}')
print(f'  function_threshold: {params[\"function_threshold\"]}')
print(f'  trace_limit: {params[\"trace_limit\"]}')
print(f'  trace_eagerness: {params[\"trace_eagerness\"]}')
print(f'  max_unroll_loops: {params.get(\"max_unroll_loops\", \"N/A\")}')
print()
print('Threshold means: function must be called this many times before JIT compiles it')
print(f'Current threshold: {params[\"threshold\"]} calls')
"

echo ""
echo ""
echo "Test 3: Test with EXPLICIT loop count that exceeds threshold"
echo "=================================================="
/root/venv/bin/python3 -c "
import __pypy__
params = __pypy__.jit_parameters()
threshold = params['threshold']

print(f'JIT threshold: {threshold}')
print(f'Running {threshold * 3} iterations to FORCE JIT compilation...')
print()

from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb
import time

board = ChessBoard()
def perft(b, d):
    if d == 0: return 1
    n = 0
    for f, t, p in b.generate_moves():
        b.make_move(f, t, p)
        k = get_lsb(b.pieces[1-b.side_to_move][5])
        if not b.is_square_attacked(k, b.side_to_move):
            n += perft(b, d-1)
        b.unmake_move()
    return n

# Exceed threshold by 3x
iterations = threshold * 3
for i in range(iterations):
    perft(board, 2)
    if i % 500 == 0:
        print(f'  Iteration {i}/{iterations}...')

# Now test
print()
print('Testing after exceeding threshold...')
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps = int(nodes/elapsed)
print(f'NPS: {nps:,}')

if nps > 50000:
    print('✓ JIT IS WORKING!')
elif nps > 15000:
    print('⚠ Partial JIT optimization')
else:
    print('✗ JIT STILL NOT WORKING - something else is wrong')
"

echo ""
echo ""
echo "Test 4: Compare with a SIMPLE loop (should JIT compile easily)"
echo "=================================================="
/root/venv/bin/python3 -c "
import time

# Simple loop - should JIT compile perfectly
def simple_loop():
    total = 0
    for i in range(100000):
        total += i * 2
    return total

# Warmup
for _ in range(100):
    simple_loop()

# Test
start = time.time()
for _ in range(1000):
    simple_loop()
elapsed = time.time() - start

print(f'Simple loop: {elapsed*1000:.1f}ms for 1000 iterations')
if elapsed < 0.1:
    print('✓ JIT can optimize simple loops')
else:
    print('✗ JIT not working even for simple loops!')
"

echo ""
echo ""
echo "=========================================="
echo "DIAGNOSIS"
echo "=========================================="
echo ""
echo "If traces compiled: JIT is trying but failing (trace too long)"
echo "If no traces: JIT not triggering (threshold too high or disabled)"
echo "If simple loop fast but perft slow: Code complexity issue"
echo ""
