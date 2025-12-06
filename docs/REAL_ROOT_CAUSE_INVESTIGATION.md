# Deep Investigation: 6k NPS Catastrophe

## The Problem

**Observed**: PyPy getting 6k NPS vs CPython getting 40k NPS (7x SLOWER!)  
**Status**: Previous JIT optimization hypothesis was WRONG

## Why JIT Trace Issue Was Wrong Hypothesis

1. **"trace too long: 6"** would make PyPy fall back to **interpreter mode**
2. PyPy interpreter ≈ CPython interpreter speed (maybe 0.8-1.2x)
3. We're seeing **7x SLOWER** - this is NOT explainable by JIT fallback
4. Something else is fundamentally broken

## Possible Root Causes (Ranked by Likelihood)

### 1. Position Wrapper Overhead (HIGH PROBABILITY)

**Evidence from VPS diagnostic:**
```
Position wrapper: 32.4ms vs ChessBoard: 14.1ms (2.3x overhead)
```

**Theory**: Position class adds method call overhead that PyPy can't optimize:
- Every perft call goes through `Position._board.generate_moves()`
- Attribute access `self._board` on every operation
- Extra indirection prevents JIT from inlining

**Test**: Run `investigate_real_problem.sh` Test 1a vs 1b to compare direct ChessBoard vs Position wrapper

---

### 2. Import/Module Loading Bottleneck (MEDIUM PROBABILITY)

**Theory**: Circular imports or complex import chain slowing down PyPy
- `board_state.py` imports `chess_engine.py`
- `chess_engine.py` imports `move_generation.py` and `move_execution.py`
- Each imports `magic_bitboards.py`, `fast_ops.py`, etc.
- PyPy might be re-loading modules or struggling with import resolution

**Test**: Check import times and module count in investigation script

---

### 3. PyPy Version/Compatibility Issue (MEDIUM PROBABILITY)

**Theory**: VPS running older/incompatible PyPy version
- Older PyPy versions had performance bugs
- Incompatible bytecode compilation
- Missing JIT optimizations in that version

**Current VPS**: PyPy 3.9.18 (7.3.15)
**Test**: Check if newer PyPy available, compare with dev container

---

### 4. C Extension Interference (LOW PROBABILITY)

**Theory**: Some C extension being loaded that PyPy can't optimize
- Would show up in `sys.modules` with `.so` or `.pyd` extension
- PyPy's C extension compatibility layer is slow

**Test**: Check for C extensions in investigation script

---

### 5. CPU Throttling / Resource Limits (LOW PROBABILITY)

**Theory**: VPS has CPU throttled or memory-limited
- Would affect all Python code, not just PyPy
- User said 1.2GB memory usage is normal for TT

**Test**: Check `/proc/cpuinfo`, `free -h`, `uptime` for constraints

---

### 6. Recursive Function Overhead (LOW PROBABILITY - ALREADY RULED OUT)

**Theory**: Nested `_perft()` function prevents optimization
- **COUNTER-EVIDENCE**: CPython also uses nested function but gets 40k NPS
- If this was the issue, CPython would be slow too

**Status**: UNLIKELY - this is not the root cause

---

## Investigation Plan

### Step 1: Run Deep Investigation Script on VPS

```bash
cd /root/pipier_love_api
bash investigate_real_problem.sh
```

This will test all 7 hypotheses systematically.

### Step 2: Interpret Results

**If Direct ChessBoard is MUCH faster than Position wrapper:**
→ **Root cause is Position wrapper overhead**
→ Fix: Optimize Position class or use ChessBoard directly

**If both Direct ChessBoard AND Position are slow on PyPy:**
→ **Root cause is PyPy environment issue**
→ Fix: Check PyPy version, CPU throttling, or reinstall PyPy

**If CPython is also slow:**
→ **Root cause is VPS hardware/throttling**
→ Fix: Upgrade VPS or optimize hardware usage

**If import time > 100ms:**
→ **Root cause is import bottleneck**
→ Fix: Refactor circular imports, lazy loading

---

## Expected Investigation Output

### Scenario A: Position Wrapper Problem
```
Direct ChessBoard: 35,000 NPS     ← Good!
Position wrapper: 6,000 NPS       ← PROBLEM!
CPython Position wrapper: 40,000 NPS  ← CPython handles wrapper fine
```
**Diagnosis**: PyPy can't optimize through Position wrapper indirection  
**Fix**: Use ChessBoard directly or mark Position methods for inlining

### Scenario B: PyPy Environment Problem
```
Direct ChessBoard: 6,000 NPS      ← PROBLEM!
Position wrapper: 6,000 NPS       ← Also slow
CPython ChessBoard direct: 45,000 NPS  ← CPython fine
JIT enabled: False                 ← AHA!
```
**Diagnosis**: PyPy JIT not actually enabled or broken  
**Fix**: Reinstall PyPy, check environment variables

### Scenario C: Hardware Throttling
```
Direct ChessBoard: 6,000 NPS      ← Slow
Position wrapper: 6,000 NPS       ← Slow
CPython ChessBoard: 8,000 NPS     ← Also slow!
CPU MHz: 800 (throttled)          ← AHA!
```
**Diagnosis**: VPS CPU throttled to save power/cost  
**Fix**: Upgrade VPS plan or optimize algorithm further

---

## Next Steps After Investigation

1. **Run investigation script on VPS**
2. **Identify which scenario matches**
3. **Apply minimal, safe fix for actual root cause**
4. **Verify fix with perft test**
5. **Deploy to production**

---

## Key Insight

**6k NPS is TOO SLOW to be a code optimization issue.** Something environmental or architectural is fundamentally wrong. The investigation script will reveal the true culprit.

Your instinct was 100% correct to question the JIT hypothesis!
