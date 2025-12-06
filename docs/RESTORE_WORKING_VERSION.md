# RESTORE WORKING PYPY VERSION

## Discovery
User remembered: "very old versions had PyPy performance of 100k-200k NPS"

Found in `PYPY_QUICKSTART.md`:
```
PyPy: 197,281 nodes in 0.2s = 986,405 NPS
```

Found in `CHANGES_SUMMARY.md` - document describing the WORKING version:
- PyPy got 986k NPS by REMOVING fast_ops imports
- Used direct imports from magic_bitboards instead
- No dynamic dispatch (no `pop_lsb = pop_lsb_fast` reassignments)

## Current Broken Code

**`src/move_generation.py` (BROKEN - 9k NPS):**
```python
from .magic_bitboards import pop_lsb, count_bits, get_lsb

from .fast_ops import (
    pop_lsb_fast,
    get_lsb_fast,
    count_bits_fast,
    ...
)

# DYNAMIC REASSIGNMENT - KILLS PyPy JIT!
pop_lsb = pop_lsb_fast
get_lsb = get_lsb_fast  
count_bits = count_bits_fast
```

**`src/chess_engine.py` (BROKEN):**
```python
from .magic_bitboards import (
    pop_lsb as _pop_lsb_orig,
    get_lsb as _get_lsb_orig,
    count_bits as _count_bits_orig,
)
# ... then imports from fast_ops and reassigns
```

## Fix: Restore Old Working Version

According to CHANGES_SUMMARY.md, the working version:

1. **Remove all fast_ops imports**
2. **Use direct imports from magic_bitboards only**
3. **Inline helper functions instead of importing them**

### File 1: `src/move_generation.py`

**Remove:**
```python
from .fast_ops import (
    pop_lsb_fast,
    get_lsb_fast,
    count_bits_fast,
    get_bit,
    get_pawn_single_push,
    get_pawn_double_push,
    is_promotion_square_lookup,
    can_double_push,
)

pop_lsb = pop_lsb_fast
get_lsb = get_lsb_fast  
count_bits = count_bits_fast
```

**Keep:**
```python
from .magic_bitboards import pop_lsb, count_bits, get_lsb
# Direct imports - NO reassignment!
```

**Inline helpers (add after imports):**
```python
# Inline helpers for PyPy JIT optimization
_WHITE_PROMO_RANK = frozenset(range(56, 64))  # Rank 8
_BLACK_PROMO_RANK = frozenset(range(0, 8))    # Rank 1
_WHITE_DOUBLE_RANK = frozenset(range(8, 16))  # Rank 2
_BLACK_DOUBLE_RANK = frozenset(range(48, 56)) # Rank 7

def get_bit(sq: int) -> int:
    return 1 << sq

def is_promotion_square_lookup(sq: int, side: int) -> bool:
    return sq in (_WHITE_PROMO_RANK if side == 0 else _BLACK_PROMO_RANK)

def can_double_push(sq: int, side: int) -> bool:
    return sq in (_WHITE_DOUBLE_RANK if side == 0 else _BLACK_DOUBLE_RANK)

def get_pawn_single_push(sq: int, side: int) -> int:
    return sq + 8 if side == 0 else sq - 8

def get_pawn_double_push(sq: int, side: int) -> int:
    return sq + 16 if side == 0 else sq - 16
```

### File 2: `src/chess_engine.py`

**Current broken:**
```python
from .magic_bitboards import (
    pop_lsb as _pop_lsb_orig,
    get_lsb as _get_lsb_orig,
    count_bits as _count_bits_orig,
)
# ... then tries to import from fast_ops
```

**Fix to:**
```python
from .magic_bitboards import (
    MagicBitboards,
    PreCalculatedAttacks,
    pop_lsb,  # Direct import - NO reassignment
    get_lsb,  # Direct import - NO reassignment  
    count_bits,  # Direct import - NO reassignment
)
```

## Expected Result

After restoring old working version:
- **PyPy**: 986k NPS (as documented in PYPY_QUICKSTART.md)
- **CPython**: 34k NPS (baseline)
- **Speedup**: 29x faster

## Why This Works

**PyPy JIT Requirements:**
1. Function calls must be DIRECT, not through variable references
2. No runtime reassignment of functions
3. Stable call targets for JIT to inline

**What Breaks PyPy JIT:**
```python
pop_lsb = pop_lsb_fast  # Variable reference
result = pop_lsb(bb)    # JIT can't inline - needs variable lookup
```

**What Allows PyPy JIT:**
```python
from magic_bitboards import pop_lsb  # Direct import
result = pop_lsb(bb)  # JIT can inline - stable target
```

## Implementation Steps

1. Backup current code (already in git)
2. Apply fixes to `src/move_generation.py`
3. Apply fixes to `src/chess_engine.py`
4. Run perft test (verify correctness)
5. Run diagnostic.py (should show 500k-1M NPS)
6. Deploy to VPS

## Risk Assessment

**SAFE:**
- CHANGES_SUMMARY.md documents this exact change worked before
- Someone accidentally reverted it by adding fast_ops back
- All tests passed with this version previously
- Expected 986k NPS is documented

**Action:** Restore the working version that gave 986k NPS!
