#!/bin/bash
# Reproduce the EXACT test that showed 60k NPS

cd /root/pipier_love_api

echo "=========================================="
echo "REPRODUCING EXACT TEST FROM find_optimal_warmup.sh"
echo "=========================================="
echo ""

# This is the EXACT code from find_optimal_warmup.sh that showed 60k
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
"

echo ""
echo "=========================================="
echo "ANALYSIS"
echo "=========================================="
echo ""
echo "Compare these results to your earlier run:"
echo "You reported: 500 warmups → 54,700 NPS"
echo "             2000 warmups → 59,525 NPS"
echo ""
echo "If current results are similar:"
echo "  → The code never changed, my interpretation was wrong"
echo ""
echo "If current results are much lower:"
echo "  → Something external changed on the VPS"
echo ""
