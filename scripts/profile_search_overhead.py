#!/usr/bin/env python3
"""
Profile Search Overhead - Identify which part of search infrastructure is slowest

This profiles the 70% "search overhead" found in Test 4 to determine:
- Is it TT probe/store operations?
- Is it move ordering (killer/history)?
- Is it PV line management?
- Is it repetition detection?
"""

import sys
import os
import cProfile
import pstats
import io

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import alpha_beta, SearchStats, TranspositionTable, MoveOrderer

print("=" * 80)
print("SEARCH OVERHEAD PROFILING")
print("=" * 80)
print()
print("This profiles alpha_beta search to find the slowest operations")
print("in the search infrastructure (TT, move ordering, PV, repetition).")
print()
print("Running 100 depth-3 searches...")
print()

board = ChessBoard()
evaluator = Evaluator()

def run_searches():
    """Run 100 searches to get good profiling data"""
    for _ in range(100):
        tt = TranspositionTable(size_mb=64)
        orderer = MoveOrderer()
        stats = SearchStats()
        pv_line = []
        repetition_stack = []
        alpha_beta(board, 3, 0, -999999, 999999, evaluator, tt, orderer, 
                  stats, pv_line, repetition_stack)

# Profile the function
profiler = cProfile.Profile()
profiler.enable()
run_searches()
profiler.disable()

# Print results
print("=" * 80)
print("TOP 40 HOTSPOTS (by cumulative time)")
print("=" * 80)
print()

s = io.StringIO()
stats = pstats.Stats(profiler, stream=s)
stats.sort_stats('cumulative')
stats.print_stats(40)
print(s.getvalue())

print()
print("=" * 80)
print("TOP 20 HOTSPOTS (by self time)")
print("=" * 80)
print()

s = io.StringIO()
stats = pstats.Stats(profiler, stream=s)
stats.sort_stats('time')
stats.print_stats(20)
print(s.getvalue())

print()
print("=" * 80)
print("ANALYSIS GUIDE")
print("=" * 80)
print()
print("Look for high cumulative time in:")
print("  • TranspositionTable.probe")
print("  • TranspositionTable.store")
print("  • MoveOrderer.order_moves")
print("  • list.count (repetition detection)")
print("  • list operations (PV line, killer moves)")
print()
print("Compare 'tottime' (self time) vs 'cumtime' (cumulative):")
print("  • High tottime = function itself is slow (optimize this)")
print("  • High cumtime but low tottime = calls slow functions (optimize callees)")
print()
print("Next steps:")
print("  1. Identify the top 2-3 slowest operations")
print("  2. Implement targeted optimizations (numpy arrays, dicts, etc.)")
print("  3. Re-run this profiler to measure improvement")
