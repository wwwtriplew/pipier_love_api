"""
Test incremental pawn hash updates to verify cache efficiency.
"""

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator


def test_pawn_hash_preservation():
    """Test that pawn hash is preserved when non-pawn pieces move."""
    print("=" * 70)
    print("INCREMENTAL PAWN HASH TEST")
    print("=" * 70)
    print()
    
    board = ChessBoard()
    evaluator = Evaluator()
    
    # Get initial pawn hash and evaluation
    initial_pawn_hash = board.pawn_hash
    score1 = evaluator.evaluate(board)
    print(f"Starting position:")
    print(f"  Pawn hash: {initial_pawn_hash}")
    print(f"  Score: {score1} cp")
    print(f"  Cache stats: {evaluator.pawn_hash_table.hits} hits, {evaluator.pawn_hash_table.misses} misses")
    print()
    
    # Make a knight move (no pawn change)
    print("Making knight move: Nf3 (no pawn change)")
    board.make_move(62, 45)  # g1 to f3
    
    pawn_hash_after_knight = board.pawn_hash
    score2 = evaluator.evaluate(board)
    
    print(f"  Pawn hash: {pawn_hash_after_knight}")
    print(f"  Score: {score2} cp")
    print(f"  Cache stats: {evaluator.pawn_hash_table.hits} hits, {evaluator.pawn_hash_table.misses} misses")
    
    if pawn_hash_after_knight == initial_pawn_hash:
        print(f"  ✓ Pawn hash PRESERVED (cache hit expected)")
    else:
        print(f"  ✗ Pawn hash CHANGED (cache miss - BAD!)")
        print(f"    Expected: {initial_pawn_hash}")
        print(f"    Got: {pawn_hash_after_knight}")
    print()
    
    # Make another non-pawn move
    print("Black moves knight: Nc6 (no pawn change)")
    board.make_move(57, 42)  # b8 to c6
    
    pawn_hash_after_knight2 = board.pawn_hash
    score3 = evaluator.evaluate(board)
    
    print(f"  Pawn hash: {pawn_hash_after_knight2}")
    print(f"  Score: {score3} cp")
    print(f"  Cache stats: {evaluator.pawn_hash_table.hits} hits, {evaluator.pawn_hash_table.misses} misses")
    
    if pawn_hash_after_knight2 == initial_pawn_hash:
        print(f"  ✓ Pawn hash PRESERVED (cache hit expected)")
    else:
        print(f"  ✗ Pawn hash CHANGED (cache miss - BAD!)")
    print()
    
    # Now make a pawn move
    print("Making pawn move: e4 (pawn changes)")
    board.make_move(12, 28)  # e2 to e4
    
    pawn_hash_after_pawn_move = board.pawn_hash
    score4 = evaluator.evaluate(board)
    
    print(f"  Pawn hash: {pawn_hash_after_pawn_move}")
    print(f"  Score: {score4} cp")
    print(f"  Cache stats: {evaluator.pawn_hash_table.hits} hits, {evaluator.pawn_hash_table.misses} misses")
    
    if pawn_hash_after_pawn_move != initial_pawn_hash:
        print(f"  ✓ Pawn hash CHANGED (cache miss expected)")
    else:
        print(f"  ✗ Pawn hash UNCHANGED (should have changed!)")
    print()
    
    # Make another non-pawn move - should use new hash
    print("White moves knight: Nf3 (no pawn change from previous position)")
    board.make_move(61, 45)  # g1 to f3
    
    pawn_hash_after_another_knight = board.pawn_hash
    score5 = evaluator.evaluate(board)
    
    print(f"  Pawn hash: {pawn_hash_after_another_knight}")
    print(f"  Score: {score5} cp")
    print(f"  Cache stats: {evaluator.pawn_hash_table.hits} hits, {evaluator.pawn_hash_table.misses} misses")
    
    if pawn_hash_after_another_knight == pawn_hash_after_pawn_move:
        print(f"  ✓ Pawn hash PRESERVED after pawn move (cache hit expected)")
    else:
        print(f"  ✗ Pawn hash CHANGED (cache miss - BAD!)")
    print()
    
    # Final summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    stats = evaluator.get_stats()
    print(f"Total evaluations: {stats['evaluations']}")
    print(f"Cache hits: {stats['pawn_hash']['hits']}")
    print(f"Cache misses: {stats['pawn_hash']['misses']}")
    print(f"Hit rate: {stats['pawn_hash']['hit_rate']:.1%}")
    print()
    
    expected_misses = 2  # Initial eval + after pawn move
    expected_hits = stats['evaluations'] - expected_misses
    
    if stats['pawn_hash']['misses'] == expected_misses:
        print(f"✓ Cache working optimally!")
        print(f"  - {expected_misses} misses (expected: initial + pawn move)")
        print(f"  - {expected_hits} hits (all non-pawn moves)")
    else:
        print(f"✗ Cache not optimal")
        print(f"  - Expected {expected_misses} misses, got {stats['pawn_hash']['misses']}")
    print()
    
    # Verify incremental correctness by recomputing from bitboards
    print("=" * 70)
    print("CORRECTNESS CHECK")
    print("=" * 70)
    
    # Recompute hash from current bitboards
    from src.zobrist_keys import compute_pawn_hash
    recomputed_hash = compute_pawn_hash(board.white_pawns, board.black_pawns)
    
    print(f"Incremental hash: {board.pawn_hash}")
    print(f"Recomputed hash:  {recomputed_hash}")
    
    if board.pawn_hash == recomputed_hash:
        print("✓ Incremental updates are CORRECT!")
        print("  Hash matches recomputed value from current bitboards")
    else:
        print("✗ Incremental updates are WRONG!")
        print("  This is a critical bug - hash doesn't match recomputed value")
    print()


if __name__ == "__main__":
    test_pawn_hash_preservation()
