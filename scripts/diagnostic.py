#!/usr/bin/env python3
"""
Diagnostic to identify WHY PyPy JIT isn't optimizing the chess engine.
Based on: loop shape, guards, polymorphism, and JIT behavior analysis.
"""

import sys
import time
import platform

print("=" * 80)
print("PYPY JIT DIAGNOSTIC")
print("=" * 80)
print(f"Implementation: {platform.python_implementation()}")
print(f"Version: {sys.version}")

try:
    import __pypy__
    import pypyjit
    print(f"JIT: Enabled")
    try:
        print(f"JIT params: {pypyjit.get_params()}")
    except:
        print("JIT params: Not available")
    IS_PYPY = True
except ImportError:
    print("JIT: N/A (CPython)")
    IS_PYPY = False

print()

# =============================================================================
# TEST 1: Ultra-thin loop (CPython 3.11+ should win with PEP 659)
# =============================================================================
print("=" * 80)
print("TEST 1: Ultra-thin loop (minimal work per iteration)")
print("=" * 80)

def thin_loop():
    s = 0
    for i in range(100000):
        s += i * 2
    return s

# Warmup
for _ in range(100):
    thin_loop()

# Test
t0 = time.perf_counter()
for _ in range(100):
    thin_loop()
t1 = time.perf_counter()

thin_time = (t1 - t0) * 1000
print(f"Time: {thin_time:.1f}ms (100 iterations of 100k loop)")
print(f"Expected: CPython 3.12 <20ms, PyPy <10ms if JIT works")
print()

# =============================================================================
# TEST 2: Rich loop (more work per iteration - should favor PyPy)
# =============================================================================
print("=" * 80)
print("TEST 2: Rich loop (substantial work per iteration)")
print("=" * 80)

def rich_loop():
    s = 0
    a = [1, 2, 3, 4, 5, 6, 7, 8]
    for i in range(10000):
        b = a[i & 7]
        s += (i ^ s) + (b * 3) - (i >> 2)
        if (s & 3) == 0:
            s += b
    return s

# Warmup
for _ in range(50):
    rich_loop()

# Test
t0 = time.perf_counter()
for _ in range(50):
    rich_loop()
t1 = time.perf_counter()

rich_time = (t1 - t0) * 1000
print(f"Time: {rich_time:.1f}ms (50 iterations)")
print(f"Expected: PyPy should be faster here if JIT works")
print()

# =============================================================================
# TEST 3: Chess bitboard operations (core hot path)
# =============================================================================
print("=" * 80)
print("TEST 3: Bitboard operations (chess hot path)")
print("=" * 80)

from src.magic_bitboards import pop_lsb, get_lsb, count_bits

def bitboard_loop():
    """Simulate hot path: bitboard manipulation."""
    bb = 0xFFFFFFFFFFFFFFFF
    total = 0
    
    for _ in range(1000):
        temp_bb = bb
        while temp_bb:
            sq, temp_bb = pop_lsb(temp_bb)
            total += sq
    
    return total

# Warmup
for _ in range(10):
    bitboard_loop()

# Test
t0 = time.perf_counter()
for _ in range(10):
    bitboard_loop()
t1 = time.perf_counter()

bitboard_time = (t1 - t0) * 1000
print(f"Time: {bitboard_time:.1f}ms (10 iterations)")
print()

# =============================================================================
# TEST 4: Actual perft (SMALL depth for speed)
# =============================================================================
print("=" * 80)
print("TEST 4: Real chess perft (depth 3)")
print("=" * 80)

from src.chess_engine import ChessBoard

def perft(board, depth):
    if depth == 0:
        return 1
    nodes = 0
    for from_sq, to_sq, promo in board.generate_moves():
        board.make_move(from_sq, to_sq, promo)
        king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])
        if not board.is_square_attacked(king_sq, board.side_to_move):
            nodes += perft(board, depth - 1)
        board.unmake_move()
    return nodes

board = ChessBoard()

# Small warmup
print("Warmup (50 iterations)...")
for _ in range(50):
    perft(board, 2)

# Test depth 3 only
print("Testing depth 3...")
t0 = time.perf_counter()
nodes = perft(board, 3)
t1 = time.perf_counter()

perft_time = (t1 - t0) * 1000
nps = int(nodes / (perft_time / 1000))
print(f"Nodes: {nodes:,}")
print(f"Time: {perft_time:.1f}ms")
print(f"NPS: {nps:,}")
print()

# =============================================================================
# ANALYSIS
# =============================================================================
print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()

if IS_PYPY:
    print("PyPy JIT Analysis:")
    print("-" * 80)
    
    if thin_time > 20:
        print("❌ Thin loop SLOW (>20ms)")
        print("   → JIT might not be optimizing simple loops")
        print("   → Or CPU too old for modern JIT")
    else:
        print("✓ Thin loop OK (<20ms)")
    
    if rich_time < thin_time:
        print("✓ Rich loop FASTER than thin loop")
        print("   → JIT is working on richer workloads")
    else:
        print("❌ Rich loop NOT faster than thin")
        print("   → JIT not providing expected benefits")
    
    if nps < 20000:
        print("❌ Perft NPS VERY LOW (<20k)")
        print("   → Something fundamentally wrong:")
        print("     • Too many guards/deopts in hot path")
        print("     • Polymorphic call sites")
        print("     • JIT giving up on traces")
    elif nps < 50000:
        print("⚠️  Perft NPS MODERATE (20-50k)")
        print("   → JIT working but not optimally:")
        print("     • Loop body might be too complex")
        print("     • Some polymorphism present")
        print("     • Guards costing per iteration")
    else:
        print("✓ Perft NPS GOOD (>50k)")
        print("   → JIT is optimizing the workload")
    
    print()
    print("RECOMMENDATION:")
    print("-" * 80)
    
    if nps < 40000:
        print("❌ PyPy is NOT providing significant benefit")
        print("   → Switch to CPython 3.12+ for:")
        print("     • Simpler deployment")
        print("     • Predictable performance")
        print("     • PEP 659 specialization handles simple loops well")
        print(f"   → Expected CPython NPS: 30-50k")
    else:
        print("✓ PyPy is providing benefit over CPython")
        print("   → Keep PyPy")
        print("   → Consider more warmup in production")

else:
    print("CPython Baseline:")
    print("-" * 80)
    print(f"Thin loop: {thin_time:.1f}ms")
    print(f"Rich loop: {rich_time:.1f}ms")
    print(f"Perft NPS: {nps:,}")
    print()
    print("This is your baseline. PyPy should beat this on perft if it's working.")

print()
print("=" * 80)
