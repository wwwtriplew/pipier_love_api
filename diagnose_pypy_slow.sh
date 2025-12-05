#!/bin/bash

echo "=========================================="
echo "Deep PyPy Performance Diagnostic"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "1. Check PyPy JIT status:"
echo "-------------------------------------------"
/root/venv/bin/python3 -c "
import sys
print('PyPy version:', sys.version)
print('Implementation:', sys.implementation.name)

# Check if JIT is enabled
try:
    import __pypy__
    print('JIT enabled:', __pypy__.jit_enabled())
    print('JIT parameters:', __pypy__.jit_parameters())
except Exception as e:
    print('Error checking JIT:', e)
"

echo ""
echo "2. Test perft with PYPYLOG to see JIT activity:"
echo "-------------------------------------------"
echo "Running perft(3) with JIT logging..."

PYPYLOG=jit-summary:- /root/venv/bin/python3 -c "
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

# Warmup more to trigger JIT
print('Warming up JIT...')
for i in range(5):
    perft(board, 2)
print('Warmup complete')

print('')
print('Testing perft(3)...')
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed) if elapsed > 0 else 0

print(f'Result: {nodes:,} nodes in {elapsed:.3f}s = {nps:,} NPS')
" 2>&1 | tail -50

echo ""
echo "3. Check for C extensions or slow imports:"
echo "-------------------------------------------"
/root/venv/bin/python3 -c "
import sys
sys.path.insert(0, 'src')

print('Checking loaded modules...')
import chess_engine

# Check what's actually loaded
for name, module in sorted(sys.modules.items()):
    if 'chess' in name.lower() or 'magic' in name.lower() or 'zobrist' in name.lower():
        try:
            file = getattr(module, '__file__', 'builtin')
            print(f'  {name}: {file}')
        except:
            pass
"

echo ""
echo "4. Compare direct ChessBoard vs through imports:"
echo "-------------------------------------------"
/root/venv/bin/python3 -c "
import sys
import time
sys.path.insert(0, 'src')

# Test 1: Direct import
print('Test 1: Direct ChessBoard import')
from chess_engine import ChessBoard
board1 = ChessBoard()
start = time.time()
moves = board1.generate_moves()
for _ in range(100):
    moves = board1.generate_moves()
elapsed1 = time.time() - start
print(f'  100 generate_moves calls: {elapsed1*1000:.1f}ms')

# Test 2: Through Position wrapper
print('')
print('Test 2: Through Position wrapper')
from board_state import Position
board2 = Position()
start = time.time()
for _ in range(100):
    moves = board2.legal_moves()
elapsed2 = time.time() - start
print(f'  100 legal_moves calls: {elapsed2*1000:.1f}ms')

if elapsed2 > elapsed1 * 5:
    print('')
    print('⚠️  WARNING: Position wrapper is 5x+ slower!')
    print('   This suggests the wrapper adds significant overhead')
"

echo ""
echo "5. Check sys.setrecursionlimit or other settings:"
echo "-------------------------------------------"
/root/venv/bin/python3 -c "
import sys
print('Recursion limit:', sys.getrecursionlimit())
print('Switch interval:', sys.getswitchinterval())
"

echo ""
echo "=========================================="
echo "Analysis Complete"
echo "=========================================="
