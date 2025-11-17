"""
Test mobility on a perfectly symmetric empty position.
"""

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator


def test_empty_board_mobility():
    """Test mobility on a nearly empty symmetric position."""
    evaluator = Evaluator()
    WHITE = 0
    BLACK = 1
    
    # Just kings and one knight each, perfectly symmetric
    fen = "4k3/8/8/8/8/8/8/4K1N1 w - - 0 1"
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    mg_white, eg_white = evaluator._evaluate_mobility_side(board, WHITE)
    mg_black, eg_black = evaluator._evaluate_mobility_side(board, BLACK)
    
    print("Position:", fen)
    print("White mobility (raw):", mg_white, eg_white)
    print("Black mobility (raw):", mg_black, eg_black)
    print("Difference:", mg_white - mg_black)
    print()
    
    # Now test the mirror
    fen2 = "4k1n1/8/8/8/8/8/8/4K3 w - - 0 1"
    board2 = ChessBoard()
    board2.setup_from_fen(fen2)
    
    mg_white2, eg_white2 = evaluator._evaluate_mobility_side(board2, WHITE)
    mg_black2, eg_black2 = evaluator._evaluate_mobility_side(board2, BLACK)
    
    print("Mirror position:", fen2)
    print("White mobility (raw):", mg_white2, eg_white2)
    print("Black mobility (raw):", mg_black2, eg_black2)
    print("Difference:", mg_white2 - mg_black2)
    print()
    
    # In mirror, white knight becomes black knight
    # So white mobility in original should equal black mobility in mirror
    if mg_white == mg_black2 and mg_black == mg_white2:
        print("✓ Perfect symmetry!")
    else:
        print("✗ Asymmetry detected")
        print(f"  White (orig) vs Black (mirror): {mg_white} vs {mg_white2} (diff: {mg_white - mg_white2})")
        print(f"  Black (orig) vs White (mirror): {mg_black} vs {mg_black2} (diff: {mg_black - mg_black2})")


if __name__ == "__main__":
    test_empty_board_mobility()
