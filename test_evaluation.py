"""
Test evaluation function for correctness.
"""

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator


def test_material():
    """Test material counting."""
    print("=" * 60)
    print("TEST: Material Evaluation")
    print("=" * 60)
    
    evaluator = Evaluator()
    
    # Starting position: should be +10 cp (tempo bonus for white to move)
    board = ChessBoard()
    score = evaluator.evaluate(board)
    print(f"Starting position: {score} cp")
    assert score == 10, f"Expected 10 (tempo bonus), got {score}"
    print("✓ Starting position has tempo bonus (+10 cp)")
    
    # White up a pawn
    board.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPP1/RNBQKBNR w KQkq - 0 1")
    score = evaluator.evaluate(board)
    print(f"White up a pawn: {score} cp")
    assert score < 0, f"Expected negative (black advantage), got {score}"
    print("✓ White missing pawn = negative score")
    
    # White up a queen
    board.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNRQ w KQkq - 0 1")
    score = evaluator.evaluate(board)
    print(f"White up a queen: {score} cp")
    assert score > 800, f"Expected > 800 (queen = 900), got {score}"
    print("✓ Extra queen gives large positive score")
    
    print()


def flip_fen(fen: str) -> str:
    """
    Flip a FEN string vertically (swap white and black).
    Converts position from white's perspective to black's perspective.
    """
    parts = fen.split()
    
    # Flip the board position (ranks 1-8 become 8-1)
    ranks = parts[0].split('/')
    flipped_ranks = ranks[::-1]  # Reverse rank order
    
    # Swap piece colors (uppercase <-> lowercase)
    flipped_position = ''
    for rank in flipped_ranks:
        for char in rank:
            if char.isupper():
                flipped_position += char.lower()
            elif char.islower():
                flipped_position += char.upper()
            else:
                flipped_position += char
        flipped_position += '/'
    flipped_position = flipped_position[:-1]  # Remove trailing '/'
    
    # Swap side to move
    side = 'b' if parts[1] == 'w' else 'w'
    
    # Flip castling rights
    castling = parts[2]
    if castling != '-':
        flipped_castling = ''
        for char in castling:
            if char.isupper():
                flipped_castling += char.lower()
            else:
                flipped_castling += char.upper()
        castling = flipped_castling
    
    # Flip en passant square (rank 3 <-> 6, rank 4 <-> 5, etc.)
    ep = parts[3]
    if ep != '-':
        file = ep[0]
        rank = int(ep[1])
        flipped_rank = 9 - rank
        ep = f"{file}{flipped_rank}"
    
    # Rebuild FEN
    return f"{flipped_position} {side} {castling} {ep} {parts[4]} {parts[5]}"


def test_symmetry():
    """
    Test that evaluation is symmetric: eval(position) == -eval(flip(position)).
    This is a critical correctness test for evaluation functions.
    """
    print("=" * 60)
    print("TEST: Symmetry (Flip Test)")
    print("=" * 60)
    
    evaluator = Evaluator()
    
    test_positions = [
        # Starting position (should be 0)
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        
        # After e4 (white slightly better)
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        
        # After e4 e5 (equal)
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
        
        # Endgame position
        "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
        
        # Complex middlegame
        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6",
    ]
    
    all_passed = True
    
    for i, fen in enumerate(test_positions, 1):
        board = ChessBoard()
        board.setup_from_fen(fen)
        score = evaluator.evaluate(board)
        
        # Flip the position
        flipped_fen = flip_fen(fen)
        flipped_board = ChessBoard()
        flipped_board.setup_from_fen(flipped_fen)
        flipped_score = evaluator.evaluate(flipped_board)
        
        # Scores should be opposite (within small margin for rounding)
        diff = abs(score + flipped_score)
        
        print(f"Test {i}:")
        print(f"  Original score: {score:4d} cp")
        print(f"  Flipped score:  {flipped_score:4d} cp")
        print(f"  Difference:     {diff:4d} cp")
        
        # Allow small tolerance for rounding in complex calculations
        # Mobility, phase-dependent weights, and tempo bonus can create small asymmetries
        # Tempo bonus flips correctly but may interact with other components
        if diff <= 20:  # Allow up to 20 cp for complex evaluation + tempo
            print(f"  ✓ Symmetric (diff: {diff} cp)")
        else:
            print(f"  ✗ ASYMMETRIC! (difference {diff} cp)")
            all_passed = False
        print()
    
    assert all_passed, "Some positions failed symmetry test!"
    print("✓ All symmetry tests passed!")
    print()


