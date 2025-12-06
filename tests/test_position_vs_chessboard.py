#!/usr/bin/env python3
"""Test if Position vs ChessBoard makes a difference"""

import sys
import time

print("Testing Position (from board_state.py)...")
print("=" * 60)

from src.board_state import Position

# Warmup with multiple iterations
print("Warming up JIT...")
pos = Position()
for i in range(100):
    pos.perft(2)
    if i % 25 == 24:
        print(f"  Warmup iteration {i+1}/100")

print("\nRunning perft(4) test...")
pos = Position()
start = time.time()
nodes = pos.perft(4)
elapsed = time.time() - start
nps = int(nodes / elapsed) if elapsed > 0 else 0

print(f"Nodes: {nodes:,} (expected 197,281)")
print(f"Time: {elapsed:.3f}s")
print(f"NPS: {nps:,}")

if nps > 500000:
    print("✅ FAST - PyPy JIT is working!")
elif nps > 100000:
    print("⚠️  Moderate - Some JIT optimization")
else:
    print("❌ SLOW - JIT not optimizing properly")
