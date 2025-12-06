#!/usr/bin/env python
"""
Check if PyPy JIT is compiling specific functions.
Requires: PYPYLOG environment variable to see JIT activity.
"""
import sys
import os

# Set PYPYLOG to see JIT compilation
os.environ['PYPYLOG'] = 'jit-log-opt:pypyjit.log'

print("="*80)
print("PyPy JIT Compilation Check")
print("="*80)
print("\n⚠️  This will create a 'pypyjit.log' file showing JIT activity")
print("Looking for: 'compiling' messages for our functions\n")

try:
    import __pypy__
    print("✅ Running on PyPy", sys.version)
except ImportError:
    print("❌ Not running on PyPy - this test requires PyPy")
    sys.exit(1)

# Now import and run chess code
print("\nImporting chess modules...")
from src.board_state import BoardState
from src.move_generation import MoveGenerator
from src.evaluation import Evaluation
from src.search import Search

print("✅ Modules imported\n")

# Run some operations to trigger JIT
print("Running operations to trigger JIT compilation...")
print("(This may take 30-60 seconds)\n")

board = BoardState()
gen = MoveGenerator()
evaluator = Evaluation()
search = Search()

# Warmup - trigger JIT threshold
print("1. Warming up move generation (10000 calls)...")
for i in range(10000):
    moves = gen.generate_legal_moves(board)
    if i % 2000 == 0:
        print(f"   {i}/10000...")

print("\n2. Warming up evaluation (10000 calls)...")
for i in range(10000):
    score = evaluator.evaluate(board)
    if i % 2000 == 0:
        print(f"   {i}/10000...")

print("\n3. Warming up search (100 calls at depth=2)...")
for i in range(100):
    move, score = search.search(board, depth=2, alpha=-10000, beta=10000)
    if i % 20 == 0:
        print(f"   {i}/100...")

print("\n" + "="*80)
print("DONE - Check pypyjit.log for compilation messages")
print("="*80)

# Analyze the log
print("\nAnalyzing JIT log...")
try:
    with open('pypyjit.log', 'r') as f:
        log = f.read()
    
    # Count compilation messages
    compiling_count = log.count('[jit-log-opt-loop]')
    
    print(f"\nFound {compiling_count} JIT-compiled loops")
    
    # Look for our functions
    functions_to_check = [
        'generate_legal_moves',
        'generate_moves',
        'evaluate',
        'alpha_beta',
        'quiescence',
        'make_move',
        'unmake_move',
    ]
    
    print("\nChecking if our functions were JIT-compiled:")
    for func_name in functions_to_check:
        if func_name in log:
            print(f"  ✅ {func_name} - mentioned in JIT log")
        else:
            print(f"  ❌ {func_name} - NOT in JIT log (may not be compiled)")
    
    # Check for "too long" or "too large" messages
    if 'too long' in log.lower() or 'too large' in log.lower():
        print("\n⚠️  WARNING: Found 'too long/large' messages - functions may be too big to compile")
        print("This is the likely cause of poor performance!")
    
    print("\n" + "="*80)
    print("Full log saved to: pypyjit.log")
    print("You can search for 'alpha_beta' or 'quiescence' to see if they compiled")
    print("="*80)
    
except FileNotFoundError:
    print("\n❌ pypyjit.log not created - JIT logging may not be working")
except Exception as e:
    print(f"\n⚠️  Error analyzing log: {e}")
