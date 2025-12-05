#!/bin/bash
# Critical Check: Is the SERVICE actually using PyPy?

echo "=========================================="
echo "CRITICAL: Which Python is uvicorn using?"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "1. Check what 'uvicorn' executable is"
echo "--------------------------------------"
which uvicorn
file $(which uvicorn)
head -1 $(which uvicorn)

echo ""
echo "2. Check venv bin directory"
echo "--------------------------------------"
ls -la /root/venv/bin/ | grep -E "python|pypy|uvicorn"

echo ""
echo "3. Check if uvicorn is using PyPy"
echo "--------------------------------------"
/root/venv/bin/uvicorn --version 2>&1 | head -5

echo ""
echo "4. Check what Python the running service uses"
echo "--------------------------------------"
SERVICE_PID=$(pgrep -f "uvicorn main:app")
if [ -n "$SERVICE_PID" ]; then
    echo "Service PID: $SERVICE_PID"
    echo "Command line:"
    ps aux | grep $SERVICE_PID | grep -v grep
    echo ""
    echo "Executable:"
    ls -la /proc/$SERVICE_PID/exe
else
    echo "Service not running!"
fi

echo ""
echo "5. Test: Which Python does uvicorn use when called from venv?"
echo "--------------------------------------"
/root/venv/bin/python3 -c "import sys; print(f'Python: {sys.executable}'); print(f'Implementation: {sys.implementation.name}')"

echo ""
echo "6. Check if venv/bin/python3 is symlinked to pypy3"
echo "--------------------------------------"
ls -la /root/venv/bin/python3
readlink -f /root/venv/bin/python3

echo ""
echo "7. THE SMOKING GUN TEST"
echo "--------------------------------------"
echo "Testing perft with the EXACT command the service would use:"
cd /root/pipier_love_api
/root/venv/bin/python3 -c "
import sys
print(f'Running under: {sys.implementation.name}')
print(f'Executable: {sys.executable}')

if sys.implementation.name == 'cpython':
    print('⚠️ SERVICE IS USING CPYTHON, NOT PYPY!')
elif sys.implementation.name == 'pypy':
    print('✓ Service is using PyPy')
    
    # Test JIT
    import __pypy__
    try:
        print(f'JIT enabled: {__pypy__.jit_enabled()}')
    except:
        print('JIT status unknown')

# Test performance
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

start = time.time()
nodes = perft(board, 3)
nps = int(nodes / (time.time() - start))
print(f'NPS: {nps:,}')
"

echo ""
echo "=========================================="
echo "DIAGNOSIS"
echo "=========================================="
echo ""
echo "If service is using CPython:"
echo "  - Explains 7.6k NPS (CPython in production is slower due to load)"
echo "  - Fix: Make sure venv is created with --copies flag and pypy3"
echo ""
echo "If service is using PyPy:"
echo "  - Something else is wrong (uvicorn overhead? async issues?)"
echo "  - Need deeper investigation"
echo ""
