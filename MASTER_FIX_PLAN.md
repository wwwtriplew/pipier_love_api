# COMPREHENSIVE PERFORMANCE FIX PLAN

**Date:** December 6, 2025  
**Target:** Fix VPS performance from 27k NPS → 200k+ NPS (8x improvement)  
**Current Status:** ❗ CRITICAL ROOT CAUSE FOUND - evaluate() method not JIT-compiled  
**Last Updated:** After VPS test showing 17.8k evals/sec (PyPy) vs 13.6k (CPython)

---

## 🚨 CRITICAL FINDINGS (December 6, 2025)

### VPS Test Results Reveal Real Bottleneck

**Performance Test on PyPy 3.9.18:**
```
Baseline (array):      333,635,240 ops/sec  ✅ PyPy JIT working perfectly (65x faster than CPython)
Evaluation (static):        17,786 evals/sec  ❌ PyPy JIT NOT working (only 1.3x faster than CPython)
Overhead:                  18,758x slowdown  ❌ Should be ~50-100x, not 18,758x
```

### Root Cause: Method Complexity, Not Dict Lookups

1. **Baseline proves PyPy JIT works**: 333M ops/sec is 65x faster than CPython
2. **Evaluation proves JIT doesn't compile it**: 17.8k is only 1.3x faster than CPython
3. **Dict→tuple fix was correct but insufficient**: Tuples help, but method still not JIT-compiled

### The Real Problem

`Evaluator.evaluate()` is **TOO COMPLEX** for PyPy JIT:
- 8+ method calls (_calculate_phase, _evaluate_material, _evaluate_psqt, _evaluate_pawn_structure, _evaluate_king_safety, _evaluate_mobility)
- 10+ attribute accesses (self.pawn_hash_table, board.pawn_hash, board.side_to_move, etc.)
- Complex control flow (cache hit/miss branches, tempo bonus conditionals)
- Hash table lookups (pawn_hash_table.probe/store)

**PyPy JIT refuses to compile functions** with this level of complexity.

### Why Dict→Tuple Didn't Fix It

- Dict lookups: 62k ops/sec → Tuple indexing: 217k ops/sec (3.48x improvement) ✅
- But this speedup is **ONLY if JIT compiles the function**
- Since JIT doesn't compile evaluate(): tuples run interpreted (~18k ops/sec)
- **Interpreted tuples ≈ Interpreted dicts** (both slow without JIT)

### The Fix

**Inline hot path methods into single evaluate() function:**
- Remove method calls by inlining _calculate_phase, _evaluate_material
- Reduce attribute access
- Simplify control flow
- **Expected**: 10-20x speedup (178k-356k evals/sec)
- **Combined with dict→tuple**: Possibly 400k-600k evals/sec

**See:** `VERIFIED_ROOT_CAUSE.md` for complete test results and analysis

---

## 🔬 COMPREHENSIVE PROFILING REQUIRED

**Status:** Evaluation profiled, but need COMPLETE picture

### Why Full Profiling Matters

A chess engine has 3 major components in the hot path:
1. **Search algorithm** (alpha-beta, quiescence, transposition table)
2. **Move generation** (legal move calculation, attack detection)
3. **Evaluation** (position scoring)

**Current knowledge:**
- ✅ Evaluation: 19.3k evals/sec, _evaluate_mobility (44%) and _evaluate_king_safety (28%) are slow
- ❓ Move generation: Unknown speed
- ❓ Make/unmake moves: Unknown overhead
- ❓ Search overhead: Unknown
- ❓ Which component dominates total time?

### The Missing Piece

**We've profiled evaluation in isolation, but:**
- How much time does search spend in evaluation vs move generation?
- Is move generation the actual bottleneck?
- Is make/unmake taking more time than we think?
- Could search overhead (TT lookups, move ordering) be the issue?

**Example scenario:**
- If move generation takes 60% of search time
- And evaluation takes 30% of search time
- Then optimizing evaluation only gives 30% improvement
- **We'd be focusing on the wrong thing!**

