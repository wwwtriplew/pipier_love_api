#!/usr/bin/env python3
"""
Test to compare Polyglot hashes between our implementation and python-chess.
"""

import sys
import os
import chess
import chess.polyglot

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.chess_engine import ChessBoard
from src.opening_book import PolyglotZobrist

def test_position(fen: str, description: str):
    """Compare hashes for a position."""
    print(f"\n{description}")
    print(f"FEN: {fen}")
    
    # python-chess hash (reference)
    chess_board = chess.Board(fen)
    reference_hash = chess.polyglot.zobrist_hash(chess_board)
    print(f"  python-chess hash: {reference_hash:016x}")
    
    # Our implementation hash
    our_board = ChessBoard()
    our_board.setup_from_fen(fen)
    our_hash = PolyglotZobrist.compute_hash(our_board)
    print(f"  Our hash:          {our_hash:016x}")
    
    if reference_hash == our_hash:
        print(f"  ✓ MATCH")
        return True
    else:
        print(f"  ✗ MISMATCH")
        print(f"  XOR diff:          {(reference_hash ^ our_hash):016x}")
        return False

def main():
    print("=" * 60)
    print("POLYGLOT HASH COMPARISON TEST")
    print("=" * 60)
    
    test_positions = [
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "Starting position"),
        ("rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1", "After 1.d4"),
        ("r1bqkbnr/pppppppp/2n5/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 1 2", "After 1.d4 Nc6"),
        ("r1bqkbnr/pppppppp/2n5/8/3P4/5N2/PPP1PPPP/RNBQKB1R b KQkq - 2 2", "After 1.d4 Nc6 2.Nf3"),
        ("r1bqkbnr/pppp1ppp/2n1p3/8/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 0 3", "After 1.d4 Nc6 2.Nf3 e6"),
    ]
    
    matches = 0
    for fen, desc in test_positions:
        if test_position(fen, desc):
            matches += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {matches}/{len(test_positions)} positions match")
    print("=" * 60)
    
    if matches == len(test_positions):
        print("✓ All hashes match - implementation is correct!")
    else:
        print("✗ Hash mismatch detected - need to fix implementation")

if __name__ == "__main__":
    main()
