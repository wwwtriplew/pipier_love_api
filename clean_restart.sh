#!/bin/bash
# Force clean restart - clear all caches and restart service

echo "=========================================="
echo "FULL CLEAN RESTART"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Step 1: Stop the service"
echo "----------------------------------------"
sudo systemctl stop piperlove
echo "✓ Service stopped"

echo ""
echo "Step 2: Clear all Python bytecode caches"
echo "----------------------------------------"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✓ Bytecode cache cleared"

echo ""
echo "Step 3: Restart the service"
echo "----------------------------------------"
sudo systemctl start piperlove
sleep 2
sudo systemctl status piperlove --no-pager | head -15

echo ""
echo "Step 4: Test performance after clean restart"
echo "----------------------------------------"
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

print('Warming up (500 iterations)...')
for _ in range(500):
    perft(board, 2)

print('Testing...')
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)

print(f'NPS after clean restart: {nps:,}')
print()
if nps > 50000:
    print('✓ Back to normal (>50k)')
elif nps > 30000:
    print('⚠ Lower than before but acceptable')
else:
    print('✗ Still broken (<30k)')
"

echo ""
echo "=========================================="
echo "ANALYSIS"
echo "=========================================="
echo ""
echo "If NPS is back to 50-60k:"
echo "  → Bytecode cache was the issue"
echo "  → Problem solved"
echo ""
echo "If NPS still ~10k:"
echo "  → Something else is wrong"
echo "  → Need to investigate further"
echo ""
