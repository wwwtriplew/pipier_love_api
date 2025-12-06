# PyPy JIT "Trace Too Long" Analysis

## Problem Identified

PyPy JIT diagnostic shows:
```
abort: trace too long: 6
```

This means 6 hot code paths exceed PyPy's JIT trace length limit, forcing them to run in **slow interpreter mode** instead of fast compiled code.

**Impact**: PyPy running at 6k NPS vs CPython 30k NPS (5x SLOWER!)

## Root Causes

### 1. **perft() Nested Recursion** (board_state.py:137)
```python
def perft(self, depth: int) -> int:
    def _perft(board, d):  # ❌ Nested function
        if d == 0:
            return 1
        nodes = 0
        for from_sq, to_sq, promo in board.generate_moves():  # ❌ Loop
            board.make_move(from_sq, to_sq, promo)
            king_sq = get_lsb(board.pieces[1 - board.side_to_move][KING])
            if not board.is_square_attacked(king_sq, board.side_to_move):
                nodes += _perft(board, d - 1)  # ❌ Recursion
            board.unmake_move()
        return nodes
    return _perft(self._board, depth)
```
**Why too long**: Nested function + loop + recursion + multiple function calls inside loop

### 2. **generate_pawn_moves()** (move_generation.py:396)
- 103 lines long
- Multiple while loops (outer while pawns, inner while captures)
- Nested conditionals (promotion checks, double push checks, en passant)
- Many tuple appends in different branches
**Why too long**: Too many operations in single function body

### 3. **is_king_move_safe()** (move_generation.py:174)
- Complex safety checking for king moves
- Multiple attack table lookups
- Called inside generate_king_moves() loop
**Why too long**: When inlined into caller, creates very long trace

### 4. **generate_castling_moves()** (move_generation.py:206)
- Long conditional chains for each castling type (4 types)
- Multiple bitboard operations per condition
- Multiple is_square_attacked() calls
**Why too long**: Long if-statement chains with multiple function calls

### 5. **generate_check_evasions()** (move_generation.py:246)
- Calls generate_capture_moves() and generate_moves_to_square()
- Iterates over between_squares
- Multiple nested loops when inlined
**Why too long**: Complex call graph with loops

### 6. **make_move()/unmake_move()** (chess_engine.py)
- Already optimized, but still complex
- Called thousands of times during perft
- May be hitting trace limit when combined with caller context

## Solution Strategy

### Phase 1: Simplify Hot Functions (Target: 0 trace aborts)

1. **Flatten perft()** - Move _perft to module level, avoid nested function
2. **Split generate_pawn_moves()** - Break into smaller functions:
   - generate_pawn_pushes()
   - generate_pawn_captures()  
   - generate_pawn_promotions()
3. **Simplify is_king_move_safe()** - Extract complex checks into helpers
4. **Split generate_castling_moves()** - Separate functions per side
5. **Inline simple functions** - Help PyPy see full trace

### Phase 2: Verify JIT Success

Run after refactoring:
```bash
bash diagnose_pypy_slow.sh
```

Expected result:
```
abort: trace too long: 0  ← Success!
```

### Phase 3: Performance Target

- **Current**: 6k NPS (PyPy slower than CPython)
- **After fix**: 200k-500k NPS (30-80x improvement)
- **Gameplay**: 12-second search explores 2.4-6M nodes instead of 100k

## Implementation Priority

1. **HIGHEST**: Fix perft() (used in diagnostics and testing)
2. **HIGH**: Split generate_pawn_moves() (called most frequently)
3. **MEDIUM**: Simplify castling and king safety
4. **LOW**: Inline micro-optimizations

## Expected Outcome

With 0 trace aborts, PyPy JIT can compile all hot loops into machine code. This gives ~50-100x speedup over interpreter mode, achieving our 200k+ NPS target.
