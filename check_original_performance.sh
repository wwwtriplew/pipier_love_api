#!/bin/bash
# Check what the performance was BEFORE any optimization attempts

cd /root/pipier_love_api

echo "=========================================="
echo "TESTING: What was the ORIGINAL performance?"
echo "=========================================="
echo ""

echo "Current commit: $(git rev-parse --short HEAD)"
echo "Current branch: $(git branch --show-current)"
echo ""

echo "Testing current performance:"
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

# Test cold
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps_cold = int(nodes / elapsed)
print(f'Cold start: {nps_cold:,} NPS')

# Warmup
for _ in range(500):
    perft(board, 2)

# Test warm
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps_warm = int(nodes / elapsed)
print(f'After warmup: {nps_warm:,} NPS')
"

echo ""
echo "=========================================="
echo "Checking if there's a commit to revert to:"
echo "=========================================="
git log --oneline --all -10

echo ""
echo "Show me the commit where performance was good (if exists)"
