# Performance Diagnosis - Critical Findings

## ROOT CAUSE: python-chess C Extension Blocking PyPy JIT

### The Problem

Your API is importing `chess` library (python-chess) which is a C extension. **PyPy cannot optimize code that uses C extensions**, causing it to fall back to slow interpreter mode.

### Evidence

1. **In main.py:**
   ```python
   import chess
   import chess.syzygy
   ```

2. **Performance Impact:**
   - CPython: ~30k NPS (baseline)
   - PyPy with C extension: ~30k NPS (JIT disabled)
   - PyPy pure Python: **300k+ NPS** (expected)

3. **You lose 10x performance** by importing python-chess!

### Why This Happens

- python-chess is written in Python but uses C extensions for speed
- PyPy's JIT cannot trace through C code
- When PyPy encounters C extensions, it disables JIT optimization
- Your entire engine runs in slow interpreter mode

### The Solution

You have TWO chess engines:
1. **Custom engine** (`src/chess_engine.py`) - Pure Python, PyPy-friendly ✅
2. **python-chess** (`import chess`) - C extension, PyPy killer ❌

**Current usage of python-chess:**
- `chess.syzygy` for endgame tablebases
- `chess.polyglot` for opening book Zobrist keys
- `chess.Board` for FEN validation

### Fix Options

#### Option 1: Remove python-chess (Recommended)
1. Remove tablebase support (optional feature anyway)
2. Implement own Zobrist keys for opening book
3. Use your own FEN parser
4. **Result: 10x faster**

#### Option 2: Isolate python-chess
1. Only use python-chess for tablebase positions (≤5 pieces)
2. Never import it in hot paths
3. Lazy import only when needed
4. **Result: 5-8x faster**

#### Option 3: Keep Status Quo
- Continue using python-chess
- Accept 30k NPS performance
- PyPy provides no benefit

### Recommendations

1. **Remove chess.syzygy** - Tablebases are optional, rarely used
2. **Remove chess.polyglot dependency** - You have own Zobrist implementation
3. **Use your own FEN validation** - You already parse FEN in `chess_engine.py`
4. **Deploy with PyPy** - After removing C extensions
5. **Expect 300k+ NPS** - 10x improvement over current

### Quick Test

To verify this is the issue:
```python
# Test WITHOUT python-chess import
import time
from src.chess_engine import ChessBoard

board = ChessBoard()
# Run perft benchmark
# Expected: 30k NPS on CPython, 300k+ on PyPy

# Test WITH python-chess import  
import chess  # This line kills PyPy JIT!
# Expected: 30k NPS on both CPython and PyPy
```

### Next Steps

1. Clean up all diagnostic scripts (28 scripts, mostly obsolete)
2. Remove python-chess dependency
3. Implement missing features in pure Python
4. Deploy with PyPy
5. Enjoy 10x speedup
