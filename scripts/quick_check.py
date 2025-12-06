#!/usr/bin/env python3
"""Quick correctness check after fixing frozenset issue."""

import sys
import os
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb

def perft(board, depth):
    if depth == 0:
        return 1
    nodes = 0
    for from_sq, to_sq, promo in board.generate_moves():
        board.make_move(from_sq, to_sq, promo)
        king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])
        if not board.is_square_attacked(king_sq, board.side_to_move):
            nodes += perft(board, depth - 1)
        board.unmake_move()
    return nodes

board = ChessBoard()
expected = {0: 1, 1: 20, 2: 400, 3: 8902}

print("Quick correctness check:")
for depth in range(4):
    result = perft(board, depth)
    status = "✓" if result == expected[depth] else "✗"
    print(f"perft({depth}) = {result:>6} (expected {expected[depth]:>6}) {status}")
    if result != expected[depth]:
        print(f"\n✗✗✗ BROKEN! Do not deploy!")
        sys.exit(1)

print(f"\n✓ Correctness OK - safe to test on VPS")
