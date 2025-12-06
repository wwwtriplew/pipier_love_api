"""
Test illegal castling validation.
Verifies that execute_move validates rook existence BEFORE modifying board state.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chess_engine import ChessBoard
from zobrist_full import compute_full_hash


def test_illegal_castling_no_rook():
    """Test that castling without a rook is rejected WITHOUT corrupting board state."""
    
    print("=" * 80)
    print("Test: Illegal Castling Without Rook")
    print("=" * 80)
    
    # Setup: King on e8, no rooks, but castling rights set (invalid FEN)
    fen = "4k3/8/8/8/8/8/8/4K3 b KQkq - 0 1"
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    print(f"\nStarting FEN: {fen}")
    print(f"Castling rights: {board.castling_rights:04b} (should be 1111 = 15)")
    print(f"Black king position: e8 (square 60)")
    print(f"Black rooks: {bin(board.pieces[1][3])} (should be 0)")
    
    # Save initial state
    initial_king_bb = board.pieces[1][5]  # Black king
    initial_rook_bb = board.pieces[1][3]  # Black rooks
    initial_hash = board.zobrist_key
    initial_side = board.side_to_move
    
    print(f"\nInitial state:")
    print(f"  King bitboard: {bin(initial_king_bb)} (should have bit 60)")
    print(f"  Rook bitboard: {bin(initial_rook_bb)} (should be 0)")
    print(f"  Zobrist hash:  {initial_hash:016x}")
    print(f"  Side to move:  {'Black' if initial_side == 1 else 'White'}")
    
    # Try to castle kingside (e8 -> g8 = squares 60 -> 62)
    print(f"\n{'=' * 80}")
    print("Attempting illegal kingside castling: e8g8")
    print("Expected: execute_move returns False, board state unchanged")
    print("=" * 80)
    
    result = board.make_move(60, 62, None)
    
    # Check result
    final_king_bb = board.pieces[1][5]
    final_rook_bb = board.pieces[1][3]
    final_hash = board.zobrist_key
    final_side = board.side_to_move
    
    print(f"\nResult: {'FAILED (returned True)' if result else 'REJECTED (returned False)'}")
    print(f"\nFinal state:")
    print(f"  King bitboard: {bin(final_king_bb)}")
    print(f"  Rook bitboard: {bin(final_rook_bb)}")
    print(f"  Zobrist hash:  {final_hash:016x}")
    print(f"  Side to move:  {'Black' if final_side == 1 else 'White'}")
    
    # Verify board state is unchanged
    tests_passed = 0
    tests_total = 0
    
    print(f"\n{'=' * 80}")
    print("Board State Verification")
    print("=" * 80)
    
    tests_total += 1
    if result == False:
        print("✓ execute_move returned False (move rejected)")
        tests_passed += 1
    else:
        print("✗ execute_move returned True (SHOULD HAVE BEEN REJECTED!)")
    
    tests_total += 1
    if final_king_bb == initial_king_bb:
        print("✓ King bitboard unchanged")
        tests_passed += 1
    else:
        print(f"✗ King bitboard MODIFIED: {bin(initial_king_bb)} -> {bin(final_king_bb)}")
    
    tests_total += 1
    if final_rook_bb == initial_rook_bb:
        print("✓ Rook bitboard unchanged (still 0)")
        tests_passed += 1
    else:
        print(f"✗ Rook bitboard MODIFIED: {bin(initial_rook_bb)} -> {bin(final_rook_bb)}")
        if final_rook_bb != 0:
            print("  ⚠️  PHANTOM ROOK CREATED!")
    
    tests_total += 1
    if final_hash == initial_hash:
        print("✓ Zobrist hash unchanged")
        tests_passed += 1
    else:
        print(f"✗ Zobrist hash MODIFIED: {initial_hash:016x} -> {final_hash:016x}")
        print("  ⚠️  HASH MISMATCH - Board state corrupted!")
    
    tests_total += 1
    if final_side == initial_side:
        print("✓ Side to move unchanged")
        tests_passed += 1
    else:
        print(f"✗ Side to move CHANGED: {initial_side} -> {final_side}")
    
    # Verify hash matches board state
    tests_total += 1
    computed_hash = compute_full_hash(board)
    if computed_hash == final_hash:
        print("✓ Hash matches board state (consistent)")
        tests_passed += 1
    else:
        print(f"✗ Hash MISMATCH:")
        print(f"  Stored hash:   {final_hash:016x}")
        print(f"  Computed hash: {computed_hash:016x}")
        print("  ⚠️  CRITICAL BUG: Hash out of sync with board state!")
    
    print(f"\n{'=' * 80}")
    print(f"Result: {tests_passed}/{tests_total} tests passed")
    print("=" * 80)
    
    if tests_passed == tests_total:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("The fix is working correctly!")
        return True
    else:
        print(f"\n✗✗✗ {tests_total - tests_passed} TEST(S) FAILED ✗✗✗")
        print("Board state corruption detected!")
        return False


def test_legal_castling_with_rook():
    """Test that legal castling still works correctly."""
    
    print("\n\n" + "=" * 80)
    print("Test: Legal Castling With Rook")
    print("=" * 80)
    
    # Setup: Kings and rooks in place
    fen = "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"
    board = ChessBoard()
    board.setup_from_fen(fen)
    
    print(f"\nStarting FEN: {fen}")
    print(f"Black king: e8 (square 60)")
    print(f"Black rooks: a8 (56) and h8 (63)")
    
    # Save initial state
    initial_king_bb = board.pieces[1][5]
    initial_rook_bb = board.pieces[1][3]
    initial_hash = board.zobrist_key
    
    print(f"\nInitial state:")
    print(f"  King bitboard: {bin(initial_king_bb)}")
    print(f"  Rook bitboard: {bin(initial_rook_bb)}")
    print(f"  Zobrist hash:  {initial_hash:016x}")
    
    # Try legal kingside castling
    print(f"\n{'=' * 80}")
    print("Attempting LEGAL kingside castling: e8g8")
    print("Expected: execute_move returns True, board state updated correctly")
    print("=" * 80)
    
    result = board.make_move(60, 62, None)  # e8 -> g8
    
    final_king_bb = board.pieces[1][5]
    final_rook_bb = board.pieces[1][3]
    final_hash = board.zobrist_key
    final_side = board.side_to_move
    
    print(f"\nResult: {'ACCEPTED (returned True)' if result else 'REJECTED (returned False)'}")
    print(f"\nFinal state:")
    print(f"  King bitboard: {bin(final_king_bb)}")
    print(f"  Rook bitboard: {bin(final_rook_bb)}")
    print(f"  Zobrist hash:  {final_hash:016x}")
    print(f"  Side to move:  {'White' if final_side == 0 else 'Black'}")
    
    # Verify castling happened correctly
    tests_passed = 0
    tests_total = 0
    
    print(f"\n{'=' * 80}")
    print("Castling Verification")
    print("=" * 80)
    
    tests_total += 1
    if result == True:
        print("✓ execute_move returned True (move accepted)")
        tests_passed += 1
    else:
        print("✗ execute_move returned False (SHOULD HAVE BEEN ACCEPTED!)")
    
    tests_total += 1
    king_on_g8 = bool(final_king_bb & (1 << 62))  # g8 = square 62
    if king_on_g8:
        print("✓ King moved to g8")
        tests_passed += 1
    else:
        print(f"✗ King NOT on g8: {bin(final_king_bb)}")
    
    tests_total += 1
    rook_on_f8 = bool(final_rook_bb & (1 << 61))  # f8 = square 61
    if rook_on_f8:
        print("✓ Rook moved to f8")
        tests_passed += 1
    else:
        print(f"✗ Rook NOT on f8: {bin(final_rook_bb)}")
    
    tests_total += 1
    rook_not_on_h8 = not bool(final_rook_bb & (1 << 63))  # h8 = square 63
    if rook_not_on_h8:
        print("✓ Rook removed from h8")
        tests_passed += 1
    else:
        print(f"✗ Rook still on h8: {bin(final_rook_bb)}")
    
    tests_total += 1
    if final_side == 0:  # WHITE
        print("✓ Side to move changed to White")
        tests_passed += 1
    else:
        print(f"✗ Side to move is still Black")
    
    tests_total += 1
    if final_hash != initial_hash:
        print("✓ Zobrist hash updated")
        tests_passed += 1
    else:
        print("✗ Zobrist hash UNCHANGED (should have been updated)")
    
    # Verify hash matches board state
    tests_total += 1
    computed_hash = compute_full_hash(board)
    if computed_hash == final_hash:
        print("✓ Hash matches board state (consistent)")
        tests_passed += 1
    else:
        print(f"✗ Hash MISMATCH:")
        print(f"  Stored hash:   {final_hash:016x}")
        print(f"  Computed hash: {computed_hash:016x}")
    
    print(f"\n{'=' * 80}")
    print(f"Result: {tests_passed}/{tests_total} tests passed")
    print("=" * 80)
    
    if tests_passed == tests_total:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        return True
    else:
        print(f"\n✗✗✗ {tests_total - tests_passed} TEST(S) FAILED ✗✗✗")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ILLEGAL CASTLING VALIDATION TEST SUITE")
    print("=" * 80)
    print("\nThis test verifies that execute_move validates castling BEFORE")
    print("modifying board state, preventing board corruption.")
    print("\n" + "=" * 80)
    
    test1_passed = test_illegal_castling_no_rook()
    test2_passed = test_legal_castling_with_rook()
    
    print("\n\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if test1_passed and test2_passed:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("\nThe fix is working correctly:")
        print("  1. Illegal castling is rejected WITHOUT corrupting board state")
        print("  2. Legal castling still works correctly")
        print("  3. Zobrist hash remains consistent with board state")
        sys.exit(0)
    else:
        print("\n✗✗✗ SOME TESTS FAILED ✗✗✗")
        if not test1_passed:
            print("\n  Test 1 FAILED: Board corruption detected on illegal castling")
        if not test2_passed:
            print("\n  Test 2 FAILED: Legal castling not working correctly")
        sys.exit(1)
