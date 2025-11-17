# Testing Setup - Quick Start

## 🎯 Goal

Test your Piper Love evaluation against Stockfish to measure quality and find areas for improvement.

---

## 📦 Prerequisites

### 1. Install Stockfish

```bash
brew install stockfish
```

**Verify installation:**
```bash
stockfish
# Should open Stockfish console
# Type "quit" to exit
```

---

## 🚀 Run Evaluation Test

### Basic Test (50 positions, depth 15)

```bash
cd ~/piper_love
python3 test_against_stockfish.py --positions 50 --depth 15
```

**Expected output:**
```
✅ Stockfish started successfully
Generating 50 test positions...
✅ Generated 50 positions
Testing 50 positions...

RESULTS
======================================================================
Positions evaluated: 50
Mean difference:     127.3 cp
Correlation:         0.742

✅ GOOD: Moderate correlation (≥0.6)
```

---

## 📊 Interpreting Results

### Correlation Score

| Score | Quality | Next Steps |
|-------|---------|------------|
| 0.8+  | Excellent | Ready for search implementation! |
| 0.6-0.8 | Good | Add more positional features |
| 0.4-0.6 | Fair | Review evaluation weights |
| <0.4  | Poor | Major issues, debug evaluation |

### Your Target

**Current features:** Material, PSQT, Pawns, King Safety, Mobility  
**Expected correlation:** 0.6-0.7  
**Goal:** Reach 0.75+ before adding search

---

## 🔧 Test Options

### Quick Test (fast, less accurate)
```bash
python3 test_against_stockfish.py --positions 20 --depth 10
```

### Thorough Test (slow, more accurate)
```bash
python3 test_against_stockfish.py --positions 200 --depth 18
```

### Default (recommended)
```bash
python3 test_against_stockfish.py --positions 100 --depth 15
```

---

## 📁 Output Files

After running, you'll get:

- **Terminal output:** Summary statistics
- **`evaluation_comparison.txt`:** Detailed results for every position

---

## 🐛 Troubleshooting

### Error: "Stockfish not found"

```bash
# Install Stockfish
brew install stockfish

# Verify it's in PATH
which stockfish
# Should output: /opt/homebrew/bin/stockfish (or similar)
```

### Error: "ModuleNotFoundError"

```bash
# Make sure you're in the piper_love directory
cd ~/piper_love

# Verify files exist
ls -la test_against_stockfish.py
```

---

## 🎓 Understanding Deviations

### Normal Large Deviations

**Tactical positions** - Stockfish sees ahead, Piper doesn't:
```
Stockfish: +300 cp (finds winning tactic)
Piper:     +50 cp  (static evaluation)
Difference: 250 cp ← This is expected!
```

**Endgames** - Require deep calculation:
```
Stockfish: +400 cp (knows white wins)
Piper:     +10 cp  (sees material equality)
Difference: 390 cp ← Also expected!
```

### Concerning Deviations

**Material evaluation** - Should be close:
```
Stockfish: +300 cp (white up a piece)
Piper:     +100 cp (white up a piece)
Difference: 200 cp ← Check material values!
```

**Quiet positions** - Should agree:
```
Stockfish: +50 cp  (slight advantage)
Piper:     -200 cp (thinks black is winning)
Difference: 250 cp ← Bug in evaluation!
```

---

## 📈 Benchmarking Progress

Keep track of improvements:

```bash
# Test 1 (baseline)
python3 test_against_stockfish.py --positions 100 --depth 15 | tee results_v1.txt

# Add rook evaluation...

# Test 2 (with rooks)
python3 test_against_stockfish.py --positions 100 --depth 15 | tee results_v2.txt

# Compare correlations
grep "Correlation:" results_v1.txt
grep "Correlation:" results_v2.txt
```

---

## 🎯 Next Steps

1. **Run baseline test:**
   ```bash
   python3 test_against_stockfish.py --positions 100 --depth 15
   ```

2. **Check correlation:**
   - If 0.6-0.7: ✅ Good! Add more features (rooks, bishop pair)
   - If 0.4-0.6: ⚠️  Review evaluation weights
   - If <0.4: ❌ Debug evaluation function

3. **Analyze largest deviations:**
   - Look at `evaluation_comparison.txt`
   - Identify position types with biggest errors
   - Add evaluation features for those positions

4. **Iterate:**
   - Add feature
   - Retest
   - Measure improvement
   - Repeat!

---

## 📚 More Information

See **`docs/STOCKFISH_TESTING.md`** for:
- Detailed interpretation guide
- How to test specific position types
- Expected performance benchmarks
- Improvement roadmap

---

## ✅ Quick Checklist

- [ ] Stockfish installed (`brew install stockfish`)
- [ ] Stockfish working (`stockfish` command works)
- [ ] In piper_love directory (`cd ~/piper_love`)
- [ ] Run test: `python3 test_against_stockfish.py`
- [ ] Check results: correlation and mean difference
- [ ] Review largest deviations
- [ ] Identify improvement areas

**Ready to test!** 🚀
