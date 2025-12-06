# NEXT STEPS - Complete Engine Profiling Required

**Date:** December 6, 2025  
**Status:** Evaluation profiled, need complete picture

---

## Current Situation

### What We've Learned ✅
1. **Method calls NOT the issue:** Only 5% overhead (Test 2)
2. **PyPy JIT IS working:** 878k calls/sec for simple methods (Test 3)
3. **Evaluation bottlenecks identified:** Mobility (44%) + King Safety (28%) = 72% of eval time
4. **Dict→tuple was correct:** But only affects 25% of eval time

### Critical Knowledge Gap ❌

**We've only profiled EVALUATION in isolation!**

A chess engine has 3 major hot path components:
1. **Search** (alpha-beta, transposition table, move ordering)
2. **Move generation** (legal moves, attack detection)
3. **Evaluation** (position scoring)

**We don't know:**
- What % of total time is spent in each component?
- Is evaluation even the main bottleneck?
- Could move generation be slower?
- Is make/unmake taking significant time?

---

## Why This Matters

### Example Scenario A: Evaluation Dominates
```
Alpha-beta search (depth 3):  100 ms total
  ├─ Evaluation:       60 ms (60%)  ← OPTIMIZE THIS
  ├─ Move generation:  25 ms (25%)
  └─ Make/unmake:      15 ms (15%)
```
**Strategy:** Focus on mobility/king_safety optimization  
**Impact:** 3x eval speedup = 2x total speedup ✅

### Example Scenario B: Move Generation Dominates
```
Alpha-beta search (depth 3):  100 ms total
  ├─ Move generation:  60 ms (60%)  ← OPTIMIZE THIS
  ├─ Evaluation:       25 ms (25%)
  └─ Make/unmake:      15 ms (15%)
```
**Strategy:** Profile and optimize move generation  
**Impact:** 3x eval speedup = only 1.4x total speedup ❌

### Example Scenario C: Balanced
```
Alpha-beta search (depth 3):  100 ms total
  ├─ Evaluation:       35 ms (35%)  ← OPTIMIZE
  ├─ Move generation:  35 ms (35%)  ← OPTIMIZE  
  └─ Make/unmake:      30 ms (30%)  ← OPTIMIZE
```
**Strategy:** Need to optimize ALL THREE components  
**Impact:** Must fix multiple things to reach target

---

## Immediate Action Required

### Test 4: Complete Hot Path Profile

**File created:** `scripts/test_complete_profile.py`

**Run on VPS:**
```bash
cd /root/pipier_love_api
git pull origin main
source venv/bin/activate
python3 scripts/test_complete_profile.py 2>&1 | tee test4_results.txt
```

**What it measures:**
1. Move generation speed (calls/sec)
2. Make/unmake move overhead (cycles/sec)
3. Evaluation speed (already know: 19.3k/sec)
4. Alpha-beta search at depth 3 (NPS, time breakdown)
5. Perft depth 4 (pure move generation benchmark)

**Critical output:**
```
TIME BREAKDOWN IN SEARCH:
  Evaluation:       XX.X ms (XX%)
  Move generation:  XX.X ms (XX%)
  Make/unmake:      XX.X ms (XX%)
  Search overhead:  XX.X ms (XX%)
```

This will tell us WHERE to focus optimization effort!

---

## Decision Matrix Based on Test 4

### Outcome 1: Evaluation > 50% of search time
**Action:** Optimize evaluation (mobility/king_safety)  
**Approaches:**
- Cache mobility scores in pawn hash or separate table
- Skip mobility in quiescence search
- Use cheaper approximations for deep nodes
- Profile magic bitboard operations

**Expected:** 2-3x eval speedup = 1.5-2x total speedup

### Outcome 2: Move Generation > 50% of search time
**Action:** Optimize move generation  
**Approaches:**
- Profile each move type (pawn, knight, etc.)
- Check magic bitboard attack generation
- Look for redundant legal move checks
- Optimize is_square_attacked()

**Expected:** 2-4x movegen speedup = 1.5-3x total speedup

### Outcome 3: Make/Unmake > 30% of search time
**Action:** Optimize state management  
**Approaches:**
- Profile what's being saved/restored
- Check for unnecessary copying
- Consider incremental zobrist updates
- Reduce state tuple size

**Expected:** 1.5-2x speedup

### Outcome 4: Search Overhead > 30% of search time
**Action:** Optimize alpha-beta itself  
**Approaches:**
- Profile transposition table lookups
- Check move ordering overhead
- Look at killer move heuristics
- Reduce function call overhead

**Expected:** 1.5-2x speedup

### Outcome 5: Balanced (no single component > 40%)
**Action:** Multi-pronged optimization  
**Strategy:** Must optimize 2-3 components to reach target  
**Priority:** Start with largest component, then iterate

---

## Why We Can't Skip This

**Risk of optimizing wrong component:**
- Waste 2-3 hours on wrong fix
- Still far from 200k NPS target
- Miss the actual bottleneck
- Team loses confidence

**Benefit of complete profiling (15 minutes):**
- Know exactly where to focus
- Predict improvement accurately
- Choose right optimization strategy
- Can measure progress objectively

---

## After Test 4: Optimization Path

### Phase 1: Identify (15 min)
✅ Run Test 4  
✅ Update MASTER_FIX_PLAN with results  
✅ Determine which component to optimize

### Phase 2: Deep Profile (30 min)
- Create focused test for slow component
- Identify specific slow operations
- Understand why it's slow

### Phase 3: Implement (1-2 hours)
- Implement targeted fix
- Test correctness (perft)
- Measure improvement

### Phase 4: Validate (15 min)
- Run Test 4 again
- Compare before/after
- If still < 200k NPS: iterate

### Phase 5: Deploy (15 min)
- Push to VPS
- Restart service
- Test API performance
- Celebrate! 🎉

---

## Timeline Estimate

**If we skip Test 4:**
- Unknown where to optimize: ???
- Might fix wrong thing: 2-3 hours wasted
- Still slow: repeat forever
- **Total: Could be days**

**If we run Test 4 first:**
- Run test: 15 min
- Identify bottleneck: 5 min
- Deep profile: 30 min
- Implement fix: 1-2 hours
- Validate: 15 min
- **Total: 2.5-3.5 hours to solution**

---

## Commands Summary

```bash
# Get latest code
cd /root/pipier_love_api
git pull origin main
source venv/bin/activate

# Run complete profile (CRITICAL NEXT STEP)
python3 scripts/test_complete_profile.py 2>&1 | tee test4_results.txt

# View results
cat test4_results.txt

# Share results for analysis and next steps
```

---

**BOTTOM LINE:** We cannot proceed with targeted optimization until we know which component (search/movegen/eval) is the actual bottleneck. Test 4 will tell us in 15 minutes.