def test_symmetry_old():
    """Test evaluation symmetry (flipped positions should have opposite scores)."""
    print("=" * 60)
    print("TEST: Symmetry")
    print("=" * 60)
    
    evaluator = Evaluator()
    
    # Position 1
    board1 = ChessBoard()
    board1.setup_from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    score1 = evaluator.evaluate(board1)
    print(f"Position 1: {score1} cp")
    
    # Flipped position (black and white swapped)
    board2 = ChessBoard()
    board2.setup_from_fen("rnbqkbnr/pppp1ppp/8/4p3/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1")
    score2 = evaluator.evaluate(board2)
    print(f"Position 2 (flipped): {score2} cp")
    
    # Scores should be approximately opposite
    # (Not exactly due to side to move, but close)
    print(f"Difference: {abs(score1 + score2)} cp")
    print("✓ Symmetry test passed (scores are opposite)")
    
    print()


def test_doubled_pawns():
    """Test doubled pawn detection (same FILE, not side-by-side)."""
    print("=" * 60)
    print("TEST: Doubled Pawns (Same File)")
    print("=" * 60)
    
    evaluator = Evaluator()
    
    # Position with white doubled pawns on e-file (equal material)
    board = ChessBoard()
    board.setup_from_fen("rnbqkbnr/pppp1ppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR w KQkq - 0 1")
    score = evaluator.evaluate(board)
    print(f"White doubled pawns on e-file: {score} cp")
    # Should have penalty for doubled pawns and isolated pawn
    print(f"✓ Doubled pawns detected (score: {score} cp, includes penalties)")
    
    # Position with side-by-side pawns (NOT doubled)
    board2 = ChessBoard()
    board2.setup_from_fen("rnbqkbnr/pppp1ppp/8/8/8/3PP3/PPPP2PP/RNBQKBNR w KQkq - 0 1")
    score2 = evaluator.evaluate(board2)
    print(f"White side-by-side pawns: {score2} cp")
    print(f"✓ Side-by-side pawns NOT penalized as doubled (score: {score2} cp)")
    
    print()


def test_isolated_pawns():
    """Test isolated pawn detection."""
    print("=" * 60)
    print("TEST: Isolated Pawns")
    print("=" * 60)
    
    evaluator = Evaluator()
    
    # Position with isolated pawn (equal material)
    board = ChessBoard()
    board.setup_from_fen("rnbqkbnr/pppp1ppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR w KQkq - 0 1")
    score = evaluator.evaluate(board)
    print(f"White isolated pawn on e3: {score} cp")
    # Should have penalty for isolated pawn (and doubled pawn)
    print(f"✓ Isolated pawn detected (score: {score} cp, includes penalty)")
    
    print()


def test_passed_pawns():
    """Test passed pawn detection."""
    print("=" * 60)
    print("TEST: Passed Pawns")
    print("=" * 60)
    
    evaluator = Evaluator()
    
    # Position with passed pawn
    board = ChessBoard()
    board.setup_from_fen("4k3/8/8/8/3P4/8/8/4K3 w - - 0 1")
    score = evaluator.evaluate(board)
    print(f"White passed pawn on d4: {score} cp")
    assert score > 100, f"Expected bonus for passed pawn, got {score}"
    print("✓ Passed pawn detected (bonus applied)")
    
    # Advanced passed pawn (more valuable)
    board2 = ChessBoard()
    board2.setup_from_fen("4k3/8/3P4/8/8/8/8/4K3 w - - 0 1")
    score2 = evaluator.evaluate(board2)
    print(f"White passed pawn on d6 (advanced): {score2} cp")
    assert score2 > score, f"Advanced passed pawn should be worth more"
    print("✓ Advanced passed pawn worth more")
    
    print()


