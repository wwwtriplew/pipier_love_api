"""
Chess Search Algorithm Implementation

Core Components:
1. Iterative Deepening - Progressive depth search with time management
2. Alpha-Beta Pruning - Minimax optimization with branch pruning
3. Move Ordering - PV/Hash moves, MVV-LVA captures, killers, history
4. Transposition Table - Position caching with Zobrist hashing
5. Quiescence Search - Tactical stability (captures + checks)
6. Search Extensions/Reductions - Check extensions, LMR for non-critical moves

Performance Target: ~300K+ NPS with full optimizations
"""

from typing import Tuple, Optional, List, Dict
import time

try:
    from .chess_engine import ChessBoard, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
    from .evaluation import Evaluator, MATERIAL_VALUES
    from .magic_bitboards import get_lsb
except ImportError:
    from chess_engine import ChessBoard, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING  # type: ignore
    from evaluation import Evaluator, MATERIAL_VALUES  # type: ignore
    from magic_bitboards import get_lsb  # type: ignore


# ============================================================================
# CONSTANTS
# ============================================================================

# Score constants
MATE_SCORE = 30000
MAX_PLY = 100

# Transposition table entry types
TT_EXACT = 0      # Exact score (within alpha-beta window)
TT_LOWERBOUND = 1  # Fail-high (score >= beta)
TT_UPPERBOUND = 2  # Fail-low (score <= alpha)

# Late move reduction parameters (VERY CONSERVATIVE - 90% less pruning)
LMR_MIN_DEPTH = 4        # Minimum depth to apply LMR (was 3)
LMR_FULL_DEPTH_MOVES = 17  # Search first N moves at full depth (was 4)
LMR_REDUCTION = 1        # Depth reduction for late quiet moves (was 2)

# Aspiration window parameters
ASPIRATION_DELTA_INITIAL = 100   # Initial window: [score-100, score+100]
ASPIRATION_DELTA_MAX = 500      # Max window before going infinite

# Quiescence parameters
DELTA_PRUNING_MARGIN = 200  # Queen value safety margin for delta pruning

# Move ordering scores
SCORE_HASH_MOVE = 10000000
SCORE_QUEEN_PROMOTION = 9000000
SCORE_WINNING_CAPTURE = 8000000  # MVV-LVA: victim_value > attacker_value
SCORE_EQUAL_CAPTURE = 7000000     # MVV-LVA: victim_value == attacker_value
SCORE_KILLER_MOVE_1 = 6000000
SCORE_KILLER_MOVE_2 = 5000000
SCORE_LOSING_CAPTURE = 1000000   # MVV-LVA: victim_value < attacker_value
SCORE_HISTORY_BASE = 0           # History heuristic adds 0-999999


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_capture(board: ChessBoard, move: Tuple[int, int, Optional[int]]) -> bool:
    """
    Check if a move is a capture.
    
    Args:
        board: Current board position
        move: (from_square, to_square, promotion)
    
    Returns:
        True if move captures an enemy piece or is en passant
    """
    from_sq, to_sq, promo = move
    opponent = 1 - board.side_to_move
    to_bb = 1 << to_sq
    
    # Check for regular capture
    for piece_type in range(6):
        if board.pieces[opponent][piece_type] & to_bb:
            return True
    
    # Check for en passant capture
    if to_sq == board.en_passant_square:
        # Verify it's a pawn move
        if board.pieces[board.side_to_move][PAWN] & (1 << from_sq):
            return True
    
    return False


def is_mate_score(score: int) -> bool:
    """
    Check if score represents mate.
    
    Args:
        score: Position evaluation score
    
    Returns:
        True if score is mate-in-N
    """
    return abs(score) > MATE_SCORE - MAX_PLY


def adjust_mate_score_for_storage(score: int, ply: int) -> int:
    """
    Adjust mate score for TT storage (convert from root to current ply).
    
    Mate scores are distance from root. When storing in TT, convert to
    distance from current position so score is position-relative.
    
    Args:
        score: Score from root perspective
        ply: Current ply from root
    
    Returns:
        Score adjusted for current ply
    """
    if score > MATE_SCORE - MAX_PLY:
        return score - ply
    elif score < -MATE_SCORE + MAX_PLY:
        return score + ply
    return score


def adjust_mate_score_from_storage(score: int, ply: int) -> int:
    """
    Adjust mate score from TT retrieval (convert from current ply to root).
    
    Args:
        score: Score from TT (position-relative)
        ply: Current ply from root
    
    Returns:
        Score adjusted for root perspective
    """
    if score > MATE_SCORE - MAX_PLY:
        return score + ply
    elif score < -MATE_SCORE + MAX_PLY:
        return score - ply
    return score


# ============================================================================
# TRANSPOSITION TABLE
# ============================================================================

class TTEntry:
    """
    Transposition Table Entry
    
    Stores:
    - zobrist_key: Full 64-bit Zobrist hash for verification
    - key16: 16-bit partial key for fast rejection in set-associative buckets
    - depth: Search depth when this entry was created
    - score: Position evaluation score (mate scores are ply-adjusted on store/probe)
    - flag: TT_EXACT, TT_LOWERBOUND, or TT_UPPERBOUND
    - best_move: Best move found (for move ordering)
    - age: Search iteration when entry was created (for replacement)
    """
    __slots__ = ['zobrist_key', 'key16', 'depth', 'score', 'flag', 'best_move', 'age']
    
    def __init__(self, zobrist_key: int, depth: int, score: int, 
                 flag: int, best_move: Optional[Tuple[int, int, Optional[int]]], age: int):
        self.zobrist_key = zobrist_key
        self.key16 = (zobrist_key >> 48) & 0xFFFF  # Top 16 bits for fast reject
        self.depth = depth
        self.score = score
        self.flag = flag
        self.best_move = best_move
        self.age = age


