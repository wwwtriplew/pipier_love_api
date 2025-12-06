#!/usr/bin/env python3
"""
DEEP DIAGNOSTIC: Find PyPy bottleneck

Test individual components to find what's killing PyPy JIT performance.
"""

import time
import sys

print("=" * 70)
print("DEEP PYPY DIAGNOSTIC - Component Analysis")
print("=" * 70)
print(f"Python: {sys.version}")
print()

# ============================================================================
# TEST 1: Pure bitboard operations (baseline)
# ============================================================================
print("TEST 1: Pure bitboard operations (no chess logic)")
print("-" * 70)

def test_pure_bitboard():
    """Pure bitboard manipulation - should be FAST on PyPy"""
    total = 0
    for _ in range(100000):
        bb = 0xFF00  # Starting position
        count = 0
        while bb:
            lsb = bb & -bb
            sq = (lsb).bit_length() - 1
            bb ^= lsb
            count += sq
        total += count
    return total

# Warmup
for _ in range(10):
    test_pure_bitboard()

start = time.time()
result = test_pure_bitboard()
elapsed = time.time() - start
print(f"Result: {result}")
print(f"Time: {elapsed*1000:.1f}ms")
print(f"Expected: PyPy <50ms, CPython >500ms")
if elapsed < 0.05:
    print("✅ PyPy JIT working on pure bitboard ops!")
else:
    print("❌ PyPy JIT NOT optimizing bitboard ops")
print()

# ============================================================================
# TEST 2: Move generation (list creation overhead)
# ============================================================================
print("TEST 2: Move generation overhead")
print("-" * 70)

from src.board_state import Position

def test_move_generation():
    """Test if move generation is the bottleneck"""
    pos = Position()
    total = 0
    for _ in range(1000):
        moves = pos.legal_moves()  # Generates list
        total += len(moves)
    return total

# Warmup
for _ in range(10):
    test_move_generation()

start = time.time()
result = test_move_generation()
elapsed = time.time() - start
print(f"Generated {result} moves in {elapsed*1000:.1f}ms")
print(f"Moves per second: {result/elapsed:,.0f}")
print()

# ============================================================================
# TEST 3: Make/Unmake overhead
# ============================================================================
print("TEST 3: Make/Unmake move overhead")
print("-" * 70)

def test_make_unmake():
    """Test make/unmake performance"""
    pos = Position()
    moves = pos.legal_moves()
    total = 0
    
    for _ in range(100):
        for move in moves:
            pos.make_move(move)
            pos.unmake_move()
            total += 1
    
    return total

# Warmup
for _ in range(5):
    test_make_unmake()

start = time.time()
result = test_make_unmake()
elapsed = time.time() - start
print(f"Made/unmade {result} moves in {elapsed*1000:.1f}ms")
print(f"Moves per second: {result/elapsed:,.0f}")
print()

# ============================================================================
# TEST 4: Tuple unpacking overhead
# ============================================================================
print("TEST 4: Tuple unpacking overhead")
print("-" * 70)

def test_tuple_overhead():
    """Test if tuple returns are killing performance"""
    def return_tuple(x):
        return (x, x+1, x+2)
    
    total = 0
    for _ in range(1000000):
        a, b, c = return_tuple(5)
        total += a + b + c
    return total

# Warmup
for _ in range(10):
    test_tuple_overhead()

start = time.time()
result = test_tuple_overhead()
elapsed = time.time() - start
print(f"Result: {result}")
print(f"Time: {elapsed*1000:.1f}ms")
print(f"Expected: PyPy <100ms, CPython >1000ms")
if elapsed < 0.1:
    print("✅ PyPy JIT eliminating tuple allocations!")
else:
    print("❌ PyPy JIT NOT eliminating tuples")
print()

# ============================================================================
# TEST 5: Polymorphic type overhead (Optional)
# ============================================================================
print("TEST 5: Polymorphic type overhead")
print("-" * 70)

def test_polymorphic():
    """Test Optional[int] overhead"""
    def process(promo):  # Can be None or int
        if promo is not None:
            return promo * 2
        return 0
    
    total = 0
    for i in range(1000000):
        # Alternating None and int
        val = None if i % 2 == 0 else 4
        total += process(val)
    return total

# Warmup
for _ in range(10):
    test_polymorphic()

start = time.time()
result = test_polymorphic()
elapsed = time.time() - start
print(f"Result: {result}")
print(f"Time: {elapsed*1000:.1f}ms")
if elapsed < 0.2:
    print("✅ PyPy handling polymorphic types well")
else:
    print("❌ PyPy struggling with polymorphic types")
print()

# ============================================================================
# TEST 6: Actual perft (the real workload)
# ============================================================================
print("TEST 6: Actual perft performance")
print("-" * 70)

pos = Position()

# Warmup
for _ in range(50):
    pos.perft(3)

start = time.time()
nodes = pos.perft(4)
elapsed = time.time() - start
nps = int(nodes / elapsed)

print(f"Nodes: {nodes:,}")
print(f"Time: {elapsed:.3f}s")
print(f"NPS: {nps:,}")
print()

# ============================================================================
# ANALYSIS
# ============================================================================
print("=" * 70)
print("BOTTLENECK ANALYSIS")
print("=" * 70)

print("\nIf pure bitboard ops are fast BUT perft is slow:")
print("  → Bottleneck is in chess logic (move gen, make/unmake)")
print("\nIf tuple test is slow:")
print("  → PyPy not eliminating allocations")
print("\nIf polymorphic test is slow:")
print("  → Optional types causing guard overhead")
print("\nIf move generation is slow:")
print("  → List creation is the problem")
print()
