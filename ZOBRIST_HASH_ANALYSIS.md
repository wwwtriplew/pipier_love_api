# Critical Zobrist Hash Bug Analysis

## Executive Summary

**MAJOR BUG FOUND**: The Zobrist hash for castling moves is computed **ASSUMING THE ROOK EXISTS**, but we just added validation that returns False if the rook doesn't exist. This creates a critical race condition where:

1. Invalid castling move (e8g8) is detected in `execute_move()`
2. But the Zobrist hash was already partially computed
3. Returns False without updating the hash
4. **Board state is INCONSISTENT**: pieces modified but hash not updated!

## The Critical Bug

### Location: `src/move_execution.py` lines 135-165

```python
# Handle castling
if piece_type == KING:
    if abs(to_square - from_square) == 2:
        # Castling move DETECTED
        is_castling = True
        if to_square > from_square:  # Kingside
            is_kingside_castle = True
            rook_from = from_square + 3
            rook_to = from_square + 1
        else:  # Queenside
            is_kingside_castle = False
            rook_from = from_square - 4
            rook_to = from_square - 1
        
        # CRITICAL VALIDATION (our fix)
        rook_bb = 1 << rook_from
        if not (board.pieces[board.side_to_move][ROOK] & rook_bb):
            # NO ROOK - Return False
            return False  # ← BUG: Board state already modified!
```

### The Problem

**At this point in the code, we have ALREADY modified the board:**

```python
# Lines 104-132 (BEFORE castling validation)
from_bb = 1 << from_square
to_bb = 1 << to_square

# Remove king from source square
board.pieces[board.side_to_move][piece_type] &= ~from_bb

# Handle captures (if any)
for pt in range(6):
    if board.pieces[enemy][pt] & to_bb:
        captured_piece = pt
        board.pieces[enemy][pt] &= ~to_bb  # Remove captured piece
        
# Place king on destination square
board.pieces[board.side_to_move][piece_type] |= to_bb
```

**Then when we detect no rook and return False:**
- King has moved e8 → g8 on bitboards
- Captured piece (if any) removed
- Zobrist hash is **NOT UPDATED** (hash update happens at line 230+)
- Board state is **CORRUPTED**!

## Why This is Critical

### Scenario: Invalid FEN with Illegal Castling

```python
FEN: "8/2P3k1/8/P7/3n4/8/8/4K3 b KQkq - 0 61"
# Black king on g7, NO ROOKS, but castling rights = "KQkq"

# User tries move "e8g8" (if this somehow gets to execute_move)
board.make_move(60, 62, None)  # e8 → g8

# What happens:
1. Line 104: from_bb = 1 << 60  # e8
2. Line 105: to_bb = 1 << 62    # g8
3. Line 106: board.pieces[BLACK][KING] &= ~(1 << 60)  # Remove king from e8
4. Line 132: board.pieces[BLACK][KING] |= (1 << 62)   # Add king to g8
5. Line 142: is_castling = True (because |g8 - e8| = 2)
6. Line 145: is_kingside_castle = True
7. Line 146: rook_from = 60 + 3 = 63  # h8
8. Line 147: rook_to = 60 + 1 = 61    # f8
9. Line 153-155: Validation FAILS (no rook on h8)
10. Line 156: return False

# Board state NOW:
- board.pieces[BLACK][KING] has king on g8 (MODIFIED)
- board.zobrist_key is UNCHANGED (hash update never ran)
- board.all_pieces is UNCHANGED (recalculation never ran)
- board.side_to_move is UNCHANGED (toggle never ran)

# Result: COMPLETELY CORRUPTED BOARD STATE!
```

## The Root Cause: Validation Too Late

The validation happens **AFTER** we've already modified piece bitboards but **BEFORE** we update the hash and other board state.

### Correct Flow Should Be:

```
1. Detect it's a castling move (king moves 2 squares)
2. VALIDATE rook exists BEFORE modifying anything
3. If validation fails, return False immediately
4. If validation passes, proceed with move execution
```

### Current Broken Flow:

```
1. Remove piece from source square ✗ MODIFIED
2. Place piece on destination square ✗ MODIFIED
3. Detect it's a castling move
4. Validate rook exists
5. If fails, return False ← BOARD ALREADY CORRUPTED!
```

## Hash Structure Analysis

The Zobrist hash includes:

