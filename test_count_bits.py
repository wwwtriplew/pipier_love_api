#!/usr/bin/env python3
"""Test count_bits optimization correctness."""

from src.magic_bitboards import count_bits

# Test cases: (bitboard, expected_count)
test_cases = [
    (0, 0),
    (1, 1),
    (0xFF, 8),
    (0xFFFF, 16),
    (0xFFFFFFFF, 32),
    (0xFFFFFFFFFFFFFFFF, 64),
    (0x0101010101010101, 8),  # A-file
    (0x8080808080808080, 8),  # H-file
    (0xAA55AA55AA55AA55, 32),  # Checkerboard pattern
]

print("Testing count_bits optimization...")
all_pass = True

for bb, expected in test_cases:
    result = count_bits(bb)
    status = "✓" if result == expected else "✗"
    print(f"{status} count_bits({hex(bb):18s}) = {result:2d} (expected {expected:2d})")
    if result != expected:
        all_pass = False

print()
if all_pass:
    print("✅ All count_bits tests passed!")
else:
    print("❌ Some tests failed!")
    exit(1)
