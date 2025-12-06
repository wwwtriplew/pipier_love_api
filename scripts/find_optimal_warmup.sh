#!/bin/bash
# Find the EXACT warmup count needed for PyPy JIT

echo "=========================================="
echo "FINDING OPTIMAL WARMUP COUNT"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Testing with progressive warmup counts..."
echo ""

/root/venv/bin/python3 -c "
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

print('Warmup iterations → NPS')
print('-' * 40)

test_counts = [0, 10, 25, 50, 100, 200, 500, 1000, 2000]

for count in test_counts:
    # Fresh board each time
    board = ChessBoard()
    
    # Warmup
    for _ in range(count):
        perft(board, 2)
    
    # Test
    start = time.time()
    nodes = perft(board, 3)
    elapsed = time.time() - start
    nps = int(nodes / elapsed)
    
    print(f'{count:4d} warmups → {nps:>7,} NPS')

print()
print('Analyzing results...')
"

echo ""
echo ""
echo "Test 2: Simple loop warmup progression"
echo "=================================================="
/root/venv/bin/python3 -c "
import time

def simple():
    total = 0
    for i in range(100000):
        total += i * 2
    return total

print('Testing simple loop with increasing warmup:')
print()

for warmup_count in [0, 10, 50, 100, 500, 1000, 5000]:
    # Warmup
    for _ in range(warmup_count):
        simple()
    
    # Test
    start = time.time()
    for _ in range(100):
        simple()
    elapsed = time.time() - start
    
    print(f'{warmup_count:4d} warmups → {elapsed*1000:6.1f}ms (100 iterations)')
    
    if elapsed < 0.01:
        print(f'      ✓ JIT FULLY OPTIMIZED at {warmup_count} warmups!')
        break

print()
"

echo ""
echo "=========================================="
echo "FINDING MEMORY IMPACT"
echo "=========================================="
echo ""

echo "Current memory state:"
free -h
echo ""

echo "Testing if clearing cache helps..."
sudo sync
sudo sysctl -w vm.drop_caches=3 >/dev/null 2>&1
echo "Cache cleared"
echo ""

echo "Memory after clearing:"
free -h
echo ""

echo "Testing NPS after freeing memory..."
/root/venv/bin/python3 -c "
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
for i in range(500):
    perft(board, 2)

start = time.time()
nodes = perft(board, 3)
nps = int(nodes / (time.time() - start))
print(f'NPS with 500 warmups + cleared cache: {nps:,}')
"

echo ""
echo "=========================================="
echo "CONCLUSION"
echo "=========================================="
echo ""
echo "If NPS increases with warmup count:"
echo "  → JIT works, just needs more warmup"
echo ""
echo "If NPS plateaus below 50k:"
echo "  → Memory/CPU limitation blocking full JIT optimization"
echo ""
echo "If NPS reaches 100k+ with enough warmup:"
echo "  → SOLUTION: Increase warmup iterations in jit_warmup.py"
echo ""
