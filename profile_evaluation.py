#!/usr/bin/env python3
"""
Detailed profiling of evaluation function.

Measures:
- Overall evaluation time
- Time per component (material, PSQT, pawn, king safety, mobility)
- Cache hit rates
- Evaluations per second
- Estimate of True NPS (with evaluation in search)
"""

import sys
import time
from typing import Dict, List
from collections import defaultdict

sys.path.insert(0, 'src')

from board_state import new_game, from_fen
from evaluation import Evaluator
from chess_engine import ChessBoard


class DetailedProfiler:
    """Detailed profiler for evaluation function."""
    
    def __init__(self):
        self.component_times = defaultdict(float)
        self.component_calls = defaultdict(int)
        self.total_evals = 0
        self.total_time = 0.0
    
    def reset(self):
        """Reset all statistics."""
        self.component_times.clear()
        self.component_calls.clear()
        self.total_evals = 0
        self.total_time = 0.0
    
    def profile_evaluation(self, evaluator: Evaluator, board: ChessBoard) -> int:
        """
        Profile a single evaluation with component timing.
        
        Returns:
            Evaluation score
        """
        start_total = time.perf_counter()
        
        # Manually call each component to measure timing
        phase = evaluator._calculate_phase(board)
        
        # 1. Material
        t0 = time.perf_counter()
        material = evaluator._evaluate_material(board)
        self.component_times['material'] += time.perf_counter() - t0
        self.component_calls['material'] += 1
        
        # 2. PSQT (non-pawns)
        t0 = time.perf_counter()
        mg_psqt, eg_psqt = evaluator._evaluate_psqt(board)
        self.component_times['psqt'] += time.perf_counter() - t0
        self.component_calls['psqt'] += 1
        
        # 3. Pawn structure (with hash probe)
        t0 = time.perf_counter()
        pawn_entry = evaluator.pawn_hash_table.probe(board.pawn_hash)
        if pawn_entry is None:
            mg_pawn, eg_pawn, mg_pawn_psqt, eg_pawn_psqt = evaluator._evaluate_pawn_structure(board)
            evaluator.pawn_hash_table.store(board.pawn_hash, mg_pawn, eg_pawn, mg_pawn_psqt, eg_pawn_psqt)
        self.component_times['pawn'] += time.perf_counter() - t0
        self.component_calls['pawn'] += 1
        
        # 4. King safety
        t0 = time.perf_counter()
        mg_king_safety = evaluator._evaluate_king_safety(board, phase)
        self.component_times['king_safety'] += time.perf_counter() - t0
        self.component_calls['king_safety'] += 1
        
        # 5. Mobility
        t0 = time.perf_counter()
        mg_mob, eg_mob = evaluator._evaluate_mobility(board, phase)
        self.component_times['mobility'] += time.perf_counter() - t0
        self.component_calls['mobility'] += 1
        
        # Now call the actual evaluator to get the score
        score = evaluator.evaluate(board)
        
        self.total_time += time.perf_counter() - start_total
        self.total_evals += 1
        
        return score
    
    def print_report(self):
        """Print detailed profiling report."""
        print("=" * 70)
        print("DETAILED EVALUATION PROFILING")
        print("=" * 70)
        print()
        
        print(f"Total evaluations: {self.total_evals:,}")
        print(f"Total time: {self.total_time:.3f}s")
        print(f"Average time per eval: {self.total_time / self.total_evals * 1e6:.1f} μs")
        print()
        
        print("Component Breakdown:")
        print("-" * 70)
        print(f"{'Component':<20} {'Time (ms)':<12} {'%':<8} {'Avg (μs)':<12}")
        print("-" * 70)
        
        components = ['material', 'psqt', 'pawn', 'king_safety', 'mobility']
        for comp in components:
            if comp in self.component_times:
                comp_time = self.component_times[comp]
                percentage = (comp_time / self.total_time) * 100
                avg_us = (comp_time / self.component_calls[comp]) * 1e6
                print(f"{comp:<20} {comp_time * 1000:>10.2f}  {percentage:>6.1f}%  {avg_us:>10.1f}")
        
        print()


def generate_test_positions(count: int = 100) -> List[ChessBoard]:
    """Generate diverse test positions."""
    import random
    
    positions = []
    
    # Starting position
    pos = new_game()
    positions.append(pos._board)
    
    # Generate positions from random games
    for _ in range(count - 1):
        pos = new_game()
        moves_played = 0
        max_moves = random.randint(10, 40)
        
        while moves_played < max_moves and not pos.is_game_over:
            legal_moves = pos.legal_moves()
            if not legal_moves:
                break
            
            move = random.choice(legal_moves)
            pos.make_move(move)
            moves_played += 1
        
        positions.append(pos._board)
    
    return positions


