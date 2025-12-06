#!/usr/bin/env python3
"""
Comprehensive Pre-Commit Safety Test
Tests correctness, performance, and PyPy sanity before deployment.
"""

import sys
import time
import os

# Add src to path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)


def check_pypy():
    """Check if running under PyPy and report version."""
    print("=" * 80)
    print("ENVIRONMENT CHECK")
    print("=" * 80)
    
    try:
        import __pypy__  # type: ignore[import-not-found]
        pypy_version = sys.version
        print(f"✓ Running under PyPy")
        print(f"  Version: {pypy_version}")
        
        # Check JIT availability
        if hasattr(__pypy__, 'jit_enabled'):
            jit = __pypy__.jit_enabled()
            print(f"  JIT: {'Enabled' if jit else 'Disabled'}")
        else:
            print(f"  JIT: Status unknown (jit_enabled() not available)")
        
        return True
    except ImportError:
        print(f"✓ Running under CPython")
        print(f"  Version: {sys.version}")
        return False


def test_imports():
    """Test all critical imports."""
    print("\n" + "=" * 80)
    print("IMPORT TEST")
    print("=" * 80)
    
    errors = []
    
    try:
        from src.chess_engine import ChessBoard, pop_lsb, get_lsb, count_bits
        print("✓ chess_engine imports OK")
    except Exception as e:
        errors.append(f"chess_engine: {e}")
        print(f"✗ chess_engine import FAILED: {e}")
    
    try:
        from src.magic_bitboards import pop_lsb, get_lsb, count_bits
        print("✓ magic_bitboards imports OK")
    except Exception as e:
        errors.append(f"magic_bitboards: {e}")
        print(f"✗ magic_bitboards import FAILED: {e}")
    
    try:
        from src.move_generation import (
            is_promotion_square_lookup,
            can_double_push,
            get_pawn_single_push,
            get_pawn_double_push,
            get_bit
        )
        print("✓ move_generation helpers import OK")
    except Exception as e:
        errors.append(f"move_generation: {e}")
        print(f"✗ move_generation import FAILED: {e}")
    
    if errors:
        print(f"\n✗✗✗ IMPORT FAILURES - DO NOT COMMIT ✗✗✗")
        return False
    
    return True


def test_bitboard_ops():
    """Test bitboard operations are correct."""
    print("\n" + "=" * 80)
    print("BITBOARD OPERATIONS TEST")
    print("=" * 80)
    
    from src.magic_bitboards import pop_lsb, get_lsb, count_bits
    
    errors = []
    
    # Test pop_lsb
    test_bb = 0x0000000000000001
    sq, remaining = pop_lsb(test_bb)
    if sq != 0 or remaining != 0:
        errors.append(f"pop_lsb(0x1): expected (0, 0), got ({sq}, {remaining})")
    
    test_bb = 0x0000000000000003  # Bits 0 and 1
    sq, remaining = pop_lsb(test_bb)
    if sq != 0 or remaining != 0x2:
        errors.append(f"pop_lsb(0x3): expected (0, 2), got ({sq}, {remaining})")
    
    # Test get_lsb
    if get_lsb(0x0000000000000001) != 0:
        errors.append(f"get_lsb(0x1): expected 0")
    if get_lsb(0x0000000000000100) != 8:
        errors.append(f"get_lsb(0x100): expected 8")
    
    # Test count_bits
    if count_bits(0x00FF) != 8:
        errors.append(f"count_bits(0xFF): expected 8")
    if count_bits(0xFFFF) != 16:
        errors.append(f"count_bits(0xFFFF): expected 16")
    
    if errors:
        for e in errors:
            print(f"✗ {e}")
        print(f"\n✗✗✗ BITBOARD OP FAILURES ✗✗✗")
        return False
    
    print("✓ pop_lsb works correctly")
    print("✓ get_lsb works correctly")
    print("✓ count_bits works correctly")
    return True