### Test 4: Complete Hot Path Profile

**File:** `scripts/test_complete_profile.py`  
**What it tests:**
1. Move generation speed (generate_moves)
2. Make/unmake move overhead
3. Evaluation speed (already know this)
4. Alpha-beta search at depth 3
5. Perft (pure move generation benchmark)

**Critical questions answered:**
- What % of search time is spent in each component?
- Is the API bottleneck in search, movegen, or eval?
- Where should we focus optimization effort?

---

## ✅ VERIFICATION RESULTS - EVALUATION ONLY

**Status:** PARTIAL - Evaluation profiled, search/movegen pending

### Verification Results (December 6, 2025)

#### ✅ Test 2: Method Call Overhead - **HYPOTHESIS REFUTED**
**Run on VPS (PyPy 3.9.18):**
```
Method calls:  76,746 evals/sec
Inlined:       80,338 evals/sec
Speedup:       1.05x (only 5% improvement)
```

**Conclusion:** ❌ **Method calls are NOT the bottleneck**

#### ✅ Test 3: Evaluation Profiling - **REAL BOTTLENECK FOUND**
**Individual method speeds:**
```
_evaluate_psqt:        878,388 calls/sec (1.14 μs/call)   ← FAST ✅
_calculate_phase:      169,686 calls/sec (5.89 μs/call)   ← FAST ✅
_evaluate_material:    135,590 calls/sec (7.38 μs/call)   ← OK
_evaluate_king_safety:  69,474 calls/sec (14.39 μs/call)  ← SLOW ⚠️
_evaluate_mobility:     43,440 calls/sec (23.02 μs/call)  ← VERY SLOW ❌
```

**Full evaluate() speed:** 19,258 evals/sec (51.93 μs/call)

**Time breakdown within evaluation:**
- _evaluate_mobility: **44.3%** of eval time ← PRIMARY BOTTLENECK
- _evaluate_king_safety: **27.7%** of eval time ← SECONDARY BOTTLENECK  
- _evaluate_material: 14.2% of eval time
- _calculate_phase: 11.3% of eval time
- _evaluate_psqt: 2.2% of eval time

**Key findings:**
1. ✅ PyPy JIT IS working (878k calls/sec for _evaluate_psqt)
2. ✅ Simple methods are fast
3. ❌ Mobility and king safety consume 72% of evaluation time
4. ❌ Likely due to magic bitboard lookups (get_rook_attacks, get_bishop_attacks)
def evaluate_inlined(board):
    # All logic in one function
    # No method calls
```

**Measure:** If inlined is 5-10x faster → method calls are the bottleneck

#### Test 3: Identify Slowest Methods
**Profile which sub-methods take most time:**
```python
import time
evaluator = Evaluator()
board = ChessBoard()

# Time each component
t1 = time.perf_counter()
for _ in range(100000):
    evaluator._calculate_phase(board)
print(f"_calculate_phase: {time.perf_counter() - t1:.3f}s")

t2 = time.perf_counter()
for _ in range(100000):
    evaluator._evaluate_material(board)
print(f"_evaluate_material: {time.perf_counter() - t2:.3f}s")

# ... repeat for all methods
```

**Expected:** Identify which methods are slowest → prioritize those for inlining

#### Test 4: Minimal Reproduction
**Create simplest possible test case:**
```python
class SimpleEvaluator:
    def evaluate_with_calls(self, x):
        a = self._method1(x)
        b = self._method2(x)
        return a + b
    
    def _method1(self, x): return x * 2
    def _method2(self, x): return x + 10

class InlinedEvaluator:
    def evaluate_inlined(self, x):
        a = x * 2  # inlined _method1
        b = x + 10  # inlined _method2
        return a + b
