"""
Test the illegal castling move bug fix.

This script tests the fixes for the critical bug where the engine
was generating illegal castling moves (e8g8, e8c8) when no rooks existed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chess_engine import ChessBoard
from search import move_to_uci

def test_no_castling_without_rooks():
    """Test that castling moves are not generated when rooks don't exist."""
    print("=" * 70)
    print("TEST 1: No castling without rooks")
    print("=" * 70)
    
    # Position from user's game (where bug occurred)
    fen = "8/2P3k1/8/P7/3n4/8/8/4K3 b KQkq - 0 61"
    print(f"\nFEN: {fen}")
    print(f"Position: No rooks on board, but castling rights = KQkq (invalid!)")
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    moves = board.generate_moves()
    
    print(f"\nGenerated {len(moves)} legal moves:")
    for move in moves:
        from_sq, to_sq, promo = move
        from_file = chr(ord('a') + from_sq % 8)
        from_rank = from_sq // 8 + 1
        to_file = chr(ord('a') + to_sq % 8)
        to_rank = to_sq // 8 + 1
        promo_str = {4: 'q', 3: 'r', 2: 'b', 1: 'n'}.get(promo, '')
        
        move_str = f"{from_file}{from_rank}{to_file}{to_rank}{promo_str}"
        print(f"  {move_str}")
    
    # Check for illegal castling moves
    castling_moves = []
    for move in moves:
        from_sq, to_sq = move[0], move[1]
        # Castling moves have king moving 2 squares
        if abs(to_sq - from_sq) == 2:
            # Verify it's a king move (from e-file)
            if from_sq % 8 == 4:  # e-file
                castling_moves.append(move)
    
    print(f"\n❌ BEFORE FIX: Would have included e8g8 (60→62) and e8c8 (60→58)")
    print(f"✅ AFTER FIX: Found {len(castling_moves)} castling moves (expected: 0)")
    
    if len(castling_moves) == 0:
        print("✅ PASS: No illegal castling moves generated!")
        return True
    else:
        print("❌ FAIL: Still generating illegal castling moves:")
        for move in castling_moves:
            print(f"  {move_to_uci(move)}")
        return False

def test_valid_castling_with_rooks():
    """Test that valid castling still works when rooks exist."""
    print("\n" + "=" * 70)
    print("TEST 2: Valid castling with rooks")
    print("=" * 70)
    
    # Test White to move
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    print(f"\nFEN: {fen}")
    print(f"Position: All 4 rooks present, White to move")
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    moves = board.generate_moves()
    
    # Find White's castling moves
    castling_moves = []
    for move in moves:
        from_sq, to_sq = move[0], move[1]
        if abs(to_sq - from_sq) == 2 and from_sq % 8 == 4:
            castling_moves.append(move)
    
    print(f"\nWhite's castling moves: {len(castling_moves)}")
    for move in castling_moves:
        print(f"  {move_to_uci(move)}")
    
    white_pass = len(castling_moves) == 2
    if white_pass:
        print("✅ White can castle both ways (e1g1, e1c1)")
    else:
        print(f"❌ Expected 2 White castling moves, found {len(castling_moves)}")
    
    # Test Black to move
    fen = "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"
    print(f"\nFEN: {fen}")
    print(f"Position: All 4 rooks present, Black to move")
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    moves = board.generate_moves()
    
    # Find Black's castling moves
    castling_moves = []
    for move in moves:
        from_sq, to_sq = move[0], move[1]
        if abs(to_sq - from_sq) == 2 and from_sq % 8 == 4:
            castling_moves.append(move)
    
    print(f"\nBlack's castling moves: {len(castling_moves)}")
    for move in castling_moves:
        print(f"  {move_to_uci(move)}")
    
    black_pass = len(castling_moves) == 2
    if black_pass:
        print("✅ Black can castle both ways (e8g8, e8c8)")
    else:
        print(f"❌ Expected 2 Black castling moves, found {len(castling_moves)}")
    
    if white_pass and black_pass:
        print("\n✅ PASS: Valid castling works for both sides!")
        return True
    else:
        print("\n❌ FAIL: Castling validation broken")
        return False

def test_partial_castling_rights():
    """Test castling when only some rooks exist - THE CRITICAL TEST."""
    print("\n" + "=" * 70)
    print("TEST 3: Partial castling rights (CRITICAL BUG TEST)")
    print("=" * 70)
    
    # Black has only kingside rook, but FEN says it has queenside rights
    fen = "4k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"
    print(f"\nFEN: {fen}")
    print(f"Position: Black king on e8, Black rook ONLY on h8")
    print(f"Castling rights: KQkq (includes 'q' for Black queenside)")
    print(f"❌ BEFORE FIX: Would generate e8c8 (no rook on a8!)")
    print(f"✅ AFTER FIX: Should only generate e8g8 (rook on h8)")
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    moves = board.generate_moves()
    
    castling_moves = []
    for move in moves:
        from_sq, to_sq = move[0], move[1]
        if abs(to_sq - from_sq) == 2 and from_sq % 8 == 4:
            castling_moves.append(move)
    
    print(f"\nBlack's castling moves: {len(castling_moves)}")
    for move in castling_moves:
        print(f"  {move_to_uci(move)}")
    
    found_uci = [move_to_uci(m) for m in castling_moves]
    has_illegal_e8c8 = 'e8c8' in found_uci
    has_legal_e8g8 = 'e8g8' in found_uci
    
    if len(castling_moves) == 1 and has_legal_e8g8 and not has_illegal_e8c8:
        print(f"✅ PASS: Only e8g8 generated, no illegal e8c8!")
        return True
    else:
        print(f"❌ FAIL: Expected 1 move (e8g8), found {len(castling_moves)}")
        if has_illegal_e8c8:
            print(f"  ⚠️  CRITICAL: Illegal move e8c8 generated (no rook on a8)!")
        if not has_legal_e8g8:
            print(f"  ⚠️  Missing legal move e8g8 (rook exists on h8)!")
        return False

def test_kings_only():
    """Test position with only kings (extreme case)."""
    print("\n" + "=" * 70)
    print("TEST 4: Kings only (extreme case)")
    print("=" * 70)
    
    fen = "4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1"
    print(f"\nFEN: {fen}")
    print(f"Position: Only kings, but FEN claims castling rights = KQkq")
    
    board = ChessBoard()
    board.setup_from_fen(fen)
    moves = board.generate_moves()
    
    castling_moves = []
    for move in moves:
        from_sq, to_sq = move[0], move[1]
        if abs(to_sq - from_sq) == 2 and from_sq % 8 == 4:
            castling_moves.append(move)
    
    print(f"\nGenerated {len(moves)} total moves")
    print(f"Castling moves: {len(castling_moves)} (expected: 0)")
    
    if len(castling_moves) == 0:
        print("✅ PASS: No castling with kings only!")
        return True
    else:
        print("❌ FAIL: Still generating castling moves without rooks:")
        for move in castling_moves:
            print(f"  {move_to_uci(move)}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ILLEGAL CASTLING MOVE BUG - REGRESSION TESTS")
    print("=" * 70)
    
    results = []
    
    results.append(("No castling without rooks", test_no_castling_without_rooks()))
    results.append(("Valid castling with rooks", test_valid_castling_with_rooks()))
    results.append(("Partial castling rights", test_partial_castling_rights()))
    results.append(("Kings only", test_kings_only()))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Bug is fixed!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! Bug still present!")
        sys.exit(1)
