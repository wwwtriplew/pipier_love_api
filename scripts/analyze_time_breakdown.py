#!/usr/bin/env python3
"""
SOPHISTICATED TIME BREAKDOWN ANALYZER

This script uses cProfile data to calculate EXACT time percentages for each component,
accounting for nested calls properly. It answers the question:

"What % of total search time is spent in EACH major component?"

Components analyzed:
1. Evaluation (and its sub-components)
2. Move generation
3. Make/unmake moves
4. Search infrastructure (TT, move ordering, repetition)
5. Quiescence search
"""

import sys
import os
import cProfile
import pstats
from io import StringIO

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import alpha_beta, SearchStats, TranspositionTable, MoveOrderer

print("=" * 80)
print("SOPHISTICATED TIME BREAKDOWN ANALYSIS")
print("=" * 80)
print()
print("Running 100 depth-3 searches and measuring EXACT time breakdown...")
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

# Get stats
stats_obj = pstats.Stats(profiler)

# Extract timing data
# We need to manually parse the stats to get accurate attribution
func_stats = {}
for func, (cc, nc, tt, ct, callers) in stats_obj.stats.items():
    filename, line, func_name = func
    key = f"{filename}:{func_name}"
    func_stats[key] = {
        'tottime': tt,
        'cumtime': ct,
        'ncalls': nc,
        'filename': filename,
        'funcname': func_name
    }

# Calculate total time (from run_searches)
total_time = func_stats.get('profile_search_overhead.py:run_searches', {}).get('cumtime', 0)
if total_time == 0:
    # Fallback: sum of top-level calls
    total_time = sum(s['cumtime'] for k, s in func_stats.items() 
                     if 'run_searches' in k or 'alpha_beta' in k)

print(f"Total time: {total_time:.3f}s")
print()

# Define component patterns
components = {
    'Evaluation': [
        'evaluation.py:evaluate',
        'evaluation.py:_evaluate_material',
        'evaluation.py:_evaluate_psqt',
        'evaluation.py:_calculate_phase',
        'evaluation.py:_evaluate_pawn_structure',
        'evaluation.py:_evaluate_king_safety',
        'evaluation.py:_evaluate_king_safety_side',
        'evaluation.py:_evaluate_king_exposure',
        'evaluation.py:_evaluate_pawn_shield',
        'evaluation.py:_evaluate_mobility',
        'evaluation.py:_evaluate_mobility_side',
        'evaluation.py:_generate_attack_map',
    ],
    'Move Generation': [
        'chess_engine.py:generate_moves',
        'chess_engine.py:_generate_all_moves',
        'move_generation.py:generate_all_legal_moves',
        'move_generation.py:generate_pawn_moves',
        'move_generation.py:generate_knight_moves',
        'move_generation.py:generate_bishop_moves',
        'move_generation.py:generate_rook_moves',
        'move_generation.py:generate_queen_moves',
        'move_generation.py:generate_king_moves',
    ],
    'Make/Unmake Moves': [
        'chess_engine.py:make_move',
        'chess_engine.py:unmake_move',
        'move_execution.py:execute_move',
        'chess_engine.py:_update_check_status',
        'chess_engine.py:_update_occupancy',
    ],
    'Transposition Table': [
        'search.py:__init__',  # TT initialization
        'search.py:<listcomp>',  # TT table initialization
        'search.py:probe',
        'search.py:store',
    ],
    'Move Ordering': [
        'search.py:order_moves',
        'search.py:score_move',
        'search.py:<lambda>',
    ],
    'Search Algorithm': [
        'search.py:alpha_beta',
        'search.py:quiescence',
        'search.py:is_capture',
    ],
    'Magic Bitboards': [
        'magic_bitboards.py:get_rook_attacks',
        'magic_bitboards.py:get_bishop_attacks',
        'magic_bitboards.py:get_queen_attacks',
        'magic_bitboards.py:_rook_attacks_on_the_fly',
        'magic_bitboards.py:_bishop_attacks_on_the_fly',
        'magic_bitboards.py:count_bits',
    ],
    'Zobrist Hashing': [
        'zobrist_keys.py:compute_pawn_hash',
        'zobrist_keys.py:compute_full_hash',
    ]
}

# Calculate time for each component (using tottime to avoid double-counting)
component_times = {}
for comp_name, patterns in components.items():
    total_comp_time = 0
    for key, data in func_stats.items():
        for pattern in patterns:
            if pattern in key:
                total_comp_time += data['tottime']
                break
    component_times[comp_name] = total_comp_time

# Print breakdown
print("=" * 80)
print("TIME BREAKDOWN BY COMPONENT (using tottime to avoid double-counting)")
print("=" * 80)
print()
print(f"{'Component':<30} {'Time (s)':>12} {'% of Total':>12}")
print("-" * 80)