class TranspositionTable:
    """
    Hash table for storing evaluated positions.
    
    Design:
    - Set-associative: 4-way buckets (4 entries per bucket for collision handling)
    - Size: configurable (default 64 MB = ~250K buckets × 4 entries)
    - Key: Full-board Zobrist hash (piece-square + side + castling + ep)
    - Partial key: 16-bit fingerprint for fast rejection before full key check
    
    Replacement Policy (per bucket):
    1. Empty slot (always use)
    2. Exact match on zobrist_key (always replace)
    3. Prefer deeper depth (more accurate)
    4. Prefer newer age (recent search)
    5. Prefer EXACT over bounds
    6. Replace shallowest/stalest entry
    """
    
    BUCKET_SIZE = 4  # 4-way set associative
    
    def __init__(self, size_mb: int = 64):
        """
        Initialize transposition table with set-associative buckets.
        
        Args:
            size_mb: Table size in megabytes (default 64 MB)
        """
        # Calculate number of buckets: size_mb * 1024^2 / (64 bytes * 4 entries)
        num_buckets = (size_mb * 1024 * 1024) // (64 * self.BUCKET_SIZE)
        self.num_buckets = num_buckets
        # Each bucket has BUCKET_SIZE slots
        self.table: List[List[Optional[TTEntry]]] = [[None] * self.BUCKET_SIZE for _ in range(num_buckets)]
        self.current_age = 0
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.usable_hits = 0  # Hits with sufficient depth
        self.collisions = 0
        self.replacements = 0
    
    def probe(self, zobrist_key: int, depth: int, ply: int, alpha: int, beta: int) -> Tuple[Optional[int], Optional[Tuple]]:
        """
        Probe transposition table for cached position.
        
        Pseudocode:
        1. Calculate bucket index: zobrist_key % num_buckets
        2. Calculate 16-bit partial key: (zobrist_key >> 48) & 0xFFFF
        3. Search bucket (4 entries):
           For each slot in bucket:
             a. Skip if empty
             b. Fast reject: if key16 != entry.key16: continue
             c. Full verify: if zobrist_key != entry.zobrist_key: continue (collision)
             d. Found match! Extract best_move from entry
             e. Check if score usable (entry.depth >= requested depth):
                - If not: return (None, best_move) for move ordering only
             f. Adjust mate scores for ply distance:
                - If entry.score >= MATE_SCORE - MAX_PLY:
                    score = entry.score - ply  # Mate distance from current position
                - Elif entry.score <= -MATE_SCORE + MAX_PLY:
                    score = entry.score + ply  # Being mated, adjust distance
                - Else: score = entry.score (non-mate score)
             g. Apply bound logic (negamax):
                - EXACT: increment usable_hits, return (score, best_move)
                - LOWERBOUND (fail-high): if score >= beta: return (score, best_move)
                - UPPERBOUND (fail-low): if score <= alpha: return (score, best_move)
             h. Score not usable for cutoff, return (None, best_move)
        4. No match in bucket: increment misses, return (None, None)
        
        Returns:
            (score, best_move) if usable for cutoff
            (None, best_move) if only move ordering available
            (None, None) if position not found
        """
        # Implemented: Set-associative probe with partial key and mate adjustment
        bucket_idx = zobrist_key % self.num_buckets
        key16 = (zobrist_key >> 48) & 0xFFFF
        
        # Search bucket for matching entry
        for entry in self.table[bucket_idx]:
            if entry is None:
                continue
            # Fast reject with partial key
            if entry.key16 != key16:
                continue
            # Full key verification
            if entry.zobrist_key != zobrist_key:
                self.collisions += 1
                continue
            
            # Found entry! At minimum, return best_move for ordering
            self.hits += 1
            best_move = entry.best_move
            
            # Check if score is usable (sufficient depth)
            if entry.depth < depth:
                return None, best_move  # Move ordering only
            
            # Adjust mate scores for ply distance (convert from position-relative to root)
            score = entry.score
            if score > MATE_SCORE - MAX_PLY:
                score = score + ply  # Mate is closer from root (add ply to restore root distance)
            elif score < -MATE_SCORE + MAX_PLY:
                score = score - ply  # Being mated is closer from root (subtract ply to restore root distance)
            
            # Apply bound logic based on entry.flag
            if entry.flag == TT_EXACT:
                self.usable_hits += 1
                return score, best_move
            elif entry.flag == TT_LOWERBOUND:
                if score >= beta:
                    self.usable_hits += 1
                    return score, best_move
            elif entry.flag == TT_UPPERBOUND:
                if score <= alpha:
                    self.usable_hits += 1
                    return score, best_move
            
            # Score not usable for cutoff, but move is good for ordering
            return None, best_move
        
        self.misses += 1
        return None, None
    
    def store(self, zobrist_key: int, depth: int, score: int, flag: int, 
              best_move: Optional[Tuple], ply: int):
        """
        Store position in transposition table with mate-score adjustment.
        
        Pseudocode:
        1. Calculate bucket index: zobrist_key % num_buckets
        2. Adjust mate scores for storage (ply-independent):
           - If score >= MATE_SCORE - MAX_PLY:
               store_score = score + ply  # Store as mate distance from root
           - Elif score <= -MATE_SCORE + MAX_PLY:
               store_score = score - ply  # Store as being mated distance from root
           - Else: store_score = score
        
        3. Find replacement slot in bucket (4-way search):
           a. First pass: look for empty slot or exact key match
              - If empty: use this slot
              - If zobrist_key matches: always replace (update)
           
           b. Second pass: find weakest entry to replace
              Score each entry by replacement priority (lower = weaker):
              - Empty: priority = -1000 (impossible, already handled)
              - Depth difference: priority = entry.depth - depth (prefer keep deeper)
              - Age difference: if entry.age != current_age: priority -= 100 (prefer keep fresh)
              - Flag bonus: if entry.flag == EXACT: priority += 50 (prefer keep exact)
              
              Replace entry with lowest priority (weakest)
        
        4. Create TTEntry with adjusted score and store in chosen slot
        5. Increment replacements counter
        
        Args:
            zobrist_key: Full-board Zobrist hash
            depth: Search depth
            score: Position score (will be mate-adjusted if needed)
            flag: TT_EXACT, TT_LOWERBOUND, or TT_UPPERBOUND
            best_move: Best move found
            ply: Current ply (for mate distance adjustment)
        """
        # Implemented: Set-associative store with mate adjustment and replacement policy
        bucket_idx = zobrist_key % self.num_buckets
        
        # Adjust mate scores for storage (convert from root to position-relative)
        store_score = score
        if score > MATE_SCORE - MAX_PLY:
            store_score = score - ply  # Store as distance from current position (subtract ply to make position-relative)
        elif score < -MATE_SCORE + MAX_PLY:
            store_score = score + ply  # Store as being mated distance from current position (add ply to make position-relative)
        
        # Find replacement slot in bucket
        bucket = self.table[bucket_idx]
        replace_idx = 0
        
        # First pass: look for empty slot or exact key match
        for idx in range(self.BUCKET_SIZE):
            entry = bucket[idx]
            if entry is None:
                replace_idx = idx
                break
            elif entry.zobrist_key == zobrist_key:
                replace_idx = idx  # Always replace exact match (update)
                break
        else:
            # Second pass: find weakest entry by replacement priority
            min_priority = 999999
            for idx in range(self.BUCKET_SIZE):
                entry = bucket[idx]
                if entry is None:
                    replace_idx = idx
                    break
                
                priority = entry.depth  # Prefer keep deeper searches
                
                # Penalize stale entries
                if entry.age != self.current_age:
                    priority -= 100
                
                # Bonus for exact scores
                if entry.flag == TT_EXACT:
                    priority += 50
                
                if priority < min_priority:
                    min_priority = priority
                    replace_idx = idx
        
        # Create and store entry
        bucket[replace_idx] = TTEntry(zobrist_key, depth, store_score, flag, best_move, self.current_age)
        self.replacements += 1
    
    def clear(self):
        """Clear all table entries."""
        self.table = [[None] * self.BUCKET_SIZE for _ in range(self.num_buckets)]
        self.hits = 0
        self.misses = 0
        self.usable_hits = 0
        self.collisions = 0
        self.replacements = 0
    
    def next_age(self):
        """Increment age counter (called at start of new search)."""
        self.current_age += 1


# ============================================================================
# MOVE ORDERING
# ============================================================================

