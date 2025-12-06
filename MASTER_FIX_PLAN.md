# COMPREHENSIVE PERFORMANCE FIX PLAN

**Date:** December 6, 2025  
**Target:** Fix VPS performance from 27k NPS → 200k+ NPS (8x improvement)  
**Current Status:** 🚨 **CRITICAL - SEARCH OVERHEAD IS THE BOTTLENECK (70%)**  
**Last Updated:** After Test 4 complete profiling showing search overhead dominates

---

## 🚨 BREAKTHROUGH DISCOVERY (December 6, 2025 - Test 4 Results)

### Complete Engine Profiling Reveals Shocking Truth

**VPS Test 4 Results (PyPy 3.9.18):**
```
Component               Speed            Time/Op       % of Search Time
─────────────────────────────────────────────────────────────────────
Move generation:        158,902/s        6.29 μs      1.1%  ✅ FAST
Make/unmake:            306,231/s        3.27 μs      1.7%  ✅ FAST
Evaluation:              18,856/s       53.03 μs     27.0%  ⚠️ SLOW
Search overhead:              —             —        70.3%  ❌❌❌ BOTTLENECK
─────────────────────────────────────────────────────────────────────
Alpha-beta (depth 3):         4.41/s   226.82 ms    100.0%
NPS (search):                5,083 nodes/sec
Perft (movegen only):       39,276 NPS
```

### The Real Bottleneck: NOT Evaluation

**For a depth-3 search (1,153 nodes, 226.82 ms):**
```
Search overhead:     159.49 ms  (70.3%)  ← PRIMARY BOTTLENECK ❌❌❌
Evaluation:           61.15 ms  (27.0%)  ← SECONDARY BOTTLENECK ⚠️
Make/unmake:           3.77 ms  ( 1.7%)  ✅
Move generation:       2.42 ms  ( 1.1%)  ✅
```

### Critical Analysis

**Performance Gap:**
- Current NPS: **5,083** nodes/sec
- Target NPS: **200,000** nodes/sec  
- **Gap: 39.3x slower than target** ❌

**What "Search Overhead" Means:**
- Time spent in alpha_beta function EXCLUDING evaluation/movegen/make-unmake
- Includes: TT probe/store, move ordering, PV line management, repetition detection
- **70% of search time is infrastructure, not core chess operations**

### The Smoking Gun

**Perft vs Alpha-Beta comparison:**
- Perft (pure movegen): 39,276 NPS
- Alpha-beta (with search): 5,083 NPS
- **Search infrastructure adds 7.7x overhead** ❌

**This proves:**
1. Move generation is FAST (158k calls/sec)
2. Make/unmake is FAST (306k cycles/sec)
3. Evaluation is acceptable for PyPy interpreted (19k/sec)
4. **The search infrastructure is killing performance**

### Root Cause: Python Data Structures in Hot Path

**Hypothesis:** The 70% overhead comes from:
1. **Transposition Table operations** (creating TTEntry objects, list iterations)
2. **MoveOrderer operations** (killer move arrays, history heuristic dicts)
3. **PV line management** (list operations, copying)
4. **Repetition stack** (list.count() on every node)

**Why This Matters:**
- These are Python object allocations and list/dict operations
- PyPy JIT can't optimize away the overhead for complex objects
- Every node in search (1,153 nodes) pays this penalty
- **70% of time is spent manipulating Python data structures**

---

## 🔬 COMPLETE PROFILING RESULTS

**Status:** ✅ COMPLETE - All components profiled

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
### Test Results Summary

#### ✅ Test 2: Method Call Overhead - **HYPOTHESIS REFUTED**
**Run on VPS (PyPy 3.9.18):**
```
Method calls:  76,746 evals/sec
Inlined:       80,338 evals/sec
Speedup:       1.05x (only 5% improvement)
```
**Conclusion:** ❌ **Method calls are NOT the bottleneck**

