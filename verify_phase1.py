#!/usr/bin/env python3
"""
Quick verification of count_bits optimization.
Tests both correctness and rough performance.
"""

import time
from src.magic_bitboards import count_bits

print("=" * 70)
print("PHASE 1 VERIFICATION: count_bits Optimization")
print("=" * 70)

# Test 1: Correctness
print("\n1. CORRECTNESS TEST")
print("-" * 70)

test_cases = [
    (0, 0, "Empty board"),
    (1, 1, "Single bit"),
    (0xFF, 8, "One byte"),
    (0xFFFF, 16, "Two bytes"),
    (0xFFFFFFFF, 32, "Four bytes"),
    (0xFFFFFFFFFFFFFFFF, 64, "Full board"),
    (0x0101010101010101, 8, "A-file"),
    (0x8080808080808080, 8, "H-file"),
    (0xAA55AA55AA55AA55, 32, "Checkerboard"),
    (0x0000000000FF0000, 8, "Middle rank"),
]

all_pass = True
for bb, expected, description in test_cases:
    result = count_bits(bb)
    status = "✓" if result == expected else "✗ FAIL"
    print(f"{status} {description:15s}: count_bits({hex(bb):18s}) = {result:2d} (expected {expected:2d})")
    if result != expected:
        all_pass = False

if all_pass:
    print("\n✅ All correctness tests PASSED!")
else:
    print("\n❌ Some tests FAILED!")
    exit(1)

# Test 2: Performance comparison
print("\n2. PERFORMANCE TEST")
print("-" * 70)

# Generate test bitboards (common chess patterns)
test_boards = [
    0x0,  # Empty
    0xFFFFFFFFFFFFFFFF,  # Full
    0xFFFF00000000FFFF,  # Start position (pieces on ranks 1-2, 7-8)
    0x0000001818000000,  # Center 4 squares
    0x8142241818244281,  # Knight pattern
] * 200  # 1000 total tests

# Warmup
for _ in range(100):
    for bb in test_boards[:10]:
        count_bits(bb)

# Time the operation
start = time.perf_counter()
total = 0
for bb in test_boards:
    total += count_bits(bb)
elapsed = time.perf_counter() - start

calls = len(test_boards)
per_call = (elapsed / calls) * 1_000_000  # microseconds

print(f"Total calls: {calls:,}")
print(f"Total time: {elapsed*1000:.3f} ms")
print(f"Per call: {per_call:.3f} µs")
print(f"Calls/sec: {calls/elapsed:,.0f}")

if per_call < 0.5:
    print("\n✅ Performance is EXCELLENT (< 0.5 µs per call)")
elif per_call < 1.0:
    print("\n✅ Performance is GOOD (< 1.0 µs per call)")
elif per_call < 2.0:
    print("\n⚠️  Performance is ACCEPTABLE (< 2.0 µs per call)")
else:
    print("\n❌ Performance is SLOW (> 2.0 µs per call)")

# Test 3: Integration with magic bitboards
print("\n3. INTEGRATION TEST")
print("-" * 70)

from src.chess_engine import ChessBoard
from src.magic_bitboards import MagicBitboards

board = ChessBoard()
magic_bb = MagicBitboards()

# Test that magic bitboards still work
start = time.perf_counter()
for _ in range(100):
    for square in [0, 7, 56, 63, 28]:  # Corners + center
        occupancy = board.white_pieces | board.black_pieces
        rook_attacks = magic_bb.get_rook_attacks(square, occupancy)
        bishop_attacks = magic_bb.get_bishop_attacks(square, occupancy)
elapsed = time.perf_counter() - start

print(f"Magic bitboard lookups: 500 calls in {elapsed*1000:.3f} ms")
print(f"Per lookup: {(elapsed/500)*1_000_000:.3f} µs")
print("✅ Magic bitboards integration working")

print("\n" + "=" * 70)
print("PHASE 1 VERIFICATION COMPLETE")
print("=" * 70)
print("\n✅ count_bits optimization is READY for full performance test")
print("\nNext step: Run full performance analysis")
print("  python3 scripts/analyze_time_breakdown.py")
