#!/usr/bin/env python3
"""
Test WITH vs WITHOUT TT at PRODUCTION configuration:
- 1000ms time limit (not fixed depth)
- Let iterative deepening reach natural depth
- Use BOTH 64MB and 1GB TT sizes

This answers:
1. Does larger TT (1GB) improve hit rate?
2. Does TT help at production depths (7-9)?
3. Are moves equally good?
"""

import sys
import time
from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import TranspositionTable, MoveOrderer, SearchStats, iterative_deepening

# Test positions: opening, middlegame, tactical
TEST_POSITIONS = [
    ("Opening", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("Italian", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"),
    ("Middlegame", "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 9"),
]

def run_search(board, time_ms, tt, name):
    """Run one search and return stats"""
    evaluator = Evaluator()
    orderer = MoveOrderer()
    stats = SearchStats()
    
    start = time.time()
    best_move, score, pv = iterative_deepening(
        board, time_ms, 50,  # max_depth=50 like production
        evaluator, tt, orderer, stats
    )
    elapsed = time.time() - start
    
    # Calculate final depth reached
    final_depth = 1
    for d in range(1, 51):
        if stats.nodes < (10 ** d):  # Rough heuristic
            break
        final_depth = d
    
    return {
        'move': best_move,
        'score': score,
        'depth': final_depth,
        'nodes': stats.nodes,
        'time_ms': int(elapsed * 1000),
        'nps': int(stats.nodes / elapsed) if elapsed > 0 else 0,
    }

def main():
    print("=" * 80)
    print("PRODUCTION DEPTH TEST: WITH vs WITHOUT TT")
    print("Configuration: 1000ms time limit, natural depth (iterative deepening)")
    print("=" * 80)
    
    for pos_name, fen in TEST_POSITIONS:
        print(f"\n{'='*80}")
        print(f"Position: {pos_name}")
        print(f"FEN: {fen}")
        print(f"{'='*80}")
        
        board = ChessBoard()
        board.setup_from_fen(fen)
        
        # Test 1: WITH TT (64MB) - original test size
        print("\n[1/3] WITH TT (64MB)...")
        tt_64 = TranspositionTable(size_mb=64)
        result_64 = run_search(board, 1000, tt_64, "TT-64MB")
        
        # Test 2: WITH TT (1GB) - production size
        print("[2/3] WITH TT (1024MB - PRODUCTION SIZE)...")
        board.setup_from_fen(fen)  # Reset
        tt_1gb = TranspositionTable(size_mb=1024)
        result_1gb = run_search(board, 1000, tt_1gb, "TT-1GB")
        
        # Test 3: WITHOUT TT
        print("[3/3] WITHOUT TT...")
        board.setup_from_fen(fen)  # Reset
        result_none = run_search(board, 1000, None, "NO-TT")
        
        # Display results
        print(f"\n{'='*80}")
        print(f"RESULTS for {pos_name}:")
        print(f"{'='*80}")
        print(f"{'Config':<20} {'Depth':<8} {'Nodes':<12} {'Time(ms)':<10} {'NPS':<12} {'Move':<8}")
        print("-" * 80)
        
        for name, res in [("WITH TT (64MB)", result_64), 
                          ("WITH TT (1GB)", result_1gb), 
                          ("WITHOUT TT", result_none)]:
            move_str = f"{res['move']}" if res['move'] else "None"
            print(f"{name:<20} {res['depth']:<8} {res['nodes']:<12,} "
                  f"{res['time_ms']:<10} {res['nps']:<12,} {move_str:<8}")
        
        # Analysis
        print("\n" + "="*80)
        print("ANALYSIS:")
        print("="*80)
        
        # Compare 64MB vs 1GB TT
        if result_1gb['nps'] > result_64['nps'] * 1.05:
            print(f"✓ 1GB TT is {result_1gb['nps']/result_64['nps']:.1f}x faster than 64MB TT")
            print(f"  → Larger TT improves hit rate at this depth")
        elif result_64['nps'] > result_1gb['nps'] * 1.05:
            print(f"⚠ 64MB TT is {result_64['nps']/result_1gb['nps']:.1f}x faster than 1GB TT")
            print(f"  → Larger TT adds overhead without benefit")
        else:
            print(f"≈ TT size doesn't matter much (within 5%)")
        
        # Compare best TT vs NO TT
        best_tt_nps = max(result_64['nps'], result_1gb['nps'])
        best_tt_name = "64MB" if result_64['nps'] > result_1gb['nps'] else "1GB"
        
        if result_none['nps'] > best_tt_nps * 1.05:
            improvement = (result_none['nps'] / best_tt_nps - 1) * 100
            print(f"\n🔥 WITHOUT TT is {improvement:.1f}% faster than best TT ({best_tt_name})")
            print(f"   WITHOUT TT: {result_none['nps']:,} NPS")
            print(f"   WITH TT:    {best_tt_nps:,} NPS")
            print(f"   → TT is OVERHEAD at production depth")
        elif best_tt_nps > result_none['nps'] * 1.05:
            improvement = (best_tt_nps / result_none['nps'] - 1) * 100
            print(f"\n✓ WITH TT ({best_tt_name}) is {improvement:.1f}% faster than WITHOUT TT")
            print(f"   WITH TT:    {best_tt_nps:,} NPS")
            print(f"   WITHOUT TT: {result_none['nps']:,} NPS")
            print(f"   → TT is BENEFICIAL at production depth")
        else:
            print(f"\n≈ TT vs NO-TT: No significant difference (within 5%)")
        
        # Move comparison
        if result_64['move'] == result_1gb['move'] == result_none['move']:
            print(f"\n✓ All configurations found SAME move: {result_64['move']}")
        else:
            print(f"\n⚠ DIFFERENT moves found:")
            print(f"   TT-64MB:  {result_64['move']}")
            print(f"   TT-1GB:   {result_1gb['move']}")
            print(f"   NO-TT:    {result_none['move']}")
    
    print("\n" + "="*80)
    print("OVERALL CONCLUSION:")
    print("="*80)
    print("Based on these results:")
    print("1. If WITHOUT TT consistently faster → REMOVE TT from production")
    print("2. If 1GB TT faster than 64MB → Keep TT but tune size")
    print("3. If moves differ → Need deeper analysis of move quality")
    print("="*80)

if __name__ == "__main__":
    main()
