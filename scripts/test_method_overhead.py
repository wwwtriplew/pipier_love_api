#!/usr/bin/env python3
"""
Test 2: Compare method call overhead vs inlined version.
This will prove if method calls are the bottleneck.
"""

import sys
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.chess_engine import ChessBoard, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
from src.magic_bitboards import count_bits as popcount

print("=" * 80)
print("TEST 2: Method Calls vs Inlined Code")
print("=" * 80)
print()

# Constants (same as in evaluation.py)
MATERIAL_VALUES = (100, 320, 330, 500, 900, 0)
PHASE_VALUES = (0, 1, 1, 2, 4, 0)
TOTAL_PHASE = 24

# Version A: With method calls (current pattern)
class MethodCallVersion:
    def evaluate(self, board):
        phase = self._calculate_phase(board)
        material = self._evaluate_material(board)
        return material  # Simplified - just return material
    
    def _calculate_phase(self, board):
        current_phase = 0
        for side in [WHITE, BLACK]:
            current_phase += popcount(board.pieces[side][KNIGHT]) * PHASE_VALUES[KNIGHT]
            current_phase += popcount(board.pieces[side][BISHOP]) * PHASE_VALUES[BISHOP]
            current_phase += popcount(board.pieces[side][ROOK]) * PHASE_VALUES[ROOK]
            current_phase += popcount(board.pieces[side][QUEEN]) * PHASE_VALUES[QUEEN]
        phase = 256 - (current_phase * 256 // TOTAL_PHASE)
        return max(0, min(phase, 256))
    
    def _evaluate_material(self, board):
        score = 0
        for piece_type in [PAWN, KNIGHT, BISHOP, ROOK, QUEEN]:
            count = popcount(board.pieces[WHITE][piece_type])
            score += count * MATERIAL_VALUES[piece_type]
        for piece_type in [PAWN, KNIGHT, BISHOP, ROOK, QUEEN]:
            count = popcount(board.pieces[BLACK][piece_type])
            score -= count * MATERIAL_VALUES[piece_type]
        return score

# Version B: Inlined (no method calls)
class InlinedVersion:
    def evaluate(self, board):
        # Inline _calculate_phase
        current_phase = 0
        for side in [WHITE, BLACK]:
            current_phase += popcount(board.pieces[side][KNIGHT]) * PHASE_VALUES[KNIGHT]
            current_phase += popcount(board.pieces[side][BISHOP]) * PHASE_VALUES[BISHOP]
            current_phase += popcount(board.pieces[side][ROOK]) * PHASE_VALUES[ROOK]
            current_phase += popcount(board.pieces[side][QUEEN]) * PHASE_VALUES[QUEEN]
        phase = 256 - (current_phase * 256 // TOTAL_PHASE)
        phase = max(0, min(phase, 256))
        
        # Inline _evaluate_material
        score = 0
        for piece_type in [PAWN, KNIGHT, BISHOP, ROOK, QUEEN]:
            count = popcount(board.pieces[WHITE][piece_type])
            score += count * MATERIAL_VALUES[piece_type]
        for piece_type in [PAWN, KNIGHT, BISHOP, ROOK, QUEEN]:
            count = popcount(board.pieces[BLACK][piece_type])
            score -= count * MATERIAL_VALUES[piece_type]
        
        return score

# Test
board = ChessBoard()
method_eval = MethodCallVersion()
inlined_eval = InlinedVersion()

# Verify they produce same result
result1 = method_eval.evaluate(board)
result2 = inlined_eval.evaluate(board)
assert result1 == result2, f"Results differ: {result1} vs {result2}"
print(f"✓ Both versions produce same result: {result1}")
print()

# Warmup
print("Warming up...")
for _ in range(10000):
    method_eval.evaluate(board)
    inlined_eval.evaluate(board)
print()

# Test A: Method calls version
print("Test A: Method Calls Version (current pattern)")
print("-" * 80)
iterations = 100_000
start = time.perf_counter()
for _ in range(iterations):
    result = method_eval.evaluate(board)
elapsed_method = time.perf_counter() - start
ops_method = iterations / elapsed_method

print(f"Time: {elapsed_method:.3f}s")
print(f"Speed: {ops_method:,.0f} evals/sec")
print()

# Test B: Inlined version
print("Test B: Inlined Version (no method calls)")
print("-" * 80)
start = time.perf_counter()
for _ in range(iterations):
    result = inlined_eval.evaluate(board)
elapsed_inlined = time.perf_counter() - start
ops_inlined = iterations / elapsed_inlined

print(f"Time: {elapsed_inlined:.3f}s")
print(f"Speed: {ops_inlined:,.0f} evals/sec")
print()

# Analysis
print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()
print(f"Method calls:  {ops_method:>12,.0f} evals/sec")
print(f"Inlined:       {ops_inlined:>12,.0f} evals/sec")
print(f"Speedup:       {ops_inlined/ops_method:>12.2f}x")
print()

if ops_inlined / ops_method > 3.0:
    print("✅ SIGNIFICANT IMPROVEMENT (>3x)")
    print("   → Method calls ARE a major bottleneck")
    print("   → Inlining should dramatically improve performance")
    print("   → RECOMMENDATION: Proceed with inline optimization")
elif ops_inlined / ops_method > 1.5:
    print("⚠️  MODERATE IMPROVEMENT (1.5-3x)")
    print("   → Method calls have some overhead")
    print("   → Inlining will help but may not be complete solution")
    print("   → RECOMMENDATION: Inline + investigate other factors")
elif ops_inlined / ops_method > 1.1:
    print("⚠️  MINIMAL IMPROVEMENT (1.1-1.5x)")
    print("   → Method calls not the main bottleneck")
    print("   → Inlining won't solve the problem")
    print("   → RECOMMENDATION: Look elsewhere (attribute access, operations)")
else:
    print("❌ NO IMPROVEMENT")
    print("   → Method calls are NOT the bottleneck")
    print("   → Do NOT inline - it won't help")
    print("   → RECOMMENDATION: Investigate actual hot operations")

print()
print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print()
print("1. Run this test on VPS (PyPy environment)")
print("2. If speedup > 3x: Proceed with inlining full evaluate() method")
print("3. If speedup < 3x: Run Test 3 to profile individual methods")
print("4. Document results in MASTER_FIX_PLAN.md")
