#!/bin/bash

echo "==========================================="
echo "VPS Chess Engine Performance Test"
echo "==========================================="
echo ""

# Test with whatever Python is available
echo "Testing current configuration..."
echo "-------------------------------------------"

# Determine which Python to use
PYTHON_CMD=""
if command -v pypy3 &> /dev/null; then
    PYTHON_CMD="pypy3"
    echo "Using: PyPy3 ($(which pypy3))"
elif [ -f "pypy/bin/pypy3" ]; then
    PYTHON_CMD="pypy/bin/pypy3"
    echo "Using: Local PyPy (pypy/bin/pypy3)"
else
    PYTHON_CMD="python3"
    echo "Using: CPython ($(which python3))"
fi

echo ""
$PYTHON_CMD --version 2>&1
echo ""

# Run quick perft test
echo "Running perft(4) test (197,281 nodes)..."
echo "-------------------------------------------"

$PYTHON_CMD -c "
import sys
import time
sys.path.insert(0, 'src')
from chess_engine import ChessBoard

board = ChessBoard()

# Warmup
print('Warming up...')
board.perft(2)

# Test
print('Running perft(4)...')
start = time.time()
nodes = board.perft(4)
elapsed = time.time() - start

nps = int(nodes / elapsed) if elapsed > 0 else 0

print('')
print('=' * 60)
print('RESULTS:')
print(f'  Nodes:  {nodes:,}')
print(f'  Time:   {elapsed:.3f}s')
print(f'  NPS:    {nps:,}')
print('=' * 60)
print('')

# Analysis
if nps < 30000:
    print('⚠️  VERY SLOW - This is causing your poor gameplay!')
    print(f'   Current: {nps:,} NPS')
    print('   Expected with CPython: 40,000 NPS')
    print('   Expected with PyPy: 1,000,000 NPS')
    print('')
    print('   ACTION: Switch to PyPy with: bash switch_to_pypy.sh')
elif nps < 100000:
    print('📊 Normal CPython speed')
    print(f'   Current: {nps:,} NPS')
    print('   With PyPy you could get: 1,000,000 NPS (10-25x faster)')
    print('')
    print('   ACTION: Switch to PyPy for huge speedup!')
elif nps < 500000:
    print('🚀 Good performance (likely PyPy with warmup needed)')
    print(f'   Current: {nps:,} NPS')
    print('   This should provide decent gameplay')
else:
    print('⚡ EXCELLENT performance (PyPy JIT optimized!)')
    print(f'   Current: {nps:,} NPS')
    print('   This will provide strong gameplay')

print('')
print('Browser gameplay estimates:')
if nps < 30000:
    print('  12-second search: ~300k nodes (depth 4-5) - WEAK')
elif nps < 100000:
    print('  12-second search: ~1M nodes (depth 5-6) - DECENT')
elif nps < 500000:
    print('  12-second search: ~5M nodes (depth 6-7) - GOOD')
else:
    print('  12-second search: ~12M+ nodes (depth 7-8) - STRONG')
" 2>&1

echo ""
echo "==========================================="
echo "Test complete!"
echo "==========================================="
