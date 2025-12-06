#!/usr/bin/env python3
"""
Proper PyPy vs CPython benchmark for chess engine workload.
Tests REAL workload (perft) not toy loops.
"""

import sys
import time
import platform

def show_env():
    """Show Python environment."""
    print("=" * 80)
    print("ENVIRONMENT")
    print("=" * 80)
    print(f"Implementation: {platform.python_implementation()}")
    print(f"Version: {sys.version}")
    
    try:
        import __pypy__
        try:
            import pypyjit
            print(f"JIT params: {pypyjit.get_params()}")
        except:
            print("JIT: enabled (params not available)")
    except ImportError:
        print("JIT: N/A (CPython)")
    print()


def test_rich_loop():
    """Test a RICHER loop (not ultra-thin)."""
    print("=" * 80)
    print("RICH LOOP TEST (non-trivial work per iteration)")
    print("=" * 80)
    
    def loop(n):
        s = 0
        a = [1, 2, 3, 4, 5, 6, 7, 8]  # local, stable list
        for i in range(n):
            b = a[i & 7]
            s += (i ^ s) + (b * 3) - (i >> 2)
            if (s & 3) == 0:
                s += b
        return s
    
    # Warmup
    print("Warming up...")
    for _ in range(10):
        loop(500000)
    
    # Test
    print("Testing...")
    t0 = time.perf_counter()
    result = loop(50000000)
    t1 = time.perf_counter()
    
    elapsed = t1 - t0
    iters_per_sec = 50000000 / elapsed
    
    print(f"Result: {result}")
    print(f"Elapsed: {elapsed:.3f}s")
    print(f"Iterations/sec: {iters_per_sec:,.0f}")
    print()


def test_chess_perft():
    """Test REAL chess workload (perft)."""
    print("=" * 80)
    print("CHESS PERFT TEST (real workload)")
    print("=" * 80)
    
    from src.chess_engine import ChessBoard
    from src.magic_bitboards import get_lsb
    
    def perft(board, depth):
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
    
    # Heavy warmup - drive JIT to optimize REAL workload
    print("Heavy warmup (2000 iterations at depth 2)...")
    for i in range(2000):
        perft(board, 2)
        if i % 500 == 0:
            print(f"  {i}/2000...")
    
    # Test at progressively deeper depths
    print("\nTesting steady-state performance:")
    print("-" * 80)
    
    for depth in [3, 4]:
        board = ChessBoard()  # Fresh board
        
        t0 = time.perf_counter()
        nodes = perft(board, depth)
        t1 = time.perf_counter()
        
        elapsed = t1 - t0
        nps = int(nodes / elapsed)
        
        print(f"Depth {depth}: {nodes:>8,} nodes in {elapsed:>6.3f}s = {nps:>8,} NPS")
    
    print()


def test_kiwipete():
    """Test complex position (Kiwipete)."""
    print("=" * 80)
    print("KIWIPETE POSITION TEST (complex tactical position)")
    print("=" * 80)
    
    from src.chess_engine import ChessBoard
    from src.magic_bitboards import get_lsb
    
    def perft(board, depth):
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
    board.setup_from_fen('r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -')
    
    # Warmup on this position
    print("Warmup (1000 iterations at depth 2)...")
    for _ in range(1000):
        perft(board, 2)
    
    # Test
    print("\nTesting:")
    print("-" * 80)
    
    for depth in [3]:
        board.setup_from_fen('r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -')
        
        t0 = time.perf_counter()
        nodes = perft(board, depth)
        t1 = time.perf_counter()
        
        elapsed = t1 - t0
        nps = int(nodes / elapsed)
        
        print(f"Depth {depth}: {nodes:>8,} nodes in {elapsed:>6.3f}s = {nps:>8,} NPS")
    
    print()


def main():
    """Run all benchmarks."""
    show_env()
    test_rich_loop()
    test_chess_perft()
    test_kiwipete()
    
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print()
    print("If CPython 3.12+ beats PyPy on rich loop:")
    print("  → PEP 659 specialization is winning")
    print()
    print("If PyPy beats CPython on chess perft:")
    print("  → PyPy JIT works well on REAL workload")
    print("  → Toy loops are misleading")
    print()
    print("If both are similar on chess perft:")
    print("  → This workload doesn't benefit from JIT")
    print("  → Consider CPython for simplicity")
    print()


if __name__ == "__main__":
    main()