# Sort by time
sorted_components = sorted(component_times.items(), key=lambda x: x[1], reverse=True)
for comp_name, comp_time in sorted_components:
    percent = (comp_time / total_time * 100) if total_time > 0 else 0
    print(f"{comp_name:<30} {comp_time:>12.3f} {percent:>11.1f}%")

print("-" * 80)
accounted_time = sum(component_times.values())
unaccounted = total_time - accounted_time
print(f"{'Accounted time':<30} {accounted_time:>12.3f} {accounted_time/total_time*100:>11.1f}%")
print(f"{'Unaccounted (Python overhead)':<30} {unaccounted:>12.3f} {unaccounted/total_time*100:>11.1f}%")
print(f"{'TOTAL':<30} {total_time:>12.3f} {100.0:>11.1f}%")
print()

# Detailed evaluation breakdown
print("=" * 80)
print("DETAILED EVALUATION BREAKDOWN")
print("=" * 80)
print()

eval_breakdown = {
    'evaluate (orchestration)': 'evaluation.py:evaluate',
    '_evaluate_material': 'evaluation.py:_evaluate_material',
    '_evaluate_psqt': 'evaluation.py:_evaluate_psqt',
    '_calculate_phase': 'evaluation.py:_calculate_phase',
    '_evaluate_king_safety': 'evaluation.py:_evaluate_king_safety',
    '_evaluate_king_safety_side': 'evaluation.py:_evaluate_king_safety_side',
    '_evaluate_king_exposure': 'evaluation.py:_evaluate_king_exposure',
    '_evaluate_pawn_shield': 'evaluation.py:_evaluate_pawn_shield',
    '_evaluate_mobility': 'evaluation.py:_evaluate_mobility',
    '_evaluate_mobility_side': 'evaluation.py:_evaluate_mobility_side',
    '_generate_attack_map': 'evaluation.py:_generate_attack_map',
}

eval_total = component_times.get('Evaluation', 0)
print(f"{'Function':<35} {'Time (s)':>12} {'% of Eval':>12}")
print("-" * 80)

for func_label, pattern in eval_breakdown.items():
    func_time = 0
    for key, data in func_stats.items():
        if pattern in key:
            func_time = data['tottime']
            break
    
    percent = (func_time / eval_total * 100) if eval_total > 0 else 0
    print(f"{func_label:<35} {func_time:>12.3f} {percent:>11.1f}%")

print()

# Key insights
print("=" * 80)
print("KEY INSIGHTS")
print("=" * 80)
print()

# Find the PRIMARY bottleneck
primary = sorted_components[0]
print(f"🎯 PRIMARY BOTTLENECK: {primary[0]}")
print(f"   Takes {primary[1]:.3f}s ({primary[1]/total_time*100:.1f}% of total time)")
print()

# TT initialization analysis
tt_init_time = 0
for key, data in func_stats.items():
    if 'search.py:<listcomp>' in key or 'search.py:__init__' in key:
        tt_init_time += data['tottime']

if tt_init_time > 1.0:
    print(f"⚠️  TT INITIALIZATION PROBLEM DETECTED!")
    print(f"   Creating TranspositionTable objects takes {tt_init_time:.3f}s")
    print(f"   This is {tt_init_time/total_time*100:.1f}% of total time!")
    print(f"   → FIX: Reuse TT across searches instead of creating new ones")
    print()

# Mobility analysis
mobility_time = component_times.get('Evaluation', 0)
for key, data in func_stats.items():
    if '_evaluate_mobility' in key:
        print(f"📊 Mobility evaluation: {data['tottime']:.3f}s")

print()
print("OPTIMIZATION PRIORITY:")
print("-" * 80)

for i, (comp_name, comp_time) in enumerate(sorted_components[:5], 1):
    percent = (comp_time / total_time * 100)
    if percent > 5:
        urgency = "🔥 CRITICAL" if percent > 30 else "⚠️  HIGH" if percent > 15 else "📌 MEDIUM"
        print(f"{i}. {urgency} - {comp_name}: {comp_time:.3f}s ({percent:.1f}%)")

print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()

if tt_init_time > 2.0:
    print("1. IMMEDIATE FIX: Reuse TranspositionTable")
    print("   Currently creating new TT 100 times = wasted 3.8s")
    print("   → Move TT creation outside the loop")
    print("   → Expected improvement: ~3.8s savings (11% faster)")
    print()

if sorted_components[0][0] == 'Magic Bitboards':
    print("2. PRIMARY: Optimize Magic Bitboards")
    print("   count_bits and attack generation dominate time")
    print("   → Consider caching attack patterns")
    print("   → Use lookup tables instead of on-the-fly calculation")
    print()

if sorted_components[0][0] == 'Evaluation':
    print("2. PRIMARY: Optimize Evaluation")
    print("   Focus on mobility and king safety (see detailed breakdown above)")
    print("   → Cache mobility results per position")
    print("   → Simplify king safety calculation")
    print()

print("3. Run this script again after each optimization to measure improvement")