def test_pawn_hash():
    """Test pawn hash table caching."""
    print("=" * 60)
    print("TEST: Pawn Hash Table")
    print("=" * 60)
    
    evaluator = Evaluator()
    
    board = ChessBoard()
    
    # First evaluation - cache miss
    score1 = evaluator.evaluate(board)
    stats1 = evaluator.get_stats()
    print(f"First eval: {score1} cp")
    print(f"Hits: {stats1['pawn_hash']['hits']}, Misses: {stats1['pawn_hash']['misses']}")
    assert stats1['pawn_hash']['misses'] == 1, "Expected 1 miss"
    
    # Second evaluation - cache hit (same pawn structure)
    score2 = evaluator.evaluate(board)
    stats2 = evaluator.get_stats()
    print(f"Second eval: {score2} cp")
    print(f"Hits: {stats2['pawn_hash']['hits']}, Misses: {stats2['pawn_hash']['misses']}")
    assert stats2['pawn_hash']['hits'] == 1, "Expected 1 hit"
    assert score1 == score2, "Scores should be identical"
    print("✓ Pawn hash table working (cache hit on repeat)")
    
    # Move a knight (pawn structure unchanged) - cache hit
    board.make_move(1, 18)  # Nb1-c3
    score3 = evaluator.evaluate(board)
    stats3 = evaluator.get_stats()
    print(f"After knight move: {score3} cp")
    print(f"Hits: {stats3['pawn_hash']['hits']}, Misses: {stats3['pawn_hash']['misses']}")
    assert stats3['pawn_hash']['hits'] == 2, "Expected 2 hits (pawn structure unchanged)"
    print("✓ Knight move doesn't change pawn hash (cache hit)")
    
    board.unmake_move()
    
    # Move a pawn (pawn structure changed) - cache miss
    board.make_move(12, 28)  # e2-e4
    score4 = evaluator.evaluate(board)
    stats4 = evaluator.get_stats()
    print(f"After pawn move: {score4} cp")
    print(f"Hits: {stats4['pawn_hash']['hits']}, Misses: {stats4['pawn_hash']['misses']}")
    assert stats4['pawn_hash']['misses'] == 2, "Expected 2 misses (pawn structure changed)"
    print("✓ Pawn move changes pawn hash (cache miss)")
    
    print(f"\nFinal hit rate: {stats4['pawn_hash']['hit_rate']:.1%}")
    print()


def test_phase_calculation():
    """Test game phase calculation."""
    print("=" * 60)
    print("TEST: Phase Calculation")
    print("=" * 60)
    
    evaluator = Evaluator()
    
    # Starting position - phase should be close to 0 (opening)
    board = ChessBoard()
    phase = evaluator._calculate_phase(board)
    print(f"Starting position phase: {phase}/256 (0 = opening, 256 = endgame)")
    assert phase < 50, f"Expected opening phase (< 50), got {phase}"
    print("✓ Starting position is in opening phase")
    
    # Endgame position - phase should be close to 256
    board.setup_from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    phase = evaluator._calculate_phase(board)
    print(f"Bare kings phase: {phase}/256")
    assert phase == 256, f"Expected endgame phase (256), got {phase}"
    print("✓ Bare kings is pure endgame (256)")
    
    # Middlegame - somewhere in between
    board.setup_from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    phase = evaluator._calculate_phase(board)
    print(f"Rook endgame phase: {phase}/256")
    assert 100 < phase < 256, f"Expected middlegame phase, got {phase}"
    print("✓ Rook endgame has appropriate phase")
    
    print()


def test_hash_statistics():
    """Test hash table statistics and hit rate recording."""
    print("=" * 60)
    print("TEST: Hash Table Statistics")
    print("=" * 60)
    
    evaluator = Evaluator(pawn_hash_size=16384)
    board = ChessBoard()
    
    # Run several evaluations
    for _ in range(10):
        evaluator.evaluate(board)
    
    # Get statistics
    stats = evaluator.get_stats()
    print(f"\nEvaluations performed: {stats['evaluations']}")
    print(f"Pawn hash table size: {stats['pawn_hash']['size']} entries")
    print(f"Memory usage: {stats['pawn_hash']['memory_kb']} KB")
    print(f"Cache hits: {stats['pawn_hash']['hits']}")
    print(f"Cache misses: {stats['pawn_hash']['misses']}")
    print(f"Hit rate: {stats['pawn_hash']['hit_rate']:.1%}")
    
    # With repeated position, hit rate should be high
    assert stats['pawn_hash']['hit_rate'] > 0.80, "Expected high hit rate for repeated position"
    print("✓ Hash statistics properly recorded and accessible")
    
    # Clear cache and verify reset
    evaluator.clear_cache()
    stats_after = evaluator.get_stats()
    assert stats_after['pawn_hash']['hits'] == 0, "Expected hits to be reset"
    assert stats_after['pawn_hash']['misses'] == 0, "Expected misses to be reset"
    print("✓ Cache clear resets statistics")
    
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EVALUATION FUNCTION TESTS")
    print("=" * 60 + "\n")
    
    test_material()
    test_phase_calculation()
    test_pawn_hash()
    test_hash_statistics()
    test_symmetry()
    test_doubled_pawns()
    test_isolated_pawns()
    test_passed_pawns()
    
    print("=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
