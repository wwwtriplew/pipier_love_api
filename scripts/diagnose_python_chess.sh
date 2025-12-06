#!/bin/bash
# Check if python-chess library is killing performance

echo "=========================================="
echo "TESTING: Is python-chess the blocker?"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Test 1: Our code WITHOUT python-chess import"
echo "================================================"
/usr/bin/pypy3.9 -c "
# Import ONLY our code, no python-chess
from src.board_state import Position
from src.move_generation import generate_moves
from src.magic_bitboards import get_lsb
import time

# Create position manually (no python-chess)
p = Position()

def perft(pos, depth):
    if depth == 0: return 1
    n = 0
    for f, t, pr in generate_moves(pos):
        pos.make_move(f, t, pr)
        k = get_lsb(pos.pieces[1-pos.side_to_move][5])
        from src.move_generation import is_square_attacked
        if not is_square_attacked(pos, k, pos.side_to_move):
            n += perft(pos, depth-1)
        pos.unmake_move()
    return n

# Warmup
for _ in range(500):
    perft(p, 2)

# Test
start = time.time()
nodes = perft(p, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)

print(f'WITHOUT python-chess: {nps:,} NPS')
"

echo ""
echo "Test 2: Our code WITH python-chess imported but not used"
echo "=========================================================="
/usr/bin/pypy3.9 -c "
import chess  # Import but don't use it

from src.board_state import Position
from src.move_generation import generate_moves
from src.magic_bitboards import get_lsb
import time

p = Position()

def perft(pos, depth):
    if depth == 0: return 1
    n = 0
    for f, t, pr in generate_moves(pos):
        pos.make_move(f, t, pr)
        k = get_lsb(pos.pieces[1-pos.side_to_move][5])
        from src.move_generation import is_square_attacked
        if not is_square_attacked(pos, k, pos.side_to_move):
            n += perft(pos, depth-1)
        pos.unmake_move()
    return n

for _ in range(500):
    perft(p, 2)

start = time.time()
nodes = perft(p, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)

print(f'WITH python-chess import: {nps:,} NPS')
"

echo ""
echo "Test 3: Check if chess_engine.py uses python-chess"
echo "===================================================="
echo "Checking imports in src/chess_engine.py:"
grep -n "import chess" src/chess_engine.py || echo "✓ No python-chess import"
grep -n "from chess" src/chess_engine.py || echo "✓ No python-chess import"

echo ""
echo "Test 4: Check ALL our source files for python-chess usage"
echo "=========================================================="
echo "Files importing python-chess:"
grep -r "import chess" src/ testing/ --include="*.py" || echo "✓ No files import python-chess"
grep -r "from chess" src/ testing/ --include="*.py" || echo "✓ No files import python-chess"

echo ""
echo "Test 5: Test with ChessBoard class directly"
echo "============================================"
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
nps = int(nodes / elapsed)

print(f'ChessBoard class: {nps:,} NPS')
"

echo ""
echo "Test 6: Ubuntu PyPy vs Official PyPy on SAME code"
echo "=================================================="
echo "Ubuntu PyPy 3.9.18:"
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
print(f'Ubuntu PyPy: {int(nodes/(elapsed)):.0f} NPS')
"

echo ""
echo "Official PyPy 3.10:"
/root/pypy3.10-v7.3.17-linux64/bin/pypy3 -c "
import sys
sys.path.insert(0, '/root/pipier_love_api')

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
print(f'Official PyPy: {int(nodes/(elapsed)):.0f} NPS')
"

echo ""
echo ""
echo "=========================================="
echo "ANALYSIS"
echo "=========================================="
echo ""
echo "If NPS is consistent across tests:"
echo "  → Not a python-chess issue"
echo ""
echo "If NPS drops with python-chess import:"
echo "  → python-chess library conflicts with JIT"
echo ""
echo "If Ubuntu PyPy >> Official PyPy:"
echo "  → Ubuntu build has optimizations official lacks"
echo "  → Or Official PyPy has compatibility issues"
echo ""
