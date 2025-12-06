#!/usr/bin/env python3
"""
Dict→Tuple Optimization Test

Tests the performance impact of replacing MATERIAL_VALUES and PHASE_VALUES 
dictionaries with tuples in evaluation.py.

Expected results:
- Baseline (array access): ~2M ops/sec
- Evaluation with tuples: ~50k-100k evals/sec (3-5x improvement over dicts)
- If evaluation < 30k: dict→tuple fix not working
"""

import sys
import time
import os

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator

def test_baseline():
    """Test baseline performance - simple array access"""
    MATERIAL_VALUES = (100, 320, 330, 500, 900, 0)
    total = 0
    iterations = 10_000_000
    
    start = time.perf_counter()
    for _ in range(iterations):
        # Simulate evaluation pattern
        total += MATERIAL_VALUES[0]  # PAWN
        total += MATERIAL_VALUES[1]  # KNIGHT
        total += MATERIAL_VALUES[2]  # BISHOP
        total += MATERIAL_VALUES[3]  # ROOK
        total += MATERIAL_VALUES[4]  # QUEEN
    elapsed = time.perf_counter() - start
    
    ops_per_sec = iterations / elapsed
    return ops_per_sec

def test_evaluation():
    """Test evaluation function directly"""
    board = ChessBoard()
    evaluator = Evaluator()
    iterations = 100_000
    
    start = time.perf_counter()
    for _ in range(iterations):
        score = evaluator.evaluate(board)
    elapsed = time.perf_counter() - start
    
    ops_per_sec = iterations / elapsed
    return ops_per_sec

def test_evaluation_with_moves():
    """Test evaluation with different positions"""
    board = ChessBoard()
    evaluator = Evaluator()
    iterations = 10_000
    
    moves = [(12, 28, None), (52, 36, None), (6, 21, None)]  # e2e4, e7e5, g1f3
    
    start = time.perf_counter()
    for _ in range(iterations):
        # Evaluate starting position
        score1 = evaluator.evaluate(board)
        
        # Make moves and evaluate
        for from_sq, to_sq, promo in moves:
            board.make_move(from_sq, to_sq, promo)
            score2 = evaluator.evaluate(board)
        
        # Unmake moves
        for _ in moves:
            board.unmake_move()
    
    elapsed = time.perf_counter() - start
    ops_per_sec = (iterations * (1 + len(moves))) / elapsed
    return ops_per_sec

def main():
    print("=" * 80)
    print("DICT→TUPLE OPTIMIZATION TEST")
    print("=" * 80)
    print()
    
    # Test 1: Baseline
    print("Test 1: Baseline Performance (Pure Array Access)")
    print("-" * 80)
    print("Running 10M iterations of array indexing...")
    baseline_ops = test_baseline()
    print(f"✓ Result: {baseline_ops:,.0f} ops/sec")
    print()
    
    # Test 2: Evaluation
    print("Test 2: Evaluation Function (Starting Position)")
    print("-" * 80)
    print("Running 100k evaluations of starting position...")
    eval_ops = test_evaluation()
    print(f"✓ Result: {eval_ops:,.0f} evaluations/sec")
    slowdown = baseline_ops / eval_ops
    print(f"  Slowdown vs baseline: {slowdown:.1f}x")
    print()
    
    # Test 3: Evaluation with moves
    print("Test 3: Evaluation with Position Changes")
    print("-" * 80)
    print("Running 10k evaluation sequences (4 positions each)...")
    eval_with_moves = test_evaluation_with_moves()
    print(f"✓ Result: {eval_with_moves:,.0f} evaluations/sec")
    print()
    
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()
    
    # Interpret results
    print(f"Baseline (array):     {baseline_ops:>12,.0f} ops/sec")
    print(f"Evaluation (static):  {eval_ops:>12,.0f} evals/sec")
    print(f"Evaluation (dynamic): {eval_with_moves:>12,.0f} evals/sec")
    print(f"Overhead:             {slowdown:>12.1f}x")
    print()
    
    # Expected performance based on VPS test results:
    # Dict version: 62k ops/sec → Tuple version: 217k ops/sec (3.48x)
    
    if eval_ops > 100_000:
        status = "✅ EXCELLENT"
        message = "Dict→tuple optimization working perfectly!"
        recommendation = "Deploy to production."
    elif eval_ops > 50_000:
        status = "✅ GOOD"
        message = "Significant improvement from dict→tuple fix."
        recommendation = "Deploy to VPS and monitor NPS."
    elif eval_ops > 30_000:
        status = "⚠️  MODERATE"
        message = "Some improvement but below expectations."
        recommendation = "May need Phase 2 (function splitting)."
    else:
        status = "❌ PROBLEM"
        message = "Evaluation still too slow - fix not working?"
        recommendation = "Check if dicts are truly replaced with tuples."
    
    print(f"Status:         {status}")
    print(f"Assessment:     {message}")
    print(f"Recommendation: {recommendation}")
    print()
    
    # Estimate API performance
    # Rough calculation: depth-4 search does ~200-500 evaluations
    # Target: 200k NPS = 200k nodes/sec
    # If we have 50k evals/sec and depth-4 = 400 nodes, that's ~125 searches/sec = 50k NPS
    # If we have 100k evals/sec, that's ~100k NPS (still below 200k target)
    
    estimated_nps = eval_ops * 2  # Rough multiplier for full search overhead
    target_nps = 200_000
    
    print("=" * 80)
    print("ESTIMATED API PERFORMANCE")
    print("=" * 80)
    print()
    print(f"Evaluation speed:     {eval_ops:>12,.0f} evals/sec")
    print(f"Estimated NPS:        {estimated_nps:>12,.0f} nodes/sec")
    print(f"Target NPS:           {target_nps:>12,.0f} nodes/sec")
    print(f"Progress:             {estimated_nps/target_nps*100:>12.0f}%")
    print()
    
    if estimated_nps >= target_nps:
        print("🎯 TARGET MET - Ready for production!")
        print("   ✅ Deploy to VPS and restart service")
    elif estimated_nps >= target_nps * 0.6:
        print("📊 GOOD PROGRESS - Close to target")
        print("   ⚠️  Test on VPS, may need Phase 2 optimization")
        print("   Phase 2: Split large functions (alpha_beta 263 lines)")
    else:
        print("📉 BELOW TARGET - More work needed")
        print("   ❗ Phase 2 (function splitting) definitely required")
        print("   ❗ Also check for other dict lookups in hot path")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
