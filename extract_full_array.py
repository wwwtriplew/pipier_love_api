#!/usr/bin/env python3
"""Extract complete Polyglot random array from python-chess."""

import chess.polyglot

print("# Complete Polyglot random array from python-chess reference implementation")
print("# 781 values: 768 for pieces (12 pieces * 64 squares)")
print("#             + 4 for castling rights")
print("#             + 8 for en passant files")
print("#             + 1 for side to move")
print()
print("POLYGLOT_RANDOM_ARRAY = [")

for i in range(len(chess.polyglot.POLYGLOT_RANDOM_ARRAY)):
    val = chess.polyglot.POLYGLOT_RANDOM_ARRAY[i]
    print(f"    0x{val:016x},  # {i}")

print("]")
