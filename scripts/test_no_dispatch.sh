#!/bin/bash
# Test if removing dynamic dispatch fixes PyPy JIT

echo "=========================================="
echo "TESTING: Direct function calls (no dispatch)"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Test 1: Simple loop (should be <10ms now)"
echo "==========================================="
/usr/bin/pypy3.9 -c "
import time

def simple():
    total = 0
    for i in range(100000):
        total += i * 2
    return total

# Warmup
for _ in range(1000):
    simple()

# Test
start = time.time()
for _ in range(100):
    simple()
elapsed = time.time() - start

print(f'Simple loop: {elapsed*1000:.1f}ms (100 iterations)')
if elapsed < 0.01:
    print('✓✓✓ JIT OPTIMIZED!')
elif elapsed < 0.015:
    print('✓✓ JIT working well')
elif elapsed < 0.020:
    print('✓ JIT working but not optimal')
else:
    print('✗ JIT still broken ({:.0f}ms - should be <10ms)'.format(elapsed*1000))
"

echo ""
echo "Test 2: Chess perft with NO dynamic dispatch"
echo "=============================================="
/usr/bin/pypy3.9 -c "
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

# Warmup
print('Warming up JIT...')
for i in range(500):
    perft(board, 2)
    if i % 100 == 0:
        print(f'  {i}/500')

# Test
print('Testing...')
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)

print()
print(f'NPS: {nps:,}')
print(f'Previous (with dispatch): ~60,000 NPS')
print(f'CPython baseline: ~50,000 NPS')
print(f'Target (PyPy optimized): 200,000+ NPS')
print()

if nps > 200000:
    print('✓✓✓ SUCCESS! JIT fully optimized!')
elif nps > 150000:
    print('✓✓ GOOD! Major improvement!')
elif nps > 100000:
    print('✓ BETTER! Significant speedup')
elif nps > 60000:
    print('⚠ Minor improvement - still issues')
else:
    print('✗ No improvement - something else blocking JIT')
"

echo ""
echo "Test 3: Multiple runs to verify stability"
echo "==========================================="
for run in 1 2 3; do
    echo "Run $run:"
    /usr/bin/pypy3.9 -c "
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

for _ in range(500):
    perft(board, 2)

start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
print(f'  {int(nodes/elapsed):,} NPS')
    "
done

echo ""
echo ""
echo "=========================================="
echo "ANALYSIS"
echo "=========================================="
echo ""
echo "If NPS > 200k:"
echo "  → PROBLEM SOLVED! Dynamic dispatch was the blocker"
echo "  → Deploy to production immediately"
echo ""
echo "If NPS still ~60k:"
echo "  → Dynamic dispatch wasn't the main issue"
echo "  → Need to investigate other JIT blockers"
echo ""
