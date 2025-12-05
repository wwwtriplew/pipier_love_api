#!/bin/bash
# Critical Check: Is the SERVICE actually using PyPy?

echo "=========================================="
echo "CRITICAL: Which Python is the service using?"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "1. Check venv/bin/python3 (what uvicorn uses)"
echo "--------------------------------------"
echo "Symlink:"
ls -la /root/venv/bin/python3
echo ""
echo "Resolves to:"
readlink -f /root/venv/bin/python3
echo ""
echo "Version:"
/root/venv/bin/python3 --version

echo ""
echo "2. Test what implementation venv/bin/python3 is"
echo "--------------------------------------"
/root/venv/bin/python3 -c "
import sys
print(f'Implementation: {sys.implementation.name}')
print(f'Executable: {sys.executable}')
"

echo ""
echo "3. Check running service process"
echo "--------------------------------------"
SERVICE_PID=$(pgrep -f "uvicorn main:app" | head -1)
if [ -n "$SERVICE_PID" ]; then
    echo "Service PID: $SERVICE_PID"
    echo ""
    echo "Command:"
    ps -p $SERVICE_PID -o cmd=
    echo ""
    echo "Executable path:"
    readlink -f /proc/$SERVICE_PID/exe 2>/dev/null || echo "Could not resolve"
else
    echo "Service not running!"
fi

echo ""
echo "4. Quick NPS test with venv/bin/python3"
echo "--------------------------------------"
/root/venv/bin/python3 -c "
import sys
print(f'Testing with: {sys.implementation.name}')

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
print(f'NPS with venv python3: {nps:,}')
"

echo ""
echo "=========================================="
echo "DIAGNOSIS"
echo "=========================================="
echo ""
echo "Key question: Is venv/bin/python3 -> cpython or pypy?"
echo ""
echo "If CPython → Service is NOT using PyPy (explains slow speed)"
echo "If PyPy → Service IS using PyPy (need different explanation)"
echo ""