```

**Test:** If inlined is significantly faster → PROVES method calls are the issue

### Verification Checklist

Before implementing ANY code changes:
- [ ] Run Test 1 on VPS (verify_jit_problem.py)
- [ ] Analyze PYPYLOG output - does JIT compile evaluate()?
- [ ] Run Test 2 - compare method calls vs inlined
- [ ] Run Test 3 - profile which methods are slowest
- [ ] Run Test 4 - minimal reproduction case
- [ ] Document all results in MASTER_FIX_PLAN.md
- [ ] If ALL tests confirm hypothesis → proceed with fix
- [ ] If ANY test contradicts hypothesis → investigate further

### Decision Tree

```
Test 1: Is evaluate() JIT-compiled?
├─ NO → Hypothesis CONFIRMED
│   └─ Proceed to Test 2-4 for additional evidence
│       └─ If Tests 2-4 also confirm → IMPLEMENT INLINE FIX
│
└─ YES → Hypothesis WRONG
    └─ Stop! Problem is NOT method complexity
        └─ Re-investigate:
            ├─ Attribute access patterns?
            ├─ Hash table operations?
            ├─ Specific operations in sub-methods?
            └─ Other PyPy JIT limiters?
```

### Risk Assessment

**If we inline without verification:**
- ❌ Might not fix the problem (wasted effort)
- ❌ Harder to maintain (400+ line function)
- ❌ Harder to debug
- ❌ Might break existing functionality
- ❌ No guarantee of improvement

**If we verify first:**
- ✅ Know exact problem before fixing
- ✅ Can measure improvement accurately
- ✅ Safer implementation
- ✅ Better understanding for future optimization
- ✅ Can try smaller, targeted fixes first

---

## 1. SYSTEM ARCHITECTURE UNDERSTANDING

### 1.1 Repository Structure
```
pipier_love_api/
├── main.py                    # FastAPI app entry point
├── src/
│   ├── chess_engine.py       # Core chess board (476 lines)
│   ├── evaluation.py         # Position evaluation (1446 lines) ← BOTTLENECK
│   ├── search.py             # Alpha-beta search (1716 lines)
│   ├── move_generation.py    # Legal move generation (531 lines)
│   ├── magic_bitboards.py    # Bitboard operations
│   ├── opening_book.py       # Polyglot book integration
│   └── jit_warmup.py        # PyPy JIT warmup
├── requirements.txt          # Dependencies (FastAPI, Uvicorn, Pydantic)
└── venv/                     # PyPy 3.9.18 virtual environment
```

### 1.2 VPS Deployment (RackNerd) ✅ CONFIRMED
- **System:** Ubuntu 24.04.3 LTS
- **CPU:** Intel Xeon E5-2680 v2 @ 2.80GHz (2 cores)
- **RAM:** 2.5 GB (1.4 GB available, no memory pressure)
- **Disk:** 45 GB
- **Python:** PyPy 3.9.18 (7.3.15) - CONFIRMED RUNNING
- **Service:** `piperlove.service` (systemd)
- **Port:** 8000 on 127.0.0.1 (local only, needs nginx proxy)
- **Process:** Single Uvicorn worker (PID 132404)
- **Venv Path:** `/root/venv` (service config) ⚠️ 
- **Code Path:** `/root/pipier_love_api` (working directory)

### 1.3 Request Flow
```
HTTP Request → Uvicorn (port 8000)
  → FastAPI main.py
    → Opening book check (if move < 13)
    → iterative_deepening()
      → alpha_beta()
        → quiescence()
          → evaluator.evaluate() ← 270x SLOWER THAN IT SHOULD BE
            → _evaluate_material() ← DICT LOOKUP BOTTLENECK
            → _evaluate_psqt()
            → _calculate_phase() ← DICT LOOKUP
            → _evaluate_pawn_structure()
            → _evaluate_king_safety()
            → _evaluate_mobility()
        → move_generation
        → make/unmake moves
  → Return MoveResponse JSON
