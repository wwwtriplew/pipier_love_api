#!/usr/bin/env python3
"""
DEFINITIVE TEST: Real Game Environment Simulation

Simulates actual production conditions:
- 12 second thinking time (your production setting)
- Proper PyPy JIT warmup (simulates warmed-up production server)
- Multiple positions tested (opening, middlegame, endgame)
- Measures WARM performance (what users actually experience)

This answers: What is the ACTUAL performance difference in production?
"""

import sys
import time
from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import TranspositionTable, MoveOrderer, SearchStats, iterative_deepening

# Real game positions at different stages
GAME_POSITIONS = [
    ("Opening - Move 4", "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"),
    ("Opening - Italian", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"),
    ("Early Middlegame", "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 5"),
    ("Middlegame", "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 9"),
    ("Complex Middlegame", "2rq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP2QPPP/R1BR2K1 w - - 0 12"),
    ("Tactical", "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
]

THINKING_TIME_MS = 12000  # 12 seconds - your production setting

def warmup_engine():
    """
    Warm up PyPy JIT before testing.
    Simulates production server that has already handled requests.
    """
    print("🔥 Warming up PyPy JIT (simulating production server state)...")
    
    evaluator = Evaluator()
    orderer = MoveOrderer()
    stats = SearchStats()
    
    # Run several searches to warm up JIT
    warmup_positions = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    ]
    
    for fen in warmup_positions:
        board = ChessBoard()
        board.setup_from_fen(fen)
        
        # Warmup with TT
        tt = TranspositionTable(size_mb=64)
        for _ in range(3):  # 3 searches per position
            iterative_deepening(board, 1000, 50, evaluator, tt, orderer, stats)
            board.setup_from_fen(fen)  # Reset
        
        # Warmup without TT
        for _ in range(3):
            iterative_deepening(board, 1000, 50, evaluator, None, orderer, stats)
            board.setup_from_fen(fen)  # Reset
    
    print("✓ JIT warmup complete - engine at production temperature\n")

def run_search(board, time_ms, tt, config_name):
    """Run one search and collect comprehensive stats"""
    # Reuse evaluator and orderer (like production after warmup)
    evaluator = Evaluator()
    orderer = MoveOrderer()
    stats = SearchStats()
    
    start = time.time()
    best_move, score, pv = iterative_deepening(
        board, time_ms, 50,  # max_depth=50 like production
        evaluator, tt, orderer, stats
    )
    elapsed = time.time() - start
    
    return {
        'move': best_move,
        'score': score,
        'pv': pv,
        'nodes': stats.nodes,
        'time_ms': int(elapsed * 1000),
        'nps': int(stats.nodes / elapsed) if elapsed > 0 else 0,
    }

def main():
    print("=" * 90)
    print("DEFINITIVE TEST: Real Game Environment")
    print("Configuration: 12 second thinking time, PyPy JIT warmed up")
    print("=" * 90)
    
    # Warmup first (simulates production server state)
    warmup_engine()
    
    # Results storage
    all_results = []
    
    # Test each position
    for pos_name, fen in GAME_POSITIONS:
        print(f"\n{'='*90}")
        print(f"Position: {pos_name}")
        print(f"FEN: {fen}")
        print(f"{'='*90}")
        
        board = ChessBoard()
        board.setup_from_fen(fen)
        
        # Test 1: WITH TT (1GB - production config)
        print(f"\n[1/2] WITH TT (1GB - PRODUCTION CONFIG)...")
        print(f"      Searching for {THINKING_TIME_MS/1000:.0f} seconds...")
        tt_1gb = TranspositionTable(size_mb=1024)
        result_with = run_search(board, THINKING_TIME_MS, tt_1gb, "WITH-TT")
        print(f"      Complete: {result_with['nodes']:,} nodes in {result_with['time_ms']:,}ms = {result_with['nps']:,} NPS")
        
        # Test 2: WITHOUT TT
        print(f"\n[2/2] WITHOUT TT...")
        print(f"      Searching for {THINKING_TIME_MS/1000:.0f} seconds...")
        board.setup_from_fen(fen)  # Reset
        result_without = run_search(board, THINKING_TIME_MS, None, "WITHOUT-TT")
        print(f"      Complete: {result_without['nodes']:,} nodes in {result_without['time_ms']:,}ms = {result_without['nps']:,} NPS")
        
        # Calculate improvement
        improvement = ((result_without['nps'] / result_with['nps']) - 1) * 100
        speedup = result_without['nps'] / result_with['nps']
        
        # Store results
        all_results.append({
            'position': pos_name,
            'with_tt': result_with,
            'without_tt': result_without,
            'improvement': improvement,
            'speedup': speedup,
        })
        
        # Display results for this position
        print(f"\n{'='*90}")
        print(f"RESULTS for {pos_name}:")
        print(f"{'='*90}")
        print(f"{'Config':<25} {'Nodes':<15} {'Time(ms)':<12} {'NPS':<15} {'Move':<10}")
        print("-" * 90)
        
        move_with = str(result_with['move']) if result_with['move'] else "None"
        move_without = str(result_without['move']) if result_without['move'] else "None"
        
        print(f"{'WITH TT (1GB)':<25} {result_with['nodes']:<15,} {result_with['time_ms']:<12,} "
              f"{result_with['nps']:<15,} {move_with:<10}")
        print(f"{'WITHOUT TT':<25} {result_without['nodes']:<15,} {result_without['time_ms']:<12,} "
              f"{result_without['nps']:<15,} {move_without:<10}")
        
        print("\n" + "="*90)
        print("ANALYSIS:")
        print("="*90)
        
        if improvement > 5:
            print(f"🔥 WITHOUT TT is {improvement:.1f}% FASTER ({speedup:.2f}x speedup)")
            print(f"   WITHOUT TT: {result_without['nps']:,} NPS")
            print(f"   WITH TT:    {result_with['nps']:,} NPS")
            print(f"   → Searched {result_without['nodes'] - result_with['nodes']:,} MORE nodes in same time")
        elif improvement < -5:
            print(f"⚠ WITH TT is {-improvement:.1f}% FASTER")
            print(f"   WITH TT:    {result_with['nps']:,} NPS")
            print(f"   WITHOUT TT: {result_without['nps']:,} NPS")
        else:
            print(f"≈ No significant difference ({improvement:+.1f}%)")
        
        # Move comparison
        if result_with['move'] == result_without['move']:
            print(f"✓ Both found SAME move: {result_with['move']}")
        else:
            print(f"⚠ DIFFERENT moves:")
            print(f"   WITH TT:    {result_with['move']} (score: {result_with['score']})")
            print(f"   WITHOUT TT: {result_without['move']} (score: {result_without['score']})")
    
    # Overall summary
    print("\n" + "="*90)
    print("OVERALL SUMMARY")
    print("="*90)
    
    avg_improvement = sum(r['improvement'] for r in all_results) / len(all_results)
    avg_speedup = sum(r['speedup'] for r in all_results) / len(all_results)
    
    print(f"\nTested {len(GAME_POSITIONS)} positions with {THINKING_TIME_MS/1000:.0f}-second thinking time:\n")
    
    for r in all_results:
        status = "🔥" if r['improvement'] > 5 else "≈"
        print(f"{status} {r['position']:<25} WITHOUT TT: {r['improvement']:+6.1f}% ({r['speedup']:.2f}x)")
    
    print(f"\n{'='*90}")
    print(f"AVERAGE PERFORMANCE:")
    print(f"{'='*90}")
    print(f"Average improvement: {avg_improvement:+.1f}%")
    print(f"Average speedup: {avg_speedup:.2f}x")
    
    if avg_improvement > 10:
        print(f"\n{'='*90}")
        print("✅ RECOMMENDATION: REMOVE TT from production")
        print(f"{'='*90}")
        print(f"Expected benefit:")
        print(f"  - {avg_improvement:.1f}% faster search")
        print(f"  - {avg_speedup:.2f}x more nodes searched per second")
        print(f"  - Simpler code (PyPy JIT optimizes better)")
        print(f"  - -1GB memory per request")
        print(f"  - API response time: {THINKING_TIME_MS}ms → ~{int(THINKING_TIME_MS/avg_speedup)}ms")
    elif avg_improvement < -10:
        print(f"\n{'='*90}")
        print("✅ RECOMMENDATION: KEEP TT")
        print(f"{'='*90}")
        print(f"TT provides {-avg_improvement:.1f}% performance benefit")
    else:
        print(f"\n{'='*90}")
        print("≈ RECOMMENDATION: Marginal difference")
        print(f"{'='*90}")
        print(f"Consider removing TT for:")
        print(f"  - Simpler code")
        print(f"  - Better memory efficiency (-1GB per request)")
    
    print(f"\n{'='*90}")

if __name__ == "__main__":
    main()
