#!/bin/bash
# Deep Investigation: Why is PyPy getting 6k NPS when CPython gets 40k?
# This is NOT a JIT trace issue - something else is fundamentally wrong

set -e

echo "=========================================="
echo "DEEP INVESTIGATION: 6K NPS ROOT CAUSE"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "HYPOTHESIS 1: Position wrapper overhead"
echo "=========================================="
echo ""
echo "Test 1a: Direct ChessBoard perft (should be fast)"
/root/venv/bin/pypy3 -c "
from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb
import time

board = ChessBoard()

def direct_perft(board, depth):
    if depth == 0:
        return 1
    nodes = 0
    for from_sq, to_sq, promo in board.generate_moves():
        board.make_move(from_sq, to_sq, promo)
        king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])  # KING=5
        if not board.is_square_attacked(king_sq, board.side_to_move):
            nodes += direct_perft(board, depth - 1)
        board.unmake_move()
    return nodes

# Warmup
for _ in range(5):
    direct_perft(board, 2)

start = time.time()
nodes = direct_perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)
print(f'Direct ChessBoard: {nps:,} NPS')
" 2>&1

echo ""
echo "Test 1b: Position wrapper perft (probably slow)"
/root/venv/bin/pypy3 -c "
from src.board_state import Position
import time

p = Position()

# Warmup
for _ in range(5):
    p.perft(2)

start = time.time()
nodes = p.perft(3)
elapsed = time.time() - start
nps = int(nodes / elapsed)
print(f'Position wrapper: {nps:,} NPS')
" 2>&1

echo ""
echo ""
echo "HYPOTHESIS 2: Import/module loading overhead"
echo "=========================================="
echo ""
/root/venv/bin/pypy3 -c "
import sys
import time

# Time the import
start = time.time()
from src.board_state import Position
import_time = time.time() - start
print(f'Import time: {import_time*1000:.1f}ms')

# Check what's loaded
chess_modules = [name for name in sys.modules if 'chess' in name or 'src' in name]
print(f'Loaded modules: {len(chess_modules)}')
for mod in sorted(chess_modules)[:10]:
    print(f'  - {mod}')
" 2>&1

echo ""
echo ""
echo "HYPOTHESIS 3: PyPy version and compatibility"
echo "=========================================="
echo ""
/root/venv/bin/pypy3 --version 2>&1
/root/venv/bin/pypy3 -c "
import sys
print(f'Python version: {sys.version}')
print(f'Implementation: {sys.implementation.name}')

# Check if any C extensions are being used
import sys
suspicious_modules = []
for name, module in sys.modules.items():
    if module and hasattr(module, '__file__') and module.__file__:
        if module.__file__.endswith('.so') or module.__file__.endswith('.pyd'):
            suspicious_modules.append(name)

if suspicious_modules:
    print(f'\\nC extensions loaded: {len(suspicious_modules)}')
    for mod in suspicious_modules[:10]:
        print(f'  - {mod}')
else:
    print('\\nNo C extensions detected (good)')
" 2>&1

echo ""
echo ""
echo "HYPOTHESIS 4: CPU/Memory constraints"
echo "=========================================="
echo ""
echo "CPU info:"
cat /proc/cpuinfo | grep -E "model name|cpu MHz|cache size" | head -3
echo ""
echo "Memory info:"
free -h
echo ""
echo "Load average:"
uptime

echo ""
echo ""
echo "HYPOTHESIS 5: Check if JIT is actually enabled"
echo "=========================================="
echo ""
/root/venv/bin/pypy3 -c "
try:
    import __pypy__
    print(f'PyPy detected: True')
    print(f'JIT enabled: {__pypy__.jit_enabled()}')
    
    # Get JIT parameters
    print('\\nJIT Parameters:')
    print(f'  trace_limit: {__pypy__.jit_parameters()[\"trace_limit\"]}')
    print(f'  threshold: {__pypy__.jit_parameters()[\"threshold\"]}')
    print(f'  function_threshold: {__pypy__.jit_parameters()[\"function_threshold\"]}')
except:
    print('Not running under PyPy or JIT not available')
" 2>&1

echo ""
echo ""
echo "HYPOTHESIS 6: Comparison with CPython baseline"
echo "=========================================="
echo ""
echo "CPython perft(3):"
python3 -c "
from src.board_state import Position
import time

p = Position()
start = time.time()
nodes = p.perft(3)
elapsed = time.time() - start
nps = int(nodes / elapsed)
print(f'CPython Position wrapper: {nps:,} NPS')
" 2>&1

echo ""
echo "CPython direct ChessBoard:"
python3 -c "
from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb
import time

board = ChessBoard()

def direct_perft(board, depth):
    if depth == 0:
        return 1
    nodes = 0
    for from_sq, to_sq, promo in board.generate_moves():
        board.make_move(from_sq, to_sq, promo)
        king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])
        if not board.is_square_attacked(king_sq, board.side_to_move):
            nodes += direct_perft(board, depth - 1)
        board.unmake_move()
    return nodes

start = time.time()
nodes = direct_perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)
print(f'CPython ChessBoard direct: {nps:,} NPS')
" 2>&1

echo ""
echo ""
echo "HYPOTHESIS 7: Check for recursive import issues"
echo "=========================================="
echo ""
/root/venv/bin/pypy3 -c "
import sys
import time

# Clear module cache
for key in list(sys.modules.keys()):
    if 'src' in key or 'chess' in key:
        del sys.modules[key]

# Time a fresh import
start = time.time()
from src.chess_engine import ChessBoard
first_import = time.time() - start

# Time second import (should be cached)
start = time.time()
from src.chess_engine import ChessBoard
second_import = time.time() - start

print(f'First import: {first_import*1000:.1f}ms')
print(f'Second import: {second_import*1000:.6f}ms')
print(f'Import overhead: {\"SIGNIFICANT\" if first_import > 0.1 else \"Normal\"}')
" 2>&1

echo ""
echo ""
echo "=========================================="
echo "INVESTIGATION COMPLETE"
echo "=========================================="
echo ""
echo "Key things to look for:"
echo "1. Direct ChessBoard should be MUCH faster than Position wrapper"
echo "2. PyPy should be similar or faster than CPython (not 7x slower)"
echo "3. JIT should be enabled"
echo "4. No suspicious C extensions"
echo "5. CPU not throttled"
echo ""
