#!/usr/bin/env python3
"""Debug why baron book can't find Caro-Kann Advance position."""

import sys
import os
import chess
import chess.polyglot

sys.path.insert(0, os.path.dirname(__file__))

from src.chess_engine import ChessBoard
from src.opening_book import PolyglotZobrist

# Test the position step by step
print("Building position step-by-step:")
print("=" * 60)

moves = ["e2e4", "c7c6", "d2d4", "d7d5", "e4e5"]
board = ChessBoard()
ref_board = chess.Board()

for i, move_uci in enumerate(moves):
    if i > 0:  # Skip initial position
        # Make move on our board
        from_sq = ord(move_uci[0]) - ord('a') + (int(move_uci[1]) - 1) * 8
        to_sq = ord(move_uci[2]) - ord('a') + (int(move_uci[3]) - 1) * 8
        promo = None
        board.make_move(from_sq, to_sq, promo)
        
        # Make move on reference board
        ref_board.push_uci(move_uci)
    
    print(f"\nAfter move {i}: {' '.join(moves[:i]) if i > 0 else 'starting position'}")
    print(f"Our FEN:       {board.to_fen()}")
    print(f"Reference FEN: {ref_board.fen()}")
    
    our_hash = PolyglotZobrist.compute_hash(board)
    ref_hash = chess.polyglot.zobrist_hash(ref_board)
    
    print(f"Our hash:      {our_hash:016x}")
    print(f"Ref hash:      {ref_hash:016x}")
    
    if our_hash != ref_hash:
        print("✗ HASH MISMATCH!")
        print(f"XOR diff:      {(our_hash ^ ref_hash):016x}")
        break
    else:
        print("✓ Hashes match")

print("\n" + "=" * 60)
print("Checking if issue is with FEN parsing vs incremental updates:")
print("=" * 60)

# Try loading directly from FEN
final_fen = "rnbqkbnr/pp2pppp/2p5/3pP3/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3"
board_from_fen = ChessBoard()
board_from_fen.setup_from_fen(final_fen)

ref_from_fen = chess.Board(final_fen)

our_hash_fen = PolyglotZobrist.compute_hash(board_from_fen)
ref_hash_fen = chess.polyglot.zobrist_hash(ref_from_fen)

print(f"\nLoading from FEN: {final_fen}")
print(f"Our hash:  {our_hash_fen:016x}")
print(f"Ref hash:  {ref_hash_fen:016x}")

if our_hash_fen == ref_hash_fen:
    print("✓ FEN parsing produces correct hash")
else:
    print("✗ FEN parsing has wrong hash!")
