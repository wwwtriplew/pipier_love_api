#!/bin/bash
# Compare venv vs system PyPy performance

echo "=========================================="
echo "VENV vs SYSTEM PYPY COMPARISON"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Test 1: System PyPy (/usr/bin/pypy3.9)"
echo "=========================================="
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
print(f'System PyPy: {int(nodes/elapsed):,} NPS')
"

echo ""
echo "Test 2: Venv PyPy (/root/venv/bin/python3)"
echo "=========================================="
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

for _ in range(500):
    perft(board, 2)

start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
print(f'Venv PyPy: {int(nodes/elapsed):,} NPS')
"

echo ""
echo "=========================================="
echo "EXPLANATION"
echo "=========================================="
echo ""
echo "If venv PyPy is much faster:"
echo "  → Venv has different Python version/config"
echo "  → Use venv for testing"
echo ""
echo "If both ~10k:"
echo "  → Something broke in the code itself"
echo "  → Need to find the commit that broke it"
echo ""
