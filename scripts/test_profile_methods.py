#!/usr/bin/env python3
"""
Test 3: Profile which sub-methods are slowest.
This identifies which methods to prioritize for optimization.
"""

import sys
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator

print("=" * 80)
print("TEST 3: Profile Individual Evaluation Methods")
print("=" * 80)
print()

board = ChessBoard()
evaluator = Evaluator()

# Warmup
print("Warming up...")
for _ in range(1000):
    evaluator.evaluate(board)
print()

# Profile each method
methods_to_test = [
    ('_calculate_phase', lambda: evaluator._calculate_phase(board)),
    ('_evaluate_material', lambda: evaluator._evaluate_material(board)),
    ('_evaluate_psqt', lambda: evaluator._evaluate_psqt(board)),
    ('_evaluate_king_safety', lambda: evaluator._evaluate_king_safety(board, 128)),
    ('_evaluate_mobility', lambda: evaluator._evaluate_mobility(board, 128)),
]

results = []

for method_name, method_func in methods_to_test:
    print(f"Profiling {method_name}...")
    print("-" * 80)
    
    # Test iterations (fewer for expensive methods)
    if 'mobility' in method_name or 'king_safety' in method_name:
        iterations = 10_000
    else:
        iterations = 100_000
    
    start = time.perf_counter()
    for _ in range(iterations):
        result = method_func()
    elapsed = time.perf_counter() - start
    
    ops_per_sec = iterations / elapsed
    time_per_call = (elapsed / iterations) * 1_000_000  # microseconds
    
    print(f"Time: {elapsed:.3f}s for {iterations:,} calls")
    print(f"Speed: {ops_per_sec:,.0f} calls/sec")
    print(f"Per-call: {time_per_call:.2f} μs")
    print()
    
    results.append((method_name, ops_per_sec, time_per_call))

# Now profile full evaluate()
print(f"Profiling full evaluate()...")
print("-" * 80)
iterations = 100_000

start = time.perf_counter()
for _ in range(iterations):
    result = evaluator.evaluate(board)
elapsed = time.perf_counter() - start

ops_per_sec = iterations / elapsed
time_per_call = (elapsed / iterations) * 1_000_000

print(f"Time: {elapsed:.3f}s for {iterations:,} calls")
print(f"Speed: {ops_per_sec:,.0f} calls/sec")
print(f"Per-call: {time_per_call:.2f} μs")
print()

results.append(('evaluate (FULL)', ops_per_sec, time_per_call))

# Analysis
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"{'Method':<30} {'Calls/sec':>15} {'μs/call':>12}")
print("-" * 80)

for method_name, ops, time_us in sorted(results, key=lambda x: x[1], reverse=True):
    print(f"{method_name:<30} {ops:>15,.0f} {time_us:>12.2f}")

print()
print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()

# Find slowest methods
sorted_by_speed = sorted(results[:-1], key=lambda x: x[1])  # Exclude full evaluate
slowest = sorted_by_speed[:3]

print("SLOWEST METHODS (highest overhead):")
for i, (method_name, ops, time_us) in enumerate(slowest, 1):
    print(f"{i}. {method_name}: {time_us:.2f} μs per call")

print()
print("PRIORITIZATION:")
print()

# Calculate what % of time each method takes
full_time = results[-1][2]  # Full evaluate time
print(f"Full evaluate() takes: {full_time:.2f} μs per call")
print()
print("If we optimize each method:")
for method_name, ops, time_us in sorted(results[:-1], key=lambda x: x[2], reverse=True):
    percent = (time_us / full_time) * 100
    print(f"  {method_name:<30} ~{percent:>5.1f}% of total time")

print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()

# Find methods worth inlining
high_overhead = [m for m in results[:-1] if m[2] < full_time / 5]  # Takes <20% of time but called
if high_overhead:
    print("✅ PRIORITY: Inline these fast but frequently-called methods:")
    for method_name, ops, time_us in high_overhead:
        print(f"   - {method_name} ({time_us:.2f} μs/call)")
    print("   → Small overhead per call × many calls = significant total")
else:
    print("⚠️  All methods have significant per-call cost")
    print("   → Inlining may not help much")

print()
print("Next steps:")
print("1. Focus optimization on slowest methods first")
print("2. Consider inlining methods with <5 μs per call")
print("3. Profile again after optimizations to verify improvement")