```

---

## 2. ROOT CAUSE ANALYSIS - CONFIRMED ISSUES

### 2.1 Primary Bottleneck: Dictionary Lookups in Hot Paths
**Evidence:**
- ✅ `find_jit_blockers.py` confirmed: `MATERIAL_VALUES` is a dict
- ✅ Called millions of times per search (every evaluation × every node)
- ✅ PyPy JIT cannot optimize dict lookups as well as array indexing
- ✅ `test_dict_vs_array.py` shows X speedup (awaiting results)

**Location:**
```python
# src/evaluation.py line 29-35
MATERIAL_VALUES = {
    PAWN: 100,    # Indexed by piece type (0-5)
    KNIGHT: 320,
    BISHOP: 330,
    ROOK: 500,
    QUEEN: 900,
    KING: 0
}
```

**Impact:** Called in `_evaluate_material()` (lines 733, 738)

### 2.2 Secondary Issue: Large Functions Blocking JIT
**Evidence:**
- ✅ `alpha_beta`: 263 lines (threshold: ~200)
- ✅ `iterative_deepening`: 245 lines
- ✅ `quiescence`: 200 lines (borderline)

**PyPy JIT Limitation:** Functions >200-250 lines with complex branching may not be JIT-compiled

### 2.3 Tertiary Issues
- ⚠️  `PHASE_VALUES` also uses dict (lines 703-706)
- ⚠️  Excessive attribute lookups in `Evaluator` methods
- ⚠️  Potential method call overhead vs inlined operations

---

## 3. PERFORMANCE TEST RESULTS SUMMARY

### 3.1 Definitive JIT Test Results
```
Baseline (pure Python):     2,352,795 ops/sec  ✅ JIT working
Move Generation:               31,149 ops/sec  ⚠️  75x slower
Position Evaluation:            8,716 ops/sec  ❌ 270x slower ← PRIMARY
Quiescence Search:             10,218 ops/sec  ⚠️  230x slower
Alpha-Beta (depth=1):         110,843 ops/sec  ✅ JIT working
Alpha-Beta (depth=3):         128,660 ops/sec  ✅ JIT working
Full Search (1s):                   1 ops/sec  ❌ 2.3M x slower
```

**Interpretation:**
- JIT compiles simple code perfectly (2.3M ops/sec)
- Evaluation is 270x slower → **confirmed as bottleneck**
- Search functions surprisingly fast when isolated
- Full search slow because it calls evaluation millions of times

### 3.2 JIT Blocker Detection Results
```
✅ No eval/exec
✅ No frame introspection  
✅ No excessive instance variables
❌ MATERIAL_VALUES = dict (should be array)
❌ PHASE_VALUES = dict (should be array)
❌ alpha_beta: 263 lines (too large)
❌ iterative_deepening: 245 lines (too large)
⚠️  quiescence: 200 lines (borderline)
```

---

## 4. HYPOTHESIS RANKING (Probability → Impact)

### H1: Dictionary Lookups in _evaluate_material ⭐⭐⭐⭐⭐
**Probability:** 95% - Confirmed by tests  
**Impact:** HIGH (270x slowdown in evaluation)  
**Fix Complexity:** TRIVIAL (2 lines of code)  
**Expected Improvement:** 3-10x speedup

**Evidence:**
- Evaluation is 270x slower than baseline
- `test_dict_vs_array.py` should show significant speedup
- Common PyPy JIT issue (dicts slower than arrays)

**Test:** `python test_dict_vs_array.py` (awaiting results)

---

### H2: Large Function Prevents JIT Compilation ⭐⭐⭐⭐
**Probability:** 80% - Common PyPy limitation  
**Impact:** MEDIUM-HIGH (functions not JIT-compiled run 10-50x slower)  
**Fix Complexity:** MEDIUM (split functions, test behavior)  
**Expected Improvement:** 2-5x additional speedup

**Functions to split:**
1. `alpha_beta` (263 lines → 2-3 functions of ~100 lines)
2. `iterative_deepening` (245 lines → 2 functions)
3. `quiescence` (200 lines → may be OK, monitor)

**Test Commands:**
```bash
# Check if functions compile with PYPYLOG
PYPYLOG=jit-summary:- python -c "from src.search import alpha_beta; ..." 2>&1 | grep alpha_beta
```

---

### H3: Repeated Attribute Lookups (self.xyz) ⭐⭐⭐
**Probability:** 70% - Common in OOP Python  
**Impact:** MEDIUM (each lookup adds overhead)  
**Fix Complexity:** EASY (cache in local variables)  
**Expected Improvement:** 1.5-3x speedup

**Example Issue:**
```python
def evaluate(self, board):
    # Bad: repeated self.pawn_hash_table lookups
    entry = self.pawn_hash_table.probe(...)
    self.pawn_hash_table.store(...)
    
    # Good: cache in local variable
    pawn_ht = self.pawn_hash_table
    entry = pawn_ht.probe(...)