def test_helpers():
    """Test move generation helper functions."""
    print("\n" + "=" * 80)
    print("HELPER FUNCTIONS TEST")
    print("=" * 80)
    
    from src.move_generation import (
        is_promotion_square_lookup,
        can_double_push,
        get_pawn_single_push,
        get_pawn_double_push,
        get_bit
    )
    
    errors = []
    
    # Test promotion squares
    if not is_promotion_square_lookup(56, 0):  # White a8
        errors.append("White a8 should be promotion square")
    if not is_promotion_square_lookup(63, 0):  # White h8
        errors.append("White h8 should be promotion square")
    if not is_promotion_square_lookup(0, 1):  # Black a1
        errors.append("Black a1 should be promotion square")
    if is_promotion_square_lookup(8, 0):  # Not promotion
        errors.append("a2 should NOT be promotion square")
    
    # Test double push
    if not can_double_push(8, 0):  # White a2
        errors.append("White a2 should allow double push")
    if not can_double_push(48, 1):  # Black a7
        errors.append("Black a7 should allow double push")
    if can_double_push(16, 0):  # Not valid
        errors.append("a3 should NOT allow double push")
    
    # Test single push
    if get_pawn_single_push(8, 0) != 16:
        errors.append("White a2→a3 failed")
    if get_pawn_single_push(48, 1) != 40:
        errors.append("Black a7→a6 failed")
    
    # Test double push
    if get_pawn_double_push(8, 0) != 24:
        errors.append("White a2→a4 failed")
    if get_pawn_double_push(48, 1) != 32:
        errors.append("Black a7→a5 failed")
    
    # Test get_bit
    if get_bit(0) != 1:
        errors.append("get_bit(0) failed")
    if get_bit(1) != 2:
        errors.append("get_bit(1) failed")
    if get_bit(63) != (1 << 63):
        errors.append("get_bit(63) failed")
    
    if errors:
        for e in errors:
            print(f"✗ {e}")
        print(f"\n✗✗✗ HELPER FUNCTION FAILURES ✗✗✗")
        return False
    
    print("✓ is_promotion_square_lookup correct")
    print("✓ can_double_push correct")
    print("✓ get_pawn_single_push correct")
    print("✓ get_pawn_double_push correct")
    print("✓ get_bit correct")
    return True


def perft(board, depth):
    """Simple perft for correctness testing."""
    from src.magic_bitboards import get_lsb
    
    if depth == 0:
        return 1
    
    nodes = 0
    for from_sq, to_sq, promo in board.generate_moves():
        board.make_move(from_sq, to_sq, promo)
        king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])
        if not board.is_square_attacked(king_sq, board.side_to_move):
            nodes += perft(board, depth - 1)
        board.unmake_move()
    
    return nodes


def test_perft_correctness():
    """Test move generation correctness with perft."""
    print("\n" + "=" * 80)
    print("PERFT CORRECTNESS TEST (Up to Depth 4)")
    print("=" * 80)
    
    from src.chess_engine import ChessBoard
    
    # Test starting position
    print("\nStarting Position:")
    print("-" * 80)
    
    expected = {
        0: 1,
        1: 20,
        2: 400,
        3: 8902,
        4: 197281,
    }
    
    board = ChessBoard()
    errors = []
    
    for depth in range(5):  # Test depth 0-4
        start = time.time()
        result = perft(board, depth)
        elapsed = time.time() - start
        nps = int(result / elapsed) if elapsed > 0 else 0
        
        status = "✓" if result == expected[depth] else "✗"
        print(f"perft({depth}) = {result:>8,}  (expected {expected[depth]:>8,})  {status}  [{elapsed:.3f}s, {nps:>8,} NPS]")
        
        if result != expected[depth]:
            errors.append(f"perft({depth}): expected {expected[depth]}, got {result}")
    
    # Test Kiwipete position (depth 1-3 only for speed)
    print("\nKiwipete Position:")
    print("-" * 80)
    
    kiwipete_expected = {
        1: 48,
        2: 2039,
        3: 97862,
    }
    
    board.setup_from_fen('r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -')
    
    for depth in range(1, 4):  # Test depth 1-3
        start = time.time()
        result = perft(board, depth)
        elapsed = time.time() - start
        nps = int(result / elapsed) if elapsed > 0 else 0
        
        status = "✓" if result == kiwipete_expected[depth] else "✗"
        print(f"perft({depth}) = {result:>8,}  (expected {kiwipete_expected[depth]:>8,})  {status}  [{elapsed:.3f}s, {nps:>8,} NPS]")
        
        if result != kiwipete_expected[depth]:
            errors.append(f"Kiwipete perft({depth}): expected {kiwipete_expected[depth]}, got {result}")
    
    if errors:
        print(f"\n✗✗✗ PERFT FAILURES - MOVE GENERATION BROKEN ✗✗✗")
        for e in errors:
            print(f"  {e}")
        return False
    
    print(f"\n✓ All perft tests passed - move generation 100% accurate")
    return True


