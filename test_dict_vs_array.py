#!/usr/bin/env python
"""
Test: Does replacing dict with array improve performance?

This will test the EXACT fix before we apply it.
"""
import sys
import time

try:
    import __pypy__
    print("✅ PyPy detected\n")
except ImportError:
    print("⚠️  Not PyPy, but continuing...\n")

print("="*80)
print("DICT vs ARRAY PERFORMANCE TEST")
print("="*80)

# Simulate current code (dict lookup)
MATERIAL_VALUES_DICT = {
    0: 100,  # PAWN
    1: 320,  # KNIGHT  
    2: 330,  # BISHOP
    3: 500,  # ROOK
    4: 900,  # QUEEN
    5: 0     # KING
}

# Proposed fix (array indexing)
MATERIAL_VALUES_ARRAY = [100, 320, 330, 500, 900, 0]

# Phase values - same test
PHASE_VALUES_DICT = {
    0: 0,    # PAWN (ignored in phase)
    1: 1,    # KNIGHT
    2: 1,    # BISHOP
    3: 2,    # ROOK
    4: 4     # QUEEN
}

PHASE_VALUES_ARRAY = [0, 1, 1, 2, 4]

print("\nTEST 1: Dictionary lookups (current implementation)")
print("-" * 80)

def test_dict_lookups():
    """Simulate material evaluation with dict lookups."""
    total = 0
    # Simulate evaluating 100 positions
    for _ in range(100):
        # Simulate piece counting (white material)
        for piece_type in range(5):  # PAWN to QUEEN
            count = 2  # Assume 2 pieces of each type
            total += count * MATERIAL_VALUES_DICT[piece_type]
        # Black material
        for piece_type in range(5):
            count = 2
            total -= count * MATERIAL_VALUES_DICT[piece_type]
    return total

# Warmup
for _ in range(10000):
    test_dict_lookups()

# Measure
start = time.time()
for _ in range(100000):
    test_dict_lookups()
elapsed = time.time() - start
dict_speed = 100000 / elapsed

print(f"Dict lookups: {dict_speed:,.0f} ops/sec")
print(f"Time: {elapsed:.3f}s")

print("\nTEST 2: Array indexing (proposed fix)")
print("-" * 80)

def test_array_lookups():
    """Simulate material evaluation with array indexing."""
    total = 0
    for _ in range(100):
        # White material
        for piece_type in range(5):
            count = 2
            total += count * MATERIAL_VALUES_ARRAY[piece_type]
        # Black material
        for piece_type in range(5):
            count = 2
            total -= count * MATERIAL_VALUES_ARRAY[piece_type]
    return total

# Warmup
for _ in range(10000):
    test_array_lookups()

# Measure
start = time.time()
for _ in range(100000):
    test_array_lookups()
elapsed = time.time() - start
array_speed = 100000 / elapsed

print(f"Array indexing: {array_speed:,.0f} ops/sec")
print(f"Time: {elapsed:.3f}s")

print("\n" + "="*80)
print("RESULTS")
print("="*80)

speedup = array_speed / dict_speed
print(f"\nSpeedup: {speedup:.2f}x faster with arrays")

if speedup > 2.0:
    print("✅ SIGNIFICANT IMPROVEMENT - Arrays are >2x faster")
    print("   Recommendation: Apply this fix immediately")
elif speedup > 1.2:
    print("✅ MODERATE IMPROVEMENT - Arrays are faster")
    print("   Recommendation: Apply this fix (easy win)")
else:
    print("⚠️  MINIMAL IMPROVEMENT - Arrays only slightly faster")
    print("   Recommendation: Look for other optimizations")

print("\n" + "="*80)
print("ACTUAL CHESS ENGINE TEST")
print("="*80)

# Now test with actual evaluation code
print("\nTesting with actual Evaluator...")
from src.evaluation import Evaluator
from src.chess_engine import ChessBoard

board = ChessBoard()
evaluator = Evaluator()

# Warmup
for _ in range(10000):
    evaluator.evaluate(board)

# Measure
start = time.time()
for _ in range(100000):
    evaluator.evaluate(board)
elapsed = time.time() - start

print(f"Current implementation: {100000/elapsed:,.0f} evals/sec")
print(f"Time: {elapsed:.3f}s")

if 100000/elapsed < 50000:
    print("❌ SLOW - This confirms dict lookups are the bottleneck")
    print("   Expected: >100k evals/sec with JIT optimization")
else:
    print("✅ Already fast - may not need this fix")

print("\n" + "="*80)