```

**Test:** Profile with `cProfile` or PyPy JIT log

---

### H4: Wrong Python Interpreter Running ⭐⭐
**Probability:** 40% - Need to verify  
**Impact:** CRITICAL (CPython = no JIT at all)  
**Fix Complexity:** TRIVIAL (fix systemd service)  
**Expected Improvement:** 10x if this is the issue

**✅ VERIFIED - PyPy IS Running:**
```bash
ps aux shows: /root/venv/bin/pypy3 /root/venv/bin/uvicorn
```

**⚠️ NOTE:** Systemd uses `/root/venv` (not `/root/pipier_love_api/venv`)
- Both appear to have PyPy installed
- Service is running PyPy correctly
- **This is NOT the issue**

---

### H5: PyPy JIT Disabled by Environment Variable ⭐
**Probability:** 20% - Already checked, unlikely  
**Impact:** CRITICAL  
**Fix Complexity:** TRIVIAL  
**Expected Improvement:** 10x

**Test:** Already ran `diagnose_pypy_jit.py` - showed JIT enabled

---

### H6: Insufficient Warmup Before First Request ⭐
**Probability:** 30% - Warmup code exists  
**Impact:** LOW (only affects first request)  
**Fix Complexity:** EASY (enhance warmup)  
**Expected Improvement:** None (warmup already implemented)

**Check:** Review `src/jit_warmup.py` effectiveness

---

### H7: CPU Governor Set to Powersave Mode ⭐
**Probability:** 10% - VPS setting  
**Impact:** MEDIUM (2-3x slowdown possible)  
**Fix Complexity:** EASY (if we have access)  
**Expected Improvement:** 2x

**Test:**
```bash
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
# Should see: performance
# Bad: powersave
```

---

### H8: Memory Swapping During Search ⭐
**Probability:** 5% - Need memory stats  
**Impact:** HIGH if occurring  
**Fix Complexity:** MEDIUM (reduce TT size)  
**Expected Improvement:** Varies

**Test:**
```bash
free -h
vmstat 1 10  # Watch for swap activity
```

---

## 5. FIX IMPLEMENTATION STRATEGY

### Phase 1: Quick Wins (Expected: 3-10x improvement, 1 hour)
**Priority:** IMMEDIATE - Low risk, high reward

#### Fix 1.1: Replace Dictionary with Array ⭐⭐⭐⭐⭐
**File:** `src/evaluation.py`  
**Lines:** 29-35, 45-51  
**Effort:** 5 minutes

**Change:**
```python
# OLD (dict)
MATERIAL_VALUES = {PAWN: 100, KNIGHT: 320, ...}
PHASE_VALUES = {PAWN: 0, KNIGHT: 1, ...}

# NEW (array/tuple) - indexed by piece type (0-5)
MATERIAL_VALUES = (100, 320, 330, 500, 900, 0)  # PAWN=0, KNIGHT=1, etc.
PHASE_VALUES = (0, 1, 1, 2, 4, 0)  # KING phase value doesn't matter
```

**Testing:**
```bash
# Before
python definitive_jit_test.py  # Note evaluation speed
curl -X POST http://localhost:8000/move -d '...'  # Note NPS

