#!/usr/bin/env python3
"""
Final safety verification before committing changes.
Tests:
1. All imports work correctly
2. Helper functions produce correct results
3. Move generation is accurate (perft validation)
4. No performance regression
"""

import sys
import time

def test_imports():
    """Test all imports work correctly."""
    print("=" * 60)
    print("TEST 1: Import Verification")
    print("=" * 60)
    
    try:
        from src.chess_engine import ChessBoard, pop_lsb, get_lsb, count_bits
        print("✓ chess_engine imports OK")
    except Exception as e:
        print(f"✗ chess_engine import FAILED: {e}")
        return False
    
    try:
        from src.move_generation import (
            is_promotion_square_lookup,
            can_double_push,
            get_pawn_single_push,
            get_pawn_double_push,
            get_bit
        )
        print("✓ move_generation imports OK")
    except Exception as e:
        print(f"✗ move_generation import FAILED: {e}")
        return False
    
    try:
        from src.magic_bitboards import pop_lsb, get_lsb, count_bits
        print("✓ magic_bitboards imports OK")
    except Exception as e:
        print(f"✗ magic_bitboards import FAILED: {e}")
        return False
    
    # Test they actually work
    test_bb = 0x0000000000000001
    sq, remaining = pop_lsb(test_bb)
    assert sq == 0, f"pop_lsb failed: expected 0, got {sq}"
    print("✓ pop_lsb works")
    
    sq = get_lsb(test_bb)
    assert sq == 0, f"get_lsb failed: expected 0, got {sq}"
    print("✓ get_lsb works")
    
    bits = count_bits(0x00FF)
    assert bits == 8, f"count_bits failed: expected 8, got {bits}"
    print("✓ count_bits works")
    
    return True


def test_helpers():
    """Test helper functions are correct."""
    print("\n" + "=" * 60)
    print("TEST 2: Helper Function Correctness")
    print("=" * 60)
    
    from src.move_generation import (
        is_promotion_square_lookup,
        can_double_push,
        get_pawn_single_push,
        get_pawn_double_push,
        get_bit
    )
    
    # Test promotion squares
    assert is_promotion_square_lookup(56, 0) == True, "White a8 should be promotion"
    assert is_promotion_square_lookup(0, 1) == True, "Black a1 should be promotion"
    assert is_promotion_square_lookup(8, 0) == False, "a2 should not be promotion"
    print("✓ is_promotion_square_lookup correct")
    
    # Test double push
    assert can_double_push(8, 0) == True, "White a2 can double push"
    assert can_double_push(48, 1) == True, "Black a7 can double push"
    assert can_double_push(16, 0) == False, "a3 cannot double push"
    print("✓ can_double_push correct")
    
    # Test single push
    assert get_pawn_single_push(8, 0) == 16, "White a2→a3"
    assert get_pawn_single_push(48, 1) == 40, "Black a7→a6"
    assert get_pawn_single_push(56, 0) == -1, "Cannot push from a8"
    print("✓ get_pawn_single_push correct")
    
    # Test double push
    assert get_pawn_double_push(8, 0) == 24, "White a2→a4"
    assert get_pawn_double_push(48, 1) == 32, "Black a7→a5"
    assert get_pawn_double_push(16, 0) == -1, "Cannot double push from a3"
    print("✓ get_pawn_double_push correct")
    
    # Test get_bit
    assert get_bit(0) == 1, "get_bit(0) = 1"
    assert get_bit(1) == 2, "get_bit(1) = 2"
    assert get_bit(7) == 128, "get_bit(7) = 128"
    print("✓ get_bit correct")
    
    return True


def test_perft():
    """Test move generation accuracy with perft."""
    print("\n" + "=" * 60)
    print("TEST 3: Move Generation Accuracy (Perft)")
    print("=" * 60)
    
    from src.chess_engine import ChessBoard
    from src.magic_bitboards import get_lsb
    
    board = ChessBoard()
    
    def perft(b, d):
        if d == 0:
            return 1
        n = 0
        for f, t, p in b.generate_moves():
            b.make_move(f, t, p)
            k = get_lsb(b.pieces[1 - b.side_to_move][5])
            if not b.is_square_attacked(k, b.side_to_move):
                n += perft(b, d - 1)
            b.unmake_move()
        return n
    
    # Known correct perft values
    expected = {
        0: 1,
        1: 20,
        2: 400,
        3: 8902,
        4: 197281,
    }
    
    for depth in range(4):  # Test up to depth 3
        result = perft(board, depth)
        if result != expected[depth]:
            print(f"✗ perft({depth}): expected {expected[depth]}, got {result}")
            return False
        print(f"✓ perft({depth}) = {result:,}")
    
    return True


def test_performance():
    """Test there's no performance regression."""
    print("\n" + "=" * 60)
    print("TEST 4: Performance Check")
    print("=" * 60)
    
    from src.chess_engine import ChessBoard
    from src.magic_bitboards import get_lsb
    
    board = ChessBoard()
    
    def perft(b, d):
        if d == 0:
            return 1
        n = 0
        for f, t, p in b.generate_moves():
            b.make_move(f, t, p)
            k = get_lsb(b.pieces[1 - b.side_to_move][5])
            if not b.is_square_attacked(k, b.side_to_move):
                n += perft(b, d - 1)
            b.unmake_move()
        return n
    
    # Warmup
    print("Warming up...")
    for _ in range(100):
        perft(board, 2)
    
    # Test
    print("Testing performance...")
    start = time.time()
    nodes = perft(board, 3)
    elapsed = time.time() - start
    nps = int(nodes / elapsed)
    
    print(f"NPS: {nps:,}")
    print(f"Time: {elapsed*1000:.1f}ms")
    
    # We should get at least 10k NPS even cold
    if nps < 10000:
        print(f"✗ Performance too slow: {nps:,} NPS (expected >10k)")
        return False
    
    print(f"✓ Performance acceptable: {nps:,} NPS")
    return True


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "FINAL SAFETY VERIFICATION" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    all_passed = True
    
    if not test_imports():
        print("\n✗✗✗ IMPORT TEST FAILED - DO NOT COMMIT ✗✗✗")
        all_passed = False
    
    if not test_helpers():
        print("\n✗✗✗ HELPER TEST FAILED - DO NOT COMMIT ✗✗✗")
        all_passed = False
    
    if not test_perft():
        print("\n✗✗✗ PERFT TEST FAILED - DO NOT COMMIT ✗✗✗")
        all_passed = False
    
    if not test_performance():
        print("\n✗✗✗ PERFORMANCE TEST FAILED - DO NOT COMMIT ✗✗✗")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓✓✓ ALL TESTS PASSED - SAFE TO COMMIT ✓✓✓")
        print("=" * 60)
        return 0
    else:
        print("✗✗✗ SOME TESTS FAILED - DO NOT COMMIT ✗✗✗")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
