#!/usr/bin/env python3
"""Test move generation for the exact FEN from user's bug report"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chess_engine import ChessBoard
from search import move_to_uci

# The exact FEN from the bug report
fen = "8/2P3k1/8/P7/3n4/8/8/4K3 b KQkq - 0 61"
print(f"FEN: {fen}")
print("Black to move, no rooks on board, but castling rights = KQkq\n")

board = ChessBoard()
board.setup_from_fen(fen)

moves = board.generate_moves()
print(f"Generated {len(moves)} legal moves:\n")

for i, move in enumerate(moves, 1):
    from_sq, to_sq, promo = move
    uci = move_to_uci(move)
    print(f"{i:2d}. {uci}")
    
    # Check if this is the illegal e8g8 or e8c8
    if uci == 'e8g8':
        print(f"    ⚠️  ILLEGAL: Black kingside castling without rook on h8!")
    elif uci == 'e8c8':
        print(f"    ⚠️  ILLEGAL: Black queenside castling without rook on a8!")

# Check specifically for e8g8 and e8c8
illegal_moves = [m for m in moves if move_to_uci(m) in ['e8g8', 'e8c8']]
if illegal_moves:
    print(f"\n❌ FOUND {len(illegal_moves)} ILLEGAL CASTLING MOVES!")
    for m in illegal_moves:
        print(f"   {move_to_uci(m)}")
else:
    print(f"\n✅ No illegal castling moves generated - FIX IS WORKING!")
