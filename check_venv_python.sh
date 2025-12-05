#!/bin/bash

echo "=========================================="
echo "Quick VPS Python Version Check"
echo "=========================================="
echo ""

echo "1. System Python:"
python3 --version

echo ""
echo "2. System PyPy:"
pypy3 --version 2>&1 | head -1

echo ""
echo "3. Venv Python:"
/root/venv/bin/python3 --version

echo ""
echo "4. Venv pip location:"
/root/venv/bin/pip --version

echo ""
echo "5. Check if venv is actually using PyPy:"
/root/venv/bin/python3 -c "import sys; print('Executable:', sys.executable); print('Is PyPy:', 'PyPy' in sys.version)"

echo ""
echo "6. Quick perft test with venv Python:"
cd /root/pipier_love_api
/root/venv/bin/python3 -c "
import sys
import time
sys.path.insert(0, 'src')
from chess_engine import ChessBoard

def perft(board, depth):
    if depth == 0:
        return 1
    nodes = 0
    for move in board.generate_moves():
        board.make_move(*move)
        nodes += perft(board, depth - 1)
        board.unmake_move()
    return nodes

board = ChessBoard()
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed) if elapsed > 0 else 0

print(f'Venv Python: {nodes:,} nodes in {elapsed:.3f}s = {nps:,} NPS')
"

echo ""
echo "=========================================="
echo "Analysis:"
echo "=========================================="
echo ""
echo "If step 3 shows 'CPython' instead of 'PyPy':"
echo "  → Your venv is NOT using PyPy!"
echo "  → This explains the slow performance"
echo ""
echo "If step 6 shows low NPS (< 30,000):"
echo "  → Engine is running slow even in the venv"
echo "  → This is your production performance"
echo ""
