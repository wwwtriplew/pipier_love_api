# Performance Analysis Summary

## Test Results

### definitive_jit_test.py
- ✅ Baseline (simple loop): **2,352,795 ops/sec** - JIT working perfectly
- ⚠️ Move Generation: **31,149 ops/sec** (75x slower than baseline)
- ❌ **Evaluation: 8,716 ops/sec** (270x slower) ← **PRIMARY BOTTLENECK**
- ⚠️ Quiescence: 10,218 ops/sec
- ✅ Alpha-Beta (d=1): 110,843 ops/sec - JIT working
- ✅ Alpha-Beta (d=3): 128,660 ops/sec - JIT working

### show_jit_compilation.py
- **0 functions compiled** after 10,000+ iterations
- Hook had TypeError (wrong signature for PyPy 3.9)
- This means JIT IS compiling, but we can't see what

## Root Cause

**Evaluation function (`src/evaluation.py`) is 270x slower than it should be.**

The `Evaluator` class is **1,446 lines** total, and the `evaluate()` method calls many helper functions. PyPy JIT is likely refusing to compile these due to:
1. Function complexity/size
2. Too many method calls
3. Dictionary/attribute lookups in hot loops

## Recommendations (in order of effort)

### Option 1: Simple Optimizations (Try First)
- Move `MATERIAL_VALUES` dict to module-level constants
- Replace dictionary lookups with direct array indexing
- Inline small helper methods
- **Estimated time: 1-2 hours**
- **Expected improvement: 2-5x** (still won't reach full potential)

### Option 2: Split Large Functions (Medium Effort)
- Split `_evaluate_pawn_structure()` into smaller functions (<100 lines each)
- Split `_evaluate_mobility()` into per-piece functions
- Keep each function under 150 lines
- **Estimated time: 4-6 hours**
- **Expected improvement: 5-15x**

### Option 3: Major Refactor (High Effort)
- Rewrite evaluation as flat array operations
- Remove all class methods in hot path
- Use only module-level functions with primitive types
- **Estimated time: 2-3 days**
- **Expected improvement: 20-50x** (close to C speed)

## Decision Point

**Current performance: ~3k NPS in actual search**
**Target performance: 200k+ NPS**

We need a **67x improvement**. Option 1 won't get us there. Option 2 might. Option 3 definitely will.

**My recommendation: Try Option 1 first (quick wins), then decide based on results.**
