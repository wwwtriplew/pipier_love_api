#!/usr/bin/env python3
"""Test if PGN parser extracts the Advance Caro-Kann line correctly."""

import chess.pgn
from io import StringIO

pgn_text = """
[Event "Test"]
[Site "Test"]
[Date "2025.12.06"]
[Round "2"]
[White "Various"]
[Black "Caro-Kann Advance"]
[Result "*"]

1. e4 c6 2. d4 d5 3. e5 (3. exd5 cxd5 4. c4 Nf6) 3... c5 4. dxc5 *
"""

print("Testing PGN parsing:")
print("=" * 60)

pgn = StringIO(pgn_text)
game = chess.pgn.read_game(pgn)

if not game:
    print("ERROR: Failed to parse PGN")
else:
    print("✓ PGN parsed successfully")
    
    # Walk through main line
    board = chess.Board()
    node = game
    move_num = 1
    
    print("\nMain line moves:")
    while node.variations:
        next_node = node.variation(0)  # Main variation
        if next_node.move:
            board.push(next_node.move)
            if board.turn == chess.WHITE:
                print(f"{move_num}...{board.san(next_node.move)}")
                move_num += 1
            else:
                print(f"{move_num}.{board.san(next_node.move)}", end=" ")
        node = next_node
    
    print("\n\nFinal position FEN:")
    print(board.fen())
    
    # Check if we reached the position after 3...c5
    expected_fen = "rnbqkbnr/pp2pppp/2p5/2ppP3/3P4/8/PPP2PPP/RNBQKBNR w KQkq c6 0 4"
    if board.fen().split()[0:4] == expected_fen.split()[0:4]:
        print("✓ Correctly parsed to position after 3...c5")
    else:
        print("✗ Did NOT reach position after 3...c5")
        print(f"Expected: {expected_fen}")
        print(f"Got:      {board.fen()}")
