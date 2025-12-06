#!/usr/bin/env python3
"""
Critical Performance Tests - Identify PyPy Bottlenecks

This test suite helps identify performance issues in the chess engine,
specifically testing whether PyPy's JIT is working correctly.

Expected Results:
- CPython: 30k-50k NPS
- PyPy (with python-chess): 30k-50k NPS (JIT disabled) ❌
- PyPy (pure Python): 200k-500k NPS (JIT enabled) ✅

Tests:
1. Pure engine performance (without python-chess)
2. Engine with python-chess import
3. Opening book performance
4. Search algorithm performance
5. PyPy JIT warmup effectiveness
"""

import sys
import time
import platform
from typing import Tuple, List

# Test 1: Import check - detect C extensions
def test_imports():
    """Test what dependencies are imported and their types."""
    print("=" * 80)
    print("TEST 1: Import Analysis")
    print("=" * 80)
    print(f"Python: {platform.python_implementation()} {platform.python_version()}")
    print(f"Executable: {sys.executable}")
    print()
    
    # Check for PyPy
    is_pypy = platform.python_implementation() == 'PyPy'
    print(f"PyPy detected: {is_pypy}")
    
    if is_pypy:
        try:
            import __pypy__
            print(f"PyPy JIT: {__pypy__.jit_backend_name}")
        except:
            print("PyPy JIT: Unknown")
    
    print()
    
    # Test importing python-chess
    print("Testing python-chess import...")
    try:
        import chess
        import chess.syzygy
        print("✅ python-chess imported")
        print(f"   Version: {chess.__version__ if hasattr(chess, '__version__') else 'unknown'}")
        print(f"   ⚠️  WARNING: This is a C extension - PyPy JIT will be disabled!")
    except ImportError:
        print("❌ python-chess not found (GOOD for PyPy performance)")
    
    print()


# Test 2: Pure engine perft benchmark
def test_pure_engine():
    """Test engine performance without any C extensions."""
    print("=" * 80)
    print("TEST 2: Pure Engine Performance (Perft)")
    print("=" * 80)
    
    from src.chess_engine import ChessBoard
    from src.magic_bitboards import get_lsb
    
    def perft(board: ChessBoard, depth: int) -> int:
        """Count leaf nodes at given depth."""
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
    
    board = ChessBoard()
    
    # Warmup
    print("Warming up (10 iterations at depth 2)...")
    warmup_start = time.time()
    for _ in range(10):
        perft(board, 2)
    warmup_time = time.time() - warmup_start
    print(f"Warmup complete in {warmup_time:.3f}s")
    print()
    
    # Test depth 4 (expected: 197,281 nodes)
    print("Running perft(4)...")
    start = time.time()
    nodes = perft(board, 4)
    elapsed = time.time() - start
    nps = int(nodes / elapsed) if elapsed > 0 else 0
    
    print(f"Nodes:    {nodes:,}")
    print(f"Expected: 197,281")
    print(f"Time:     {elapsed:.3f}s")
    print(f"NPS:      {nps:,}")
    print()
    
    # Performance evaluation
    if nps < 50_000:
        print("❌ SLOW: < 50k NPS (CPython baseline)")
    elif nps < 100_000:
        print("⚠️  OK: 50-100k NPS (CPython or PyPy without JIT)")
    elif nps < 200_000:
        print("✅ GOOD: 100-200k NPS (PyPy with partial JIT)")
    else:
        print("🚀 EXCELLENT: > 200k NPS (PyPy with full JIT)")
    
    print()
    return nps


# Test 3: Search performance
def test_search_performance():
    """Test search algorithm performance."""
    print("=" * 80)
    print("TEST 3: Search Algorithm Performance")
    print("=" * 80)
    
    from src.chess_engine import ChessBoard
    from src.evaluation import Evaluator
    from src.search import TranspositionTable, MoveOrderer, SearchStats, iterative_deepening
    
    board = ChessBoard()
    evaluator = Evaluator()
    tt = TranspositionTable(size_mb=64)
    orderer = MoveOrderer()
    stats = SearchStats()
    
    print("Running 1-second search from starting position...")
    start = time.time()
    
    best_move, best_score, pv_line = iterative_deepening(
        board=board,
        max_time_ms=1000,
        max_depth=50,
        evaluator=evaluator,
        tt=tt,
        orderer=orderer,
        stats=stats
    )
    
    elapsed = time.time() - start
    nps = stats.nps()
    
    print(f"Best move: {best_move}")
    print(f"Score:     {best_score}")
    print(f"Nodes:     {stats.nodes:,}")
    print(f"Time:      {elapsed:.3f}s")
    print(f"NPS:       {nps:,}")
    print()
    
    if nps < 30_000:
        print("❌ CRITICAL: < 30k NPS (something is very wrong)")
    elif nps < 100_000:
        print("⚠️  SLOW: 30-100k NPS (CPython or PyPy with JIT disabled)")
    elif nps < 300_000:
        print("✅ GOOD: 100-300k NPS (PyPy with partial JIT)")
    else:
        print("🚀 EXCELLENT: > 300k NPS (PyPy with full JIT)")
    
    print()
    return nps


