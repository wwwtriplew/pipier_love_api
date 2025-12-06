#!/usr/bin/env python
"""
Find what's blocking PyPy JIT in the chess engine.
"""
import sys
import time

def test_module_performance(module_name, test_func, iterations=10000):
    """Test if a specific module/function allows JIT compilation."""
    print(f"\nTesting: {module_name}")
    
    # Warmup
    for _ in range(100):
        test_func()
    
    # Measure
    start = time.time()
    for _ in range(iterations):
        test_func()
    elapsed = time.time() - start
    
    ops_per_sec = iterations / elapsed
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Ops/sec: {ops_per_sec:,.0f}")
    
    if ops_per_sec > 50000:
        print(f"  ✅ FAST - JIT working")
    elif ops_per_sec > 10000:
        print(f"  ⚠️  MEDIUM - partial JIT")
    else:
        print(f"  ❌ SLOW - JIT blocked")
    
    return ops_per_sec

print("="*80)
print("JIT Blocker Detection")
print("="*80)

# Test 1: Import overhead
print("\n1. Testing imports...")
start = time.time()
from src.board_state import BoardState
from src.move_generation import MoveGenerator
from src.evaluation import Evaluation
from src.search import Search
print(f"   Import time: {time.time() - start:.3f}s")

# Test 2: BoardState creation
def test_board_creation():
    board = BoardState()
    return board

print("\n2. Testing BoardState creation...")
test_module_performance("BoardState.__init__", test_board_creation, 10000)

# Test 3: Move generation
board = BoardState()
move_gen = MoveGenerator()

def test_move_gen():
    moves = move_gen.generate_legal_moves(board)
    return len(moves)

print("\n3. Testing move generation...")
test_module_performance("MoveGenerator.generate_legal_moves", test_move_gen, 1000)

# Test 4: Evaluation
evaluator = Evaluation()

def test_evaluation():
    score = evaluator.evaluate(board)
    return score

print("\n4. Testing evaluation...")
test_module_performance("Evaluation.evaluate", test_evaluation, 10000)

# Test 5: Make/unmake move
moves = move_gen.generate_legal_moves(board)
if moves:
    test_move = moves[0]
    
    def test_make_unmake():
        board.make_move(test_move)
        board.unmake_move()
        return True
    
    print("\n5. Testing make/unmake move...")
    test_module_performance("make/unmake move", test_make_unmake, 10000)

# Test 6: Search (the real bottleneck)
search = Search()

def test_search():
    move, score = search.search(board, depth=2, alpha=-10000, beta=10000)
    return move

print("\n6. Testing search (depth=2)...")
test_module_performance("Search.search", test_search, 10)

# Test 7: Check for specific JIT-blocking patterns
print("\n" + "="*80)
print("7. Checking for JIT-blocking patterns...")
print("="*80)

try:
    import pypyjit
    
    # Get JIT statistics if available
    print("\nAttempting to get JIT stats...")
    try:
        # Try to enable JIT logging temporarily
        import __pypy__
        print("✅ __pypy__ available")
        
        # Check if certain functions are JIT-compiled
        print("\nChecking function compilation status...")
        
    except Exception as e:
        print(f"⚠️  Cannot check JIT stats: {e}")
        
except ImportError:
    print("⚠️  pypyjit not available")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)
print("""
If move generation or evaluation is slow:
  - Check for: eval(), exec(), large try/except blocks
  - Check for: inspect module usage, frame manipulation
  - Check for: dynamic attribute access (getattr/setattr in hot loops)
  - Check for: large dictionaries with non-string keys

If search is slow:
  - Recursion depth may prevent JIT optimization
  - Check alpha-beta pruning logic
  - Check transposition table implementation

PyPy JIT struggles with:
  - Functions containing eval/exec
  - Functions with too many branches (>100)
  - Functions that are too large (>5000 bytecode ops)
  - Nested exception handling in loops
""")
