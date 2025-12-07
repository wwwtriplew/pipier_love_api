#!/usr/bin/env python3
"""Check what moves baron book has for the Caro-Kann Advance position."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.chess_engine import ChessBoard
from src.opening_book import OpeningBook

# Position after 1.e4 c6 2.d4 d5 3.e5
test_fen = "rnbqkbnr/pp2pppp/2p5/3pP3/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3"

print("Checking Caro-Kann Advance: 1.e4 c6 2.d4 d5 3.e5")
print(f"FEN: {test_fen}")
print("=" * 60)

board = ChessBoard()
board.setup_from_fen(test_fen)

# Check baron book
baron_book = OpeningBook("openingbook/baron343/baron30.bin")

if not baron_book.is_loaded():
    print("ERROR: Baron book failed to load")
    sys.exit(1)

print(f"\nBaron book has {len(baron_book.entries)} entries")

# Find ALL moves for this position in baron book
from src.opening_book import PolyglotZobrist
our_hash = PolyglotZobrist.compute_hash(board)

print(f"Position hash: {our_hash:016x}")
print("\nAll moves in baron book for this position:")

found_moves = []
for book_hash, book_move, weight in baron_book.entries:
    if book_hash == our_hash:
        # Decode move
        to_sq = book_move & 0x3F
        from_sq = (book_move >> 6) & 0x3F
        promo = (book_move >> 12) & 0x7
        
        from_file = from_sq % 8
        from_rank = from_sq // 8
        to_file = to_sq % 8
        to_rank = to_sq // 8
        move_str = f"{chr(ord('a') + from_file)}{from_rank + 1}{chr(ord('a') + to_file)}{to_rank + 1}"
        
        found_moves.append((move_str, weight))

if found_moves:
    # Sort by weight (highest first)
    found_moves.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Found {len(found_moves)} move(s):")
    for move, weight in found_moves:
        print(f"  {move:6s} weight={weight:4d}")
    
    if any(move.startswith('c7c5') or move.startswith('c5') for move, _ in found_moves):
        print("\n✓ c5 is in baron book!")
    else:
        print("\n✗ c5 NOT in baron book")
        print("Most popular move:", found_moves[0][0])
else:
    print("✗ Position NOT in baron book at all!")
    print("\nThis means baron30.bin doesn't have theory for this line.")
