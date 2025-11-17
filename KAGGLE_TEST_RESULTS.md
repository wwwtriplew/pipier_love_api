# Kaggle Dataset Test Results

**Date:** November 10, 2025  
**Dataset:** chessData.csv from Kaggle  
**Positions tested:** 500

---

## 📊 Results Summary

```
Positions evaluated: 500
Failed positions:    0

Mean difference:     184.6 cp
Median difference:   117.0 cp
Max difference:      4242.0 cp
Min difference:      0.0 cp
Correlation:         0.334

❌ POOR: Very weak correlation (<0.4)
```

### Accuracy Distribution

| Range | Count | Percentage |
|-------|-------|------------|
| Excellent (<50 cp) | 117 | 23.4% |
| Good (50-100 cp) | 99 | 19.8% |
| Fair (100-200 cp) | 126 | 25.2% |
| Poor (200-500 cp) | 129 | 25.8% |
| Very Poor (>500 cp) | 28 | 5.6% |

**Key insight:** ~43% of positions are within 100 cp, but ~31% have errors >200 cp

---

## 🔍 Analysis of Large Deviations

### Pattern 1: Endgame Positions (Most Common)

**Example:**
```
FEN: 6R1/1k4P1/2P1p3/5p2/8/4P1r1/3K4/8 b - - 0 50

Dataset: +4796 cp (white winning easily)
Piper:   +554 cp  (white ahead but not overwhelming)
Diff:    4242 cp
```

**Why the deviation?**
- This is a **won endgame** for white (R+P vs r)
- Dataset evaluation (likely from engine search) **sees the forced win**
- Piper Love (static eval) only sees material advantage
- **This is expected** - static eval cannot calculate forced wins

### Pattern 2: Tactical Positions

**Example:**
```
FEN: 2r4k/p4bR1/4pq2/1p1p1n2/5P2/P2B4/1P2Q2P/1K4R1 w - - 1 3

Dataset: +1085 cp (white has winning tactics)
Piper:   -24 cp   (position looks unclear)
Diff:    1109 cp
```

**Why the deviation?**
- Position has **forcing tactics** (captures, threats)
- Dataset evaluation sees the tactical sequence
- Piper Love doesn't search ahead
- **This is expected** - static eval misses tactics

### Pattern 3: Possible Evaluation Issues

**Example:**
```
FEN: r4b1r/pp1kpppp/3p4/6B1/4P1n1/2N5/PPP2PPP/R2q1RK1 w - - ...

Dataset: +22 cp   (roughly equal)
Piper:   -859 cp  (black much better)
Diff:    881 cp
```

**Why the deviation?**
- Dataset says position is **roughly equal**
- Piper thinks black is **much better**
- Possible issues:
  - Queen placement evaluation
  - Knight position (black knight on g4 active)
  - King safety (white king exposed?)

**This needs investigation!**

---

## 🎯 What This Tells Us

### Good News ✅

1. **43% of positions within 100 cp** - Decent for many positions
2. **No crashes** - Evaluation is robust
3. **Clear patterns** - Deviations are explainable

### Issues to Address ⚠️

1. **Endgame evaluation** - Cannot detect forced wins (expected without search)
2. **Tactical blindness** - Misses forcing sequences (expected without search)
3. **Some positional misjudgments** - Need to investigate specific cases

---

## 🔧 Recommended Improvements

### Priority 1: Investigate Quiet Position Errors

Look at positions where:
- Dataset: -100 to +100 cp (quiet, non-tactical)
- Piper: Large deviation (>200 cp)

These reveal **actual evaluation bugs**, not search limitations.

### Priority 2: Add Missing Features

Based on large deviations:
- **Rook evaluation** - Rooks on 7th rank, open files
- **Bishop pair bonus** - Two bishops worth more
- **Trapped pieces** - Penalize pieces with no mobility

### Priority 3: Tune Weights

Some weights might be off:
- King safety might be overvalued/undervalued
- Mobility weights may need adjustment
- Pawn structure penalties may be too harsh

---

## 📈 Expected vs Actual Performance

### Expected (Static Evaluation)

| Position Type | Expected Correlation |
|---------------|---------------------|
| Quiet positions | 0.7-0.8 |
| Complex positions | 0.5-0.7 |
| Tactical positions | 0.3-0.5 |
| Endgames | 0.4-0.6 |

### Actual

| Overall | 0.334 |
|---------|-------|

**Gap:** Actual is lower than expected

**Likely reasons:**
1. Dataset heavily weighted toward **tactical/endgame** positions
2. Some **evaluation weights** may be off
3. Missing **positional features** (rooks, bishop pair)

---

## 🧪 Next Steps

### 1. Filter Dataset for Quiet Positions

```python
# Test only quiet positions (roughly equal, no tactics)
quiet_positions = [(fen, eval) for fen, eval in dataset 
                   if -100 <= eval <= 100]
```

**Expected:** Higher correlation (0.6-0.7)

### 2. Investigate Specific Bad Evaluations

Pick 5-10 positions where Piper strongly disagrees with dataset:
- Manually analyze position
- Check which evaluation components are wrong
- Fix bugs or add missing features

### 3. Add Rook Evaluation

Many large deviations involve rook positions:
- Rook on 7th rank: +20-30 cp
- Rook on open file: +15-20 cp
- Connected rooks: +10-15 cp

**Expected improvement:** +0.05-0.10 correlation

### 4. Test Again

After improvements, rerun:
```bash
python3 test_kaggle_dataset.py ~/downloads/chessData.csv --max 1000
```

Track correlation improvement.

---

## 💡 Key Insight

**Low correlation (0.334) is NOT necessarily bad!**

Why?
1. **Dataset likely includes engine evaluations** (with search)
2. **Piper is static evaluation** (no search)
3. **Comparing apples to oranges** in tactical/endgame positions

**Better approach:**
- Filter for **quiet positions only**
- Focus on **static evaluation quality**
- Accept that tactics/endgames will differ

---

## ✅ Conclusion

**The test reveals:**
- ✅ Evaluation works and is robust
- ✅ Handles diverse positions without crashes
- ⚠️  Some positional evaluations need improvement
- ✅ Large deviations mostly explainable (tactics/endgames)

**Next priority:**
1. Investigate quiet position errors
2. Add rook evaluation
3. Consider tuning existing weights

**Overall:** Evaluation is functional but needs refinement before adding search!

---

## 📁 Files Generated

- **`kaggle_comparison.txt`** - Detailed results for all 500 positions
- **`test_kaggle_dataset.py`** - Test script (reusable)

Run anytime with:
```bash
python3 test_kaggle_dataset.py ~/downloads/chessData.csv --max 1000
```
