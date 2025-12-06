#!/bin/bash
# Find WHY venv gets 60k but direct gets 12k

echo "=========================================="
echo "FINDING THE 60k vs 12k DIFFERENCE"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Test 1: Direct Python from /root/pipier_love_api (gets 12k)"
echo "============================================================="
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
print(f'Direct from /root/pipier_love_api: {int(nodes/elapsed):,} NPS')
"

echo ""
echo "Test 2: Venv Python from /root/pipier_love_api (should get 60k)"
echo "================================================================"
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
print(f'Venv from /root/pipier_love_api: {int(nodes/elapsed):,} NPS')
"

echo ""
echo "Test 3: Check Python bytecode compilation"
echo "=========================================="
echo "Checking for .pyc files in src/__pycache__/:"
ls -lah src/__pycache__/*.pyc 2>/dev/null | head -5 || echo "No .pyc files"

echo ""
echo "Deleting all .pyc files and retesting..."
rm -rf src/__pycache__
rm -rf testing/__pycache__

echo ""
echo "Test 4: After deleting .pyc - Direct Python"
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
print(f'Direct (no .pyc): {int(nodes/elapsed):,} NPS')
"

echo ""
echo "Test 5: After deleting .pyc - Venv Python"
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
print(f'Venv (no .pyc): {int(nodes/elapsed):,} NPS')
"

echo ""
echo "Test 6: Run the EXACT script that got 60k"
echo "=========================================="
echo "Re-running find_optimal_warmup.sh first test only:"
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

# 500 warmups like the test that got 60k
for _ in range(500):
    perft(board, 2)

start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)

print(f'500 warmups (exact script): {nps:,} NPS')
"

echo ""
echo "Test 7: Multiple consecutive runs to see if it improves"
echo "========================================================"
echo "Run 1 (cold):"
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
print(f'  {int(nodes/elapsed):,} NPS')
"

echo "Run 2 (warm):"
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
print(f'  {int(nodes/elapsed):,} NPS')
"

echo "Run 3 (hot):"
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
print(f'  {int(nodes/elapsed):,} NPS')
"

echo ""
echo ""
echo "=========================================="
echo "HYPOTHESIS"
echo "=========================================="
echo ""
echo "If consecutive runs improve (12k → 30k → 60k):"
echo "  → JIT code is cached between invocations"
echo "  → First test in find_optimal_warmup.sh was HOT"
echo "  → Single tests are COLD"
echo ""
echo "If no improvement:"
echo "  → Something random/environmental"
echo "  → Need to check system load, CPU frequency, etc."
echo ""