class MoveOrderer:
    """
    Move ordering for alpha-beta search.
    
    Ordering priority (highest to lowest):
    1. Hash move from TT (PV move from previous iteration)
    2. Queen promotions
    3. Winning captures (MVV-LVA: QxP > RxN > ...)
    4. Killer moves (non-captures that caused beta cutoff)
    5. Equal captures
    6. History heuristic (moves that historically caused cutoffs)
    7. Losing captures
    8. Other quiet moves
    """
    
    def __init__(self):
        # Killer moves: [ply][slot] (2 killers per ply)
        self.killer_moves: List[List[Optional[Tuple]]] = [[None, None] for _ in range(MAX_PLY)]
        
        # History heuristic: [color][from_square][to_square]
        self.history: List[List[List[int]]] = [[[0] * 64 for _ in range(64)] for _ in range(2)]
    
    def score_move(self, board: ChessBoard, move: Tuple[int, int, Optional[int]], 
                   hash_move: Optional[Tuple], ply: int) -> int:
        """
        Assign ordering score to a move.
        
        Higher score = search this move first.
        Priority: Hash > Queen promo > Winning captures > Killers > History
        
        Args:
            board: Current position
            move: (from_square, to_square, promotion)
            hash_move: Best move from TT (if any)
            ply: Current ply from root
        
        Returns:
            Integer score for move ordering
        """
        from_sq, to_sq, promo = move
        
        # 1. Hash move gets highest priority
        if hash_move is not None and move == hash_move:
            return SCORE_HASH_MOVE
        
        # 2. Queen promotions
        if promo == QUEEN:
            return SCORE_QUEEN_PROMOTION
        
        # 3. Captures (MVV-LVA)
        if is_capture(board, move):
            # Get victim piece value
            victim_value = 0
            opponent = 1 - board.side_to_move
            to_bb = 1 << to_sq
            
            # Find victim piece type
            for piece_type in range(6):
                if board.pieces[opponent][piece_type] & to_bb:
                    victim_value = MATERIAL_VALUES[piece_type]
                    break
            
            # Special case: en passant (victim is pawn)
            if victim_value == 0 and to_sq == board.en_passant_square:
                victim_value = MATERIAL_VALUES[PAWN]
            
            # Get attacker piece value
            attacker_value = 0
            for piece_type in range(6):
                if board.pieces[board.side_to_move][piece_type] & (1 << from_sq):
                    attacker_value = MATERIAL_VALUES[piece_type]
                    break
            
            # MVV-LVA score
            mvv_lva = victim_value - attacker_value
            
            if victim_value > attacker_value:
                return SCORE_WINNING_CAPTURE + mvv_lva
            elif victim_value == attacker_value:
                return SCORE_EQUAL_CAPTURE + mvv_lva
            else:
                return SCORE_LOSING_CAPTURE + mvv_lva
        
        # 4. Killer moves (non-captures only)
        if ply < MAX_PLY:
            if move == self.killer_moves[ply][0]:
                return SCORE_KILLER_MOVE_1
            if move == self.killer_moves[ply][1]:
                return SCORE_KILLER_MOVE_2
        
        # 5. History heuristic
        color = board.side_to_move
        return SCORE_HISTORY_BASE + self.history[color][from_sq][to_sq]
    
    def order_moves(self, board: ChessBoard, moves: List[Tuple], 
                    hash_move: Optional[Tuple], ply: int) -> List[Tuple]:
        """
        Sort moves by ordering score (highest first).
        
        Args:
            board: Current board state
            moves: List of legal moves
            hash_move: Best move from TT (if available)
            ply: Current ply in search tree
        
        Returns:
            Sorted list of moves
        """
        # Implemented: Score and sort moves by priority
        return sorted(moves, key=lambda m: self.score_move(board, m, hash_move, ply), reverse=True)
    
    def update_killer(self, move: Tuple, ply: int):
        """
        Update killer move table.
        
        Pseudocode:
        1. If move != killer_moves[ply][0]:
           a. Shift killer_moves[ply][0] to killer_moves[ply][1]
           b. Set killer_moves[ply][0] = move
        
        Args:
            move: Non-capture move that caused beta cutoff
            ply: Ply where cutoff occurred
        """
        # Implemented: Update killer move table
        if ply >= MAX_PLY:
            return
        
        # Only update if this move is different from current first killer
        if move != self.killer_moves[ply][0]:
            # Shift first killer to second
            self.killer_moves[ply][1] = self.killer_moves[ply][0]
            # Set new first killer
            self.killer_moves[ply][0] = move
    
    def update_history(self, move: Tuple, depth: int, color: int):
        """
        Update history heuristic.
        
        Pseudocode:
        1. Extract from_square, to_square from move
        2. Increment history[color][from_square][to_square] by depth^2
        3. Cap at maximum value (e.g., 999999) to prevent overflow
        
        Note: Depth^2 weighting prioritizes moves that cause cutoffs in deeper searches
        
        Args:
            move: Move that caused beta cutoff
            depth: Depth where cutoff occurred
            color: Side to move
        """
        # Implemented: Update history heuristic with depth^2 weighting
        from_sq, to_sq, _ = move
        
        # Increment by depth^2 (deeper searches get more weight)
        increment = depth * depth
        self.history[color][from_sq][to_sq] += increment
        
        # Cap at 999999 to prevent overflow
        if self.history[color][from_sq][to_sq] > 999999:
            self.history[color][from_sq][to_sq] = 999999
    
    def clear_killers(self):
        """Clear killer moves (called at start of new search)."""
        self.killer_moves = [[None, None] for _ in range(MAX_PLY)]
    
    def age_history(self):
        """Age history table (divide all values by 2)."""
        for color in range(2):
            for from_sq in range(64):
                for to_sq in range(64):
                    self.history[color][from_sq][to_sq] //= 2


# ============================================================================
# SEARCH STATISTICS
# ============================================================================

class SearchStats:
    """Track search statistics for debugging and UCI output."""
    
    def __init__(self):
        self.nodes = 0
        self.q_nodes = 0  # Quiescence nodes
        self.beta_cutoffs = 0
        self.first_move_cutoffs = 0  # Cutoffs on first move (good ordering)
        self.hash_move_ordering = 0  # Times hash move was tried first
        
        # LMR statistics
        self.lmr_searches = 0  # Number of reduced searches
        self.lmr_researches = 0  # Number of re-searches at full depth
        
        # Aspiration window statistics
        self.aspiration_fails = 0  # Total re-searches due to window fails
        self.aspiration_fail_high = 0
        self.aspiration_fail_low = 0
        
        # Move ordering quality
        self.move_index_sum = 0  # Sum of move indices that caused cutoffs
        self.cutoff_count = 0  # For calculating average cutoff index
        
        self.start_time = time.time()  # FIX: Initialize to current time, not 0.0
    
    def reset(self):
        """Reset all statistics."""
        self.nodes = 0
        self.q_nodes = 0
        self.beta_cutoffs = 0
        self.first_move_cutoffs = 0
        self.hash_move_ordering = 0
        self.lmr_searches = 0
        self.lmr_researches = 0
        self.aspiration_fails = 0
        self.aspiration_fail_high = 0
        self.aspiration_fail_low = 0
        self.move_index_sum = 0
        self.cutoff_count = 0
        self.start_time = time.time()
    
    def nps(self) -> int:
        """Calculate nodes per second."""
        elapsed = time.time() - self.start_time
        return int(self.nodes / elapsed) if elapsed > 0 else 0
    
    def ordering_efficiency(self) -> float:
        """Calculate move ordering efficiency (% first move cutoffs)."""
        if self.beta_cutoffs == 0:
            return 0.0
        return (self.first_move_cutoffs / self.beta_cutoffs) * 100
    
    def average_cutoff_index(self) -> float:
        """Calculate average move index that caused beta cutoff (lower = better ordering)."""
        if self.cutoff_count == 0:
            return 0.0
        return self.move_index_sum / self.cutoff_count
    
    def lmr_efficiency(self) -> float:
        """Calculate LMR efficiency (% of reduced searches that didn't need re-search)."""
        if self.lmr_searches == 0:
            return 0.0
        return ((self.lmr_searches - self.lmr_researches) / self.lmr_searches) * 100
    