#### ✅ Test 3: Evaluation Profiling - **MOBILITY/KING_SAFETY BOTTLENECK**
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
- _evaluate_mobility: **44.3%** of eval time
- _evaluate_king_safety: **27.7%** of eval time
- _evaluate_material: 14.2%
- _calculate_phase: 11.3%
- _evaluate_psqt: 2.2%

#### ✅ Test 4: Complete Engine Profiling - **SEARCH OVERHEAD IS THE BOTTLENECK**
**Run on VPS (PyPy 3.9.18):**
```
Component               Speed            Time/Op       % of Search
────────────────────────────────────────────────────────────────────
Move generation:        158,902/s        6.29 μs      1.1%  ✅
Make/unmake:            306,231/s        3.27 μs      1.7%  ✅
Evaluation:              18,856/s       53.03 μs     27.0%  ⚠️
Search overhead:              —             —        70.3%  ❌❌❌
────────────────────────────────────────────────────────────────────
Alpha-beta (depth 3):         4.41/s   226.82 ms    100.0%
NPS (search):                5,083 nodes/sec
Perft (movegen):            39,276 NPS
```

**Time breakdown for depth-3 search (1,153 nodes, 226.82 ms):**
```
Search overhead:     159.49 ms  (70.3%)  ← PRIMARY BOTTLENECK ❌❌❌
Evaluation:           61.15 ms  (27.0%)  ← SECONDARY BOTTLENECK
Make/unmake:           3.77 ms  ( 1.7%)  ✅ FAST
Move generation:       2.42 ms  ( 1.1%)  ✅ FAST
```

**Critical Finding:**
- Perft (pure movegen): 39,276 NPS
- Alpha-beta (with search): 5,083 NPS
- **Search infrastructure adds 7.7x overhead** ❌

**Conclusion:** 
1. ✅ Move generation is FAST (no optimization needed)
2. ✅ Make/unmake is FAST (no optimization needed)
3. ⚠️ Evaluation is acceptable but could be 2-3x faster
4. ❌ **Search overhead (TT, move ordering, PV, repetition detection) is the PRIMARY bottleneck**

---

## 🎯 OPTIMIZATION STRATEGY (Updated After Test 4)

### Priority 1: Fix Search Overhead (70% of time)

**Target areas in search.py:**
1. **TranspositionTable operations** (creating TTEntry objects, bucket searches)
2. **MoveOrderer operations** (killer arrays, history heuristic)
3. **PV line management** (list operations at every node)
4. **Repetition detection** (repetition_stack.count() at every node)

**Optimization approaches:**
- Replace Python objects with primitive types where possible
- Use numpy arrays instead of lists for killer/history tables
- Simplify TT probe/store (fewer object allocations)
- Cache repetition checks (zobrist_key → bool dict)
- Profile with cProfile to find exact hotspots

**Expected improvement:** 3-5x speedup → 15k-25k NPS

### Priority 2: Optimize Evaluation (27% of time)

**Already profiled - known bottlenecks:**
- _evaluate_mobility (44% of eval time)
- _evaluate_king_safety (28% of eval time)

**Optimization approaches:**
- Cache mobility results per position
- Approximate king safety (fewer attack checks)
- Simplify mobility calculation

**Expected improvement:** 2-3x speedup → 40k-60k evals/sec

### Combined Target

**If both optimizations succeed:**
- Search overhead: 159.49ms → 40ms (4x faster)
- Evaluation: 61.15ms → 25ms (2.5x faster)
- **Total search time: 226.82ms → 70ms (3.2x faster)**
- **Target NPS: 5,083 → 16k-20k NPS**

**Still short of 200k target, but closer. May need:**
- Switch to CPython with C extensions
- More aggressive simplifications
- Algorithmic improvements (better pruning, move ordering)

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

## 2. ROOT CAUSE ANALYSIS - UPDATED AFTER TEST 4

