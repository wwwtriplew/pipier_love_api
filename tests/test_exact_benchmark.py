#!/usr/bin/env python3
"""Test with the EXACT method documented to get 986k NPS"""

import sys
import time

from src.board_state import Position

print("=" * 70)
print("Testing Position.perft() - the documented 986k NPS method")
print("=" * 70)

pos = Position()

# Warmup exactly as benchmark.py does
print("\nWarming up (depth 2)...")
pos.perft(2)

# Now test depth 4 (197,281 nodes expected)
print("\nRunning perft(4)...")
start = time.time()
nodes = pos.perft(4)
elapsed = time.time() - start
nps = int(nodes / elapsed) if elapsed > 0 else 0

print(f"\nResults:")
print(f"  Nodes:     {nodes:,} (expected 197,281)")
print(f"  Time:      {elapsed:.3f}s")
print(f"  NPS:       {nps:,}")
print("=" * 70)

if nodes != 197281:
    print("❌ WRONG node count!")
elif nps > 500000:
    print("✅ FAST - PyPy JIT working! (Target: 986k)")
elif nps > 100000:
    print("⚠️  Moderate - Some optimization (Target: 986k)")
else:
    print("❌ SLOW - Not matching documented 986k NPS")
    print("\nTrying with more warmup iterations...")
    
    # Progressive warmup
    for i in range(10):
        pos.perft(3)
    
    print("After 10x depth-3 warmups, testing again...")
    start = time.time()
    nodes = pos.perft(4)
    elapsed = time.time() - start
    nps = int(nodes / elapsed) if elapsed > 0 else 0
    print(f"  NPS after warmup: {nps:,}")
