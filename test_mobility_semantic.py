"""
Comprehensive semantic bug tests for mobility evaluation.
"""

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator


def test_truly_symmetric_position():
    """Test mobility in a perfectly symmetric position."""
    print("=" * 70)
    print("TEST: Perfectly Symmetric Position")
    print("=" * 70)
    
    evaluator = Evaluator()
    WHITE = 0
    BLACK = 1
    
    # After e4 e5 - perfectly symmetric position
    fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    # Get mobility for each side
    mg_white, eg_white = evaluator._evaluate_mobility_side(board, WHITE)
    mg_black, eg_black = evaluator._evaluate_mobility_side(board, BLACK)
    
    print(f"Position: {fen}")
    print(f"White mobility (raw): {mg_white}")
    print(f"Black mobility (raw): {mg_black}")
    print(f"Difference: {mg_white - mg_black}")
    print()
    
    # In a symmetric position, mobility should be very close
    diff = abs(mg_white - mg_black)
    
    if diff == 0:
        print("✓ Perfect symmetry!")
    elif diff <= 20:  # Allow small difference (before division by 10, so ~2 cp)
        print(f"✓ Near-symmetric (diff: {diff} raw, ~{diff//10} cp)")
    else:
        print(f"✗ Asymmetric! (diff: {diff} raw, ~{diff//10} cp)")
        print("  Investigating...")
        
        # Check attack maps
        all_pieces = board.white_pieces | board.black_pieces
        white_attacks = evaluator._generate_attack_map(board, WHITE, all_pieces)
        black_attacks = evaluator._generate_attack_map(board, BLACK, all_pieces)
        
        def popcount(bb):
            count = 0
            while bb:
                count += 1
                bb &= bb - 1
            return count
        
        print(f"  White attacks: {popcount(white_attacks)} squares")
        print(f"  Black attacks: {popcount(black_attacks)} squares")
        
        # Check safe squares
        white_safe = ~all_pieces & ~black_attacks
        black_safe = ~all_pieces & ~white_attacks
        print(f"  White safe squares: {popcount(white_safe)}")
        print(f"  Black safe squares: {popcount(black_safe)}")


def test_empty_board_mobility():
    """Test mobility on empty board (should be perfectly symmetric)."""
    print("=" * 70)
    print("TEST: Empty Board Mobility")
    print("=" * 70)
    
    evaluator = Evaluator()
    WHITE = 0
    BLACK = 1
    
    # Just kings
    fen = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    mg_white, eg_white = evaluator._evaluate_mobility_side(board, WHITE)
    mg_black, eg_black = evaluator._evaluate_mobility_side(board, BLACK)
    
    print(f"Position: {fen}")
    print(f"White mobility: {mg_white}")
    print(f"Black mobility: {mg_black}")
    print(f"Difference: {mg_white - mg_black}")
    
    if mg_white == mg_black:
        print("✓ Perfect symmetry on empty board!")
    else:
        print(f"✗ Asymmetric even on empty board (diff: {mg_white - mg_black})")
    print()


def test_single_piece_mobility():
    """Test mobility of single piece types."""
    print("=" * 70)
    print("TEST: Single Piece Mobility")
    print("=" * 70)
    
    evaluator = Evaluator()
    WHITE = 0
    BLACK = 1
    
    # Test each piece type individually
    test_cases = [
        ("4k3/8/8/8/3N4/8/8/4K3 w - - 0 1", "Knight on d4"),
        ("4k3/8/8/8/3B4/8/8/4K3 w - - 0 1", "Bishop on d4"),
        ("4k3/8/8/8/3R4/8/8/4K3 w - - 0 1", "Rook on d4"),
        ("4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1", "Queen on d4"),
    ]
    
    for fen, desc in test_cases:
        board = ChessBoard()
        board.setup_from_fen(fen)
        
        mg_white, eg_white = evaluator._evaluate_mobility_side(board, WHITE)
        mg_black, eg_black = evaluator._evaluate_mobility_side(board, BLACK)
        
        print(f"{desc}:")
        print(f"  White mobility: {mg_white} (has the piece)")
        print(f"  Black mobility: {mg_black} (no pieces)")
        
        # White should have more mobility (has a piece)
        if mg_white > mg_black:
            print(f"  ✓ Correct (white has more mobility)")
        else:
            print(f"  ✗ BUG! Black has more or equal mobility")
        print()


def test_piece_blocking():
    """Test that blocked pieces have less mobility."""
    print("=" * 70)
    print("TEST: Blocked Pieces")
    print("=" * 70)
    
    evaluator = Evaluator()
    WHITE = 0
    
    # Bishop blocked vs. open
    fen_blocked = "4k3/pppppppp/8/8/8/8/PPPPPPPP/B3K3 w - - 0 1"
    fen_open = "4k3/pppppppp/8/8/8/8/8/B3K3 w - - 0 1"
    
    board_blocked = ChessBoard()
    board_blocked.setup_from_fen(fen_blocked)
    
    board_open = ChessBoard()
    board_open.setup_from_fen(fen_open)
    
    mg_blocked, _ = evaluator._evaluate_mobility_side(board_blocked, WHITE)
    mg_open, _ = evaluator._evaluate_mobility_side(board_open, WHITE)
    
    print("Bishop blocked by pawns:")
    print(f"  Blocked: {mg_blocked} mobility")
    print(f"  Open: {mg_open} mobility")
    
    if mg_open > mg_blocked:
        print(f"  ✓ Open bishop has more mobility (diff: {mg_open - mg_blocked})")
    else:
        print(f"  ✗ BUG! Blocked bishop has equal or more mobility")
    print()


def test_attacked_squares_excluded():
    """Test that attacked squares don't count toward mobility."""
    print("=" * 70)
    print("TEST: Attacked Squares Excluded")
    print("=" * 70)
    
    evaluator = Evaluator()
    WHITE = 0
    BLACK = 1
    
    # Knight surrounded by enemy pawns
    fen = "4k3/8/8/2ppp3/2pNp3/2ppp3/8/4K3 w - - 0 1"
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    # Generate attack map manually to verify
    all_pieces = board.white_pieces | board.black_pieces
    black_attacks = evaluator._generate_attack_map(board, BLACK, all_pieces)
    
    # Knight on d4 can reach 8 squares: c2, e2, b3, f3, b5, f5, c6, e6
    # But all are occupied by black pawns OR attacked by them
    
    mg_white, _ = evaluator._evaluate_mobility_side(board, WHITE)
    
    print(f"Knight surrounded by enemy pawns:")
    print(f"  White mobility: {mg_white}")
    print(f"  (Should be very low - knight has no safe squares)")
    
    # Since all squares are occupied or attacked, mobility should be minimal
    # (Only king has some mobility)
    if mg_white < 100:  # Arbitrary small threshold
        print(f"  ✓ Low mobility as expected")
    else:
        print(f"  ⚠ Mobility seems high for surrounded knight")
    print()


if __name__ == "__main__":
    test_truly_symmetric_position()
    test_empty_board_mobility()
    test_single_piece_mobility()
    test_piece_blocking()
    test_attacked_squares_excluded()
    
    print("=" * 70)
    print("MOBILITY SEMANTIC TESTS COMPLETE")
    print("=" * 70)
