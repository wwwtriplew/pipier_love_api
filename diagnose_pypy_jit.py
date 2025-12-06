#!/usr/bin/env python
"""
Diagnose why PyPy JIT is not optimizing the code.

This script checks for common reasons PyPy JIT might not work:
1. JIT disabled by environment variable
2. Trace limits too low
3. Module imports causing issues
4. Function complexity issues
"""

import sys
import os
import platform

print("=" * 80)
print("PyPy JIT Diagnostic Tool")
print("=" * 80)
print()

# Check 1: Python version
print("1. Python Version Check")
print(f"   Implementation: {platform.python_implementation()}")
print(f"   Version: {platform.python_version()}")
print(f"   Executable: {sys.executable}")
print()

if platform.python_implementation() != "PyPy":
    print("❌ NOT running PyPy! This is the problem.")
    sys.exit(1)

# Check 2: JIT environment variables
print("2. JIT Environment Variables")
jit_vars = {
    'PYPYLOG': 'Controls JIT logging',
    'PYPY_JIT_OFF': 'Disables JIT if set',
    'PYPY_JIT_THRESHOLD': 'Function call threshold',
    'PYPY_JIT_MAX_TRACE_LIMIT': 'Max trace length',
}

jit_disabled = False
for var, desc in jit_vars.items():
    val = os.environ.get(var)
    if val:
        print(f"   {var}={val} ({desc})")
        if var == 'PYPY_JIT_OFF':
            jit_disabled = True
            print(f"   ❌ JIT IS DISABLED!")
    else:
        print(f"   {var}=<not set>")

print()

if jit_disabled:
    print("❌ PROBLEM FOUND: JIT is disabled!")
    print("   Solution: unset PYPY_JIT_OFF")
    print()

# Check 3: JIT backend
print("3. JIT Backend Check")
try:
    import __pypy__
    print("   ✅ __pypy__ module available")
    
    # Check if JIT is actually available
    try:
        # This will fail if JIT is disabled
        import pypyjit
        print("   ✅ pypyjit module available")
        
        # Try different trace limits (default is ~6000-10000)
        # 200000 is TOO HIGH and causes TraceLimitTooHigh error
        trace_limits = [20000, 50000, 100000]
        for limit in trace_limits:
            try:
                pypyjit.set_param(f'trace_limit={limit}')
                print(f"   ✅ JIT trace_limit set to {limit}")
                break
            except Exception as e:
                print(f"   ⚠️  trace_limit={limit} failed: {type(e).__name__}")
        else:
            print("   ⚠️  Using default trace_limit (likely ~6000)")
            
    except ImportError:
        print("   ❌ pypyjit module not available (JIT may be disabled)")
except ImportError:
    print("   ❌ __pypy__ module not found")

print()

# Check 4: Simple performance test
print("4. Simple Performance Test")
print("   Running tight loop...")

import time

def tight_loop(n):
    """Simple tight loop that should be JIT compiled."""
    total = 0
    for i in range(n):
        total += i
    return total

# Warmup
for _ in range(100):
    tight_loop(1000)

# Test
start = time.time()
result = tight_loop(10_000_000)
elapsed = time.time() - start

ops_per_sec = 10_000_000 / elapsed
print(f"   Result: {result}")
print(f"   Time: {elapsed:.3f}s")
print(f"   Ops/sec: {ops_per_sec:,.0f}")
print()

if ops_per_sec < 10_000_000:
    print("   ❌ SLOW: JIT not working (< 10M ops/sec)")
elif ops_per_sec < 50_000_000:
    print("   ⚠️  OK: Partial JIT (10-50M ops/sec)")
else:
    print("   ✅ FAST: JIT working well (> 50M ops/sec)")

print()

# Check 5: Import issues
print("5. Import Check")
problematic_imports = [
    ('numpy', 'C extension'),
    ('scipy', 'C extension'),
    ('pandas', 'C extension'),
    ('chess', 'C extension - BLOCKS JIT'),
]

for module, reason in problematic_imports:
    try:
        __import__(module)
        print(f"   ❌ {module} is imported ({reason})")
    except ImportError:
        print(f"   ✅ {module} not imported")

print()

# Check 6: Test actual chess engine
print("6. Chess Engine Performance Test")
try:
    from src.chess_engine import ChessBoard
    from src.magic_bitboards import get_lsb
    
    def perft_simple(board, depth):
        if depth == 0:
            return 1
        nodes = 0
        for from_sq, to_sq, promo in board.generate_moves():
            board.make_move(from_sq, to_sq, promo)
            king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])
            if not board.is_square_attacked(king_sq, board.side_to_move):
                nodes += perft_simple(board, depth - 1)
            board.unmake_move()
        return nodes
    
    board = ChessBoard()
    
    # Warmup
    print("   Warming up...")
    for _ in range(20):
        perft_simple(board, 2)
    
    # Test
    print("   Testing perft(4)...")
    start = time.time()
    nodes = perft_simple(board, 4)
    elapsed = time.time() - start
    nps = int(nodes / elapsed)
    
    print(f"   Nodes: {nodes:,}")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   NPS: {nps:,}")
    print()
    
    if nps < 50_000:
        print("   ❌ CRITICAL: < 50k NPS (JIT not working)")
    elif nps < 100_000:
        print("   ⚠️  SLOW: 50-100k NPS (Partial JIT)")
    elif nps < 200_000:
        print("   ✅ OK: 100-200k NPS (JIT working)")
    else:
        print("   🚀 EXCELLENT: > 200k NPS (Full JIT optimization)")
    
except Exception as e:
    print(f"   ❌ Error testing engine: {e}")

print()
print("=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
