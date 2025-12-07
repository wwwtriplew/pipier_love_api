#!/usr/bin/env python3
"""Check specific array indices."""

import sys
import os
import chess.polyglot

sys.path.insert(0, os.path.dirname(__file__))

from src.polyglot_constants import POLYGLOT_RANDOM_ARRAY

# White Bishop on c1 (sq=2) should use piece_idx=5 (WB)
# Array index = piece * 64 + square = 5 * 64 + 2 = 322
idx = 5 * 64 + 2
print(f"White Bishop c1: index {idx}")
print(f"  Reference: 0x{chess.polyglot.POLYGLOT_RANDOM_ARRAY[idx]:016x}")
print(f"  Ours:      0x{POLYGLOT_RANDOM_ARRAY[idx]:016x}")
print()

# Check a few more
checks = [
    (1, 8, "White Pawn a2"),
    (3, 1, "White Knight b1"),
    (5, 2, "White Bishop c1"),
    (7, 0, "White Rook a1"),
    (9, 3, "White Queen d1"),
    (11, 4, "White King e1"),
]

print("Checking piece keys:")
for piece, square, name in checks:
    idx = piece * 64 + square
    ref = chess.polyglot.POLYGLOT_RANDOM_ARRAY[idx]
    ours = POLYGLOT_RANDOM_ARRAY[idx]
    match = "✓" if ref == ours else "✗"
    print(f"{match} {name:20s} idx={idx:3d}: ref=0x{ref:016x} ours=0x{ours:016x}")
