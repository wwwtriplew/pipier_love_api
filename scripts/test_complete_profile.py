#!/usr/bin/env python3
"""
Test 4: Complete Hot Path Profiling
Profile the ENTIRE engine: search + move generation + evaluation + make/unmake

This reveals the TRUE bottleneck in the chess engine, not just evaluation.
"""

import sys
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import alpha_beta, SearchStats, TranspositionTable, MoveOrderer

print("=" * 80)
print("TEST 4: COMPLETE ENGINE HOT PATH PROFILING")
print("=" * 80)
print()

board = ChessBoard()
evaluator = Evaluator()
tt = TranspositionTable(size_mb=64)
orderer = MoveOrderer()

# Warmup
print("Warming up...")
for _ in range(100):
    stats = SearchStats()
    pv_line = []
    repetition_stack = []
    alpha_beta(board, 3, 0, -999999, 999999, evaluator, tt, orderer, stats, pv_line, repetition_stack)
print()

# ============================================================================
# Component 1: Move Generation
# ============================================================================
print("Component 1: Move Generation")
print("-" * 80)

iterations = 100_000
start = time.perf_counter()
for _ in range(iterations):
    moves = board.generate_moves()
elapsed = time.perf_counter() - start

movegen_speed = iterations / elapsed
movegen_time = (elapsed / iterations) * 1_000_000

print(f"Iterations: {iterations:,}")
print(f"Time: {elapsed:.3f}s")
print(f"Speed: {movegen_speed:,.0f} calls/sec")
print(f"Per-call: {movegen_time:.2f} μs")
print(f"Moves generated: {len(moves)} (starting position)")
print()

# ============================================================================
# Component 2: Make/Unmake Move
# ============================================================================
print("Component 2: Make/Unmake Move")
print("-" * 80)

moves = board.generate_moves()
test_move = moves[0]  # e2e4

iterations = 100_000
start = time.perf_counter()
for _ in range(iterations):
    board.make_move(test_move[0], test_move[1], test_move[2])
    board.unmake_move()
elapsed = time.perf_counter() - start

make_unmake_speed = iterations / elapsed
make_unmake_time = (elapsed / iterations) * 1_000_000

print(f"Iterations: {iterations:,}")
print(f"Time: {elapsed:.3f}s")
print(f"Speed: {make_unmake_speed:,.0f} make/unmake cycles/sec")
print(f"Per-cycle: {make_unmake_time:.2f} μs")
print()

# ============================================================================
# Component 3: Evaluation (already tested, but include for comparison)
# ============================================================================
print("Component 3: Evaluation")
print("-" * 80)

iterations = 100_000
start = time.perf_counter()
for _ in range(iterations):
    score = evaluator.evaluate(board)
elapsed = time.perf_counter() - start

eval_speed = iterations / elapsed
eval_time = (elapsed / iterations) * 1_000_000

print(f"Iterations: {iterations:,}")
print(f"Time: {elapsed:.3f}s")
print(f"Speed: {eval_speed:,.0f} evals/sec")
print(f"Per-call: {eval_time:.2f} μs")
print()

# ============================================================================
# Component 4: Alpha-Beta Search (Depth 3)
# ============================================================================
print("Component 4: Alpha-Beta Search (Depth 3)")
print("-" * 80)

iterations = 100
nodes_searched = 0

start = time.perf_counter()
for _ in range(iterations):
    # Clear TT between searches to avoid caching
    tt = TranspositionTable(size_mb=64)
    orderer = MoveOrderer()
    stats = SearchStats()
    pv_line = []
    repetition_stack = []
    score = alpha_beta(board, 3, 0, -999999, 999999, evaluator, tt, orderer, stats, pv_line, repetition_stack)
    nodes_searched += stats.nodes
elapsed = time.perf_counter() - start

search_speed = iterations / elapsed
search_time = (elapsed / iterations) * 1000  # milliseconds
avg_nodes = nodes_searched / iterations
nps = nodes_searched / elapsed

print(f"Iterations: {iterations}")
print(f"Time: {elapsed:.3f}s")
print(f"Speed: {search_speed:.2f} searches/sec")
print(f"Per-search: {search_time:.2f} ms")
print(f"Avg nodes: {avg_nodes:,.0f} nodes/search")
print(f"NPS: {nps:,.0f} nodes/sec")
print()

# ============================================================================
# Component 5: Perft (move generation stress test)
# ============================================================================
print("Component 5: Perft (Depth 4)")
print("-" * 80)

def perft(board, depth):
    if depth == 0:
        return 1
    
    count = 0
    moves = board.generate_moves()
    
    for from_sq, to_sq, promo in moves:
        board.make_move(from_sq, to_sq, promo)
        count += perft(board, depth - 1)
        board.unmake_move()
    
    return count

start = time.perf_counter()
nodes = perft(board, 4)
elapsed = time.perf_counter() - start

perft_nps = nodes / elapsed

print(f"Nodes: {nodes:,}")
print(f"Time: {elapsed:.3f}s")
print(f"NPS: {perft_nps:,.0f} nodes/sec")
print()

# ============================================================================
# ANALYSIS
# ============================================================================
print("=" * 80)
print("COMPREHENSIVE ANALYSIS")
print("=" * 80)
print()

