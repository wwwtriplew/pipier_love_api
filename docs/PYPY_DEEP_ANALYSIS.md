# DEEP ANALYSIS: Why PyPy is 7.5x SLOWER than documented 986k NPS

## Current Results
- **Peak PyPy**: 130k NPS (with 200 warmups)
- **Documented PyPy**: 986k NPS
- **Gap**: 7.5x slower than expected!

## PyPy JIT Requirements for Maximum Speed

### 1. **Type Stability** (CRITICAL)
PyPy JIT needs monomorphic types. If a variable can be different types, JIT inserts guards.

**Problem Areas to Check:**
```python
# BAD - Polymorphic (can be int or None)
def func(promo: Optional[int]):
    if promo is not None:
        # Guard inserted here!
        return promo
    return 0

# GOOD - Monomorphic
def func(promo: int):
    return promo
```

### 2. **Function Call Overhead**
Every function call has overhead. PyPy JIT inlines small functions but ONLY if:
- Function is stable (not reassigned)
- Function body is small (<15 operations)
- No dynamic dispatch

**Current Code Pattern:**
```python
from .magic_bitboards import pop_lsb, get_lsb, count_bits

# In hot loop:
for move in moves:
    sq = get_lsb(bb)  # Can PyPy inline this?
    bb = pop_lsb(bb)[1]  # Returns tuple - allocation overhead?
```

### 3. **Allocation Overhead**
PyPy JIT can eliminate allocations ONLY if objects don't escape the loop.

**Problem: Tuple Returns**
```python
def pop_lsb(bb: int) -> tuple:
    lsb = bb & -bb
    return (lsb.bit_length() - 1, bb ^ lsb)  # Tuple allocation!
```

Every call allocates a tuple. PyPy might not eliminate this.

**Solution: Use out-parameters or inline**

### 4. **List/Generator Overhead**
```python
# Expensive - creates list
for move in board.generate_moves():
    ...

# Better - generator (but still overhead)
# Best - manual iteration with bitboards
```

## HYPOTHESIS: The Real Problem

Looking at `Position.perft()`:
```python
def perft(self, depth: int) -> int:
    from .magic_bitboards import get_lsb
    
    def _perft(board, d):
        if d == 0:
            return 1
        
        nodes = 0
        for from_sq, to_sq, promo in board.generate_moves():  # ← GENERATOR!
            board.make_move(from_sq, to_sq, promo)
            king_sq = get_lsb(board.pieces[1 - board.side_to_move][KING])
            if not board.is_square_attacked(king_sq, board.side_to_move):
                nodes += _perft(board, d - 1)
            board.unmake_move()
        return nodes
    
    return _perft(self._board, depth)
```

**Problems:**
1. `generate_moves()` returns list of tuples - massive allocation
2. `promo` can be `None` or `int` - polymorphic guard
3. `board.pieces[...]` - list indexing overhead
4. Nested function closure overhead

## THE REAL SOLUTION: Bitboard-Native perft

The 986k NPS version likely had a **pure bitboard perft** that doesn't use:
- move lists
- tuple unpacking
- polymorphic types
- closure captures

**What we need:**
```python
def fast_perft(board, depth):
    """Pure bitboard perft - no allocations, no tuples, no lists"""
    if depth == 0:
        return 1
    
    nodes = 0
    # Generate moves directly into bitboards
    # Process inline without tuples/lists
    # Monomorphic types only
    return nodes
```

## PLAN TO FIX

### Step 1: Profile PyPy JIT
```bash
PYPYLOG=jit-log-opt:jit.log pypy3 test.py
# Analyze what's NOT being optimized
```

### Step 2: Check if `generate_moves()` is the bottleneck
Create a test that:
- Bypasses move generation
- Uses pure bitboard operations
- No tuple/list allocations

### Step 3: Look for polymorphic sites
- `Optional[int]` types
- Union types
- Dynamic lookups

### Step 4: Check tuple allocation overhead
`pop_lsb()` returns tuple - this might be killing performance.

**Alternative:**
```python
# Instead of tuple return
sq, bb = pop_lsb(bb)

# Use mutation
sq = get_lsb(bb)
bb = clear_bit(bb, sq)
```

## IMMEDIATE ACTION

Let me create a diagnostic to find the exact bottleneck:
1. Test pure bitboard operations (no moves)
2. Test move generation only (no make/unmake)
3. Test make/unmake only
4. Compare each component
