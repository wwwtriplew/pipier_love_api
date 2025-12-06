#!/usr/bin/env python3
"""Aggressive warmup test - find what warmup gets us to 986k NPS"""

import sys
import time
from src.board_state import Position

print("=" * 70)
print("PROGRESSIVE WARMUP TEST - Finding optimal warmup for 986k NPS")
print("=" * 70)

warmup_configs = [
    (0, "No warmup"),
    (10, "10x depth-3"),
    (50, "50x depth-3"),
    (100, "100x depth-3"),
    (200, "200x depth-3"),
    (500, "500x depth-3"),
]

results = []

for warmup_count, description in warmup_configs:
    pos = Position()
    
    # Warmup
    if warmup_count > 0:
        print(f"\n{description}...")
        for i in range(warmup_count):
            pos.perft(3)
            if i % 50 == 49 and i > 0:
                print(f"  Warmup {i+1}/{warmup_count}")
    
    # Test
    print(f"Testing perft(4)...")
    start = time.time()
    nodes = pos.perft(4)
    elapsed = time.time() - start
    nps = int(nodes / elapsed) if elapsed > 0 else 0
    
    results.append((warmup_count, nps))
    print(f"  Result: {nps:,} NPS")
    
    if nps > 500000:
        print(f"  ✅ FAST! Target reached!")
        break

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)
for warmup, nps in results:
    status = "✅" if nps > 500000 else "⚠️" if nps > 100000 else "❌"
    print(f"{status} {warmup:4d} warmups → {nps:,} NPS")

if results[-1][1] < 500000:
    print("\n⚠️  Even with 500 warmups, not reaching 986k NPS")
    print("This suggests the code structure itself may be different from the")
    print("version that achieved 986k NPS, OR that was on a different CPU/PyPy version")
