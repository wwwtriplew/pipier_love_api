#!/usr/bin/env python3
"""Check specific position for c5 move."""

import sys
import os
import chess.polyglot

sys.path.insert(0, os.path.dirname(__file__))

from src.chess_engine import ChessBoard
from src.opening_book import OpeningBook, PolyglotZobrist, get_book_chain

# The position after 1.e4 c6 2.d4 d5 3.e5
test_fen = "rnbqkbnr/pp2pppp/2p5/3pP3/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3"

print("Testing position: 1.e4 c6 2.d4 d5 3.e5")
print(f"FEN: {test_fen}")
print("=" * 60)

# Create our board
board = ChessBoard()
board.setup_from_fen(test_fen)

# Compute hash
our_hash = PolyglotZobrist.compute_hash(board)
print(f"\nOur Polyglot hash: {our_hash:016x}")

# Get reference hash
ref_board = chess.Board(test_fen)
ref_hash = chess.polyglot.zobrist_hash(ref_board)
print(f"Reference hash:    {ref_hash:016x}")

if our_hash == ref_hash:
    print("✓ Hashes match!")
else:
    print("✗ Hash mismatch!")
    sys.exit(1)

print("\n" + "=" * 60)
print("Checking books:")
print("=" * 60)

# Check custom book
custom_book = OpeningBook("openingbook/piperlove_black.bin")
if custom_book.is_loaded():
    print(f"\n1. Custom book (piperlove_black.bin): {len(custom_book.entries)} entries")
    
    # Search for this position in book
    found = False
    for book_hash, book_move, weight in custom_book.entries:
        if book_hash == our_hash:
            found = True
            # Decode move
            to_sq = book_move & 0x3F
            from_sq = (book_move >> 6) & 0x3F
            promo = (book_move >> 12) & 0x7
            
            from_file = from_sq % 8
            from_rank = from_sq // 8
            to_file = to_sq % 8
            to_rank = to_sq // 8
            move_str = f"{chr(ord('a') + from_file)}{from_rank + 1}{chr(ord('a') + to_file)}{to_rank + 1}"
            
            print(f"  ✓ Found move: {move_str} (weight={weight})")
    
    if not found:
        print(f"  ✗ Position NOT in custom book!")
        print(f"  Expected to find hash: {our_hash:016x}")

# Check baron book
baron_book = OpeningBook("openingbook/baron343/baron30.bin")
if baron_book.is_loaded():
    print(f"\n2. Baron book (baron30.bin): {len(baron_book.entries)} entries")
    
    found = False
    for book_hash, book_move, weight in baron_book.entries:
        if book_hash == our_hash:
            found = True
            to_sq = book_move & 0x3F
            from_sq = (book_move >> 6) & 0x3F
            promo = (book_move >> 12) & 0x7
            
            from_file = from_sq % 8
            from_rank = from_sq // 8
            to_file = to_sq % 8
            to_rank = to_sq // 8
            move_str = f"{chr(ord('a') + from_file)}{from_rank + 1}{chr(ord('a') + to_file)}{to_rank + 1}"
            
            print(f"  ✓ Found move: {move_str} (weight={weight})")
    
    if not found:
        print(f"  ✗ Position NOT in baron book either!")

# Test probe_book function
print("\n" + "=" * 60)
print("Testing probe_book() function:")
print("=" * 60)

from src.opening_book import probe_book

move = probe_book(board, randomize=False)
if move:
    from_sq, to_sq, promo = move
    from_file = from_sq % 8
    from_rank = from_sq // 8
    to_file = to_sq % 8
    to_rank = to_sq // 8
    move_str = f"{chr(ord('a') + from_file)}{from_rank + 1}{chr(ord('a') + to_file)}{to_rank + 1}"
    print(f"✓ probe_book() returned: {move_str}")
else:
    print(f"✗ probe_book() returned None!")

print("\n" + "=" * 60)