### 2.1 PRIMARY BOTTLENECK: Search Infrastructure (70% of time)

**Evidence from Test 4:**
- Search overhead: 159.49 ms out of 226.82 ms total (70.3%)
- Evaluation: 61.15 ms (27.0%)
- Move generation: 2.42 ms (1.1%)
- Make/unmake: 3.77 ms (1.7%)

**What "Search Overhead" includes:**
1. **TranspositionTable operations:**
   - Creating TTEntry objects on every store
   - Iterating through 4-bucket slots on every probe
   - List operations: `self.table[bucket_idx]` is a Python list
   
2. **MoveOrderer operations:**
   - 2D list for killer moves: `[[None, None] for _ in range(MAX_PLY)]`
   - 3D list for history: `[[[0]*64 for _ in range(64)] for _ in range(2)]`
   - List operations on every move ordering call
   
3. **PV line management:**
   - List operations: `pv_line = []` created at every node
   - List copying and appending
   
4. **Repetition detection:**
   - `repetition_stack.count(zobrist_key)` on EVERY node
   - O(n) operation called 1,153 times per search

**Why This is Slow:**
- Python list/object operations are expensive
- PyPy JIT can't optimize away object allocation overhead
- These operations happen at EVERY node (1,153 times per search)

**Critical insight from Perft comparison:**
- Perft (movegen only): 39,276 NPS
- Alpha-beta (with search infra): 5,083 NPS
- **Search infrastructure adds 7.7x overhead** ❌

### 2.2 SECONDARY BOTTLENECK: Evaluation (27% of time)

**Already profiled in Test 3:**
- _evaluate_mobility: 44.3% of eval time (23.02 μs/call)
- _evaluate_king_safety: 27.7% of eval time (14.39 μs/call)
- These are slow due to magic bitboard attack lookups

**Note:** Evaluation at 18,856/sec is acceptable for PyPy interpreted code.
Optimizing search overhead is higher priority (70% vs 27%).

### 2.3 NON-ISSUES (Test 4 confirmed these are FAST)

- ✅ Move generation: 158,902 calls/sec (6.29 μs) - NO OPTIMIZATION NEEDED
- ✅ Make/unmake: 306,231 cycles/sec (3.27 μs) - NO OPTIMIZATION NEEDED

---

## 3. OPTIMIZATION PLAN (Updated Based on Test 4)

### Phase 1: Profile Search Infrastructure (IMMEDIATE)

**Goal:** Identify which part of search overhead is slowest

**Create profiling script:**
```python
# scripts/profile_search_overhead.py
import cProfile
import pstats
from src.search import alpha_beta, SearchStats, TranspositionTable, MoveOrderer
from src.chess_engine import ChessBoard
from src.evaluation import Evaluator

board = ChessBoard()
evaluator = Evaluator()
tt = TranspositionTable(size_mb=64)
orderer = MoveOrderer()

def run_search():
    for _ in range(100):
        stats = SearchStats()
        pv_line = []
        repetition_stack = []
        alpha_beta(board, 3, 0, -999999, 999999, evaluator, tt, orderer, 
                  stats, pv_line, repetition_stack)

profiler = cProfile.Profile()
profiler.enable()
run_search()
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(30)  # Top 30 functions
```

**Run on VPS:**
```bash
cd /root/pipier_love_api
python3 scripts/profile_search_overhead.py 2>&1 | tee profile_results.txt
```

**Look for:**
- Time spent in `TranspositionTable.probe`
- Time spent in `TranspositionTable.store`
- Time spent in `MoveOrderer.order_moves`
- Time spent in list operations (`repetition_stack.count`, etc.)

### Phase 2: Optimize Top Bottleneck (1-2 hours)

**Option A: If TT operations are slowest (likely):**

**Problem:** Creating TTEntry objects repeatedly
```python
# Current (slow):
class TTEntry:
    def __init__(self, zobrist_key, depth, score, flag, best_move, age, key16):
        self.zobrist_key = zobrist_key
        # ... etc
```

