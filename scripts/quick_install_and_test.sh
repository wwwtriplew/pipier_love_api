#!/bin/bash

# Simple PyPy installation and test script

echo "=================================================="
echo "PyPy Installation and Performance Test"
echo "=================================================="
echo ""

# Step 1: Install PyPy
echo "Step 1: Installing PyPy3..."
echo "Running: sudo apt update && sudo apt install -y pypy3"
echo ""

sudo apt update && sudo apt install -y pypy3

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ PyPy3 installed successfully!"
else
    echo ""
    echo "✗ Installation failed"
    exit 1
fi

# Step 2: Verify installation
echo ""
echo "Step 2: Verifying installation..."
pypy3 --version
echo "PyPy location: $(which pypy3)"

# Step 3: Run quick benchmark
echo ""
echo "=================================================="
echo "Step 3: Running performance benchmark..."
echo "=================================================="
echo ""

echo "First, testing with CPython (current Python):"
echo "----------------------------------------------"
python3 -c "
import sys
import time
sys.path.insert(0, 'src')
from chess_engine import ChessBoard

board = ChessBoard()
print('Warmup...')
board.perft(2)

print('Running perft(4)...')
start = time.time()
nodes = board.perft(4)
elapsed = time.time() - start

nps = int(nodes / elapsed) if elapsed > 0 else 0
print(f'CPython: {nodes:,} nodes in {elapsed:.3f}s = {nps:,} NPS')
"

echo ""
echo "Now testing with PyPy (should be much faster):"
echo "----------------------------------------------"
pypy3 -c "
import sys
import time
sys.path.insert(0, 'src')
from chess_engine import ChessBoard

board = ChessBoard()
print('Warmup...')
board.perft(2)

print('Running perft(4)...')
start = time.time()
nodes = board.perft(4)
elapsed = time.time() - start

nps = int(nodes / elapsed) if elapsed > 0 else 0
print(f'PyPy: {nodes:,} nodes in {elapsed:.3f}s = {nps:,} NPS')
print('')
print('Speedup: {:.1f}x faster!'.format(nps / 40000.0))
"

echo ""
echo "=================================================="
echo "Installation and test complete!"
echo "=================================================="
echo ""
echo "To run your server with PyPy:"
echo "  bash run_with_pypy.sh"
echo ""
echo "To run more tests:"
echo "  bash test_with_pypy.sh"
echo ""
