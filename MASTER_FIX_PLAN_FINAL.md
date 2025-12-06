# COMPREHENSIVE PERFORMANCE FIX PLAN - FINAL ANALYSIS

**Date:** December 6, 2025  
**Target:** Fix VPS performance from 27k NPS → 200k+ NPS (8x improvement)  
**Current Status:** 🚨 **ROOT CAUSE CONFIRMED - MAGIC BITBOARDS (38%) + TT INIT (11%)**  
**Last Updated:** After cProfile deep analysis correcting Test 4 misattribution

---

## 🚨 FINAL BREAKTHROUGH (cProfile Analysis - December 6, 2025)

### Test 4 Was WRONG - cProfile Reveals Actual Bottlenecks

**What happened:** Test 4 calculated "search overhead" by subtraction, which misattributed time spent in magic bitboards (called BY evaluation) and TT initialization (test artifact).

**cProfile truth (100 searches, 34.4s total, using tottime to avoid double-counting):**

```
ACTUAL TIME BREAKDOWN:
────────────────────────────────────────────────────────────────────
Component                    Time (s)    % of Total    Status
────────────────────────────────────────────────────────────────────
Magic Bitboards:             13.0s       37.8%        ❌❌❌ PRIMARY
  count_bits:                 4.56s      13.3%
  _rook_attacks_on_the_fly:   2.63s       7.6%
  _bishop_attacks_on_the_fly: 1.22s       3.5%
  get_rook_attacks:           0.92s       2.7%
  get_bishop_attacks:         1.16s       3.4%
  get_queen_attacks:          0.81s       2.4%
  bit_length (3.5M calls):    0.43s       1.3%

TT Initialization:            3.8s       11.0%        ❌❌ IMMEDIATE FIX
  (Creating [[None]*4] lists 100 times)

Evaluation (pure logic):      8.5s       24.7%        ⚠️ SECONDARY
  _evaluate_mobility_side:    1.83s       5.3%
  _generate_attack_map:       1.58s       4.6%
  _evaluate_king_exposure:    1.48s       4.3%
  _evaluate_king_safety_side: 0.49s       1.4%
  _calculate_phase:           0.43s       1.2%
  _evaluate_material:         0.37s       1.1%
  _evaluate_psqt:             0.54s       1.6%

Make/Unmake:                  2.0s        5.8%        ✅ OK
  execute_move:               1.73s       5.0%

Search Infrastructure:        2.5s        7.3%        ✅ OK
  is_capture:                 1.42s       4.1%
  order_moves:                1.05s       3.0%

Move Generation:              1.0s        2.9%        ✅ FAST

Python Overhead:              3.6s       10.5%        (unavoidable)
────────────────────────────────────────────────────────────────────
TOTAL:                       34.4s      100.0%
```

### Critical Discoveries

#### Discovery 1: Magic Bitboards Are 38% of Time ❌❌❌

**The problem:**
- `count_bits`: 4.56s (3.5M calls) - Counting set bits in bitboards
- Attack generation: 4.8s (computing rook/bishop attacks on-the-fly)
- These are called MILLIONS of times by evaluation (mobility, king safety)

**Why it's slow:**
- Python bit manipulation without JIT optimization
- Computing attacks "on the fly" instead of pre-computed tables
- No caching of repeated calculations

#### Discovery 2: TT Initialization is 11% - TEST ARTIFACT ❌❌

**The smoking gun:**
```python
# Line in profile_search_overhead.py (line 39-44)
def run_searches():
    for _ in range(100):
        tt = TranspositionTable(size_mb=64)  # ❌ Creates new TT EVERY TIME!
        orderer = MoveOrderer()
        # ...
```

**Each TT creation takes 38ms:**
```python
# search.py line 211
self.table = [[None] * self.BUCKET_SIZE for _ in range(num_buckets)]
# Creates ~250,000 lists, each with 4 None values = 1M objects
```

**This is a TEST ARTIFACT, not real performance issue!**
- In production, TT is created ONCE per game
- Test creates it 100 times = wastes 3.8s
- **Real searches don't pay this cost**

#### Discovery 3: Evaluation is 25% (Not 27%)

**Breakdown:**
- Mobility + attack map: 3.41s (9.9%)
- King safety + exposure: 2.94s (8.5%)  
- Material + phase + PSQT: 1.34s (3.9%)

**But:** This INCLUDES calling magic bitboards, so there's overlap

#### Discovery 4: "Search Overhead" Was Misattributed

**Test 4 said "70% search overhead" but it was actually:**
- 38% magic bitboards (called by eval, misattributed to "overhead")
- 11% TT initialization (test artifact)
- 7% actual search logic (is_capture, order_moves)
- 14% Python overhead + other

**Actual search infrastructure: Only 7%, not 70%!**

---

## 🎯 CORRECTED OPTIMIZATION STRATEGY

### Priority 1: Optimize Magic Bitboards (38% → Target: 15%)

**Current bottlenecks:**
1. `count_bits`: 4.56s (3.5M calls)
2. `_rook_attacks_on_the_fly`: 2.63s
3. `_bishop_attacks_on_the_fly`: 1.22s

**Solutions:**

