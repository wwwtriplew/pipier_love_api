#!/usr/bin/env python3
"""Check baron30.bin book status."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.opening_book import OpeningBook
from src.chess_engine import ChessBoard

# Load baron book
baron_path = "openingbook/baron343/baron30.bin"
print(f"Loading {baron_path}...")

if not os.path.exists(baron_path):
    print(f"ERROR: File not found!")
    sys.exit(1)

size = os.path.getsize(baron_path)
expected_entries = size // 16
print(f"File size: {size:,} bytes")
print(f"Expected entries: {expected_entries:,}")

baron_book = OpeningBook(baron_path)

if not baron_book.is_loaded():
    print("ERROR: Failed to load book!")
    sys.exit(1)

print(f"Actual entries loaded: {len(baron_book.entries):,}")
print()

# Test some standard opening positions
test_positions = [
    ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("After 1.e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"),
    ("After 1.e4 c5", "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
    ("After 1.e4 c5 2.Nf3", "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"),
    ("After 1.d4", "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"),
    ("After 1.d4 d5", "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2"),
    ("After 1.d4 Nf6", "rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 1 2"),
    ("After 1.d4 Nf6 2.c4", "rnbqkb1r/pppppppp/5n2/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2"),
]

print("Testing baron book probes:")
for name, fen in test_positions:
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    move = baron_book.probe(board, randomize=False)
    if move:
        from_sq, to_sq, promo = move
        from_file = from_sq % 8
        from_rank = from_sq // 8
        to_file = to_sq % 8
        to_rank = to_sq // 8
        move_str = f"{chr(ord('a') + from_file)}{from_rank + 1}{chr(ord('a') + to_file)}{to_rank + 1}"
        if promo:
            promo_chars = {1: 'n', 2: 'b', 3: 'r', 4: 'q'}
            move_str += promo_chars.get(promo, '')
        print(f"  ✓ {name:30s} → {move_str}")
    else:
        print(f"  ✗ {name:30s} → (not in book)")
