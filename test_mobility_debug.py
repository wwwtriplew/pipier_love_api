"""
Debug mobility evaluation symmetry issue.
"""

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator


def test_mobility_components():
    """Test individual mobility components for symmetry."""
    evaluator = Evaluator()
    
    # Test position that fails symmetry in test (position 3)
    fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
    
    # Also test the flip
    from test_evaluation import flip_fen
    flipped_fen = flip_fen(fen)
    print("Original FEN:", fen)
    print("Flipped FEN: ", flipped_fen)
    print()
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    # Calculate mobility for both sides
    WHITE = 0
    BLACK = 1
    
    mg_white, eg_white = evaluator._evaluate_mobility_side(board, WHITE)
    mg_black, eg_black = evaluator._evaluate_mobility_side(board, BLACK)
    
    print("White mobility (raw):", mg_white, eg_white)
    print("Black mobility (raw):", mg_black, eg_black)
    print("Difference:", mg_white - mg_black, eg_white - eg_black)
    print("After /10:", (mg_white - mg_black) // 10, (eg_white - eg_black) // 10)
    print()
    
    # Test if position is truly symmetric by checking a mirrored position
    print("\n=== Testing truly symmetric position (no ep square) ===")
    sym_fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    board2 = ChessBoard()
    board2.setup_from_fen(sym_fen)
    
    mg_white2, eg_white2 = evaluator._evaluate_mobility_side(board2, WHITE)
    mg_black2, eg_black2 = evaluator._evaluate_mobility_side(board2, BLACK)
    
    print("White mobility (raw):", mg_white2, eg_white2)
    print("Black mobility (raw):", mg_black2, eg_black2)
    print("Difference:", mg_white2 - mg_black2, eg_white2 - eg_black2)
    print("After /10:", (mg_white2 - mg_black2) // 10, (eg_white2 - eg_black2) // 10)
    
    if mg_white2 == mg_black2:
        print("✓ Mobility is symmetric when ep square is removed!")
    else:
        print("✗ Still asymmetric even without ep square")
    
    # Now test the flipped position
    print("\n=== Testing flipped position ===")
    board_flip = ChessBoard()
    board_flip.setup_from_fen(flipped_fen)
    
    mg_white_flip, eg_white_flip = evaluator._evaluate_mobility_side(board_flip, WHITE)
    mg_black_flip, eg_black_flip = evaluator._evaluate_mobility_side(board_flip, BLACK)
    
    print("Flipped - White mobility (raw):", mg_white_flip, eg_white_flip)
    print("Flipped - Black mobility (raw):", mg_black_flip, eg_black_flip)
    print("Flipped - Difference:", mg_white_flip - mg_black_flip, eg_white_flip - eg_black_flip)
    print("Flipped - After /10:", (mg_white_flip - mg_black_flip) // 10, (eg_white_flip - eg_black_flip) // 10)
    
    # For symmetry, we expect:
    # Original: (w_mob - b_mob) / 10 = -2
    # Flipped:  (w_mob - b_mob) / 10 should be  +2 (negation)
    
    original_score = (mg_white - mg_black) // 10
    flipped_score = (mg_white_flip - mg_black_flip) // 10
    
    print(f"\nOriginal score: {original_score}")
    print(f"Flipped score: {flipped_score}")
    print(f"Sum (should be ~0): {original_score + flipped_score}")
    
    if abs(original_score + flipped_score) <= 1:
        print("✓ Symmetry preserved!")
    else:
        print("✗ Symmetry broken!")


if __name__ == "__main__":
    test_mobility_components()