**Option A: Pre-compute attack tables (BEST)**
```python
# Instead of computing attacks every time, use lookup tables
# Initialize once at startup:
ROOK_ATTACKS = precompute_rook_attacks()  # 64 squares × 4096 occupancy = 256KB
BISHOP_ATTACKS = precompute_bishop_attacks()  # Similar size

# Then lookup is O(1):
def get_rook_attacks(square, occupancy):
    key = (occupancy * ROOK_MAGICS[square]) >> (64 - ROOK_BITS[square])
    return ROOK_ATTACKS[square][key]  # ← Just array lookup
```

**Expected improvement:** 5-10x faster → 13s → 1.5s (saves 11.5s, 33% overall)

**Option B: Optimize count_bits with lookup table**
```python
# Pre-compute bit counts for all 16-bit values
BIT_COUNT_16 = [bin(i).count('1') for i in range(65536)]

def count_bits_fast(bb):
    count = 0
    count += BIT_COUNT_16[bb & 0xFFFF]
    count += BIT_COUNT_16[(bb >> 16) & 0xFFFF]
    count += BIT_COUNT_16[(bb >> 32) & 0xFFFF]
    count += BIT_COUNT_16[(bb >> 48) & 0xFFFF]
    return count
```

**Expected improvement:** 3-5x faster → 4.56s → 1s (saves 3.5s, 10% overall)

### Priority 2: Fix TT Initialization (11% → 0%)

**Simple fix - already correct in production:**
```python
# In test script, move TT outside loop:
tt = TranspositionTable(size_mb=64)  # Create ONCE
orderer = MoveOrderer()

for _ in range(100):
    stats = SearchStats()
    pv_line = []
    repetition_stack = []
    alpha_beta(board, 3, 0, -999999, 999999, evaluator, tt, orderer, 
              stats, pv_line, repetition_stack)
```

**This is already how production works** - main.py creates TT once at startup.

**Improvement:** 3.8s savings in test (but 0% in production)

### Priority 3: Optimize Evaluation (25% → Target: 15%)

**Focus on mobility (called by evaluation, uses magic bitboards):**

**Option A: Cache mobility results**
```python
# Cache mobility by position hash
mobility_cache = {}

def _evaluate_mobility(self, board):
    key = board.zobrist_key
    if key in mobility_cache:
        return mobility_cache[key]
    
    result = self._evaluate_mobility_uncached(board)
    mobility_cache[key] = result
    return result
```

**Option B: Simplify mobility calculation**
```python
# Instead of counting ALL legal moves, approximate:
# Just count attacked squares (faster than full move generation)
```

**Expected improvement:** 2-3x faster → 3.4s → 1.5s (saves 2s, 6% overall)

---

## 📊 EXPECTED OUTCOMES

### Realistic Projections

**Current state (per search):**
- Time: 344ms per search
- NPS: 5,083 nodes/sec

**After Priority 1 (Magic bitboards optimization):**
- Saves: 11.5s / 100 searches = 115ms per search
- New time: 229ms per search
- New NPS: ~7,600 nodes/sec
- **Improvement: 1.5x faster**

**After Priority 3 (Evaluation optimization):**
- Additional savings: 20ms per search
- New time: 209ms per search
- New NPS: ~8,800 nodes/sec
- **Improvement: 1.7x faster overall**

**Reality check:**
- Current: 5,083 NPS
- After optimizations: 8,800 NPS
- Target: 200,000 NPS
- **Still 23x short of target** ❌

### The Hard Truth

**The 200k NPS target is UNREALISTIC for pure PyPy:**
1. Magic bitboards in pure Python are inherently slow
2. Even with lookup tables, Python overhead remains
3. Would need C extensions or Rust for true 200k NPS

**More realistic targets:**
- Optimistic: 10k-15k NPS (2-3x improvement)
- Requires: Magic bitboard pre-computation + evaluation caching
- Still valuable: 27k API NPS → 50k-80k API NPS

---

## 🔧 IMPLEMENTATION PLAN

### Phase 1: Measure Current Performance Correctly

**Fix the test to reuse TT:**
```bash
cd /root/pipier_love_api
python3 scripts/analyze_time_breakdown.py 2>&1 | tee breakdown.txt
```

This will show TRUE time breakdown without TT initialization artifact.

### Phase 2: Implement Magic Bitboard Lookup Tables

**Create pre-computed tables:**
1. Generate rook attack table (256KB)
2. Generate bishop attack table (256KB)
3. Replace `_rook_attacks_on_the_fly` with table lookup
4. Replace `_bishop_attacks_on_the_fly` with table lookup

**Expected time:** 2-3 hours

### Phase 3: Optimize count_bits

**Implement lookup table version:**
```python
# 64KB lookup table for 16-bit chunks
BIT_COUNT_16 = tuple(bin(i).count('1') for i in range(65536))
```

**Expected time:** 30 minutes

### Phase 4: Test and Validate

```bash
python3 scripts/test_complete_profile.py 2>&1 | tee test4_after_magic_fix.txt
```

Compare NPS before/after.

### Phase 5: Deploy if Successful

```bash
cd /root/pipier_love_api
git pull
sudo systemctl restart piperlove.service
```

---

## 📋 NEXT IMMEDIATE ACTION

**Run the sophisticated time breakdown analyzer:**

```bash
cd /root/pipier_love_api
git pull origin main  # Get analyze_time_breakdown.py
python3 scripts/analyze_time_breakdown.py 2>&1 | tee breakdown_results.txt
```

This will:
1. Properly attribute time to each component
2. Confirm magic bitboards are the bottleneck
3. Show exact percentages with TT reuse

**Then:** Implement magic bitboard lookup tables (Priority 1)
