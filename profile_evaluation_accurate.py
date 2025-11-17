#!/usr/bin/env python3
"""
More accurate evaluation profiling with better cache behavior.
"""

import sys
import time
import random

sys.path.insert(0, 'src')

from board_state import new_game, from_fen
from evaluation import Evaluator


def benchmark_realistic_scenario():
    """
    Benchmark evaluation in a realistic search scenario.
    
    In search, we evaluate the same position multiple times
    (different branches of the tree) so cache hit rate is high.
    """
    print("=" * 70)
    print("REALISTIC EVALUATION BENCHMARK")
    print("=" * 70)
    print()
    
    # Generate 20 base positions
    print("Generating base positions...")
    base_positions = []
    for _ in range(20):
        pos = new_game()
        for _ in range(random.randint(5, 20)):
            moves = pos.legal_moves()
            if not moves:
                break
            pos.make_move(random.choice(moves))
        base_positions.append(pos._board)
    
    print(f"✅ Generated {len(base_positions)} base positions")
    print()
    
    # Create evaluator
    evaluator = Evaluator()
    
    # Warm-up with more iterations
    print("Warming up JIT (this takes ~10 seconds)...")
    for _ in range(100):
        for board in base_positions:
            evaluator.evaluate(board)
    print("✅ Warm-up complete")
    print()
    
    # Benchmark: Evaluate each position multiple times (simulating search)
    print("Benchmarking (5 seconds)...")
    test_duration = 5.0
    evals_done = 0
    start_time = time.perf_counter()
    
    while time.perf_counter() - start_time < test_duration:
        # In search, we evaluate same positions multiple times
        for board in base_positions:
            # Evaluate 5 times (simulating revisiting position in tree)
            for _ in range(5):
                evaluator.evaluate(board)
                evals_done += 1
    
    elapsed = time.perf_counter() - start_time
    evals_per_sec = evals_done / elapsed
    
    print(f"✅ Benchmark complete")
    print()
    print("Results:")
    print(f"  Evaluations: {evals_done:,}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  **Evaluations/sec: {evals_per_sec:,.0f}**")
    print()
    
    # Cache statistics
    stats = evaluator.get_stats()
    pawn_stats = stats['pawn_hash']
    
    print("Cache Statistics:")
    print(f"  Pawn hash hits: {pawn_stats['hits']:,}")
    print(f"  Pawn hash misses: {pawn_stats['misses']:,}")
    print(f"  **Hit rate: {pawn_stats['hit_rate']:.1f}%**")
    print()
    
    return evals_per_sec


def estimate_search_nps():
    """
    Estimate NPS in actual search based on evaluation benchmark.
    """
    print("=" * 70)
    print("TRUE NPS ESTIMATION")
    print("=" * 70)
    print()
    
    # Known data
    perft_nps = 459000  # From benchmark_pypy.py
    print(f"Move generation NPS (perft): {perft_nps:,}")
    
    # Benchmark evaluations
    evals_per_sec = benchmark_realistic_scenario()
    print(f"Evaluations per second: {evals_per_sec:,.0f}")
    print()
    
    # Calculate times
    time_per_move_gen_us = 1e6 / perft_nps
    time_per_eval_us = 1e6 / evals_per_sec
    
    print("Time per operation:")
    print(f"  Move generation: {time_per_move_gen_us:.2f} μs")
    print(f"  Evaluation: {time_per_eval_us:.2f} μs")
    print()
    
    # In alpha-beta search:
    # - Every node generates moves
    # - Only leaf nodes are evaluated
    # - At depth 4, branching ~35: 35^4 = 1,500,625 nodes
    # - Leaf nodes = 35^3 = 42,875 (only these are evaluated)
    # - So ~3% of nodes are evaluated at depth 4
    
    # Different scenarios
    scenarios = [
        ("Depth 4 (3% evaluated)", 0.03),
        ("Depth 5 (0.8% evaluated)", 0.008),
        ("Depth 6 (0.02% evaluated)", 0.0002),
        ("Quiescence (50% evaluated)", 0.50),
        ("Average (10% evaluated)", 0.10),
    ]
    
    print("=" * 70)
    print("NPS Estimates by Scenario")
    print("=" * 70)
    print()
    
    for name, eval_ratio in scenarios:
        # Time per node = move generation + (evaluation * ratio)
        time_per_node_us = time_per_move_gen_us + (time_per_eval_us * eval_ratio)
        nps = 1e6 / time_per_node_us
        slowdown = perft_nps / nps
        
        print(f"{name}")
        print(f"  Evaluation ratio: {eval_ratio * 100:.2f}%")
        print(f"  Time per node: {time_per_node_us:.2f} μs")
        print(f"  **NPS: {nps:,.0f}**")
        print(f"  Slowdown: {slowdown:.2f}x")
        print()
    
    # Depth reachable in 1 second
    print("=" * 70)
    print("Depth Reachable in 1 Second (10% eval ratio)")
    print("=" * 70)
    print()
    
    eval_ratio = 0.10
    time_per_node_us = time_per_move_gen_us + (time_per_eval_us * eval_ratio)
    nps = 1e6 / time_per_node_us
    
    branching_factor = 35
    
    for depth in range(1, 9):
        # Interior nodes = 1 + b + b^2 + ... + b^(d-1) = (b^d - 1)/(b - 1)
        interior_nodes = (branching_factor ** depth - 1) // (branching_factor - 1)
        leaf_nodes = branching_factor ** depth
        total_nodes = interior_nodes + leaf_nodes
        
        time_needed = total_nodes / nps
        
        status = "✓" if time_needed <= 1.0 else "✗"
        print(f"  Depth {depth}: {total_nodes:>14,} nodes in {time_needed:>8.3f}s {status}")
        
        if time_needed > 60:
            break
    
    print()
    return nps


def quick_component_timing():
    """Quick timing of each component."""
    print("=" * 70)
    print("COMPONENT TIMING")
    print("=" * 70)
    print()
    
    # Create test position
    pos = new_game()
    for _ in range(15):
        moves = pos.legal_moves()
        if moves:
            pos.make_move(random.choice(moves))
    
    board = pos._board
    evaluator = Evaluator()
    
    # Warm up
    for _ in range(1000):
        evaluator.evaluate(board)
    
    # Time each component
    iterations = 10000
    
    components = {
        'Material': lambda: evaluator._evaluate_material(board),
        'PSQT': lambda: evaluator._evaluate_psqt(board),
        'Phase': lambda: evaluator._calculate_phase(board),
        'Pawn Structure': lambda: evaluator._evaluate_pawn_structure(board),
        'King Safety': lambda: evaluator._evaluate_king_safety(board, 128),
        'Mobility': lambda: evaluator._evaluate_mobility(board, 128),
        'Full Eval': lambda: evaluator.evaluate(board),
    }
    
    print(f"Timing {iterations:,} iterations per component...")
    print()
    
    results = {}
    for name, func in components.items():
        start = time.perf_counter()
        for _ in range(iterations):
            func()
        elapsed = time.perf_counter() - start
        avg_us = (elapsed / iterations) * 1e6
        results[name] = avg_us
        print(f"{name:<20} {avg_us:>8.2f} μs")
    
    print()
    print("Percentage breakdown:")
    full_eval_time = results['Full Eval']
    
    for name in ['Material', 'PSQT', 'Phase', 'Pawn Structure', 'King Safety', 'Mobility']:
        if name in results:
            percentage = (results[name] / full_eval_time) * 100
            print(f"{name:<20} {percentage:>6.1f}%")
    
    print()


if __name__ == "__main__":
    quick_component_timing()
    print()
    estimate_search_nps()