def benchmark_evaluations_per_second():
    """Benchmark evaluations per second with PyPy."""
    print("=" * 70)
    print("EVALUATIONS PER SECOND BENCHMARK")
    print("=" * 70)
    print()
    
    # Generate test positions
    print("Generating test positions...")
    positions = generate_test_positions(100)
    print(f"✅ Generated {len(positions)} positions")
    print()
    
    # Create evaluator
    evaluator = Evaluator()
    
    # Warm-up (especially important for PyPy JIT)
    print("Warming up JIT...")
    for _ in range(3):
        for board in positions[:20]:
            evaluator.evaluate(board)
    print("✅ Warm-up complete")
    print()
    
    # Benchmark
    print("Benchmarking...")
    test_duration = 5.0  # seconds
    evals_done = 0
    start_time = time.perf_counter()
    
    while time.perf_counter() - start_time < test_duration:
        for board in positions:
            evaluator.evaluate(board)
            evals_done += 1
    
    elapsed = time.perf_counter() - start_time
    evals_per_sec = evals_done / elapsed
    
    print(f"Evaluations: {evals_done:,}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Evaluations/sec: {evals_per_sec:,.0f}")
    print()
    
    # Get cache stats
    stats = evaluator.get_stats()
    pawn_stats = stats['pawn_hash']
    
    print("Cache Statistics:")
    print(f"  Pawn hash hits: {pawn_stats['hits']:,}")
    print(f"  Pawn hash misses: {pawn_stats['misses']:,}")
    print(f"  Hit rate: {pawn_stats['hit_rate']:.1f}%")
    print()
    
    return evals_per_sec


def detailed_component_profiling():
    """Profile each evaluation component in detail."""
    print("=" * 70)
    print("COMPONENT-LEVEL PROFILING")
    print("=" * 70)
    print()
    
    # Generate test positions
    print("Generating test positions...")
    positions = generate_test_positions(100)
    print(f"✅ Generated {len(positions)} positions")
    print()
    
    # Create evaluator and profiler
    evaluator = Evaluator()
    profiler = DetailedProfiler()
    
    # Warm-up
    print("Warming up JIT...")
    for board in positions[:20]:
        evaluator.evaluate(board)
    print("✅ Warm-up complete")
    print()
    
    # Profile
    print("Profiling components...")
    for board in positions:
        profiler.profile_evaluation(evaluator, board)
    
    profiler.print_report()
    
    return profiler


def estimate_true_nps():
    """
    Estimate True NPS (nodes per second with evaluation).
    
    Combines:
    - Move generation NPS (from perft)
    - Evaluation time
    To estimate search NPS
    """
    print("=" * 70)
    print("TRUE NPS ESTIMATION")
    print("=" * 70)
    print()
    
    # Known perft NPS (from benchmark_pypy.py)
    perft_nps = 459000  # Average PyPy NPS from perft
    print(f"Move generation NPS (perft): {perft_nps:,}")
    
    # Benchmark evaluations per second
    evals_per_sec = benchmark_evaluations_per_second()
    print(f"Evaluations per second: {evals_per_sec:,.0f}")
    print()
    
    # Calculate time per operation
    time_per_move_gen = 1.0 / perft_nps  # seconds
    time_per_eval = 1.0 / evals_per_sec  # seconds
    
    print("Time per operation:")
    print(f"  Move generation: {time_per_move_gen * 1e6:.2f} μs")
    print(f"  Evaluation: {time_per_eval * 1e6:.2f} μs")
    print()
    
    # In alpha-beta search, we typically:
    # - Generate moves at each node
    # - Evaluate leaf positions
    # Assume 50% of nodes are leaf nodes (evaluated)
    # This is a rough estimate - actual depends on search depth and pruning
    
    evaluation_ratio = 0.5  # 50% of nodes are evaluated
    
    # Time per search node = move generation + (evaluation * ratio)
    time_per_node = time_per_move_gen + (time_per_eval * evaluation_ratio)
    
    true_nps = 1.0 / time_per_node
    
    print("Search Estimation:")
    print(f"  Assuming {evaluation_ratio * 100:.0f}% of nodes are evaluated")
    print(f"  Time per search node: {time_per_node * 1e6:.2f} μs")
    print(f"  **Estimated True NPS: {true_nps:,.0f}**")
    print()
    
    # Slowdown factor
    slowdown = perft_nps / true_nps
    print(f"Slowdown factor: {slowdown:.2f}x")
    print(f"(Search is {slowdown:.2f}x slower than pure move generation)")
    print()
    
    # Depth estimates
    print("Estimated depth in 1 second:")
    # Rough branching factor of 35
    branching_factor = 35
    
    for depth in range(1, 8):
        nodes = branching_factor ** depth
        time_needed = nodes / true_nps
        
        if time_needed <= 1.0:
            print(f"  Depth {depth}: {nodes:>12,} nodes in {time_needed:.3f}s ✓")
        else:
            print(f"  Depth {depth}: {nodes:>12,} nodes in {time_needed:.3f}s")
            if time_needed > 10:
                break
    
    return true_nps


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Profile evaluation function")
    parser.add_argument('--benchmark', action='store_true', help='Benchmark evals/sec')
    parser.add_argument('--components', action='store_true', help='Profile components')
    parser.add_argument('--truenps', action='store_true', help='Estimate true NPS')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    if args.all or not any([args.benchmark, args.components, args.truenps]):
        # Run everything
        detailed_component_profiling()
        print()
        estimate_true_nps()
    else:
        if args.components:
            detailed_component_profiling()
        if args.benchmark:
            benchmark_evaluations_per_second()
        if args.truenps:
            estimate_true_nps()