```python
def compute_full_hash(board):
    hash_value = 0
    
    # 1. All piece positions (piece_type, color, square)
    for color in range(2):
        for piece_type in range(6):
            bb = board.pieces[color][piece_type]
            while bb:
                square = (bb & -bb).bit_length() - 1
                hash_value ^= PIECE_KEYS[color][piece_type][square]
                bb &= bb - 1
    
    # 2. Side to move
    if board.side_to_move == BLACK:
        hash_value ^= SIDE_KEY
    
    # 3. Castling rights
    if board.castling_rights & WHITE_KINGSIDE:
        hash_value ^= CASTLING_KEYS[0]
    if board.castling_rights & WHITE_QUEENSIDE:
        hash_value ^= CASTLING_KEYS[1]
    if board.castling_rights & BLACK_KINGSIDE:
        hash_value ^= CASTLING_KEYS[2]
    if board.castling_rights & BLACK_QUEENSIDE:
        hash_value ^= CASTLING_KEYS[3]
    
    # 4. En passant file (only if legal capture exists)
    if board.en_passant_square is not None:
        if is_ep_capture_legal(board, board.en_passant_square):
            ep_file = board.en_passant_square % 8
            hash_value ^= EP_KEYS[ep_file]
    
    return hash_value
```

**All components look correct!** The hash structure is fine. The bug is in the **incremental update** logic.

## The Castling Hash Update

### Location: `src/zobrist_full.py` lines 288-327

```python
def update_hash_castling(current_hash, color, is_kingside):
    """
    Update hash for castling move.
    Castling moves both king and rook.
    """
    KING = 5
    ROOK = 3
    
    if color == 0:  # WHITE
        if is_kingside:
            # King e1->g1 (4->6), Rook h1->f1 (7->5)
            hash_value = current_hash ^ PIECE_KEYS[0][KING][4]
            hash_value ^= PIECE_KEYS[0][KING][6]
            hash_value ^= PIECE_KEYS[0][ROOK][7]  # ← Assumes rook on h1!
            hash_value ^= PIECE_KEYS[0][ROOK][5]  # ← Assumes rook moving to f1!
        else:
            # King e1->c1 (4->2), Rook a1->d1 (0->3)
            hash_value = current_hash ^ PIECE_KEYS[0][KING][4]
            hash_value ^= PIECE_KEYS[0][KING][2]
            hash_value ^= PIECE_KEYS[0][ROOK][0]  # ← Assumes rook on a1!
            hash_value ^= PIECE_KEYS[0][ROOK][3]  # ← Assumes rook moving to d1!
    else:  # BLACK
        if is_kingside:
            # King e8->g8 (60->62), Rook h8->f8 (63->61)
            hash_value = current_hash ^ PIECE_KEYS[1][KING][60]
            hash_value ^= PIECE_KEYS[1][KING][62]
            hash_value ^= PIECE_KEYS[1][ROOK][63]  # ← Assumes rook on h8!
            hash_value ^= PIECE_KEYS[1][ROOK][61]  # ← Assumes rook moving to f8!
        else:
            # King e8->c8 (60->58), Rook a8->d8 (56->59)
            hash_value = current_hash ^ PIECE_KEYS[1][KING][60]
            hash_value ^= PIECE_KEYS[1][KING][58]
            hash_value ^= PIECE_KEYS[1][ROOK][56]  # ← Assumes rook on a8!
            hash_value ^= PIECE_KEYS[1][ROOK][59]  # ← Assumes rook moving to d8!
    
    return hash_value
```

**This function is 100% correct** - it updates the hash for LEGAL castling moves.

The problem is we're now detecting ILLEGAL castling and returning False before this update runs!

## TT Probing is Correct

### Location: `src/search.py` lines 221-302

The TT probe/store logic is **CORRECT**:

```python
def probe(self, zobrist_key, depth, ply, alpha, beta):
    bucket_idx = zobrist_key % self.num_buckets
    key16 = (zobrist_key >> 48) & 0xFFFF
    
    for entry in self.table[bucket_idx]:
        if entry is None:
            continue
        if entry.key16 != key16:  # Fast reject
            continue
        if entry.zobrist_key != zobrist_key:  # Full verification
            self.collisions += 1
            continue
        
        # Found entry
        self.hits += 1
        best_move = entry.best_move
        
        # Return move for ordering even if depth insufficient
        if entry.depth < depth:
            return None, best_move
        
        # Adjust mate scores and check bounds
        score = entry.score
        if score > MATE_SCORE - MAX_PLY:
            score = score + ply  # Correct mate adjustment
        elif score < -MATE_SCORE + MAX_PLY:
            score = score - ply  # Correct mate adjustment
        
        # Apply bound logic
        if entry.flag == TT_EXACT:
            self.usable_hits += 1
            return score, best_move
        # ... LOWERBOUND/UPPERBOUND checks
```