print("COMPONENT SPEEDS:")
print("-" * 80)
print(f"{'Component':<30} {'Speed':>15} {'Time/Op':>12}")
print("-" * 80)
print(f"{'Move generation':<30} {movegen_speed:>13,.0f}/s {movegen_time:>10.2f} μs")
print(f"{'Make/unmake move':<30} {make_unmake_speed:>13,.0f}/s {make_unmake_time:>10.2f} μs")
print(f"{'Evaluation':<30} {eval_speed:>13,.0f}/s {eval_time:>10.2f} μs")
print(f"{'Alpha-beta search':<30} {search_speed:>13,.2f}/s {search_time:>10.2f} ms")
print(f"{'Perft (movegen only)':<30} {perft_nps:>13,.0f} NPS")
print(f"{'Search (with eval)':<30} {nps:>13,.0f} NPS")
print()

print("BOTTLENECK IDENTIFICATION:")
print("-" * 80)
print()

# Estimate time breakdown in alpha-beta search
# At depth 3, rough estimate: ~120 nodes, ~40 move generations, ~120 evaluations
depth3_nodes = avg_nodes
estimated_movegen_time = (depth3_nodes / 3) * movegen_time / 1000  # ms
estimated_eval_time = depth3_nodes * eval_time / 1000  # ms
estimated_make_unmake_time = depth3_nodes * make_unmake_time / 1000  # ms
overhead_time = search_time - estimated_movegen_time - estimated_eval_time - estimated_make_unmake_time

print(f"For a depth-3 search ({avg_nodes:.0f} nodes, {search_time:.2f} ms):")
print()
print(f"  Evaluation:      {estimated_eval_time:>8.2f} ms ({estimated_eval_time/search_time*100:>5.1f}%)")
print(f"  Move generation: {estimated_movegen_time:>8.2f} ms ({estimated_movegen_time/search_time*100:>5.1f}%)")
print(f"  Make/unmake:     {estimated_make_unmake_time:>8.2f} ms ({estimated_make_unmake_time/search_time*100:>5.1f}%)")
print(f"  Search overhead: {overhead_time:>8.2f} ms ({overhead_time/search_time*100:>5.1f}%)")
print(f"  ──────────────────────────────────")
print(f"  Total:           {search_time:>8.2f} ms (100.0%)")
print()

# Identify primary bottleneck
components = [
    ("Evaluation", estimated_eval_time),
    ("Move generation", estimated_movegen_time),
    ("Make/unmake", estimated_make_unmake_time),
    ("Search overhead", overhead_time)
]
components.sort(key=lambda x: x[1], reverse=True)

print("PRIMARY BOTTLENECKS (ranked by time spent):")
for i, (name, time_ms) in enumerate(components, 1):
    percent = (time_ms / search_time) * 100
    print(f"{i}. {name:<20} {time_ms:>7.2f} ms ({percent:>5.1f}%)")

print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()

primary_bottleneck = components[0]
if primary_bottleneck[1] / search_time > 0.4:
    print(f"🎯 PRIMARY BOTTLENECK: {primary_bottleneck[0]}")
    print(f"   Takes {primary_bottleneck[1]/search_time*100:.0f}% of search time")
    print(f"   PRIORITY: Optimize this component first")
    print()

if primary_bottleneck[0] == "Evaluation":
    print("   Evaluation bottleneck confirmed.")
    print("   → Focus on _evaluate_mobility and _evaluate_king_safety")
    print("   → Consider caching or approximations")
elif primary_bottleneck[0] == "Move generation":
    print("   Move generation is slow!")
    print("   → Profile move generation code")
    print("   → Check magic bitboard attack generation")
    print("   → Look for redundant work")
elif primary_bottleneck[0] == "Make/unmake":
    print("   Make/unmake overhead is high!")
    print("   → Check state saving/restoration")
    print("   → Look for unnecessary work")
    print("   → Consider incremental updates")
elif primary_bottleneck[0] == "Search overhead":
    print("   Search algorithm itself is slow!")
    print("   → Profile alpha_beta function")
    print("   → Check for inefficient data structures")
    print("   → Look at transposition table access")

print()

# Compare with target
target_nps = 200_000
current_nps = nps
gap = target_nps / current_nps

print(f"PERFORMANCE GAP ANALYSIS:")
print(f"  Current NPS:  {current_nps:>10,.0f}")
print(f"  Target NPS:   {target_nps:>10,.0f}")
print(f"  Gap:          {gap:>10.1f}x slower than target")
print()

if gap > 5:
    print("  ⚠️  LARGE GAP: Need multiple optimizations")
    print("     1. Fix primary bottleneck")
    print("     2. Profile again and iterate")
    print("     3. May need algorithmic improvements")
elif gap > 2:
    print("  ⚠️  MODERATE GAP: 1-2 optimizations should suffice")
    print("     Focus on primary and secondary bottlenecks")
else:
    print("  ✅ SMALL GAP: Close to target!")
    print("     One focused optimization should get us there")

print()
print("NEXT STEPS:")
print("1. Update MASTER_FIX_PLAN.md with complete profiling results")
print("2. Profile the primary bottleneck component in detail")
print("3. Implement targeted optimization")
print("4. Re-run this test to verify improvement")
