#!/bin/bash
# Test JIT Warmup Solution

echo "=========================================="
echo "TESTING JIT WARMUP SOLUTION"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "1. Test warmup module directly"
echo "--------------------------------------"
/root/venv/bin/python3 src/jit_warmup.py

echo ""
echo ""
echo "2. Test cold start (no warmup) - SLOW"
echo "--------------------------------------"
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

# No warmup - immediate test
start = time.time()
nodes = perft(board, 3)
nps = int(nodes / (time.time() - start))
print(f'Cold start NPS: {nps:,} (SLOW - JIT not warmed up)')
"

echo ""
echo ""
echo "3. Test with warmup - FAST"
echo "--------------------------------------"
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

# Warmup
print('Warming up JIT...')
for i in range(25):
    perft(board, 2)

# Now test - should be FAST
start = time.time()
nodes = perft(board, 3)
nps = int(nodes / (time.time() - start))
print(f'After warmup NPS: {nps:,} (FAST - JIT compiled)')
"

echo ""
echo ""
echo "=========================================="
echo "COMPARISON"
echo "=========================================="
echo ""
echo "Cold start should be ~5-8k NPS (SLOW)"
echo "After warmup should be 50k-200k+ NPS (FAST)"
echo ""
echo "The fix adds warmup at service startup so all"
echo "requests get the FAST performance!"
echo ""