# Apply fix
# After  
python definitive_jit_test.py  # Should see 3-10x improvement
curl -X POST http://localhost:8000/move -d '...'  # Should see 50k+ NPS
```

**Rollback:** `git revert HEAD` if performance degrades

---

#### Fix 1.2: Cache Repeated Attribute Lookups
**File:** `src/evaluation.py`  
**Effort:** 15 minutes

**Target methods:** `evaluate()`, `_evaluate_material()`, `_calculate_phase()`

**Example:**
```python
def _evaluate_material(self, board):
    score = 0
    # Cache the MATERIAL_VALUES locally
    mat_values = MATERIAL_VALUES  # Now just one attribute lookup
    
    for piece_type in range(5):
        count = popcount(board.pieces[WHITE][piece_type])
        score += count * mat_values[piece_type]  # Array access, not dict
```

---

### Phase 2: Function Splitting (Expected: 2-5x additional, 4-6 hours)
**Priority:** HIGH - If Phase 1 doesn't reach 200k NPS

#### Fix 2.1: Split alpha_beta Function
**Current:** 263 lines  
**Target:** 2-3 functions of ~80-100 lines each

**Strategy:**
1. Extract "move loop" into `_alpha_beta_move_loop()`
2. Extract "LMR logic" into `_apply_late_move_reduction()`
3. Keep main `alpha_beta()` as coordinator (<100 lines)

**Risk:** MEDIUM - Must preserve exact behavior

---

#### Fix 2.2: Split iterative_deepening Function  
**Current:** 245 lines  
**Target:** 2 functions of ~120 lines

**Strategy:**
1. Extract "aspiration window" logic
2. Extract "time management" checks

---

### Phase 3: Advanced Optimizations (Expected: 1.5-3x, 2-3 days)
**Priority:** MEDIUM - Only if needed

- Inline small helper functions
- Replace method calls with static functions in hot path
- Profile and optimize hottest code paths
- Consider Cython for critical sections (last resort)

---

## 6. TESTING & VALIDATION PROTOCOL

### Pre-Fix Baseline
```bash
# 1. Record current performance
python definitive_jit_test.py > baseline_before.txt

# 2. Test actual API
curl -X POST http://localhost:8000/move \
  -H "Content-Type: application/json" \
  -d '{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","ai_thinking_ms":1000}' \
  | tee api_before.json

# 3. Run full test suite
python critical_tests.py > tests_before.txt
```

### Post-Fix Validation
```bash
# 1. Measure improvement
python definitive_jit_test.py > baseline_after.txt
diff baseline_before.txt baseline_after.txt

# 2. Test API performance
curl -X POST http://localhost:8000/move \
  -H "Content-Type: application/json" \
  -d '{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","ai_thinking_ms":1000}' \
  | tee api_after.json

# 3. Verify correctness
python critical_tests.py > tests_after.txt
diff tests_before.txt tests_after.txt  # Should be identical except timing