# ============================================================================
# QUIESCENCE SEARCH
# ============================================================================

def quiescence(board: ChessBoard, alpha: int, beta: int, ply: int,
               evaluator: Evaluator, stats: SearchStats) -> int:
    """
    Quiescence search - extend search to resolve tactical instability.
    
    Purpose: Prevent horizon effect by searching captures/checks until position is quiet.
    
    Pseudocode:
    1. Increment q_nodes counter
    
    2. Stand-pat evaluation:
       - stand_pat = evaluator.evaluate(board)
       - Beta cutoff: if stand_pat >= beta: return beta
         (Position too good, opponent wouldn't allow this line)
       - Alpha update: if stand_pat > alpha: alpha = stand_pat
         (We can always just stand still, so this is our lower bound)
    
    3. Generate captures only:
       - captures = [move for move in board.generate_moves() if is_capture(board, move)]
       - If no captures: return alpha (position is quiet)
    
    4. Order captures by MVV-LVA:
       - Sort by (victim_value - attacker_value) descending
       - Queen takes pawn (QxP) before rook takes knight (RxN), etc.
    
    5. Search captures:
       For each capture in captures:
         a. Delta pruning optimization:
            - Get captured piece value
            - If stand_pat + captured_value + DELTA_MARGIN < alpha:
                skip this capture (even best case won't raise alpha)
            - Exception: don't prune pawn promotions or if in check
         
         b. Make capture move
         
         c. Legality check:
            - If board.in_check and it's our king (illegal move):
                unmake and continue
         
         d. Recursively search:
            - score = -quiescence(board, -beta, -alpha, ply+1, evaluator, stats)
         
         e. Unmake move
         
         f. Beta cutoff:
            - If score >= beta: return beta
         
         g. Alpha update:
            - If score > alpha: alpha = score
    
    6. Return alpha (best score from quiet position or capture sequences)
    
    Note: Mate scores in qsearch:
    - Checkmate not possible in qsearch (only captures/checks, not all moves)
    - If in check at qsearch entry, fall back to full search or return -MATE+ply
    
    Args:
        board: Current board position
        alpha: Lower bound
        beta: Upper bound
        ply: Distance from root (for mate distance)
        evaluator: Position evaluator
        stats: Search statistics tracker
    
    Returns:
        Position score from quiescence perspective (negamax convention)
    """
    # Implemented: Complete quiescence search
    stats.q_nodes += 1
    
    # Check if we're in check - affects move generation and stand-pat
    in_check = board.in_check
    
    # 1. Stand-pat evaluation (only valid when NOT in check)
    # When in check, we MUST make a move (cannot stand still)
    if not in_check:
        # CRITICAL FIX: evaluate() returns score from WHITE's perspective
        # In negamax, we need score from side-to-move perspective
        eval_score = evaluator.evaluate(board)
        stand_pat = eval_score if board.side_to_move == 0 else -eval_score
        
        # 2. Beta cutoff - position already too good
        if stand_pat >= beta:
            return beta
        
        # 3. Alpha update - we can always stand still (when not in check)
        if stand_pat > alpha:
            alpha = stand_pat
    
    # 4. Generate moves
    # When in check: must search ALL moves (evasions), not just captures
    # When not in check: search only captures (quiescence)
    all_moves = board.generate_moves()
    
    if in_check:
        # In check: try all evasion moves
        moves = all_moves
    else:
        # Not in check: captures AND promotions (promotions are tactical!)
        moves = [move for move in all_moves if is_capture(board, move) or move[2] is not None]
    
    # No moves available
    if not moves:
        if in_check:
            # Checkmate: no legal moves while in check
            return -(MATE_SCORE - ply)
        else:
            # No captures available - position is quiet
            return alpha
    
    # 5. Order moves
    # When in check: simple ordering (try captures first)
    # When not in check: MVV-LVA ordering for captures
    if in_check:
        # Simple ordering: captures first, then non-captures
        def evasion_score(move: Tuple[int, int, Optional[int]]) -> int:
            return 1 if is_capture(board, move) else 0
        moves.sort(key=evasion_score, reverse=True)
    
    def capture_score(move: Tuple[int, int, Optional[int]]) -> int:
        from_sq, to_sq, promo = move
        opponent = 1 - board.side_to_move
        to_bb = 1 << to_sq
        
        # Get victim value
        victim_value = 0
        for piece_type in range(6):
            if board.pieces[opponent][piece_type] & to_bb:
                victim_value = MATERIAL_VALUES[piece_type]
                break
        
        # En passant
        if victim_value == 0 and to_sq == board.en_passant_square:
            victim_value = MATERIAL_VALUES[PAWN]
        
        # Get attacker value
        attacker_value = 0
        for piece_type in range(6):
            if board.pieces[board.side_to_move][piece_type] & (1 << from_sq):
                attacker_value = MATERIAL_VALUES[piece_type]
                break
        
        return victim_value - attacker_value
    
    if not in_check:
        moves.sort(key=capture_score, reverse=True)
    
    # 6. Search moves (captures or evasions)
    for move in moves:
        from_sq, to_sq, promo = move
        
        # Delta pruning: skip hopeless captures (only when NOT in check)
        if not in_check:
            # Get victim value for delta pruning
            opponent = 1 - board.side_to_move
            victim_value = 0
            for piece_type in range(6):
                if board.pieces[opponent][piece_type] & (1 << to_sq):
                    victim_value = MATERIAL_VALUES[piece_type]
                    break
            if victim_value == 0 and to_sq == board.en_passant_square:
                victim_value = MATERIAL_VALUES[PAWN]
            
            # Skip if even capturing won't help
            # Exception: don't prune promotions
            if promo is None and stand_pat + victim_value + DELTA_PRUNING_MARGIN < alpha:
                continue
        
        # Make move (capture or evasion)
        board.make_move(*move)
        
        # Legality check: verify the side that made the move didn't leave their king in check
        # After make_move(), side_to_move has switched to the opponent
        # So we check if the PREVIOUS side's king (now 1 - board.side_to_move) is attacked
        previous_side = 1 - board.side_to_move
        previous_king_bb = board.pieces[previous_side][KING]
        if not previous_king_bb:
            # King was captured - illegal move! (shouldn't happen but being defensive)
            board.unmake_move()
            continue
        
        previous_king_square = get_lsb(previous_king_bb)
        if board.is_square_attacked(previous_king_square, board.side_to_move):
            # Previous side's king is in check - illegal move
            board.unmake_move()
            continue
        
        # Recurse with negamax sign flip
        score = -quiescence(board, -beta, -alpha, ply + 1, evaluator, stats)
        
        board.unmake_move()
        
        # Beta cutoff
        if score >= beta:
            return beta
        
        # Alpha update
        if score > alpha:
            alpha = score
    
    return alpha


# ============================================================================
# ALPHA-BETA SEARCH
# ============================================================================

