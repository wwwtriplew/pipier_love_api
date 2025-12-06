#!/usr/bin/env python3
"""
Benchmark script to compare CPython vs PyPy performance.
Tests the chess engine with a quick perft calculation.
"""

import sys
import time
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from board_state import Position

def benchmark_perft(depth=4):
    """Run a quick perft benchmark."""
    print("=" * 70)
    print(f"Chess Engine Benchmark - Perft Depth {depth}")
    print("=" * 70)
    
    # Test position: starting position
    board = Position()
    
    print(f"\nPython version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Testing position: Starting position")
    print(f"Depth: {depth}")
    
    # Warmup
    print("\nWarming up...")
    board.perft(2)
    
    # Benchmark
    print(f"\nRunning perft({depth})...")
    start_time = time.time()
    nodes = board.perft(depth)
    elapsed = time.time() - start_time
    
    nps = int(nodes / elapsed) if elapsed > 0 else 0
    
    print(f"\n{'=' * 70}")
    print(f"Results:")
    print(f"  Nodes:     {nodes:,}")
    print(f"  Time:      {elapsed:.3f}s")
    print(f"  NPS:       {nps:,}")
    print(f"{'=' * 70}")
    
    return nodes, elapsed, nps

def benchmark_search(depth=5):
    """Benchmark the search function."""
    from search import iterative_deepening_search
    
    print("\n" + "=" * 70)
    print(f"Search Benchmark - Depth {depth}")
    print("=" * 70)
    
    board = Position()
    
    print(f"\nSearching to depth {depth}...")
    start_time = time.time()
    
    result = iterative_deepening_search(board, depth, time_limit=30.0)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'=' * 70}")
    print(f"Search Results:")
    print(f"  Best move: {result.get('best_move', 'N/A')}")
    print(f"  Score:     {result.get('score', 'N/A')}")
    print(f"  Depth:     {result.get('depth', 'N/A')}")
    print(f"  Nodes:     {result.get('nodes', 0):,}")
    print(f"  Time:      {elapsed:.3f}s")
    if result.get('nodes', 0) > 0:
        print(f"  NPS:       {int(result['nodes'] / elapsed):,}")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("CHESS ENGINE PERFORMANCE BENCHMARK")
    print("=" * 70)
    
    # Quick perft test
    nodes, elapsed, nps = benchmark_perft(depth=4)
    
    # Compare with expected NPS
    print(f"\nPerformance Analysis:")
    if nps < 30000:
        print(f"  ⚠️  Slow: {nps:,} NPS (CPython typical: 30,000-50,000)")
        print(f"      PyPy can achieve 500,000-2,000,000 NPS!")
    elif nps < 100000:
        print(f"  📊 Normal: {nps:,} NPS (CPython range)")
    elif nps < 500000:
        print(f"  🚀 Fast: {nps:,} NPS (Good performance)")
    else:
        print(f"  ⚡ Very Fast: {nps:,} NPS (PyPy JIT optimized!)")
    
    # Optional: Search benchmark
    if len(sys.argv) > 1 and sys.argv[1] == "--search":
        benchmark_search(depth=5)
    
    print("\n" + "=" * 70)
    print("Benchmark complete!")
    print("=" * 70)