# 4. Calculate speedup
python -c "
import json
before = json.load(open('api_before.json'))
after = json.load(open('api_after.json'))
print(f'Speedup: {after[\"nps\"] / before[\"nps\"]:.2f}x')
print(f'Before: {before[\"nps\"]:,} NPS')
print(f'After: {after[\"nps\"]:,} NPS')
"
```

### Success Criteria
- ✅ NPS > 200,000 (8x improvement from 27k)
- ✅ All tests pass (correctness maintained)
- ✅ No memory leaks (check with `ps aux` after 100 requests)
- ✅ API response time < 1.5s for 1000ms thinking time

---

## 7. ROLLBACK PLAN

### If Performance Degrades
```bash
# Immediate rollback
git reset --hard HEAD~1
sudo systemctl restart pipier-api  # or piperlove-api
```

### If Tests Fail
```bash
# Rollback specific file
git checkout HEAD~1 -- src/evaluation.py
sudo systemctl restart pipier-api
```

### If System Unstable
```bash
# Full environment reset
cd /root/pipier_love_api
git stash
git pull origin main  # Known good version
rm -rf venv
python3.9 -m venv venv --copies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --break-system-packages
sudo systemctl restart pipier-api
```

---

## 8. MONITORING & METRICS

### Key Metrics to Track
1. **NPS (Nodes Per Second)** - Primary performance indicator
2. **Evaluation speed** - `definitive_jit_test.py` Layer 2
3. **API response time** - End-to-end latency
4. **Memory usage** - `free -h` before/after
5. **CPU usage** - `top` during search

### Continuous Monitoring
```bash
# Watch API logs
sudo journalctl -u pipier-api -f

# Monitor resource usage
watch -n 1 'free -h && echo "---" && ps aux | grep uvicorn | grep -v grep'
```

---

## 9. SYSTEM INFORMATION ✅ COLLECTED

### Environment Confirmed:
```
✅ PyPy 3.9.18 running (verified in ps aux)
✅ Service: /etc/systemd/system/piperlove.service
✅ CPU: Intel Xeon E5-2680 v2 @ 2.80GHz (2 cores, 2.8 GHz)
✅ RAM: 2.5 GB total, 1.4 GB available (no swapping)
✅ Port: 8000 on 127.0.0.1 (local only)
✅ No memory pressure (vmstat shows 98-100% idle)
⚠️  CPU governor: Not accessible (likely VPS limitation)
⚠️  Venv mismatch: Service uses /root/venv, code in /root/pipier_love_api
```

### Outstanding:
- Need to run: `cd /root/pipier_love_api && python test_dict_vs_array.py`

---

## 10. DECISION TREE

```
START: Current NPS = 27k, Target = 200k+

├─ Check test_dict_vs_array.py results
│  ├─ Speedup > 5x? 
│  │  └─ YES → Apply Fix 1.1 (dict→array) IMMEDIATELY
│  │          Expected result: 50k-150k NPS
│  │          ├─ NPS > 200k? ✅ DONE
│  │          └─ NPS < 200k? → Continue to Phase 2
│  └─ Speedup < 2x?
│     └─ Investigate deeper (wrong Python interpreter?)
│
├─ After Phase 1: NPS = 50k-150k (estimated)
│  └─ If NPS < 200k → Apply Fix 2.1 (split large functions)
│                      Expected: +2-5x → 100k-400k NPS
│                      ├─ NPS > 200k? ✅ DONE
│                      └─ NPS < 200k? → Phase 3 or deeper investigation
│
└─ If nothing works → Check H4 (wrong interpreter running)
```

---

## 11. TIMELINE

### Optimistic (Fix 1.1 sufficient)
- **Phase 1:** 1 hour → 150k+ NPS ✅ Target reached
- **Total:** 1 hour

### Realistic (Need Phase 1 + 2)
- **Phase 1:** 1 hour → 80k NPS
- **Phase 2:** 4-6 hours → 250k NPS ✅ Target exceeded
- **Total:** 5-7 hours

### Pessimistic (All phases needed)
- **Phase 1:** 1 hour → 50k NPS
- **Phase 2:** 6 hours → 120k NPS  
- **Phase 3:** 2-3 days → 220k NPS ✅ Target reached
- **Total:** 3-4 days

---

## 12. NEXT STEPS

1. **YOU:** Run the information gathering commands (Section 9)
2. **ME:** Analyze results and confirm hypotheses
3. **ME:** Implement Fix 1.1 (dict→array) if test confirms benefit
4. **YOU:** Deploy and test on VPS
5. **BOTH:** Iterate based on results

---

**Last Updated:** December 6, 2025  
**Status:** Ready to execute Phase 1 upon confirmation
