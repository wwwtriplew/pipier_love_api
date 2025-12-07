#!/usr/bin/env python3
"""Search baron book for ANY Caro-Kann positions."""

import sys
import os
import chess
import chess.polyglot

sys.path.insert(0, os.path.dirname(__file__))

from src.chess_engine import ChessBoard
from src.opening_book import OpeningBook, PolyglotZobrist

print("Checking baron book for Caro-Kann positions:")
print("=" * 60)

baron_book = OpeningBook("openingbook/baron343/baron30.bin")
print(f"Baron book loaded: {len(baron_book.entries)} entries\n")

# Test several Caro-Kann positions
test_positions = [
    ("1.e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"),
    ("1.e4 c6", "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
    ("1.e4 c6 2.d4", "rnbqkbnr/pp1ppppp/2p5/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2"),
    ("1.e4 c6 2.d4 d5", "rnbqkbnr/pp2pppp/2p5/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3"),
    ("1.e4 c6 2.d4 d5 3.e5", "rnbqkbnr/pp2pppp/2p5/3pP3/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3"),
    ("1.e4 c6 2.d4 d5 3.exd5", "rnbqkbnr/pp2pppp/2p5/8/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3"),
    ("1.e4 c6 2.d4 d5 3.Nc3", "rnbqkbnr/pp2pppp/2p5/3p4/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 1 3"),
]

for desc, fen in test_positions:
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    our_hash = PolyglotZobrist.compute_hash(board)
    
    # Search in baron book
    found = False
    for book_hash, book_move, weight in baron_book.entries:
        if book_hash == our_hash:
            found = True
            break
    
    status = "✓" if found else "✗"
    print(f"{status} {desc:30s} hash={our_hash:016x} {'IN BOOK' if found else 'NOT in book'}")

print("\n" + "=" * 60)
print("If starting position (1.e4) is in book but 1.e4 c6 is not,")
print("then baron book might not have Caro-Kann at all.")
print("If 1.e4 c6 is in book but 3.e5 is not, then it lacks this line.")
