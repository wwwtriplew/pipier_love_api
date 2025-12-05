#!/bin/bash
# Use Official PyPy Build (not broken Ubuntu package)

echo "=========================================="
echo "INSTALLING OFFICIAL PYPY"
echo "=========================================="
echo ""
echo "The Ubuntu PyPy package has a broken JIT."
echo "Let's use the official PyPy build instead."
echo ""

cd /root

echo "Step 1: Download official PyPy 7.3.17"
echo "--------------------------------------"
wget -q --show-progress https://downloads.python.org/pypy/pypy3.10-v7.3.17-linux64.tar.bz2

echo ""
echo "Step 2: Extract"
echo "--------------------------------------"
tar xf pypy3.10-v7.3.17-linux64.tar.bz2

echo ""
echo "Step 3: Test official PyPy JIT"
echo "--------------------------------------"
echo "Testing simple loop with official PyPy..."
/root/pypy3.10-v7.3.17-linux64/bin/pypy3 -c "
import time

def simple():
    total = 0
    for i in range(100000):
        total += i * 2
    return total

# Heavy warmup
for _ in range(1000):
    simple()

# Test
start = time.time()
for _ in range(100):
    simple()
elapsed = time.time() - start

print(f'Official PyPy simple loop: {elapsed*1000:.1f}ms (100 iterations)')
if elapsed < 0.01:
    print('✓ JIT WORKING PERFECTLY!')
elif elapsed < 0.05:
    print('⚠ JIT working but not optimal')
else:
    print('✗ JIT still broken')
"

echo ""
echo "Step 4: Create new venv with official PyPy"
echo "--------------------------------------"
rm -rf /root/venv-official
/root/pypy3.10-v7.3.17-linux64/bin/pypy3 -m venv /root/venv-official
echo "✓ Created venv-official"

echo ""
echo "Step 5: Install dependencies"
echo "--------------------------------------"
/root/venv-official/bin/pip install -q uvicorn fastapi pydantic python-chess
echo "✓ Installed dependencies"

echo ""
echo "Step 6: Test chess performance with official PyPy"
echo "--------------------------------------"
cd /root/pipier_love_api
/root/venv-official/bin/python3 -c "
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

# Warmup
print('Warming up official PyPy...')
for i in range(500):
    perft(board, 2)
    if i % 100 == 0:
        print(f'  {i}/500...')

# Test
print('Testing...')
start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
nps = int(nodes / elapsed)

print()
print(f'Official PyPy NPS: {nps:,}')
print(f'Ubuntu PyPy NPS: ~60,000')
print(f'CPython NPS: ~50,000')
print()

if nps > 150000:
    print('✓✓✓ SUCCESS! Official PyPy JIT works perfectly!')
    print('    This is 2.5x faster than CPython!')
elif nps > 80000:
    print('✓✓ GOOD! Significant improvement!')
elif nps > 60000:
    print('⚠ Marginal improvement - still issues')
else:
    print('✗ No improvement - something else is wrong')
"

echo ""
echo ""
echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo ""
echo "If official PyPy gets >150k NPS:"
echo "  → Update service to use /root/venv-official"
echo "  → Edit /etc/systemd/system/piperlove.service"
echo "  → Change: /root/venv/bin/uvicorn"
echo "  → To: /root/venv-official/bin/uvicorn"
echo ""
echo "If official PyPy is still slow:"
echo "  → Hardware limitation (CPU too old for JIT?)"
echo "  → Use CPython (50k NPS is acceptable)"
echo ""
