# VERIFICATION PLAN - Before Making Any Code Changes

## Objective
Prove with hard data that method complexity is the bottleneck, not just speculation.

## Current Situation
- **Known:** PyPy JIT works (333M ops/sec baseline)
- **Known:** evaluate() is slow (17.8k evals/sec, only 1.3x faster than CPython)
- **Hypothesis:** Method calls + complexity block JIT compilation
- **Risk:** Premature optimization without proof

## Test Suite

### Test 1: JIT Compilation Verification (CRITICAL)
**File:** `scripts/verify_jit_problem.py`  
**Run on VPS:**
```bash
cd /root/pipier_love_api
source venv/bin/activate
python3 scripts/verify_jit_problem.py 2>&1 | tee vps_jit_verification.log
```

**What it does:**
- Enables PYPYLOG to see JIT activity
- Runs simple baseline (should show JIT compilation)
- Runs evaluate() warmup (should show JIT compilation IF hypothesis wrong)

**Evidence needed:**
- ✅ CONFIRMS hypothesis: No "Tracing"/"Backend" messages for evaluate
- ❌ REFUTES hypothesis: Sees JIT messages for evaluate

**Time:** 2 minutes

---

### Test 2: Method Call Overhead
**File:** `scripts/test_method_overhead.py`  
**Run on VPS:**
```bash
python3 scripts/test_method_overhead.py
```

**What it does:**
- Version A: evaluate() with method calls (_calculate_phase, _evaluate_material)
- Version B: evaluate() with everything inlined
- Measures speedup of inlined version

**Evidence needed:**
- >3x speedup: Method calls ARE major bottleneck → inline
- 1.5-3x speedup: Method calls have overhead → inline + investigate more
- <1.5x speedup: Method calls NOT the issue → don't inline

**Time:** 1 minute

---

### Test 3: Method Profiling
**File:** `scripts/test_profile_methods.py`  
**Run on VPS:**
```bash
python3 scripts/test_profile_methods.py
```

**What it does:**
- Profiles each sub-method individually
- Identifies which methods are slowest
- Shows what % of time each takes

**Evidence needed:**
- Identifies 2-3 slowest methods
- Shows if some methods are fast (inline candidates)
- Shows if all methods are slow (different problem)

**Time:** 2 minutes

---

## Decision Matrix

### Scenario A: All Tests Confirm Hypothesis
**Test 1:** No JIT compilation of evaluate()  
**Test 2:** >3x speedup with inlining  
**Test 3:** Multiple fast methods being called repeatedly

**Decision:** ✅ Proceed with inline optimization  
**Expected improvement:** 10-20x (200k-400k evals/sec)

---

### Scenario B: Mixed Results
**Test 1:** No JIT compilation  
**Test 2:** 1.5-3x speedup  
**Test 3:** Some methods very slow

**Decision:** ⚠️ Targeted optimization  
- Inline only fast, frequently-called methods
- Optimize slow methods separately
**Expected improvement:** 5-10x (90k-180k evals/sec)

---

### Scenario C: Tests Refute Hypothesis
**Test 1:** JIT IS compiling evaluate()  
**Test 2:** <1.5x speedup  
**Test 3:** All methods slow

**Decision:** ❌ Do NOT inline  
**Action:** Investigate actual bottleneck:
- Attribute access patterns?
- Specific operations (popcount, bit operations)?
- Hash table implementation?
- Magic bitboard lookups?

---

## Timeline

**Phase 1: Verification (Total: 10 minutes)**
1. Commit test scripts (done)
2. Push to repo (done)
3. SSH to VPS
4. Pull latest code
5. Run Test 1 (2 min)
6. Run Test 2 (1 min)
7. Run Test 3 (2 min)
8. Analyze results (5 min)

**Phase 2: Documentation (5 minutes)**
1. Update MASTER_FIX_PLAN.md with results
2. Document which scenario (A/B/C) we're in
3. Write specific implementation plan

**Phase 3: Implementation (ONLY if verified)**
- If Scenario A: Implement full inline (30 min)
- If Scenario B: Targeted optimization (20 min)
- If Scenario C: Re-investigate (start over)

## Commands to Run on VPS

```bash
# 1. Get latest tests
cd /root/pipier_love_api
git pull origin main

# 2. Activate PyPy environment
source venv/bin/activate

# 3. Run verification suite
echo "=== TEST 1: JIT Compilation ===" > verification_results.txt
python3 scripts/verify_jit_problem.py 2>&1 | tee -a verification_results.txt

echo "" >> verification_results.txt
echo "=== TEST 2: Method Overhead ===" >> verification_results.txt
python3 scripts/test_method_overhead.py 2>&1 | tee -a verification_results.txt

echo "" >> verification_results.txt
echo "=== TEST 3: Method Profiling ===" >> verification_results.txt
python3 scripts/test_profile_methods.py 2>&1 | tee -a verification_results.txt

# 4. View results
cat verification_results.txt
```

## Success Criteria

We can proceed with implementation ONLY if:
- [ ] Test 1 confirms no JIT compilation of evaluate()
- [ ] Test 2 shows >1.5x speedup with inlining
- [ ] Test 3 identifies specific slow methods
- [ ] All results are consistent and point to same solution
- [ ] MASTER_FIX_PLAN.md updated with verified data

## Risks of Skipping Verification

1. **Wrong diagnosis** → Waste time on ineffective fix
2. **Code complexity** → 400+ line function hard to maintain
3. **Regression risk** → Might break existing functionality
4. **Missed opportunity** → Real bottleneck remains unfixed
5. **Lost confidence** → Team loses trust in optimization process

## Benefits of Verification

1. **Certainty** → Know exactly what to fix
2. **Measurable** → Can predict improvement accurately
3. **Targeted** → Fix only what needs fixing
4. **Reversible** → If wrong, easy to backtrack
5. **Learning** → Understand PyPy JIT behavior for future

---

**Next Action:** Run verification suite on VPS, report results, then decide.
