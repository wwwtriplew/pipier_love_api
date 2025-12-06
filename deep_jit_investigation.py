#!/usr/bin/env python
"""
Deep dive: WHY is PyPy JIT not compiling our code?

This test will:
1. Enable PYPYLOG to see exact JIT activity
2. Run isolated tests on each component
3. Identify the EXACT reason JIT is failing
"""
import sys
import os

# Enable PyPy JIT logging
os.environ['PYPYLOG'] = 'jit-summary:-'

try:
    import __pypy__
    print("="*80)
    print("DEEP JIT INVESTIGATION")
    print("="*80)
    print(f"PyPy {sys.version}\n")
except ImportError:
    print("❌ This test requires PyPy")
    sys.exit(1)

import time

print("TEST 1: Pure Python - Baseline")
print("-" * 80)

def pure_python_loop():
    """Pure Python with no imports - should JIT compile."""
    total = 0
    for i in range(1000):
        total += i * 2
    return total

# Warmup to trigger JIT
for _ in range(10000):
    pure_python_loop()

start = time.time()
for _ in range(100000):
    pure_python_loop()
elapsed = time.time() - start
print(f"Pure Python: {100000/elapsed:,.0f} ops/sec")
print(f"Expected: >1M ops/sec if JIT compiles\n")

print("TEST 2: Import chess_engine module only")
print("-" * 80)

from src.chess_engine import ChessBoard

def create_board():
    """Just create a board - minimal complexity."""
    board = ChessBoard()
    return board

# Warmup
for _ in range(10000):
    create_board()

start = time.time()
for _ in range(100000):
    create_board()
elapsed = time.time() - start
print(f"Board creation: {100000/elapsed:,.0f} ops/sec")
print(f"Expected: >100k ops/sec if class creation is optimized\n")

print("TEST 3: Call board.generate_moves() - pure method")
print("-" * 80)

board = ChessBoard()

def call_generate_moves():
    """Call generate_moves - tests if method calls block JIT."""
    moves = board.generate_moves()
    return len(moves)

# Warmup
for _ in range(10000):
    call_generate_moves()

start = time.time()
for _ in range(100000):
    call_generate_moves()
elapsed = time.time() - start
print(f"generate_moves: {100000/elapsed:,.0f} ops/sec")
print(f"Expected: >50k ops/sec if JIT compiles\n")

print("TEST 4: Import and use Evaluator")
print("-" * 80)

from src.evaluation import Evaluator

evaluator = Evaluator()

def call_evaluate():
    """Call evaluate - tests if Evaluator complexity blocks JIT."""
    score = evaluator.evaluate(board)
    return score

# Warmup
for _ in range(10000):
    call_evaluate()

start = time.time()
for _ in range(100000):
    call_evaluate()
elapsed = time.time() - start
print(f"evaluate: {100000/elapsed:,.0f} ops/sec")
print(f"Expected: >50k ops/sec if JIT compiles\n")

print("TEST 5: Test dictionary lookups (common JIT blocker)")
print("-" * 80)

# Test if dictionary lookups in hot loops block JIT
test_dict = {0: 100, 1: 320, 2: 330, 3: 500, 4: 900}

def dict_lookup_loop():
    """Dictionary lookups in tight loop - may block JIT."""
    total = 0
    for i in range(1000):
        total += test_dict.get(i % 5, 0)
    return total

# Warmup
for _ in range(10000):
    dict_lookup_loop()

start = time.time()
for _ in range(100000):
    dict_lookup_loop()
elapsed = time.time() - start
print(f"Dict lookups: {100000/elapsed:,.0f} ops/sec")
print(f"Expected: >500k ops/sec if JIT compiles\n")

print("TEST 6: Test array indexing (JIT-friendly)")
print("-" * 80)

# Same as dict but with array
test_array = [100, 320, 330, 500, 900]

def array_lookup_loop():
    """Array indexing in tight loop - JIT should optimize."""
    total = 0
    for i in range(1000):
        total += test_array[i % 5]
    return total

# Warmup
for _ in range(10000):
    array_lookup_loop()

start = time.time()
for _ in range(100000):
    array_lookup_loop()
elapsed = time.time() - start
print(f"Array lookups: {100000/elapsed:,.0f} ops/sec")
print(f"Expected: >1M ops/sec if JIT compiles\n")

print("TEST 7: Test bitboard operations")
print("-" * 80)

def bitboard_ops():
    """Bitboard operations - should be JIT-friendly."""
    bb = 0xFF00
    total = 0
    for _ in range(1000):
        bb = ((bb << 1) | (bb >> 1)) & 0xFFFFFFFFFFFFFFFF
        total += bin(bb).count('1')
    return total

# Warmup
for _ in range(10000):
    bitboard_ops()

start = time.time()
for _ in range(100000):
    bitboard_ops()
elapsed = time.time() - start
print(f"Bitboard ops: {100000/elapsed:,.0f} ops/sec")
print(f"Expected: >500k ops/sec if JIT compiles\n")

print("="*80)
print("ANALYSIS")
print("="*80)

print("""
Check the PyPy JIT summary above for:

1. "Tracing" messages - shows JIT is trying to compile
2. "Abort" messages - shows WHY JIT gave up:
   - "Trace too long" - function is too complex
   - "Trace too many operations" - loop body too large
   - "Call to slow path" - hitting un-optimizable code
   - "Bridge failed" - can't optimize transitions

3. Look for specific function names:
   - If you see "generate_moves" in traces → it's being compiled
   - If you see "evaluate" in aborts → that's our problem

Key patterns:
- If dict lookups are slow but array lookups are fast → use arrays
- If board creation is slow → class initialization overhead
- If evaluate is slow but generate_moves is fast → Evaluator is the issue

Next steps based on results:
- If NOTHING compiles → environment/setup issue
- If simple code compiles but chess code doesn't → complexity issue
- If everything compiles but still slow → algorithmic issue
""")

print("\nNow check the JIT summary output above!")
print("="*80)