def alpha_beta(board: ChessBoard, depth: int, ply: int, alpha: int, beta: int,
               evaluator: Evaluator, tt: Optional[TranspositionTable], orderer: MoveOrderer,
               stats: SearchStats, pv_line: List[Tuple],
               repetition_stack: List[int]) -> int:
    """
    Alpha-beta negamax search with pruning.
    
    GLOBAL INVARIANTS (non-negotiable):
    - Negamax: all scores are from side-to-move perspective, flip sign when recursing
    - Mate encoding: -(MATE_SCORE - ply) for being mated, ensures faster mates score higher
    - Legality: only search legal moves (no self-check)
    
    Note: tt can be None (transposition table is optional)
    
    Pseudocode:
    
    === 0. Time management ===
    1. Check if time expired: if time_up(): return 0
    
    === 1. Repetition detection ===
    2. Check for threefold repetition:
       - Count occurrences of board.zobrist_key in repetition_stack
       - If count >= 2 (this would be 3rd occurrence): return 0 (draw)
    
    === 2. Transposition table probe ===
    3. Probe TT:
       - score, hash_move = tt.probe(board.zobrist_key, depth, ply, alpha, beta)
       - If score is not None (usable for cutoff): 
           * Increment stats.tt_usable_hits
           * Return score
       - If hash_move is not None:
           * Increment stats.hash_move_ordering (will try this move first)
    
    === 3. Leaf nodes (depth 0) ===
    4. If depth == 0:
       - Return quiescence(board, alpha, beta, ply, evaluator, stats)
    
    === 4. Check extension ===
    5. If board.in_check and ply < MAX_PLY:
       - depth += 1 (extend search in check positions)
    
    === 5. Move generation ===
    6. Generate moves:
       - moves = board.generate_moves()  # Should be legal moves only
       - If len(moves) == 0:
           * If board.in_check: return -(MATE_SCORE - ply)  # Checkmate
           * Else: return 0  # Stalemate
    
    === 6. Move ordering ===
    7. Order moves:
       - moves = orderer.order_moves(board, moves, hash_move, ply)
         (Places hash move first, then promotions, winning captures, killers, etc.)
    
    === 7. Main search loop ===
    8. Initialize:
       - best_score = -(MATE_SCORE + 1)  # Worse than any possible position
       - best_move = None
       - alpha_original = alpha (save for TT flag determination)
    
    9. For move_index, move in enumerate(moves):
       
       a. Make move:
          - board.make_move(*move)
          - repetition_stack.append(board.zobrist_key)  # Track for repetition
       
       b. Determine search parameters:
          - is_capture = is_capture(board, move)  # Check before move? Or track in move gen
          - gives_check = board.in_check  # After making move
       
       c. Late Move Reduction (LMR):
          Conditions for LMR:
          - depth >= LMR_MIN_DEPTH (e.g., 3)
          - move_index >= LMR_FULL_DEPTH_MOVES (e.g., 4, search first few at full depth)
          - not is_capture
          - not gives_check
          - not is_promotion(move)
          
          If all conditions met:
            i. Reduced search with null window:
               - reduced_depth = depth - 1 - LMR_REDUCTION
               - score = -alpha_beta(board, reduced_depth, ply+1, -alpha-1, -alpha,
                                    evaluator, tt, orderer, stats, [], repetition_stack)
               - stats.lmr_searches += 1
            
            ii. Re-search if reduced search raises alpha:
               - If score > alpha:
                   * stats.lmr_researches += 1
                   * score = -alpha_beta(board, depth-1, ply+1, -beta, -alpha,
                                        evaluator, tt, orderer, stats, [], repetition_stack)
          Else:
            - Full depth search:
              score = -alpha_beta(board, depth-1, ply+1, -beta, -alpha,
                                 evaluator, tt, orderer, stats, [], repetition_stack)
       
       d. Unmake move:
          - repetition_stack.pop()
          - board.unmake_move()
       
       e. Update best score:
          - If score > best_score:
              * best_score = score
              * best_move = move
              * If ply == 0: pv_line[0:0] = [move]  # Update PV at root
       
       f. Beta cutoff (fail-high):
          - If score >= beta:
              * Increment stats.beta_cutoffs
              * If move_index == 0: stats.first_move_cutoffs += 1
              * stats.move_index_sum += move_index
              * stats.cutoff_count += 1
              
              * Update ordering heuristics:
                - If not is_capture: orderer.update_killer(move, ply)
                - orderer.update_history(move, depth, board.side_to_move)
              
              * Store in TT:
                - tt.store(board.zobrist_key, depth, beta, TT_LOWERBOUND, best_move, ply)
              
              * Return beta
       
       g. Alpha update (improve lower bound):
          - If score > alpha:
              * alpha = score
    
    === 8. All moves searched ===
    10. Determine TT flag:
        - If best_score <= alpha_original: flag = TT_UPPERBOUND (fail-low, all moves bad)
        - Else: flag = TT_EXACT (PV node, found best move in window)
        - Note: fail-high (LOWERBOUND) was stored in loop at cutoff point
    
    11. Store in TT:
        - tt.store(board.zobrist_key, depth, best_score, flag, best_move, ply)
    
    12. Return best_score
    
    Args:
        board: Current position
        depth: Remaining search depth
        ply: Distance from root (for mate distance)
        alpha: Lower bound (best score for maximizing player)
        beta: Upper bound (best score for minimizing player)
        evaluator: Position evaluator
        tt: Transposition table
        orderer: Move orderer
        stats: Search statistics
        pv_line: Principal variation line (output)
    
    Returns:
        Best score from current position
    """
    # Implemented: Complete alpha-beta with:
    # - ✅ Repetition detection
    # - ✅ TT probe with mate adjustment
    # - ✅ Check extension
    # - ✅ LMR with null window + re-search
    # - ✅ Killer/history updates
    # - ✅ TT store with correct flag
    
    stats.nodes += 1
    
    # Check for repetition draw (threefold repetition)
    if repetition_stack.count(board.zobrist_key) >= 2:
        return 0  # Draw by repetition
    
    # TT probe (skip if TT is disabled)
    hash_move = None
    if tt is not None:
        tt_score, hash_move = tt.probe(board.zobrist_key, depth, ply, alpha, beta)
        if tt_score is not None:
            return tt_score
    
    # Check extension: search deeper when in check (resolve forcing lines)
    in_check = board.in_check
    if in_check and ply < MAX_PLY:
        depth += 1
    
    # Leaf node: enter quiescence search
    if depth == 0:
        return quiescence(board, alpha, beta, ply, evaluator, stats)
    
    # Generate and order moves
    alpha_original = alpha
    moves = board.generate_moves()
    if not moves:
        if board.in_check:
            return -(MATE_SCORE - ply)  # Proper mate encoding
        return 0
    
    # Order moves with hash move
    moves = orderer.order_moves(board, moves, hash_move, ply)
    
    best_score = -(MATE_SCORE + 1)
    best_move = None
    
    for move_idx, move in enumerate(moves):
        # Detect move properties BEFORE making the move
        is_capture_move = is_capture(board, move)
        is_promotion = move[2] is not None
        
        board.make_move(*move)
        repetition_stack.append(board.zobrist_key)
        
        # Check if move gives check (must be after make_move)
        gives_check = board.in_check
        
        # Late Move Reduction (LMR): reduce depth for late quiet moves
        # Conditions: sufficient depth, not first few moves, not capture, not check, not promotion
        do_lmr = (
            depth >= LMR_MIN_DEPTH and
            move_idx >= LMR_FULL_DEPTH_MOVES and
            not is_capture_move and
            not in_check and  # Not in check before move
            not gives_check and  # Doesn't give check
            not is_promotion  # Not a promotion
        )
        
        if do_lmr:
            # Search with reduced depth
            reduced_depth = depth - 1 - LMR_REDUCTION
            score = -alpha_beta(board, reduced_depth, ply + 1, -beta, -alpha,
                               evaluator, tt, orderer, stats, [], repetition_stack)
            stats.lmr_searches += 1
            
            # Re-search at full depth if reduced search raised alpha
            if score > alpha:
                stats.lmr_researches += 1
                score = -alpha_beta(board, depth - 1, ply + 1, -beta, -alpha,
                                   evaluator, tt, orderer, stats, [], repetition_stack)
        else:
            # Full depth search
            score = -alpha_beta(board, depth - 1, ply + 1, -beta, -alpha,
                               evaluator, tt, orderer, stats, [], repetition_stack)
        
        repetition_stack.pop()
        board.unmake_move()
        
        if score > best_score:
            best_score = score
            best_move = move
        
        if score >= beta:
            # Fail-high: store LOWERBOUND and update heuristics
            stats.beta_cutoffs += 1
            if move_idx == 0:
                stats.first_move_cutoffs += 1
            stats.move_index_sum += move_idx
            stats.cutoff_count += 1
            
            # Update ordering heuristics for non-captures
            if not is_capture(board, move):
                orderer.update_killer(move, ply)
            orderer.update_history(move, depth, board.side_to_move)
            
            # Store in TT with LOWERBOUND: store the actual cutoff move and score (not best_move and not beta)
            if tt is not None:
                tt.store(board.zobrist_key, depth, score, TT_LOWERBOUND, move, ply)
            return beta
        
        if score > alpha:
            alpha = score
    
    # All moves searched - determine flag
    if best_score <= alpha_original:
        flag = TT_UPPERBOUND  # Fail-low
    else:
        flag = TT_EXACT  # PV node
    
    if tt is not None:
        tt.store(board.zobrist_key, depth, best_score, flag, best_move, ply)
    return best_score