# Test 4: Python-chess impact test
def test_pythonchess_impact():
    """Test performance impact of importing python-chess."""
    print("=" * 80)
    print("TEST 4: Python-Chess Impact Test")
    print("=" * 80)
    
    try:
        # Import python-chess AFTER running pure tests
        import chess
        print("✅ python-chess imported")
        print("⚠️  PyPy JIT is now DISABLED for this process")
        print()
        
        # Run quick perft to show impact
        from src.chess_engine import ChessBoard
        from src.magic_bitboards import get_lsb
        
        def perft(board: ChessBoard, depth: int) -> int:
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
        
        board = ChessBoard()
        start = time.time()
        nodes = perft(board, 4)
        elapsed = time.time() - start
        nps = int(nodes / elapsed) if elapsed > 0 else 0
        
        print(f"Performance with python-chess loaded:")
        print(f"  Nodes: {nodes:,}")
        print(f"  Time:  {elapsed:.3f}s")
        print(f"  NPS:   {nps:,}")
        print()
        
        if nps < 100_000:
            print("❌ CONFIRMED: python-chess is killing PyPy performance")
            print("   Recommendation: Remove python-chess dependency")
        
    except ImportError:
        print("❌ python-chess not installed")
        print("✅ This is GOOD - pure Python is much faster with PyPy")
    
    print()


# Test 5: JIT compilation detection
def test_jit_status():
    """Detect if PyPy JIT is actually working."""
    print("=" * 80)
    print("TEST 5: PyPy JIT Status")
    print("=" * 80)
    
    is_pypy = platform.python_implementation() == 'PyPy'
    
    if not is_pypy:
        print("❌ Not running on PyPy - JIT not available")
        print("   Current: CPython")
        print("   Switch to PyPy for 5-10x speedup")
        print()
        return
    
    print("✅ Running on PyPy")
    
    try:
        import __pypy__
        # Try to get backend name if available
        try:
            backend = __pypy__.jit_backend_name
            print(f"   Backend: {backend}")
        except AttributeError:
            print("   Backend: JIT enabled (backend name not available)")
        
        # Try to get JIT info
        try:
            from pypyjit import get_stats
            stats = get_stats()
            print(f"   Compiled loops: {stats.compiled_loops if hasattr(stats, 'compiled_loops') else 'unknown'}")
        except:
            print("   JIT stats: Not available")
        
    except ImportError:
        print("⚠️  Cannot import __pypy__ module")
    
    print()


# Test 6: Memory efficiency
def test_memory_efficiency():
    """Test memory usage of core data structures."""
    print("=" * 80)
    print("TEST 6: Memory Efficiency")
    print("=" * 80)
    
    import sys
    from src.chess_engine import ChessBoard
    from src.search import TranspositionTable
    
    # Test board size
    board = ChessBoard()
    board_size = sys.getsizeof(board)
    print(f"ChessBoard object size: {board_size:,} bytes")
    
    # Test TT size
    tt_small = TranspositionTable(size_mb=1)
    tt_large = TranspositionTable(size_mb=1024)
    
    print(f"TT (1MB):    {tt_small.size:,} entries")
    print(f"TT (1024MB): {tt_large.size:,} entries")
    print()


# Run all tests
def main():
    """Run all critical performance tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "CRITICAL PERFORMANCE TEST SUITE".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    results = {}
    
    # Run tests
    test_imports()
    test_jit_status()
    results['pure_engine'] = test_pure_engine()
    results['search'] = test_search_performance()
    test_memory_efficiency()
    test_pythonchess_impact()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    print(f"Python Implementation: {platform.python_implementation()}")
    print(f"Pure Engine NPS:       {results['pure_engine']:,}")
    print(f"Search NPS:            {results['search']:,}")
    print()
    
    # Recommendations
    print("RECOMMENDATIONS:")
    print()
    
    is_pypy = platform.python_implementation() == 'PyPy'
    pure_fast = results['pure_engine'] > 150_000
    search_fast = results['search'] > 150_000
    
    if not is_pypy:
        print("1. ⚠️  Install and use PyPy for 5-10x speedup")
        print("   - Download: https://www.pypy.org/download.html")
        print("   - Install: pypy3 -m pip install -r requirements.txt")
        print("   - Run: pypy3 -m uvicorn main:app")
    
    if pure_fast and not search_fast:
        print("2. ⚠️  Search is slower than expected")
        print("   - Check for unnecessary operations in search loop")
        print("   - Profile with: pypy3 -m cProfile")
    
    if not pure_fast and is_pypy:
        print("2. ❌ PyPy JIT is not working properly")
        print("   - Check for C extension imports")
        print("   - Remove python-chess dependency")
        print("   - Use pure Python implementations only")
    
    if results['pure_engine'] < 50_000:
        print("3. ❌ Performance is critically slow")
        print("   - Expected: 30-50k NPS on CPython, 200-500k on PyPy")
        print("   - Current: Below baseline")
        print("   - Action: Profile code to find bottleneck")
    
    print()


if __name__ == "__main__":
    main()
