#!/usr/bin/env python3
"""
Diagnostic script to check opening book status.
Run this on VPS to see what's happening with the book.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.chess_engine import ChessBoard
from src.opening_book import get_default_book, probe_book

def main():
    print("=" * 60)
    print("OPENING BOOK DIAGNOSTIC")
    print("=" * 60)
    
    # Check book file existence
    print("\n1. Checking book file locations:")
    book_paths = [
        "openingbook/piperlove_black.bin",
        "openingbook/baron343/baron30.bin",
        "openingbook/baron343/book.bin",
        "openingbook/book.bin",
    ]
    
    for path in book_paths:
        exists = "✓" if os.path.exists(path) else "✗"
        size = os.path.getsize(path) if os.path.exists(path) else 0
        print(f"  {exists} {path:45s} ({size:,} bytes)")
    
    # Try to load book
    print("\n2. Loading default book:")
    book = get_default_book()
    if book:
        print(f"  ✓ Book loaded successfully")
        print(f"  ✓ Entries: {book.num_entries}")
    else:
        print(f"  ✗ Failed to load book")
        return
    
    # Test opening positions
    print("\n3. Testing book probes:")
    test_positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("After 1.d4", "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"),
        ("After 1.d4 Nc6", "r1bqkbnr/pppppppp/2n5/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 1 2"),
        ("After 1.d4 Nc6 2.Nf3", "r1bqkbnr/pppppppp/2n5/8/3P4/5N2/PPP1PPPP/RNBQKB1R b KQkq - 2 2"),
        ("After 1.d4 Nc6 2.Nf3 e6", "r1bqkbnr/pppp1ppp/2n1p3/8/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 0 3"),
    ]
    
    for name, fen in test_positions:
        board = ChessBoard()
        board.setup_from_fen(fen)
        
        move = probe_book(board, randomize=False)
        if move:
            from_sq, to_sq, promo = move
            # Convert to algebraic
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
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