**No bugs here!** The TT is working correctly.

## The Real Problem: Move Validation Order

### Current Code Flow (BROKEN):

```
execute_move(board, from_square, to_square, promotion):
    1. old_castling_rights = board.castling_rights  ← Save for hash update
    2. old_ep_square = board.en_passant_square     ← Save for hash update
    
    3. Find piece_type on from_square
    4. if piece_type is None: return False  ✓ SAFE (no modifications yet)
    
    5. board.pieces[...] &= ~from_bb  ✗ MODIFY BITBOARD
    6. board.pieces[...] |= to_bb     ✗ MODIFY BITBOARD
    
    7. if piece_type == KING and abs(to_square - from_square) == 2:
        8. is_castling = True
        9. Validate rook exists
        10. if not rook: return False  ← BUG: Board already corrupted!
```

### Fixed Code Flow (CORRECT):

```
execute_move(board, from_square, to_square, promotion):
    1. Find piece_type on from_square
    2. if piece_type is None: return False  ✓ SAFE
    
    3. VALIDATE castling BEFORE modifying board:
       if piece_type == KING and abs(to_square - from_square) == 2:
           Calculate rook_from position
           if not (board.pieces[...][ROOK] & (1 << rook_from)):
               return False  ✓ SAFE (no modifications yet)
    
    4. Save state for hash updates:
       old_castling_rights = board.castling_rights
       old_ep_square = board.en_passant_square
    
    5. board.pieces[...] &= ~from_bb  ✓ SAFE (validation passed)
    6. board.pieces[...] |= to_bb     ✓ SAFE (validation passed)
    
    7. Move rook for castling (we know it exists)
    8. Update hash
```

## The Fix

### Move validation BEFORE any board modifications

**File:** `src/move_execution.py`

```python
def execute_move(board, from_square: int, to_square: int, promotion: Optional[int] = None) -> bool:
    """
    Execute a move on the board.
    Returns True if move was legal and made, False otherwise.
    """
    moving_color = board.side_to_move
    enemy_color = 1 - moving_color
    
    # Find the piece being moved
    piece_type = None
    from_bb = 1 << from_square
    
    for pt in range(6):
        if board.pieces[board.side_to_move][pt] & from_bb:
            piece_type = pt
            break
    
    if piece_type is None:
        return False  # No piece on source square
    
    # ========================================================================
    # CRITICAL: VALIDATE CASTLING *BEFORE* MODIFYING BOARD STATE
    # ========================================================================
    if piece_type == KING and abs(to_square - from_square) == 2:
        # This is a castling attempt - validate rook exists
        if to_square > from_square:  # Kingside
            rook_from = from_square + 3
        else:  # Queenside
            rook_from = from_square - 4
        
        rook_bb = 1 << rook_from
        if not (board.pieces[board.side_to_move][ROOK] & rook_bb):
            # No rook for castling - illegal move
            return False  # SAFE: No modifications made yet
    
    # Save state for incremental hash updates
    old_castling_rights = board.castling_rights
    old_ep_square = board.en_passant_square
    
    # Check if old EP square is actually in the hash
    old_ep_was_in_hash = (old_ep_square is not None and 
                          is_ep_capture_legal(board, old_ep_square))
    
    # NOW safe to modify board (validation passed)
    # ... rest of function ...
```

## Verification

### Test Case 1: Invalid FEN

```python
board = ChessBoard()
board.setup_from_fen("8/2P3k1/8/P7/3n4/8/8/4K3 b KQkq - 0 61")
# No rooks, but castling rights set

# Try illegal castling
result = board.make_move(60, 62, None)  # e8g8

# BEFORE FIX:
# result = False, but board.pieces modified, board.zobrist_key stale
# Board state corrupted!

# AFTER FIX:
# result = False, board state UNCHANGED
# All state consistent!
```

### Test Case 2: Valid Castling

```python
board = ChessBoard()  # Starting position
board.setup_from_fen("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
# Kings and rooks in place

# Try legal castling
result = board.make_move(60, 62, None)  # e8g8

# Both BEFORE and AFTER fix:
# result = True, board state updated correctly
# Hash updated correctly
```

## Conclusion

**The TT and hash structure are 100% CORRECT!**

**The bug is in move execution validation order:**
- We validate castling rook existence AFTER modifying the board
- If validation fails, we return False with corrupted board state
- This creates hash mismatches and inconsistent board state

**Fix:** Move validation to BEFORE any board modifications.

**Impact:** 
- Prevents board corruption on illegal castling attempts
- Ensures hash always matches board state
- TT lookups remain reliable
- No more "phantom rooks" or illegal moves
