#!/usr/bin/env python3
"""
Measure Phase 1 performance improvement.
Compares current performance with baseline.
"""

import time
import sys
from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import TranspositionTable, MoveOrderer, SearchStats, iterative_deepening

print("=" * 70)
print("PHASE 1 PERFORMANCE MEASUREMENT")
print("=" * 70)

# Initialize engine
print("\nInitializing engine...")
board = ChessBoard()
evaluator = Evaluator()

# Warm up PyPy JIT
print("Warming up PyPy JIT...")
for _ in range(5):
    tt = TranspositionTable(size_mb=64)
    orderer = MoveOrderer()
    stats = SearchStats()
    result = iterative_deepening(board, 1000, 3, evaluator, tt, orderer, stats)

# Run performance test
print("\nRunning performance test (10 searches at depth 4)...")
print("-" * 70)

total_time = 0
total_nodes = 0
searches = 10

for i in range(searches):
    tt = TranspositionTable(size_mb=64)
    orderer = MoveOrderer()
    stats = SearchStats()
    
    start = time.perf_counter()
    best_move, best_score, pv = iterative_deepening(board, 10000, 4, evaluator, tt, orderer, stats)
    elapsed = time.perf_counter() - start
    
    nodes = stats.nodes
    nps = nodes / elapsed if elapsed > 0 else 0
    
    total_time += elapsed
    total_nodes += nodes
    
    print(f"Search {i+1:2d}: {elapsed*1000:6.1f} ms | {nodes:6d} nodes | {nps:8.0f} NPS")

# Calculate averages
avg_time = total_time / searches
avg_nodes = total_nodes / searches
avg_nps = avg_nodes / avg_time if avg_time > 0 else 0

print("-" * 70)
print(f"\nAVERAGE PERFORMANCE:")
print(f"  Time per search: {avg_time*1000:.1f} ms")
print(f"  Nodes per search: {avg_nodes:.0f}")
print(f"  NPS: {avg_nps:.0f}")

# Compare with baseline
baseline_nps = 5083
improvement = ((avg_nps - baseline_nps) / baseline_nps) * 100

print(f"\nCOMPARISON TO BASELINE:")
print(f"  Baseline NPS: {baseline_nps:,.0f}")
print(f"  Current NPS: {avg_nps:,.0f}")
print(f"  Improvement: {improvement:+.1f}%")

# Expected improvement from Phase 1
expected_min = 6000
expected_max = 6800

print(f"\nPHASE 1 TARGET:")
print(f"  Expected range: {expected_min:,} - {expected_max:,} NPS")

if avg_nps >= expected_min:
    print(f"  ✅ TARGET ACHIEVED! ({improvement:+.1f}% improvement)")
elif avg_nps > baseline_nps:
    print(f"  ⚠️  Partial improvement ({improvement:+.1f}%), but below target")
else:
    print(f"  ❌ No improvement detected")

print("\n" + "=" * 70)

# Exit with appropriate code
if avg_nps >= expected_min:
    sys.exit(0)
else:
    sys.exit(1)
