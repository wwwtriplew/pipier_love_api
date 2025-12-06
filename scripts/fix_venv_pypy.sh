#!/bin/bash

echo "=========================================="
echo "Fix VPS to Use PyPy Properly"
echo "=========================================="
echo ""

echo "This script will:"
echo "  1. Backup current venv"
echo "  2. Create new venv with PyPy"
echo "  3. Install requirements"
echo "  4. Restart service"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

cd /root/pipier_love_api

echo ""
echo "Step 1: Backing up current venv..."
if [ -d "venv" ]; then
    mv venv venv.backup.$(date +%s)
    echo "✓ Backed up to venv.backup.*"
else
    echo "No existing venv found"
fi

echo ""
echo "Step 2: Creating new venv with PyPy..."
pypy3 -m venv venv
if [ $? -ne 0 ]; then
    echo "✗ Failed to create venv with PyPy"
    echo "Trying to install venv module..."
    pypy3 -m pip install virtualenv
    pypy3 -m virtualenv venv
fi

echo ""
echo "Step 3: Activating venv and installing requirements..."
source venv/bin/activate

echo "Python version in new venv:"
python --version

echo ""
echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Step 4: Testing new venv performance..."
python -c "
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

print(f'New venv: {nodes:,} nodes in {elapsed:.3f}s = {nps:,} NPS')

if nps < 30000:
    print('⚠️  Still slow! PyPy might not be working properly.')
elif nps < 100000:
    print('📊 Normal CPython speed - venv might not be using PyPy')
else:
    print('🚀 Fast! PyPy is working!')
"

deactivate

echo ""
echo "Step 5: Restarting service..."
sudo systemctl restart piperlove.service

echo ""
echo "Step 6: Checking service status..."
sleep 2
sudo systemctl status piperlove.service --no-pager | head -20

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
echo ""
echo "To verify:"
echo "  journalctl -u piperlove.service -f"
echo ""
echo "Watch for the NPS in the logs during gameplay."
echo "Should see: nps 100000+ instead of nps 12000"
echo ""
