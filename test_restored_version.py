#!/usr/bin/env python3
"""Quick test: Verify correctness after removing fast_ops"""

from src.chess_engine import ChessBoard
import time

def perft(cb, depth):
    if depth == 0:
        return 1
    nodes = 0
    for move in cb.generate_legal_moves():
        cb.make_move(*move)
        nodes += perft(cb, depth - 1)
        cb.unmake_move()
    return nodes

print("Testing perft correctness...")
print("=" * 60)

cb = ChessBoard()
expected_results = [1, 20, 400, 8902]

all_correct = True
for depth in range(4):
    start = time.time()
    nodes = perft(cb, depth)
    elapsed = time.time() - start
    nps = int(nodes / elapsed) if elapsed > 0 else 0
    expected = expected_results[depth]
    
    is_correct = nodes == expected
    all_correct = all_correct and is_correct
    status = '✓ CORRECT' if is_correct else '✗ WRONG'
    
    print(f"perft({depth}) = {nodes:,} (expected {expected:,}) {status}")
    print(f"  Time: {elapsed:.3f}s, NPS: {nps:,}")

print("=" * 60)
if all_correct:
    print("✅ ALL TESTS PASSED - Code is correct!")
    print("\nNow test with PyPy for speed:")
    print("  pypy3 test_restored_version.py")
else:
    print("❌ TESTS FAILED - Something is broken!")