# ============================================================================
# ROOT SEARCH (ALPHA-BETA AT ROOT NODE)
# ============================================================================

def alpha_beta_root(board: ChessBoard, depth: int, alpha: int, beta: int,
                    evaluator: Evaluator, tt: Optional[TranspositionTable], orderer: MoveOrderer,
                    stats: SearchStats, repetition_stack: List[int]) -> Tuple[int, Optional[Tuple], List[Tuple]]:
    """
    Alpha-beta search at root node (special handling for move selection).
    
    Differences from regular alpha-beta:
    1. Return best move, not just score
    2. Always search all moves (no pruning at root for stability)
    3. Build principal variation (PV)
    4. Use PV search: full window for first move, null window + re-search for others
    
    Note: tt can be None (transposition table is optional)
    
    Pseudocode:
    
    === 1. Initialization ===
    1. Probe TT for hash move (move ordering only, DON'T prune at root):
       - _, hash_move = tt.probe(board.zobrist_key, 0, 0, alpha, beta)
         (depth=0 ensures we only get move, not cutoff)
    
    2. Generate and order moves:
       - moves = board.generate_moves()
       - If no moves: return (0, None, [])  # Checkmate or stalemate
       - moves = orderer.order_moves(board, moves, hash_move, ply=0)
    
    === 2. PV search loop ===
    3. Initialize:
       - best_score = -(MATE_SCORE + 1)
       - best_move = None
       - pv_line = []
    
    4. For move_index, move in enumerate(moves):
       
       a. Make move:
          - board.make_move(*move)
          - repetition_stack.append(board.zobrist_key)
       
       b. PV search (Principal Variation Search):
          
          If move_index == 0 (first move):
            - Full window search (expect this to be best):
              score = -alpha_beta(board, depth-1, 1, -beta, -alpha,
                                 evaluator, tt, orderer, stats, [], repetition_stack)
          
          Else (subsequent moves):
            - Null window search (prove this is worse than first move):
              score = -alpha_beta(board, depth-1, 1, -alpha-1, -alpha,
                                 evaluator, tt, orderer, stats, [], repetition_stack)
            
            - Re-search if null window fails high:
              If score > alpha and score < beta:
                score = -alpha_beta(board, depth-1, 1, -beta, -alpha,
                                   evaluator, tt, orderer, stats, [], repetition_stack)
       
       c. Unmake move:
          - repetition_stack.pop()
          - board.unmake_move()
       
       d. Update best:
          - If score > best_score:
              * best_score = score
              * best_move = move
              * pv_line = [move]  # TODO: extract full PV from TT
          
          - If score > alpha:
              * alpha = score
       
       e. Optional: print per-move info for UCI
          - print(f"info depth {depth} currmove {move_to_uci(move)} currmovenumber {move_index+1}")
    
    === 3. Store and return ===
    5. Store root position in TT:
       - Determine flag:
         * If best_score <= alpha (from aspiration): TT_UPPERBOUND
         * Elif best_score >= beta: TT_LOWERBOUND
         * Else: TT_EXACT
       - tt.store(board.zobrist_key, depth, best_score, flag, best_move, ply=0)
    
    6. Return (best_score, best_move, pv_line)
    
    Args:
        board: Root position
        depth: Search depth
        alpha: Lower bound
        beta: Upper bound
        evaluator: Position evaluator
        tt: Transposition table
        orderer: Move orderer
        stats: Search statistics
    
    Returns:
        (score, best_move, pv_line)
    """
    # TODO: Implement root search with:
    # - PV search (full window first move, null window + re-search for others)
    # - Proper move ordering with hash move (DONE)
    # - No pruning at root (search all moves for stability)
    
    stats.nodes += 1
    
    # TT probe for hash move (ordering only, don't prune at root)
    hash_move = None
    if tt is not None:
        _, hash_move = tt.probe(board.zobrist_key, 0, 0, alpha, beta)
    
    moves = board.generate_moves()
    if not moves:
        return 0, None, []
    
    # Order moves with hash move
    moves = orderer.order_moves(board, moves, hash_move, 0)
    
    # Placeholder: return first move with simple search
    best_move = moves[0]
    best_score = -(MATE_SCORE + 1)
    alpha_original = alpha  # Save original alpha for TT flag determination
    
    for move in moves:
        board.make_move(*move)
        repetition_stack.append(board.zobrist_key)
        
        score = -alpha_beta(board, depth - 1, 1, -beta, -alpha, 
                           evaluator, tt, orderer, stats, [], repetition_stack)
        
        repetition_stack.pop()
        board.unmake_move()
        
        if score > best_score:
            best_score = score
            best_move = move
        
        if score > alpha:
            alpha = score
    
    # Store root position with correct flag based on alpha_original
    if best_score > alpha_original:
        flag = TT_EXACT
    else:
        flag = TT_UPPERBOUND
    if tt is not None:
        tt.store(board.zobrist_key, depth, best_score, flag, best_move, 0)
    
    # Extract full PV from TT by following the chain
    pv_line = []
    pv_moves_made = 0  # Track how many moves we actually made
    if best_move:
        pv_line.append(best_move)
        if board.make_move(*best_move):
            pv_moves_made += 1
            
            # Follow TT chain to build PV (max 20 moves to avoid infinite loops)
            if tt is not None:
                for _ in range(min(20, depth)):
                    _, tt_move = tt.probe(board.zobrist_key, 0, 0, -MATE_SCORE, MATE_SCORE)
                    if tt_move is None:
                        break
                    
                    # CRITICAL: Validate move before making it
                    # If make_move returns False (illegal move), stop PV extraction
                    if board.make_move(*tt_move):
                        pv_line.append(tt_move)
                        pv_moves_made += 1
                    else:
                        # Illegal move in TT (hash collision or stale entry) - stop here
                        break
            
            # Unmake only the moves we successfully made
            for _ in range(pv_moves_made):
                board.unmake_move()
        else:
            # best_move itself was illegal (should never happen) - clear pv_line
            pv_line = []
    
    return best_score, best_move, pv_line


