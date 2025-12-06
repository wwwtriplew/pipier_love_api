#!/usr/bin/env python
"""
Show EXACTLY which functions PyPy JIT compiles.

This uses PyPy's internal JIT hooks to see compilation in real-time.
"""
import sys

try:
    import __pypy__
    import pypyjit
    print("="*80)
    print("REAL-TIME JIT COMPILATION MONITOR")
    print("="*80)
    print(f"PyPy {sys.version}\n")
except ImportError:
    print("❌ This test requires PyPy")
    sys.exit(1)

# Track which functions get compiled
compiled_functions = set()
compilation_events = []

def jit_event_handler(event_type, jit_driver_name, greenkey, reason):
    """Callback for JIT events."""
    if event_type == 'abort':
        # JIT gave up compiling this function
        compilation_events.append({
            'type': 'ABORT',
            'name': jit_driver_name,
            'reason': reason
        })
        print(f"❌ JIT ABORT: {jit_driver_name} - {reason}")
    elif event_type == 'compiled':
        # JIT successfully compiled
        compiled_functions.add(jit_driver_name)
        compilation_events.append({
            'type': 'COMPILED',
            'name': jit_driver_name
        })
        print(f"✅ JIT COMPILED: {jit_driver_name}")

# Set up JIT hooks
try:
    pypyjit.set_compile_hook(jit_event_handler)
    print("✅ JIT compile hook installed\n")
    print("Now running chess engine operations...\n")
    print("="*80)
except Exception as e:
    print(f"⚠️  Could not set JIT hook: {e}")
    print("Continuing without hooks...\n")

# Import and run chess code
import time
from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import (
    TranspositionTable, MoveOrderer, SearchStats,
    alpha_beta, quiescence
)

board = ChessBoard()
evaluator = Evaluator()
tt = TranspositionTable(size_mb=64)
orderer = MoveOrderer()
stats = SearchStats()
stats.start_time = time.time()

print("Running operations to trigger JIT compilation...")
print("(Watch for ✅ COMPILED or ❌ ABORT messages above)\n")

# 1. Move generation (should compile)
print("1. Testing move generation (10000 iterations)...")
for i in range(10000):
    moves = board.generate_moves()
    if i % 2000 == 0:
        print(f"   {i}/10000 - {len(compiled_functions)} functions compiled so far")

# 2. Evaluation (should compile)
print("\n2. Testing evaluation (10000 iterations)...")
for i in range(10000):
    score = evaluator.evaluate(board)
    if i % 2000 == 0:
        print(f"   {i}/10000 - {len(compiled_functions)} functions compiled so far")

# 3. Quiescence (may not compile if too large)
print("\n3. Testing quiescence search (1000 iterations)...")
for i in range(1000):
    score = quiescence(board, -10000, 10000, 0, evaluator, stats)
    if i % 200 == 0:
        print(f"   {i}/1000 - {len(compiled_functions)} functions compiled so far")

# 4. Alpha-beta (likely won't compile if too large)
print("\n4. Testing alpha-beta search depth=1 (500 iterations)...")
for i in range(500):
    stats.nodes = 0
    score = alpha_beta(board, 1, 0, -10000, 10000, evaluator, tt, orderer, stats, [], [])
    if i % 100 == 0:
        print(f"   {i}/500 - {len(compiled_functions)} functions compiled so far")

print("\n5. Testing alpha-beta search depth=3 (100 iterations)...")
for i in range(100):
    stats.nodes = 0
    score = alpha_beta(board, 3, 0, -10000, 10000, evaluator, tt, orderer, stats, [], [])
    if i % 20 == 0:
        print(f"   {i}/100 - {len(compiled_functions)} functions compiled so far")

print("\n" + "="*80)
print("COMPILATION SUMMARY")
print("="*80)

print(f"\n✅ Successfully compiled: {len(compiled_functions)} functions")
print(f"❌ Aborted compilations: {len([e for e in compilation_events if e['type'] == 'ABORT'])}")

if compilation_events:
    print("\nDetailed events:")
    for event in compilation_events[:50]:  # Show first 50
        if event['type'] == 'COMPILED':
            print(f"  ✅ {event['name']}")
        else:
            print(f"  ❌ {event['name']} - {event['reason']}")
    
    if len(compilation_events) > 50:
        print(f"\n  ... and {len(compilation_events) - 50} more events")

# Check for specific functions we care about
print("\n" + "="*80)
print("CRITICAL FUNCTIONS CHECK")
print("="*80)

critical_functions = [
    'alpha_beta',
    'quiescence', 
    'generate_moves',
    'evaluate',
    'make_move',
    'unmake_move',
]

print("\nSearching compiled functions for our critical code...")
for func in critical_functions:
    # Search in compiled function names (may be mangled)
    found = any(func.lower() in name.lower() for name in compiled_functions)
    
    # Also check abort reasons
    aborted = [e for e in compilation_events 
               if e['type'] == 'ABORT' and func.lower() in e['name'].lower()]
    
    if found:
        print(f"  ✅ {func}: COMPILED")
    elif aborted:
        print(f"  ❌ {func}: ABORTED - {aborted[0]['reason']}")
    else:
        print(f"  ⚠️  {func}: Not detected (may be called differently)")

print("\n" + "="*80)
print("VERDICT")
print("="*80)

aborted_funcs = [e for e in compilation_events if e['type'] == 'ABORT']
if aborted_funcs:
    print("\n❌ PROBLEM IDENTIFIED: Some functions could not be JIT-compiled")
    print("\nAborted functions:")
    for event in aborted_funcs:
        print(f"  • {event['name']}")
        print(f"    Reason: {event['reason']}")
    
    if any('too long' in e.get('reason', '').lower() or 'too large' in e.get('reason', '').lower() 
           for e in aborted_funcs):
        print("\n✅ DEFINITIVE PROOF: Functions are TOO LARGE for JIT compilation")
        print("   Recommendation: Split large functions (<150 lines each)")
else:
    print("\n⚠️  No abort events captured")
    print("   This could mean:")
    print("   1. All functions compiled successfully")
    print("   2. Hooks didn't capture the events")
    print("   3. Functions weren't called enough times to trigger compilation")

print("\n" + "="*80)
