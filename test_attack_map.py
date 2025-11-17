"""
Debug attack map generation for symmetry.
"""

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator


def count_bits(bb):
    """Count set bits in a bitboard."""
    count = 0
    while bb:
        count += 1
        bb &= bb - 1
    return count


def test_attack_symmetry():
    """Test if attack maps are symmetric."""
    evaluator = Evaluator()
    WHITE = 0
    BLACK = 1
    
    # Symmetric position
    fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    all_pieces = board.white_pieces | board.black_pieces
    
    # Generate attack maps
    white_attacks = evaluator._generate_attack_map(board, WHITE, all_pieces)
    black_attacks = evaluator._generate_attack_map(board, BLACK, all_pieces)
    
    print("White attacks:", count_bits(white_attacks), "squares")
    print("Black attacks:", count_bits(black_attacks), "squares")
    print()
    
    # Generate safe squares for each side
    white_safe = ~all_pieces & ~black_attacks
    black_safe = ~all_pieces & ~white_attacks
    
    print("White safe squares:", count_bits(white_safe))
    print("Black safe squares:", count_bits(black_safe))
    print()
    
    # If position is symmetric, attack counts should be equal
    if count_bits(white_attacks) == count_bits(black_attacks):
        print("✓ Attack maps have same size")
    else:
        print("✗ Attack maps differ!")
        print(f"  Difference: {abs(count_bits(white_attacks) - count_bits(black_attacks))} squares")
    
    if count_bits(white_safe) == count_bits(black_safe):
        print("✓ Safe squares are symmetric")
    else:
        print("✗ Safe squares differ!")
        print(f"  Difference: {abs(count_bits(white_safe) - count_bits(black_safe))} squares")


if __name__ == "__main__":
    test_attack_symmetry()
