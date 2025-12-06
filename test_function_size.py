#!/usr/bin/env python
"""
Quick test: Does function size block PyPy JIT?
"""
import time
import sys

print("="*80)
print("Function Size vs PyPy JIT Performance")
print("="*80)

# Check if we're on PyPy
try:
    import __pypy__
    print("✅ Running on PyPy", sys.version)
except ImportError:
    print("❌ Not running on PyPy")
    sys.exit(1)

print("\n" + "="*80)
print("Test 1: Small tight function (should JIT-compile)")
print("="*80)

def small_function(n):
    """Small function - easy to JIT compile."""
    total = 0
    for i in range(n):
        total += i * 2
    return total

# Warmup
for _ in range(1000):
    small_function(100)

# Measure
start = time.time()
for _ in range(100000):
    small_function(100)
elapsed = time.time() - start
print(f"Time: {elapsed:.3f}s")
print(f"Calls/sec: {100000/elapsed:,.0f}")
if elapsed < 0.1:
    print("✅ VERY FAST - JIT working perfectly")
else:
    print("❌ SLOW - JIT not working")

print("\n" + "="*80)
print("Test 2: Large function with many branches (may block JIT)")
print("="*80)

def large_function(n):
    """Large function with many branches - may be too complex for JIT."""
    total = 0
    
    # Lots of branching code (simulating alpha_beta complexity)
    for i in range(n):
        if i % 2 == 0:
            if i % 3 == 0:
                total += i * 3
            elif i % 5 == 0:
                total += i * 5
            else:
                total += i
        else:
            if i % 7 == 0:
                total -= i
            elif i % 11 == 0:
                total -= i * 2
            else:
                total += i // 2
                
        # More complexity
        if total > 1000:
            total = total % 1000
        elif total < -1000:
            total = -(-total % 1000)
            
        # Even more branches
        if i % 13 == 0:
            if i % 17 == 0:
                total += 100
            else:
                total -= 50
        
        # Simulate recursive-like logic
        temp = total
        for j in range(3):
            if temp % (j+1) == 0:
                temp += j
        total = temp
        
    return total

# Warmup
for _ in range(1000):
    large_function(100)

# Measure
start = time.time()
for _ in range(100000):
    large_function(100)
elapsed = time.time() - start
print(f"Time: {elapsed:.3f}s")
print(f"Calls/sec: {100000/elapsed:,.0f}")
if elapsed < 0.5:
    print("✅ FAST - JIT working")
elif elapsed < 2.0:
    print("⚠️  MEDIUM - partial JIT")
else:
    print("❌ SLOW - JIT not working well")

print("\n" + "="*80)
print("Test 3: Function with recursion (common in chess search)")
print("="*80)

call_count = 0

def recursive_function(depth, value):
    """Recursive function - may block JIT if too deep/complex."""
    global call_count
    call_count += 1
    
    if depth <= 0:
        return value
    
    # Simulate alpha-beta style recursion with branching
    result = value
    for i in range(3):
        new_value = recursive_function(depth - 1, value + i)
        if new_value > result:
            result = new_value
    
    return result

# Warmup
for _ in range(100):
    call_count = 0
    recursive_function(3, 0)

# Measure
start = time.time()
for _ in range(1000):
    call_count = 0
    recursive_function(3, 0)
elapsed = time.time() - start
print(f"Time: {elapsed:.3f}s")
print(f"Calls/sec: {1000/elapsed:,.0f}")
print(f"Avg recursive calls per invocation: {call_count/1000:.0f}")
if elapsed < 0.1:
    print("✅ FAST - JIT working with recursion")
elif elapsed < 0.5:
    print("⚠️  MEDIUM - partial JIT with recursion")
else:
    print("❌ SLOW - JIT struggles with recursion")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)
print("""
If Test 1 is fast but Test 2/3 are slow:
  → Function complexity/size is blocking JIT

If all tests are slow:
  → JIT is disabled or broken

If all tests are fast:
  → Problem is elsewhere (imports, C extensions, etc.)

PyPy JIT limitations:
- Functions >200-300 lines may not JIT-compile
- Functions with >100-150 branches may not JIT-compile
- Deep recursion (>10-20 levels) may not JIT-optimize well
- Mixed recursion+branching is worst case
""")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

# Now test actual chess module
print("\nTesting actual chess move generation...")
try:
    from src.board_state import BoardState
    from src.move_generation import MoveGenerator
    
    board = BoardState()
    gen = MoveGenerator()
    
    # Warmup
    for _ in range(100):
        moves = gen.generate_legal_moves(board)
    
    # Measure
    start = time.time()
    for _ in range(10000):
        moves = gen.generate_legal_moves(board)
    elapsed = time.time() - start
    
    print(f"Move generation time: {elapsed:.3f}s")
    print(f"Calls/sec: {10000/elapsed:,.0f}")
    
    if elapsed < 0.5:
        print("✅ Move generation is fast")
    else:
        print("❌ Move generation is slow - likely JIT blocker here")
        
except Exception as e:
    print(f"❌ Could not test chess module: {e}")