**Solution:** Use tuples or numpy arrays
```python
# Fast: TTEntry as tuple (immutable, faster)
TTEntry = namedtuple('TTEntry', ['zobrist_key', 'depth', 'score', 'flag', 
                                  'best_move', 'age', 'key16'])

# Or even faster: store as numpy array
import numpy as np
self.table = np.zeros((num_buckets, 4, 7), dtype=np.int64)
# [zobrist_key, depth, score, flag, move_from, move_to, age]
```

**Option B: If repetition detection is slowest:**

**Problem:** `repetition_stack.count(zobrist_key)` is O(n)
```python
# Current (slow):
if repetition_stack.count(board.zobrist_key) >= 2:
    return 0
```

**Solution:** Use set or dict for O(1) lookup
```python
# Fast: track counts in dict
repetition_counts = {}
def check_repetition(key):
    count = repetition_counts.get(key, 0)
    return count >= 2

def make_move_with_repetition(key):
    repetition_counts[key] = repetition_counts.get(key, 0) + 1

def unmake_move_with_repetition(key):
    repetition_counts[key] -= 1
    if repetition_counts[key] == 0:
        del repetition_counts[key]
```

**Option C: If move ordering is slowest:**

**Problem:** Python lists for killer/history
```python
# Current (slow):
self.killer_moves: List[List[Optional[Tuple]]] = [[None, None] for _ in range(MAX_PLY)]
self.history: List[List[List[int]]] = [[[0]*64 for _ in range(64)] for _ in range(2)]
```

**Solution:** Use numpy arrays
```python
# Fast:
import numpy as np
self.killer_moves = np.zeros((MAX_PLY, 2, 3), dtype=np.int16)  # [from, to, promo]
self.history = np.zeros((2, 64, 64), dtype=np.int32)
```

### Phase 3: Optimize Evaluation (if time permits)

**Target:** _evaluate_mobility and _evaluate_king_safety (72% of eval time)

**Options:**
1. Cache mobility results (position hash → mobility score)
2. Approximate king safety (fewer attack checks)
3. Simplify mobility calculation (fewer piece types)

### Phase 4: Validate and Deploy

**Test improvement:**
```bash
python3 scripts/test_complete_profile.py 2>&1 | tee test4_after_fix.txt
```

**Compare:**
- Before: 5,083 NPS (search overhead 70%)
- Target: 15k-25k NPS (search overhead 30-40%)

**Deploy if successful:**
```bash
cd /root/pipier_love_api
git pull
sudo systemctl restart piperlove.service
curl http://localhost:8000/move -X POST -H "Content-Type: application/json" \
  -d '{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","ai_thinking_ms":1000}'
```

---

## 4. EXPECTED OUTCOMES

### Realistic Expectations

**Phase 1-2 (Search optimization):**
- Current: 5,083 NPS (search overhead 159ms)
- Target: 15k-20k NPS (search overhead 40-50ms)
- **Improvement: 3-4x speedup**

**Phase 3 (Evaluation optimization):**
- Current: 18,856 evals/sec
- Target: 40k-60k evals/sec
- **Improvement: 2-3x speedup**

**Combined:**
- Current: 5,083 NPS
- Target: 20k-30k NPS
- **Still 7-10x short of 200k NPS target**

### Reality Check

**The 200k NPS target may be unrealistic for pure PyPy:**
- Test 4 shows fundamental Python overhead (70% in search infrastructure)
- PyPy JIT can't eliminate object allocation costs
- May need to switch to CPython + C extensions for critical paths

**Alternative approaches if optimization doesn't reach target:**
1. Hybrid: CPython + Cython for hot paths
2. Simplify search (reduce TT size, simpler move ordering)
3. Lower target to realistic 30k-50k NPS
4. Profile on faster VPS hardware

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