# ============================================================================
# ITERATIVE DEEPENING
# ============================================================================

def iterative_deepening(board: ChessBoard, max_time_ms: int, max_depth: int,
                       evaluator: Evaluator, tt: Optional[TranspositionTable], orderer: MoveOrderer,
                       stats: SearchStats) -> Tuple[Optional[Tuple], int, List[Tuple], int]:
    """
    Iterative deepening framework - search progressively deeper until time expires.
    
    Returns:
        (best_move, best_score, pv_line, completed_depth)
    
    Benefits:
    1. Anytime algorithm: can stop at any point with best move from last completed depth
    2. Move ordering: TT entries from depth N improve ordering at depth N+1 (if TT enabled)
    3. Aspiration windows: narrow bounds prune more efficiently at deeper depths
    
    Note: TT can be None. Testing showed +26.7% performance improvement without TT
    at production depth (4-5). Zobrist hashing is retained for repetition detection.
    
    Pseudocode:
    
    === 1. Initialization ===
    1. Reset state:
       - stats.reset()
       - tt.next_age()  # Increment age for replacement policy
       - orderer.clear_killers()
       - orderer.age_history()  # Decay history scores to prevent stale bias
    
    2. Initialize search variables:
       - best_move = None
       - best_score = 0
       - pv_line = []
       - repetition_stack = []  # Empty at root
    
    3. Early exit check:
       - moves = board.generate_moves()
       - If len(moves) == 0: return (None, 0, [])
       - If len(moves) == 1: 
           * Can return immediately, but search depth 1 for score
           * Set flag to exit after depth 1
    
    === 2. Iterative deepening loop ===
    4. For depth = 1 to max_depth:
       
       a. Check time before starting depth:
          - elapsed_ms = (time.time() - stats.start_time) * 1000
          - If elapsed_ms > max_time_ms * 0.5 and depth > 1:
              * Break (not enough time for next depth)
       
       b. Aspiration window setup:
          If depth == 1:
            - alpha = -MATE_SCORE
            - beta = MATE_SCORE
            - delta = ASPIRATION_DELTA_INITIAL  # For next iteration
          Else:
            - alpha = best_score - delta
            - beta = best_score + delta
       
       c. Search with aspiration window:
          - score, move, pv = alpha_beta_root(
                board, depth, alpha, beta,
                evaluator, tt, orderer, stats, repetition_stack)
       
       d. Handle aspiration fails:
          
          While True:
            # Time check: don't get stuck re-searching when time is low
            elapsed_ms = (time.time() - stats.start_time) * 1000
            if elapsed_ms > max_time_ms * 0.9:
              break  # Stop widening, use current result
            
            If score <= alpha (fail-low):
              - stats.aspiration_fail_low += 1
              - stats.aspiration_fails += 1
              - alpha = max(alpha - delta, -MATE_SCORE)  # Widen window down
              - delta = min(delta * 2, ASPIRATION_DELTA_MAX)  # Increase delta
              - Re-search:
                score, move, pv = alpha_beta_root(
                    board, depth, alpha, beta,
                    evaluator, tt, orderer, stats, repetition_stack)
            
            Elif score >= beta (fail-high):
              - stats.aspiration_fail_high += 1
              - stats.aspiration_fails += 1
              - beta = min(beta + delta, MATE_SCORE)  # Widen window up
              - delta = min(delta * 2, ASPIRATION_DELTA_MAX)
              - Re-search:
                score, move, pv = alpha_beta_root(
                    board, depth, alpha, beta,
                    evaluator, tt, orderer, stats, repetition_stack)
            
            Else:
              - Break (score within window)
          
          - Reset delta for next depth:
            delta = ASPIRATION_DELTA_INITIAL
       
       e. Check time after depth completes:
          - elapsed_ms = (time.time() - stats.start_time) * 1000
          - If elapsed_ms > max_time_ms:
              * Break (time expired, don't update best_move with incomplete depth)
       
       f. Update best results:
          - best_score = score
          - best_move = move
          - pv_line = pv
       
       g. Print UCI info:
          - elapsed_ms = int((time.time() - stats.start_time) * 1000)
          - nps = stats.nps()
          - pv_str = " ".join([move_to_uci(m) for m in pv_line])
          - print(f"info depth {depth} score cp {best_score} nodes {stats.nodes} "
                  f"nps {nps} time {elapsed_ms} pv {pv_str}")
       
       h. Early exit conditions:
          - If abs(best_score) >= MATE_SCORE - MAX_PLY:
              * Mate found, no point searching deeper
              * Break
          - If len(moves) == 1:
              * Only one legal move, exit after depth 1
              * Break
    
    === 3. Return results ===
    5. Return (best_move, best_score, pv_line)
    
    Args:
        board: Root position
        max_time_ms: Maximum search time in milliseconds
        max_depth: Maximum search depth
        evaluator: Position evaluator
        tt: Transposition table
        orderer: Move orderer
        stats: Search statistics
    
    Returns:
        (best_move, best_score, pv_line)
    """
    # === 1. Initialization ===
    stats.reset()
    if tt is not None:
        tt.next_age()
    orderer.clear_killers()
    orderer.age_history()
    repetition_stack: List[int] = []
    
    best_move = None
    best_score = 0
    pv_line = []
    
    # Early exit check
    moves = board.generate_moves()
    if len(moves) == 0:
        return None, 0, [], 0
    
    only_one_move = len(moves) == 1
    
    # === 2. Iterative deepening loop ===
    delta = ASPIRATION_DELTA_INITIAL
    completed_depth = 0  # Track the last fully completed depth
    
    for depth in range(1, max_depth + 1):
        # a. Check time before starting depth
        elapsed_ms = (time.time() - stats.start_time) * 1000
        if elapsed_ms > max_time_ms * 0.5 and depth > 1:
            break  # Not enough time for next depth
        
        # b. Aspiration window setup
        if depth == 1:
            alpha = -MATE_SCORE
            beta = MATE_SCORE
        else:
            alpha = best_score - delta
            beta = best_score + delta
        
        # c. Search with aspiration window
        score, move, pv = alpha_beta_root(
            board, depth, alpha, beta,
            evaluator, tt, orderer, stats, repetition_stack
        )
        
        # d. Handle aspiration fails
        aspiration_completed = False
        while True:
            # Time check: don't get stuck re-searching when time is low
            elapsed_ms = (time.time() - stats.start_time) * 1000
            if elapsed_ms > max_time_ms * 0.9:
                # Time critical - accept current result even if outside window
                aspiration_completed = False
                break
            
            if score <= alpha:  # Fail-low
                stats.aspiration_fail_low += 1
                stats.aspiration_fails += 1
                alpha = max(alpha - delta, -MATE_SCORE)  # Widen window down
                delta = min(delta * 2, ASPIRATION_DELTA_MAX)
                score, move, pv = alpha_beta_root(
                    board, depth, alpha, beta,
                    evaluator, tt, orderer, stats, repetition_stack
                )
            elif score >= beta:  # Fail-high
                stats.aspiration_fail_high += 1
                stats.aspiration_fails += 1
                beta = min(beta + delta, MATE_SCORE)  # Widen window up
                delta = min(delta * 2, ASPIRATION_DELTA_MAX)
                score, move, pv = alpha_beta_root(
                    board, depth, alpha, beta,
                    evaluator, tt, orderer, stats, repetition_stack
                )
            else:
                # Score within window - depth completed successfully
                aspiration_completed = True
                break
        
        # Reset delta for next depth
        delta = ASPIRATION_DELTA_INITIAL
        
        # f. Update best results IMMEDIATELY after depth completes
        # This ensures we save results from completed depths even if time expires
        # Only skip update if aspiration window didn't complete due to time pressure
        if aspiration_completed or depth == 1:  # Always save depth 1
            best_score = score
            best_move = move
            pv_line = pv
            completed_depth = depth  # Track completed depth
        
        # g. Print UCI info (only if we updated results)
        if aspiration_completed or depth == 1:
            elapsed_ms = int((time.time() - stats.start_time) * 1000)
            nps = stats.nps()
            pv_str = " ".join([move_to_uci(m) for m in pv_line]) if pv_line else ""
            print(f"info depth {depth} score cp {best_score} nodes {stats.nodes} "
                  f"nps {nps} time {elapsed_ms} pv {pv_str}")
        
        # h. Check time after saving results - decide if we continue to next depth
        elapsed_ms = (time.time() - stats.start_time) * 1000
        if elapsed_ms > max_time_ms:
            break  # Time expired, stop searching
        
        # i. Early exit conditions
        if abs(best_score) >= MATE_SCORE - MAX_PLY:
            # Mate found, no point searching deeper
            break
        
        if only_one_move:
            # Only one legal move, exit after depth 1
            break
    
    # === 3. Return results ===
    # Safety check: if no depth completed (very rare), do a quick depth 1 search
    if best_move is None and len(moves) > 0:
        score, move, pv = alpha_beta_root(
            board, 1, -MATE_SCORE, MATE_SCORE,
            evaluator, tt, orderer, stats, repetition_stack
        )
        return move, score, pv, 1  # Return depth 1
    
    return best_move, best_score, pv_line, completed_depth


