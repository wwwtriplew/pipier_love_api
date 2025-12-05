#!/bin/bash
# Find what's BLOCKING PyPy JIT

echo "=========================================="
echo "FINDING THE JIT BLOCKER"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Test 1: Minimal Python code (no imports)"
echo "=================================================="
/root/venv/bin/python3 -c "
import time

def simple():
    total = 0
    for i in range(100000):
        total += i * 2
    return total

# No warmup - just run
start = time.time()
for _ in range(100):
    simple()
elapsed = time.time() - start
print(f'100 iterations of 100k loop: {elapsed*1000:.1f}ms')
print(f'Expected with JIT: <10ms')
print(f'Expected without JIT: ~50-100ms')
if elapsed > 0.15:
    print(f'Result: CATASTROPHICALLY SLOW ({elapsed*1000:.0f}ms)')
"

echo ""
echo ""
echo "Test 2: Check if venv has issues - use system PyPy directly"
echo "=================================================="
/usr/bin/pypy3 -c "
import time

def simple():
    total = 0
    for i in range(100000):
        total += i * 2
    return total

start = time.time()
for _ in range(100):
    simple()
elapsed = time.time() - start
print(f'System PyPy: {elapsed*1000:.1f}ms')
if elapsed < 0.015:
    print('✓ System PyPy JIT WORKS!')
elif elapsed < 0.1:
    print('⚠ System PyPy working but slow')
else:
    print('✗ System PyPy ALSO broken')
"

echo ""
echo ""
echo "Test 3: Check venv creation method"
echo "=================================================="
echo "Current venv python:"
ls -la /root/venv/bin/python3
readlink -f /root/venv/bin/python3
echo ""
echo "How was venv created?"
if [ -f /root/venv/pyvenv.cfg ]; then
    echo "pyvenv.cfg contents:"
    cat /root/venv/pyvenv.cfg
else
    echo "No pyvenv.cfg - venv might be corrupted"
fi

echo ""
echo ""
echo "Test 4: Check for PyPy environment pollution"
echo "=================================================="
echo "Checking for conflicting environment variables..."
env | grep -i py | grep -v "PATH" | grep -v "PWD"
echo ""
echo "Checking sys.path for pollution..."
/root/venv/bin/python3 -c "
import sys
print('sys.path:')
for p in sys.path:
    print(f'  {p}')
print()
print('Checking for CPython contamination...')
cpython_paths = [p for p in sys.path if 'python3.1' in p.lower() or 'cpython' in p.lower()]
if cpython_paths:
    print('⚠ WARNING: CPython paths in PyPy sys.path!')
    for p in cpython_paths:
        print(f'  {p}')
else:
    print('✓ No CPython contamination')
"

echo ""
echo ""
echo "Test 5: Test if JIT can be manually enabled"
echo "=================================================="
/root/venv/bin/python3 -c "
import sys
print(f'PyPy version: {sys.version}')
print()

# Try to force JIT on
import __pypy__
print('Checking JIT status...')
try:
    jit_enabled = __pypy__.jit_enabled()
    print(f'JIT enabled: {jit_enabled}')
    if not jit_enabled:
        print('⚠ JIT IS DISABLED!')
except AttributeError:
    print('jit_enabled() not available')

# Try to set JIT options
try:
    __pypy__.set_param(None, 'trace_eagerness', 1)  # Compile more aggressively
    print('✓ Set trace_eagerness to 1')
except:
    print('Cannot modify JIT parameters')
"

echo ""
echo ""
echo "Test 6: Memory pressure test"
echo "=================================================="
echo "Available memory:"
free -m | grep "^Mem:"
echo ""
echo "Testing if memory pressure disables JIT..."
/root/venv/bin/python3 -c "
import gc
import time

# Force garbage collection
gc.collect()

def simple():
    total = 0
    for i in range(100000):
        total += i * 2
    return total

# Test with minimal memory footprint
start = time.time()
for _ in range(100):
    simple()
elapsed = time.time() - start
print(f'Elapsed: {elapsed*1000:.1f}ms')
"

echo ""
echo ""
echo "Test 7: Check if uvicorn/FastAPI imports break JIT"
echo "=================================================="
/root/venv/bin/python3 -c "
import time

# Test 1: Before any imports
def simple():
    total = 0
    for i in range(100000):
        total += i * 2
    return total

start = time.time()
for _ in range(100):
    simple()
before_imports = time.time() - start

# Now import our code
from src.chess_engine import ChessBoard

# Test 2: After imports
start = time.time()
for _ in range(100):
    simple()
after_imports = time.time() - start

print(f'Before imports: {before_imports*1000:.1f}ms')
print(f'After imports: {after_imports*1000:.1f}ms')

if after_imports > before_imports * 2:
    print('⚠ Imports make JIT WORSE!')
elif before_imports > 0.15:
    print('✗ JIT broken even before imports')
else:
    print('✓ Imports not the issue')
"

echo ""
echo ""
echo "=========================================="
echo "DIAGNOSIS FRAMEWORK"
echo "=========================================="
echo ""
echo "If system PyPy works but venv doesn't:"
echo "  → Venv creation issue - recreate venv properly"
echo ""
echo "If both are slow:"
echo "  → System-wide PyPy issue - reinstall or use official PyPy"
echo ""
echo "If memory <200MB:"
echo "  → Memory pressure disables JIT - reduce TT size"
echo ""
echo "If imports break JIT:"
echo "  → Module conflict - isolate the problematic import"
echo ""
