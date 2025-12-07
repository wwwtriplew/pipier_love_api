#!/usr/bin/env python3
"""Extract reference Polyglot random array from python-chess."""

import chess.polyglot

print("First 20 python-chess Polyglot random values:")
for i in range(20):
    print(f"{i:3d}: 0x{chess.polyglot.POLYGLOT_RANDOM_ARRAY[i]:016x}")

print("\nLast 20 python-chess Polyglot random values:")
total = len(chess.polyglot.POLYGLOT_RANDOM_ARRAY)
for i in range(total - 20, total):
    print(f"{i:3d}: 0x{chess.polyglot.POLYGLOT_RANDOM_ARRAY[i]:016x}")

print(f"\nTotal array size: {total}")
