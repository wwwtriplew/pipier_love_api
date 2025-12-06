#!/usr/bin/env python3
"""
Verify that PyPy JIT is NOT compiling the evaluate() method.
This will prove the bottleneck is method complexity, not dict lookups.
"""

import sys
import os

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

print("=" * 80)
print("PYPYVERIFICATION: Is evaluate() Being JIT-Compiled?")
print("=" * 80)
print()

# Check we're on PyPy
try:
    import __pypy__
    print(f"✅ Running on PyPy {sys.version}")
    print(f"✅ JIT enabled: {__pypy__.jit_enabled()}")
except ImportError:
    print("❌ Not running on PyPy - this test is meaningless")
    sys.exit(1)

print()
print("=" * 80)
print("Test 1: Check JIT Activity for Simple Loop")
print("=" * 80)

# Enable JIT logging
os.environ['PYPYLOG'] = 'jit-summary:-'

# Import after setting env var
from src.chess_engine import ChessBoard
from src.evaluation import Evaluator

print("\nRunning simple baseline loop...")
print("(This should show 'Tracing' and 'Backend' messages)")
print()

# Simple loop - should JIT compile
MATERIAL_VALUES = (100, 320, 330, 500, 900, 0)
total = 0

for _ in range(1000):
    for j in range(100):
        total += MATERIAL_VALUES[j % 6]

print(f"Baseline total: {total}")
print()

print("=" * 80)
print("Test 2: Check JIT Activity for evaluate()")
print("=" * 80)
print("\nRunning evaluate() warmup...")
print("(If NO 'Tracing' messages for 'evaluate', then JIT is NOT compiling it)")
print()

board = ChessBoard()
evaluator = Evaluator()

# Warmup - give JIT chance to compile
for _ in range(10000):
    score = evaluator.evaluate(board)

print(f"Evaluate score: {score}")
print()

print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()
print("Check the output above:")
print()
print("IF you see messages like:")
print("  '[Tracing 123] evaluate'")
print("  '[Backend] evaluate'")
print("→ JIT IS compiling evaluate() - bottleneck is elsewhere")
print()
print("IF you see NO such messages for 'evaluate':")
print("→ JIT is NOT compiling evaluate() - THIS IS THE BOTTLENECK!")
print("→ Reason: Method too complex (8+ method calls, attribute access, branches)")
print("→ Solution: Inline hot path methods into single function")
print()
print("Expected result: NO JIT compilation of evaluate() method")
print()