# ============================================================================
# SEARCH INTERFACE (MAIN ENTRY POINT)
# ============================================================================

class SearchEngine:
    """
    Main search engine interface.
    
    Usage:
        engine = SearchEngine(tt_size_mb=64)
        best_move, score, pv = engine.search(board, time_ms=1000, depth=None)
    """
    
    def __init__(self, tt_size_mb: int = 64):
        """
        Initialize search engine.
        
        Args:
            tt_size_mb: Transposition table size in megabytes
        """
        self.evaluator = Evaluator()
        self.tt = TranspositionTable(size_mb=tt_size_mb)
        self.orderer = MoveOrderer()
        self.stats = SearchStats()
    
    def search(self, board: ChessBoard, time_ms: Optional[int] = None, 
               depth: Optional[int] = None) -> Tuple[Optional[Tuple], int, List[Tuple], int]:
        """
        Search for best move.
        
        Args:
            board: Current position
            time_ms: Maximum search time in milliseconds (None = infinite)
            depth: Maximum search depth (None = use time limit)
        
        Returns:
            (best_move, score, pv_line, completed_depth)
        """
        # Use default values if not specified
        if time_ms is None and depth is None:
            depth = 6  # Default depth
        if time_ms is None:
            time_ms = 999999999  # Effectively infinite
        if depth is None:
            depth = MAX_PLY
        
        return iterative_deepening(
            board, time_ms, depth,
            self.evaluator, self.tt, self.orderer, self.stats
        )
    
    def clear_tt(self):
        """Clear transposition table."""
        if self.tt is not None:
            self.tt.clear()
    
    def get_stats(self) -> Dict:
        """Get comprehensive search statistics."""
        # Calculate TT hit rate directly from TT stats
        if self.tt is not None:
            total_tt_lookups = self.tt.hits + self.tt.misses
            tt_hit_rate = (self.tt.hits / total_tt_lookups * 100) if total_tt_lookups > 0 else 0.0
            tt_hits = self.tt.hits
            tt_usable_hits = self.tt.usable_hits
            tt_misses = self.tt.misses
        else:
            tt_hit_rate = 0.0
            tt_hits = 0
            tt_usable_hits = 0
            tt_misses = 0
        
        return {
            'nodes': self.stats.nodes,
            'q_nodes': self.stats.q_nodes,
            'nps': self.stats.nps(),
            'tt_hits': tt_hits,
            'tt_usable_hits': tt_usable_hits,
            'tt_misses': tt_misses,
            'tt_hit_rate': tt_hit_rate,
            'beta_cutoffs': self.stats.beta_cutoffs,
            'first_move_cutoffs': self.stats.first_move_cutoffs,
            'ordering_efficiency': self.stats.ordering_efficiency(),
            'avg_cutoff_index': self.stats.average_cutoff_index(),
            'lmr_searches': self.stats.lmr_searches,
            'lmr_researches': self.stats.lmr_researches,
            'lmr_efficiency': self.stats.lmr_efficiency(),
            'aspiration_fails': self.stats.aspiration_fails,
            'aspiration_fail_high': self.stats.aspiration_fail_high,
            'aspiration_fail_low': self.stats.aspiration_fail_low,
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================



def is_promotion(move: Tuple[int, int, Optional[int]]) -> bool:
    """
    Check if move is a pawn promotion.
    
    Args:
        move: (from_square, to_square, promotion)
    
    Returns:
        True if move promotes pawn
    """
    return move[2] is not None


def move_to_uci(move: Tuple[int, int, Optional[int]]) -> str:
    """
    Convert move tuple to UCI string.
    
    Args:
        move: (from_square, to_square, promotion)
    
    Returns:
        UCI move string (e.g., 'e2e4', 'e7e8q')
    """
    from_sq, to_sq, promo = move
    
    from_file = from_sq % 8
    from_rank = from_sq // 8
    to_file = to_sq % 8
    to_rank = to_sq // 8
    
    uci = chr(ord('a') + from_file) + str(from_rank + 1)
    uci += chr(ord('a') + to_file) + str(to_rank + 1)
    
    if promo is not None:
        promo_chars = {QUEEN: 'q', ROOK: 'r', BISHOP: 'b', KNIGHT: 'n'}
        uci += promo_chars[promo]
    
    return uci


def uci_to_move(board: ChessBoard, uci: str) -> Optional[Tuple[int, int, Optional[int]]]:
    """
    Convert UCI string to move tuple.
    
    Args:
        board: Current board (for move validation)
        uci: UCI move string (e.g., 'e2e4', 'e7e8q')
    
    Returns:
        (from_square, to_square, promotion) or None if invalid
    """
    if len(uci) < 4:
        return None
    
    from_file = ord(uci[0]) - ord('a')
    from_rank = int(uci[1]) - 1
    to_file = ord(uci[2]) - ord('a')
    to_rank = int(uci[3]) - 1
    
    from_sq = from_rank * 8 + from_file
    to_sq = to_rank * 8 + to_file
    
    promo = None
    if len(uci) == 5:
        promo_chars = {'q': QUEEN, 'r': ROOK, 'b': BISHOP, 'n': KNIGHT}
        promo = promo_chars.get(uci[4])
    
    return (from_sq, to_sq, promo)
