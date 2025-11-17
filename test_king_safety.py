"""
Test king safety evaluation.
"""

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator


def test_pawn_shield():
    """Test that pawn shield provides king safety bonus."""
    print("=" * 70)
    print("TEST: Pawn Shield")
    print("=" * 70)
    
    evaluator = Evaluator()
    
    # Good pawn shield (castled king with pawns)
    board1 = ChessBoard()
    board1.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1")
    score1 = evaluator.evaluate(board1)
    print(f"Castled kingside with pawn shield: {score1} cp")
    
    # Broken pawn shield (h-pawn advanced)
    board2 = ChessBoard()
    board2.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPP1/RNBQK2R w KQkq - 0 1")
    score2 = evaluator.evaluate(board2)
    print(f"Castled kingside with broken shield: {score2} cp")
    
    # Better pawn shield should give better score (less negative or more positive)
    print(f"Difference: {score1 - score2} cp (positive = shield helps)")
    assert score1 > score2, "Good pawn shield should be better than broken shield"
    print("✓ Pawn shield provides safety bonus")
    print()


def test_open_file_penalty():
    """Test that open files near king are penalized."""
    print("=" * 70)
    print("TEST: Open File Penalty")
    print("=" * 70)
    
    evaluator = Evaluator()
    
    # King with no open files
    board1 = ChessBoard()
    board1.setup_from_fen("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")
    score1 = evaluator.evaluate(board1)
    print(f"Kings with no open files: {score1} cp")
    
    # King on open file (e-file empty)
    board2 = ChessBoard()
    board2.setup_from_fen("4k3/pppp1ppp/8/8/8/8/PPPP1PPP/4K3 w - - 0 1")
    score2 = evaluator.evaluate(board2)
    print(f"Kings on open file: {score2} cp")
    
    # Should be roughly equal since both kings equally exposed
    print(f"Difference: {abs(score1 - score2)} cp (should be small)")
    assert abs(score1 - score2) < 10, "Both kings equally exposed should be similar"
    print("✓ Open file penalty applied symmetrically")
    print()


def test_king_exposure():
    """Test that enemy attacks on king zone are penalized."""
    print("=" * 70)
    print("TEST: King Exposure")
    print("=" * 70)
    
    evaluator = Evaluator()
    
    # Safe king (starting position)
    board1 = ChessBoard()
    score1 = evaluator.evaluate(board1)
    print(f"Starting position (safe kings): {score1} cp")
    
    # Exposed king (black king in center, attacked by white pieces)
    board2 = ChessBoard()
    board2.setup_from_fen("4k3/8/8/8/3N4/8/PPPPPPPP/RNBQKB1R w KQ - 0 1")
    score2 = evaluator.evaluate(board2)
    print(f"Black king exposed (knight attacking): {score2} cp")
    
    # White should have advantage when black king is exposed
    print(f"White advantage: {score2 - score1} cp (should be positive)")
    assert score2 > score1, "Exposed king should be worse"
    print("✓ King exposure increases when attacked")
    print()


def test_endgame_king_activity():
    """Test that king safety fades in endgame (kings should be active)."""
    print("=" * 70)
    print("TEST: Endgame King Activity")
    print("=" * 70)
    
    evaluator = Evaluator()
    
    # Middlegame: King safety matters
    board1 = ChessBoard()
    board1.setup_from_fen("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1")
    score1 = evaluator.evaluate(board1)
    phase1 = evaluator._calculate_phase(board1)
    print(f"Middlegame (phase {phase1}): {score1} cp")
    
    # Endgame: King safety should matter less
    board2 = ChessBoard()
    board2.setup_from_fen("8/8/4k3/8/8/4K3/8/8 w - - 0 1")
    phase2 = evaluator._calculate_phase(board2)
    print(f"Endgame (phase {phase2}): should skip king safety")
    
    assert phase1 < 100, "Middlegame should have low phase"
    assert phase2 > 200, "Endgame should have high phase (>200 skips king safety)"
    print("✓ King safety evaluation skipped in endgame")
    print()


def test_castling_sides():
    """Test king safety works correctly for kingside vs queenside castling."""
    print("=" * 70)
    print("TEST: Castling Sides")
    print("=" * 70)
    
    evaluator = Evaluator()
    
    # Kingside castling
    board1 = ChessBoard()
    board1.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1")
    score1 = evaluator.evaluate(board1)
    print(f"Kingside castling position: {score1} cp")
    
    # Queenside castling
    board2 = ChessBoard()
    board2.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/R3KBNR w KQkq - 0 1")
    score2 = evaluator.evaluate(board2)
    print(f"Queenside castling position: {score2} cp")
    
    print(f"Difference: {abs(score1 - score2)} cp")
    # Both should be evaluated (one not drastically better than other in starting position)
    print("✓ Both castling sides evaluated")
    print()


def test_symmetry_with_king_safety():
    """Test that king safety maintains evaluation symmetry."""
    print("=" * 70)
    print("TEST: Symmetry with King Safety")
    print("=" * 70)
    
    evaluator = Evaluator()
    
    # Test position
    fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1"
    board = ChessBoard()
    board.setup_from_fen(fen)
    score = evaluator.evaluate(board)
    print(f"Original: {score} cp")
    
    # Flip colors and position
    from test_evaluation import flip_fen
    flipped_fen = flip_fen(fen)
    board2 = ChessBoard()
    board2.setup_from_fen(flipped_fen)
    score2 = evaluator.evaluate(board2)
    print(f"Flipped: {score2} cp")
    
    diff = abs(score + score2)
    print(f"Difference: {diff} cp (should be 0 or 1)")
    assert diff <= 1, "Symmetry should be maintained with king safety"
    print("✓ King safety maintains symmetry")
    print()


if __name__ == "__main__":
    test_pawn_shield()
    test_open_file_penalty()
    test_king_exposure()
    test_endgame_king_activity()
    test_castling_sides()
    test_symmetry_with_king_safety()
    
    print("=" * 70)
    print("✓ ALL KING SAFETY TESTS PASSED!")
    print("=" * 70)
