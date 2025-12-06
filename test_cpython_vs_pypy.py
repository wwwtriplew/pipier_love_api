#!/usr/bin/env python3
"""
Critical Test: CPython vs PyPy Performance
==========================================

HYPOTHESIS: CPython might be FASTER than PyPy for our chess engine!

Why this might be true:
1. PyPy JIT overhead for complex object-oriented code
2. CPython's simpler interpreter may have less overhead for deep recursion
3. Our code is NOT JIT-friendly (heavy OOP, lots of function calls)
4. Bitboard operations are simple enough that CPython is fine

This test compares:
- CPython with TT
- CPython without TT (if TT overhead is killing us)
- PyPy with TT (current baseline)
"""

import sys
import time
from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import TranspositionTable, MoveOrderer, SearchStats, iterative_deepening

print("=" * 70)
print("CPYTHON vs PYPY PERFORMANCE TEST")
print("=" * 70)
print()

# Detect which Python we're running
try:
    import __pypy__
    python_impl = "PyPy"
    version = sys.version.split()[0]
except ImportError:
    python_impl = "CPython"
    version = sys.version.split()[0]

print(f"Running on: {python_impl} {version}")
print()

board = ChessBoard()
evaluator = Evaluator()

# Test 1: WITH Transposition Table
print("=" * 70)
print("TEST 1: WITH Transposition Table")
print("=" * 70)

# Warmup
for _ in range(3):
    tt = TranspositionTable(size_mb=64)
    orderer = MoveOrderer()
    stats = SearchStats()
    iterative_deepening(board, 500, 3, evaluator, tt, orderer, stats)

# Run test
results_with_tt = []
for i in range(10):
    tt = TranspositionTable(size_mb=64)
    orderer = MoveOrderer()
    stats = SearchStats()
    
    start = time.perf_counter()
    best_move, score, pv = iterative_deepening(board, 5000, 5, evaluator, tt, orderer, stats)
    elapsed = time.perf_counter() - start
    
    nodes = stats.nodes + stats.q_nodes
    nps = nodes / elapsed if elapsed > 0 else 0
    results_with_tt.append((elapsed, nodes, nps))
    
    print(f"Run {i+1:2d}: {elapsed*1000:6.1f}ms | {nodes:7d} nodes | {nps:8.0f} NPS")

avg_time_with = sum(r[0] for r in results_with_tt) / len(results_with_tt)
avg_nodes_with = sum(r[1] for r in results_with_tt) / len(results_with_tt)
avg_nps_with = avg_nodes_with / avg_time_with

print(f"\nAVERAGE WITH TT: {avg_time_with*1000:.1f}ms | {avg_nodes_with:.0f} nodes | {avg_nps_with:.0f} NPS")

# Test 2: WITHOUT Transposition Table (use None)
print()
print("=" * 70)
print("TEST 2: WITHOUT Transposition Table")
print("=" * 70)
print("(Using alpha-beta only, no hash table)")
print()

# Warmup
for _ in range(3):
    from src.search import alpha_beta
    orderer = MoveOrderer()
    stats = SearchStats()
    pv = []
    reps = []
    alpha_beta(board, 3, 0, -999999, 999999, evaluator, None, orderer, stats, pv, reps)

# Run test
results_no_tt = []
for i in range(10):
    from src.search import alpha_beta
    orderer = MoveOrderer()
    stats = SearchStats()
    pv = []
    reps = []
    
    start = time.perf_counter()
    score = alpha_beta(board, 5, 0, -999999, 999999, evaluator, None, orderer, stats, pv, reps)
    elapsed = time.perf_counter() - start
    
    nodes = stats.nodes + stats.q_nodes
    nps = nodes / elapsed if elapsed > 0 else 0
    results_no_tt.append((elapsed, nodes, nps))
    
    print(f"Run {i+1:2d}: {elapsed*1000:6.1f}ms | {nodes:7d} nodes | {nps:8.0f} NPS")

avg_time_no = sum(r[0] for r in results_no_tt) / len(results_no_tt)
avg_nodes_no = sum(r[1] for r in results_no_tt) / len(results_no_tt)
avg_nps_no = avg_nodes_no / avg_time_no

print(f"\nAVERAGE NO TT: {avg_time_no*1000:.1f}ms | {avg_nodes_no:.0f} nodes | {avg_nps_no:.0f} NPS")

# Analysis
print()
print("=" * 70)
print("ANALYSIS")
print("=" * 70)
print()

print(f"Python: {python_impl} {version}")
print()
print(f"WITH TT:    {avg_nps_with:8.0f} NPS")
print(f"WITHOUT TT: {avg_nps_no:8.0f} NPS")
print()

if avg_nps_no > avg_nps_with:
    improvement = (avg_nps_no - avg_nps_with) / avg_nps_with * 100
    print(f"🔥 NO TT IS {improvement:.1f}% FASTER!")
    print()
    print("RECOMMENDATION:")
    print("  - Remove TranspositionTable (it's overhead, not benefit)")
    print("  - Simplify to pure alpha-beta search")
    print("  - Expected API improvement: 2-3x faster")
else:
    improvement = (avg_nps_with - avg_nps_no) / avg_nps_no * 100
    print(f"✓ TT helps: {improvement:.1f}% faster")
    print()
    print("RECOMMENDATION:")
    print("  - Keep TranspositionTable")
    print("  - Focus on other optimizations")

print()
print("NEXT STEP:")
if python_impl == "PyPy":
    print("  Run this SAME test with CPython:")
    print("  python3 test_cpython_vs_pypy.py")
    print()
    print("  Compare NPS between CPython and PyPy")
else:
    print("  You're already on CPython!")
    print("  Compare these results with PyPy results")