def test_performance():
    """Test performance is acceptable."""
    print("\n" + "=" * 80)
    print("PERFORMANCE TEST")
    print("=" * 80)
    
    from src.chess_engine import ChessBoard
    
    board = ChessBoard()
    
    # Warmup
    print("Warming up (500 iterations)...")
    for i in range(500):
        perft(board, 2)
        if i % 100 == 0 and i > 0:
            print(f"  {i}/500...")
    
    # Test depth 3 performance
    print("\nTesting depth 3 performance...")
    start = time.time()
    nodes = perft(board, 3)
    elapsed = time.time() - start
    nps = int(nodes / elapsed)
    
    print(f"Nodes: {nodes:,}")
    print(f"Time: {elapsed:.3f}s")
    print(f"NPS: {nps:,}")
    
    # Performance thresholds
    # CPython typically gets 30-50k NPS
    # PyPy should get 100k+ NPS with optimizations
    # Without optimizations: 10-60k NPS
    
    min_nps = 8000  # Absolute minimum (something is very wrong below this)
    
    if nps < min_nps:
        print(f"\n⚠️  Performance warning: {nps:,} NPS is very slow (expected >{min_nps:,})")
        print(f"   This might indicate a problem, but not blocking commit.")
    else:
        print(f"\n✓ Performance acceptable: {nps:,} NPS")
    
    return True  # Don't block commit on performance


def test_simple_loop():
    """Test simple loop optimization (PyPy JIT sanity check)."""
    print("\n" + "=" * 80)
    print("PYPY JIT SANITY CHECK (Simple Loop)")
    print("=" * 80)
    
    def simple_loop():
        total = 0
        for i in range(100000):
            total += i * 2
        return total
    
    # Warmup
    print("Warming up (1000 iterations)...")
    for _ in range(1000):
        simple_loop()
    
    # Test
    print("Testing...")
    start = time.time()
    for _ in range(100):
        simple_loop()
    elapsed = time.time() - start
    
    print(f"Time for 100 iterations: {elapsed*1000:.1f}ms")
    
    # Expected: <10ms with PyPy JIT, ~15-20ms with CPython
    if elapsed < 0.010:
        print(f"✓✓✓ EXCELLENT: JIT is fully optimizing loops!")
    elif elapsed < 0.020:
        print(f"✓✓ GOOD: Performance is acceptable")
    elif elapsed < 0.030:
        print(f"✓ OK: Performance acceptable (JIT might need more warmup)")
    else:
        print(f"⚠️  SLOW: {elapsed*1000:.1f}ms (expected <20ms)")
        print(f"   JIT might not be optimizing properly")
    
    return True  # Don't block commit


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PRE-COMMIT SAFETY TEST" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    all_passed = True
    
    # Environment check (informational)
    is_pypy = check_pypy()
    
    # Critical tests (must pass)
    if not test_imports():
        all_passed = False
    
    if not test_bitboard_ops():
        all_passed = False
    
    if not test_helpers():
        all_passed = False
    
    if not test_perft_correctness():
        all_passed = False
    
    # Informational tests (don't block commit)
    test_performance()
    test_simple_loop()
    
    # Final verdict
    print("\n" + "=" * 80)
    if all_passed:
        print("✓✓✓ ALL CRITICAL TESTS PASSED - SAFE TO COMMIT ✓✓✓")
        print("=" * 80)
        print("\nChanges are verified correct and safe to deploy.")
        if is_pypy:
            print("Run on VPS to test final PyPy JIT performance.")
        return 0
    else:
        print("✗✗✗ CRITICAL TESTS FAILED - DO NOT COMMIT ✗✗✗")
        print("=" * 80)
        print("\nFix the errors above before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
