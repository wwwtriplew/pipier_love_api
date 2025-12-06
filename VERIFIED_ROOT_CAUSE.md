# VERIFIED ROOT CAUSE - Mobility & King Safety Bottleneck

**Date:** December 6, 2025  
**Status:** ✅ VERIFIED with hard data from VPS tests

---

## Executive Summary

**Original Hypothesis:** Method calls and complexity block PyPy JIT  
**Verification Result:** **HYPOTHESIS WRONG**  
**Actual Problem:** `_evaluate_mobility()` and `_evaluate_king_safety()` consume 72% of evaluation time

---

## Test Results (VPS - PyPy 3.9.18)

### Test 2: Method Call Overhead
```
Method calls:  76,746 evals/sec
Inlined:       80,338 evals/sec
Speedup:       1.05x (only 5% improvement)
```

**Conclusion:** ❌ Method calls are NOT the bottleneck

### Test 3: Method Profiling (The Smoking Gun)
```
Method                  Calls/sec    μs/call    % of Total
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_evaluate_mobility      43,440       23.02      44.3%  ← PRIMARY BOTTLENECK
_evaluate_king_safety   69,474       14.39      27.7%  ← SECONDARY BOTTLENECK
_evaluate_material     135,590        7.38      14.2%
_calculate_phase       169,686        5.89      11.3%
_evaluate_psqt         878,388        1.14       2.2%
───────────────────────────────────────────────────────────
evaluate() FULL         19,258       51.93     100.0%
```

**Key Finding:** 72% of evaluation time is spent in mobility (44%) + king safety (28%)

---

## Why Our Hypothesis Was Wrong

### What We Thought
- Method calls add overhead → PyPy can't JIT-compile complex functions
- Dict lookups slow → need tuple indexing
- Inlining would help

### What We Found
- Method calls add only 5% overhead (not significant)
- Fast methods are VERY fast (878k calls/sec for _evaluate_psqt)
- PyPy JIT IS working for simple methods
- Slow methods are slow because of WHAT they do, not HOW they're called

### The Real Culprits

**_evaluate_mobility() - 44% of time:**
- Calls magic bitboard lookups extensively
- Generates attack maps for all pieces
- Complex bit manipulation
- Many nested loops

**_evaluate_king_safety() - 28% of time:**
- Attack map generation
- Pawn shield calculations (already cached?)
- King exposure scoring
- Open file detection

---

## Performance Analysis

### Current State
```
Full evaluate():     19,258 evals/sec (51.93 μs/call)
API performance:     ~27k NPS
```

### If We Fix Mobility (2x speedup from 23μs → 11μs)
```
Time saved:          23 - 11 = 12 μs
New evaluate time:   52 - 12 = 40 μs
New eval speed:      25,000 evals/sec (30% improvement)
New API:             ~35k NPS
```

### If We Fix Both Mobility + King Safety
```
Mobility: 23 → 11 μs (save 12 μs)
King safety: 14 → 7 μs (save 7 μs)
Total saved: 19 μs (37% of current 52 μs)

New evaluate time: 52 - 19 = 33 μs
New eval speed:    30,300 evals/sec (57% improvement)
New API:           ~42k NPS
```

**Still far from 200k NPS target!**

---

## Why Dict→Tuple Didn't Help Much

The dict→tuple fix targeted:
- MATERIAL_VALUES (used in _evaluate_material: 14% of time)
- PHASE_VALUES (used in _calculate_phase: 11% of time)

**Total impact:** ~25% of evaluation time  
**But the real bottleneck:** 72% of time in mobility/king_safety

**Analogy:** Like optimizing the engine of a car that has flat tires. The engine is fine, but you're not going anywhere fast.

---

## Root Cause: Magic Bitboard Lookups

Both slow methods heavily use:
```python
magic_bb.get_rook_attacks(square, occupancy)
magic_bb.get_bishop_attacks(square, occupancy)
```

These involve:
1. Hash table lookups
2. Bit manipulation
3. Mask applications
4. Index calculations

**Hypothesis:** These operations are either:
- Not JIT-compiled (too complex?)
- Suffering cache misses
- Inherently expensive even with JIT

---

## NEW Fix Strategy

### Option A: Cache Mobility Scores (RECOMMENDED)
**Idea:** Store mobility in pawn hash table or separate cache
- Mobility changes only when pieces move
- Can cache for 2-3 plies
- Expected: 2-3x speedup (reduce from 44% to 15-20% of time)

### Option B: Approximate Mobility
**Idea:** Use cheaper approximation for non-critical positions
- Full calculation only near root
- Simpler heuristic deeper in tree
- Expected: 2-4x speedup for deep nodes

### Option C: Optimize Magic Bitboard Implementation
**Idea:** Make get_*_attacks() faster
- Profile the magic bitboard code itself
- Look for Python-specific slowdowns
- Consider lookup table optimizations
- Expected: 1.5-2x speedup

### Option D: Skip Expensive Terms in Quiescence
**Idea:** Mobility/king safety less important in tactical sequences
- Full eval in alpha-beta
- Simplified eval in quiescence
- Expected: 1.5-2x speedup in quiescence

### Option E: Reduce Mobility Granularity
**Idea:** Current implementation might be too detailed
- Count mobility zones instead of individual squares
- Reduce attack map calculations
- Expected: 1.5-2x speedup

---

## Recommended Actions

### Immediate (Next 30 minutes)
1. ✅ Update MASTER_FIX_PLAN.md with verified findings
2. ✅ Document why hypothesis was wrong
3. ✅ Create new optimization plan targeting mobility/king_safety

### Phase 1: Investigation (1 hour)
1. Profile magic bitboard operations specifically
2. Check if mobility/king_safety are cached properly
3. Analyze call patterns (how often called, with what boards)
4. Look at other engines - do they skip mobility in quiescence?

### Phase 2: Implementation (2-4 hours)
1. Implement caching for mobility scores
2. Test performance improvement
3. If insufficient, try approximation approach
4. Measure actual API NPS improvement

### Phase 3: Validation
1. Verify evaluation still correct (perft test)
2. Measure new API NPS on VPS
3. If still < 200k, profile again and iterate

---

## Lessons Learned

### What Went Right ✅
- Systematic verification before major changes
- Hard data prevented premature optimization
- Now know exactly where to focus

### What Went Wrong ❌
- Initial hypothesis was based on speculation
- Assumed complexity = slow (not always true)
- Didn't profile BEFORE optimizing dicts

### For Future
- **ALWAYS profile first** before optimizing
- Don't assume - measure
- Verification plan saved us from wasting time on wrong fix
- Small tests can reveal big insights

---

## Bottom Line

**We were about to inline 400+ lines of code for a 5% improvement.**

**Instead, we now know:**
- 72% of time is in 2 methods
- Optimizing those could give 2-4x speedup
- But even that only gets us to ~40-80k NPS
- Need to investigate why magic bitboards are slow

**Next step:** Profile magic bitboard operations to find the REAL root cause.
