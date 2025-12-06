"""
Chess Position Evaluation with Tapered Eval and Pawn Hash Table

This module provides position evaluation with:
- Material counting
- Piece-square tables (middlegame/endgame)
- Pawn structure evaluation (cached in pawn hash table)
- Tapered evaluation (Fruit's formula)
- Optional king safety and mobility

Performance target: 750-900 cycles per evaluation
"""

from typing import Tuple, Optional

try:
    from .chess_engine import ChessBoard, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
    from .magic_bitboards import MagicBitboards, PreCalculatedAttacks, count_bits as popcount
except ImportError:
    import os
    import sys
    _SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    if _SRC_DIR not in sys.path:
        sys.path.append(_SRC_DIR)
    from chess_engine import ChessBoard, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING  # type: ignore
    from magic_bitboards import MagicBitboards, PreCalculatedAttacks, count_bits as popcount  # type: ignore


# ============================================================================
# EVALUATION CONSTANTS
# ============================================================================

# Material values (centipawns)
MATERIAL_VALUES = {
    PAWN: 100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK: 500,
    QUEEN: 900,
    KING: 0  # King is invaluable
}

# Phase calculation values (Fruit's convention)
# Used to interpolate between middlegame and endgame
PHASE_VALUES = {
    PAWN: 0,
    KNIGHT: 1,
    BISHOP: 1,
    ROOK: 2,
    QUEEN: 4
}

TOTAL_PHASE = 24  # Starting material: 4N + 4B + 4R + 2Q = 24

# Pawn structure penalties/bonuses (centipawns)
DOUBLED_PAWN_PENALTY = 30
ISOLATED_PAWN_PENALTY = 25
BACKWARD_PAWN_PENALTY = 15

# Passed pawn bonuses by rank (0-7, where 0 is 1st rank, 7 is 8th rank)
# From white's perspective (indexed by rank)
# Rank 6 (7th rank in chess notation, one move from promotion) = 600 cp
# Rank 7 would be after promotion (shouldn't occur in legal positions)
PASSED_PAWN_BONUS = [0, 20, 30, 50, 100, 200, 600, 0]

# King safety evaluation parameters
# Pawn shield bonuses (pawns directly in front of and next to king)
PAWN_SHIELD_BONUS = 15  # Bonus per pawn in shield
PAWN_SHIELD_FAR_BONUS = 10  # Bonus for pawn 2 squares away

# Open/semi-open file penalties near king
OPEN_FILE_NEAR_KING_PENALTY = 25  # No pawns on file near king
SEMI_OPEN_FILE_NEAR_KING_PENALTY = 15  # Only enemy pawns on file

# King exposure penalties (enemy piece attacks on king zone)
# King zone = 8 squares adjacent to king (not the king square itself)
# Lowered from 20 cp - was causing king safety to be overvalued
KING_ZONE_ATTACK_PENALTY = 10  # Penalty per enemy piece attacking king zone

# King safety only matters in middlegame (fades to 0 in endgame)
# We'll weight by (256 - phase) to scale with middlegame material

# Mobility evaluation parameters
# Mobility measures SAFE squares only (reachable, unattacked, empty)
# Weight ratios: Knight > Bishop > Queen > Rook (11:7:4:3 base)
# Queens and rooks scale with phase to encourage activity in endgame
# Using simple integers for PyPy JIT optimization
MOBILITY_KNIGHT_WEIGHT = 11   # Constant - knights always need activity
MOBILITY_BISHOP_WEIGHT = 7    # Constant - bishops always benefit from open diagonals
MOBILITY_QUEEN_WEIGHT_MG = 4  # Opening/middlegame - avoid early queen development
MOBILITY_QUEEN_WEIGHT_EG = 10 # Endgame - active queen is crucial
MOBILITY_ROOK_WEIGHT_MG = 3   # Opening/middlegame - rooks develop later
MOBILITY_ROOK_WEIGHT_EG = 8   # Endgame - rooks dominate open files

# Tempo bonus - side to move has slight advantage
TEMPO_BONUS = 10  # +10 cp for having the move

# Evaluation component weights (relative importance: Material:PSQT:Pawn:King:Mobility = 10:10:7:8:6)
# These will be tuned later with Texel tuning for optimal play strength
WEIGHT_MATERIAL = 10
WEIGHT_PSQT = 10
WEIGHT_PAWN = 7
WEIGHT_KING_SAFETY = 8
WEIGHT_MOBILITY = 6
WEIGHT_DIVISOR = 10  # Divide to normalize (keeps scores in reasonable range)

# File masks for pawn structure analysis
FILE_MASKS = [
    0x0101010101010101,  # A-file
    0x0202020202020202,  # B-file
    0x0404040404040404,  # C-file
    0x0808080808080808,  # D-file
    0x1010101010101010,  # E-file
    0x2020202020202020,  # F-file
    0x4040404040404040,  # G-file
    0x8080808080808080,  # H-file
]

# Adjacent file masks (for isolated pawn detection)
ADJACENT_FILE_MASKS = [
    0x0202020202020202,  # Files adjacent to A (B only)
    0x0505050505050505,  # Files adjacent to B (A, C)
    0x0A0A0A0A0A0A0A0A,  # Files adjacent to C (B, D)
    0x1414141414141414,  # Files adjacent to D (C, E)
    0x2828282828282828,  # Files adjacent to E (D, F)
    0x5050505050505050,  # Files adjacent to F (E, G)
    0xA0A0A0A0A0A0A0A0,  # Files adjacent to G (F, H)
    0x4040404040404040,  # Files adjacent to H (G only)
]


# ============================================================================
# PIECE-SQUARE TABLES (PeSTO's Evaluation Function)
# ============================================================================
# Values are from white's perspective (index 0 = a1, 63 = h8)
# Positive values mean good for the piece on that square
# Tables are [middlegame, endgame] for tapered evaluation

# Pawn PSQ tables
PAWN_PSQ_MG = [
      0,   0,   0,   0,   0,   0,   0,   0,
     98, 134,  61,  95,  68, 126,  34, -11,
     -6,   7,  26,  31,  65,  56,  25, -20,
    -14,  13,   6,  21,  23,  12,  17, -23,
    -27,  -2,  -5,  12,  17,   6,  10, -25,
    -26,  -4,  -4, -10,   3,   3,  33, -12,
    -35,  -1, -20, -23, -15,  24,  38, -22,
      0,   0,   0,   0,   0,   0,   0,   0,
]

PAWN_PSQ_EG = [
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8,  10,  13,   0,   2,  -7,
      0,   0,   0,   0,   0,   0,   0,   0,
]

# Knight PSQ tables
KNIGHT_PSQ_MG = [
    -167, -89, -34, -49,  61, -97, -15, -107,
     -73, -41,  72,  36,  23,  62,   7,  -17,
     -47,  60,  37,  65,  84, 129,  73,   44,
      -9,  17,  19,  53,  37,  69,  18,   22,
     -13,   4,  16,  13,  28,  19,  21,   -8,
     -23,  -9,  12,  10,  19,  17,  25,  -16,
     -29, -53, -12,  -3,  -1,  18, -14,  -19,
    -105, -21, -58, -33, -17, -28, -19,  -23,
]

KNIGHT_PSQ_EG = [
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
]

# Bishop PSQ tables
BISHOP_PSQ_MG = [
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21,
]

BISHOP_PSQ_EG = [
    -14, -21, -11,  -8, -7,  -9, -17, -24,
     -8,  -4,   7, -12, -3, -13,  -4, -14,
      2,  -8,   0,  -1, -2,   6,   0,   4,
     -3,   9,  12,   9, 14,  10,   3,   2,
     -6,   3,  13,  19,  7,  10,  -3,  -9,
    -12,  -3,   8,  10, 13,   3,  -7, -15,
    -14, -18,  -7,  -1,  4,  -9, -15, -27,
    -23,  -9, -23,  -5, -9, -16,  -5, -17,
]

# Rook PSQ tables
ROOK_PSQ_MG = [
     32,  42,  32,  51, 63,  9,  31,  43,
     27,  32,  58,  62, 80, 67,  26,  44,
     -5,  19,  26,  36, 17, 45,  61,  16,
    -24, -11,   7,  26, 24, 35,  -8, -20,
    -36, -26, -12,  -1,  9, -7,   6, -23,
    -45, -25, -16, -17,  3,  0,  -5, -33,
    -44, -16, -20,  -9, -1, 11,  -6, -71,
    -19, -13,   1,  17, 16,  7, -37, -26,
]

ROOK_PSQ_EG = [
    13, 10, 18, 15, 12,  12,   8,   5,
    11, 13, 13, 11, -3,   3,   8,   3,
     7,  7,  7,  5,  4,  -3,  -5,  -3,
     4,  3, 13,  1,  2,   1,  -1,   2,
     3,  5,  8,  4, -5,  -6,  -8, -11,
    -4,  0, -5, -1, -7, -12,  -8, -16,
    -6, -6,  0,  2, -9,  -9, -11,  -3,
    -9,  2,  3, -1, -5, -13,   4, -20,
]

# Queen PSQ tables
QUEEN_PSQ_MG = [
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -31, -50,
]

QUEEN_PSQ_EG = [
     -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  23,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41,
]

# King PSQ tables
KING_PSQ_MG = [
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14,
]

KING_PSQ_EG = [
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43,
]

# Organize tables by piece type for easy access
PSQ_TABLES_MG = [
    PAWN_PSQ_MG,
    KNIGHT_PSQ_MG,
    BISHOP_PSQ_MG,
    ROOK_PSQ_MG,
    QUEEN_PSQ_MG,
    KING_PSQ_MG,
]

PSQ_TABLES_EG = [
    PAWN_PSQ_EG,
    KNIGHT_PSQ_EG,
    BISHOP_PSQ_EG,
    ROOK_PSQ_EG,
    QUEEN_PSQ_EG,
    KING_PSQ_EG,
]


# ============================================================================
# PAWN HASH TABLE
# ============================================================================

class PawnHashEntry:
    """
    Pawn hash table entry - stores precomputed pawn structure evaluation.
    
    Stores:
    - Pawn structure scores (doubled, isolated, passed pawns)
    - Pawn PSQT scores (position bonuses for pawns)
    
    This caches everything about pawn positions since they change rarely.
    """
    __slots__ = ['key', 'mg_score', 'eg_score', 'mg_psqt', 'eg_psqt', 'age']
    
    def __init__(self):
        self.key = 0           # Pawn hash for verification
        self.mg_score = 0      # Middlegame pawn structure evaluation
        self.eg_score = 0      # Endgame pawn structure evaluation
        self.mg_psqt = 0       # Middlegame pawn PSQT score
        self.eg_psqt = 0       # Endgame pawn PSQT score
        self.age = 0           # Age for replacement policy


class PawnHashTable:
    """
    Pawn structure hash table for caching expensive pawn evaluations.
    
    Size: 128K entries (2-way set associative) = ~10 MB
    Expected hit rate: 95-99% in typical positions
    """
    
    def __init__(self, size=131072):
        """
        Initialize pawn hash table with 2-way set associativity.
        
        Args:
            size: Number of buckets (must be power of 2 for fast modulo)
                  Each bucket holds 2 entries
        """
        if size & (size - 1) != 0:
            raise ValueError(f"Size must be power of 2, got {size}")
        
        self.size = size
        self.mask = size - 1  # For fast modulo with bitwise AND
        # 2-way set associative: each bucket has 2 entries
        self.table = [[PawnHashEntry(), PawnHashEntry()] for _ in range(size)]
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.collisions = 0  # Count of times we overwrite existing entry
        self.probes = 0      # Total number of probes
        self.generation = 0  # For age-based replacement
    
    def probe(self, pawn_hash: int) -> Optional[PawnHashEntry]:
        """
        Probe pawn hash table (2-way set associative).
        
        Args:
            pawn_hash: Pawn structure hash from board
        
        Returns:
            PawnHashEntry if hit, None if miss
        """
        self.probes += 1
        index = pawn_hash & self.mask
        bucket = self.table[index]
        
        # Check both entries in the bucket
        for entry in bucket:
            if entry.key == pawn_hash:
                self.hits += 1
                return entry
        
        self.misses += 1
        return None
    
    def store(self, pawn_hash: int, mg_score: int, eg_score: int, mg_psqt: int, eg_psqt: int):
        """
        Store pawn evaluation in hash table (2-way set associative).
        Uses age-based replacement: prefer replacing older entries.
        
        Args:
            pawn_hash: Pawn structure hash
            mg_score: Middlegame pawn structure evaluation
            eg_score: Endgame pawn structure evaluation
            mg_psqt: Middlegame pawn PSQT score
            eg_psqt: Endgame pawn PSQT score
        """
        index = pawn_hash & self.mask
        bucket = self.table[index]
        
        # Try to find empty slot or exact match first
        for entry in bucket:
            if entry.key == 0 or entry.key == pawn_hash:
                if entry.key != 0 and entry.key != pawn_hash:
                    self.collisions += 1
                entry.key = pawn_hash
                entry.mg_score = mg_score
                entry.eg_score = eg_score
                entry.mg_psqt = mg_psqt
                entry.eg_psqt = eg_psqt
                entry.age = self.generation
                return
        
        # Both slots occupied - replace older entry
        self.collisions += 1
        victim = bucket[0] if bucket[0].age < bucket[1].age else bucket[1]
        victim.key = pawn_hash
        victim.mg_score = mg_score
        victim.eg_score = eg_score
        victim.mg_psqt = mg_psqt
        victim.eg_psqt = eg_psqt
        victim.age = self.generation
    
    def get_hit_rate(self) -> float:
        """Get current hit rate (0.0 to 1.0)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def clear(self):
        """Clear all entries and reset statistics."""
        for bucket in self.table:
            for entry in bucket:
                entry.key = 0
                entry.mg_score = 0
                entry.eg_score = 0
                entry.mg_psqt = 0
                entry.eg_psqt = 0
                entry.age = 0
        self.hits = 0
        self.misses = 0
        self.collisions = 0
        self.probes = 0
        self.generation = 0
    
    def get_stats(self) -> dict:
        """Get comprehensive hash table statistics."""
        # Calculate true occupancy
        occupied_slots = 0
        for bucket in self.table:
            for entry in bucket:
                if entry.key != 0:
                    occupied_slots += 1
        
        total_slots = self.size * 2  # 2-way set associative
        occupancy_rate = occupied_slots / total_slots if total_slots > 0 else 0
        
        # Reuse factor: how many hits per unique insertion
        reuse_factor = self.hits / self.misses if self.misses > 0 else 0
        
        # Collision rate: fraction of stores that evicted existing entry
        collision_rate = self.collisions / self.misses if self.misses > 0 else 0
        
        return {
            'size': self.size,
            'total_slots': total_slots,
            'occupied_slots': occupied_slots,
            'occupancy_rate': occupancy_rate,
            'hits': self.hits,
            'misses': self.misses,
            'probes': self.probes,
            'collisions': self.collisions,
            'hit_rate': self.get_hit_rate(),
            'reuse_factor': reuse_factor,
            'collision_rate': collision_rate,
            'memory_kb': (total_slots * 48) // 1024  # 6 x 8 bytes per entry (added age)
        }


# ============================================================================
# EVALUATOR CLASS
# ============================================================================

class Evaluator:
    """
    Chess position evaluator with tapered evaluation and pawn hash table.
    
    Features:
    - Material counting
    - Piece-square tables (TODO)
    - Pawn structure evaluation (cached)
    - Tapered evaluation (middlegame → endgame)
    - Optional king safety and mobility (TODO)
    
    Performance: Target 750-900 cycles per evaluation
    """
    
    def __init__(self, pawn_hash_size=131072):
        """
        Initialize evaluator.
        
        Args:
            pawn_hash_size: Number of buckets in pawn hash table (power of 2)
                           Each bucket holds 2 entries (2-way set associative)
                           Default: 131072 buckets = 262144 total slots = ~12 MB
        """
        self.pawn_hash_table = PawnHashTable(pawn_hash_size)
        
        # Attack tables for king safety
        self.magic_bb = MagicBitboards()
        self.pre_calc_attacks = PreCalculatedAttacks()
        
        # Precompute pawn shield masks for all king positions
        # [side][king_square] -> (close_mask, far_mask)
        self.pawn_shield_masks = self._precompute_pawn_shield_masks()
        
        # Statistics
        self.eval_count = 0
    
    def _precompute_pawn_shield_masks(self):
        """
        Precompute pawn shield masks for all 64 king positions.
        
        Shield = 3 pawns in front of king (close + far ranks).
        Rarely change since kings don't move much in opening/middlegame.
        
        Returns:
            Dict[side][square] -> (close_mask, far_mask)
        """
        masks = [{}, {}]  # WHITE, BLACK
        
        for square in range(64):
            king_rank = square // 8
            king_file = square % 8
            
            # WHITE: pawns above king
            if king_rank < 7:
                # Close shield: 1 square ahead
                close_mask = 0
                shield_rank = (king_rank + 1) * 8
                if king_file > 0:
                    close_mask |= (1 << (shield_rank + king_file - 1))
                close_mask |= (1 << (shield_rank + king_file))
                if king_file < 7:
                    close_mask |= (1 << (shield_rank + king_file + 1))
                
                # Far shield: 2 squares ahead
                far_mask = 0
                if king_rank < 6:
                    shield_rank2 = (king_rank + 2) * 8
                    if king_file > 0:
                        far_mask |= (1 << (shield_rank2 + king_file - 1))
                    far_mask |= (1 << (shield_rank2 + king_file))
                    if king_file < 7:
                        far_mask |= (1 << (shield_rank2 + king_file + 1))
                
                masks[WHITE][square] = (close_mask, far_mask)
            else:
                masks[WHITE][square] = (0, 0)
            
            # BLACK: pawns below king
            if king_rank > 0:
                # Close shield: 1 square ahead
                close_mask = 0
                shield_rank = (king_rank - 1) * 8
                # Check bounds to avoid negative shifts
                if king_file > 0:
                    sq = shield_rank + king_file - 1
                    if 0 <= sq < 64:
                        close_mask |= (1 << sq)
                sq = shield_rank + king_file
                if 0 <= sq < 64:
                    close_mask |= (1 << sq)
                if king_file < 7:
                    sq = shield_rank + king_file + 1
                    if 0 <= sq < 64:
                        close_mask |= (1 << sq)
                
                # Far shield: 2 squares ahead
                far_mask = 0
                if king_rank > 1:
                    shield_rank2 = (king_rank - 2) * 8
                    # Check bounds to avoid negative shifts
                    if king_file > 0:
                        sq = shield_rank2 + king_file - 1
                        if 0 <= sq < 64:
                            far_mask |= (1 << sq)
                    sq = shield_rank2 + king_file
                    if 0 <= sq < 64:
                        far_mask |= (1 << sq)
                    if king_file < 7:
                        sq = shield_rank2 + king_file + 1
                        if 0 <= sq < 64:
                            far_mask |= (1 << sq)
                
                masks[BLACK][square] = (close_mask, far_mask)
            else:
                masks[BLACK][square] = (0, 0)
        
        return masks
    
    def evaluate(self, board: ChessBoard) -> int:
        """
        Evaluate position from white's perspective.
        
        Returns evaluation in centipawns:
        - Positive = white advantage
        - Negative = black advantage
        - 0 = equal position
        
        Uses Fruit's tapered evaluation formula:
        eval = (mg_score * (256 - phase) + eg_score * phase) / 256
        
        where phase 0 = opening, phase 256 = endgame
        
        Args:
            board: ChessBoard instance
        
        Returns:
            Evaluation score in centipawns
        """
        self.eval_count += 1
        
        # Calculate game phase (0-256, where 256 = pure endgame)
        phase = self._calculate_phase(board)
        
        # Initialize scores
        mg_score = 0  # Middlegame
        eg_score = 0  # Endgame
        
        # 1. Material evaluation (weight: 10/10 = 1.0x)
        material = self._evaluate_material(board)
        mg_score += (material * WEIGHT_MATERIAL) // WEIGHT_DIVISOR
        eg_score += (material * WEIGHT_MATERIAL) // WEIGHT_DIVISOR
        
        # 2. Piece-square tables (weight: 10/10 = 1.0x)
        mg_psqt, eg_psqt = self._evaluate_psqt(board)
        mg_score += (mg_psqt * WEIGHT_PSQT) // WEIGHT_DIVISOR
        eg_score += (eg_psqt * WEIGHT_PSQT) // WEIGHT_DIVISOR
        
        # 3. Pawn evaluation (weight: 7/10 = 0.7x)
        # Includes both pawn structure AND pawn PSQT scores
        # WITH CACHING via pawn hash table
        pawn_entry = self.pawn_hash_table.probe(board.pawn_hash)
        if pawn_entry is not None:
            # HIT: Use cached pawn evaluation (structure + PSQT)
            mg_pawn_total = pawn_entry.mg_score + pawn_entry.mg_psqt
            eg_pawn_total = pawn_entry.eg_score + pawn_entry.eg_psqt
            mg_score += (mg_pawn_total * WEIGHT_PAWN) // WEIGHT_DIVISOR
            eg_score += (eg_pawn_total * WEIGHT_PAWN) // WEIGHT_DIVISOR
        else:
            # MISS: Calculate pawn structure + PSQT and store in cache
            mg_pawn, eg_pawn, mg_pawn_psqt, eg_pawn_psqt = self._evaluate_pawn_structure(board)
            self.pawn_hash_table.store(board.pawn_hash, mg_pawn, eg_pawn, mg_pawn_psqt, eg_pawn_psqt)
            mg_pawn_total = mg_pawn + mg_pawn_psqt
            eg_pawn_total = eg_pawn + eg_pawn_psqt
            mg_score += (mg_pawn_total * WEIGHT_PAWN) // WEIGHT_DIVISOR
            eg_score += (eg_pawn_total * WEIGHT_PAWN) // WEIGHT_DIVISOR
        
        # 4. King safety (weight: 8/10 = 0.8x, middlegame only)
        mg_king_safety = self._evaluate_king_safety(board, phase)
        mg_score += (mg_king_safety * WEIGHT_KING_SAFETY) // WEIGHT_DIVISOR
        # King safety is primarily a middlegame concern, so only affects MG score
        
        # 5. Mobility (weight: 6/10 = 0.6x)
        # Queens and rooks scale with phase to encourage endgame activity
        mg_mob, eg_mob = self._evaluate_mobility(board, phase)
        mg_score += (mg_mob * WEIGHT_MOBILITY) // WEIGHT_DIVISOR
        eg_score += (eg_mob * WEIGHT_MOBILITY) // WEIGHT_DIVISOR
        
        # Taper between middlegame and endgame (Fruit's formula)
        # phase 0 = opening (full material) → use mg_score
        # phase 256 = endgame (minimal material) → use eg_score
        final_score = (mg_score * (256 - phase) + eg_score * phase) // 256
        
        # Tempo bonus - side to move has advantage
        if board.side_to_move == WHITE:
            final_score += TEMPO_BONUS
        else:
            final_score -= TEMPO_BONUS
        
        return final_score
    
    def _calculate_phase(self, board: ChessBoard) -> int:
        """
        Calculate game phase (0-256) using Fruit's convention.
        
        Phase represents "endgame weight":
        - phase = 0   → opening (all pieces on board, use 100% MG score)
        - phase = 128 → middlegame (use 50% MG, 50% EG)
        - phase = 256 → endgame (minimal material, use 100% EG score)
        
        Material contribution (pawns excluded):
        - Knight/Bishop: 1 point each
        - Rook: 2 points each
        - Queen: 4 points each
        - Total starting: 24 points (4N + 4B + 4R + 2Q)
        
        Formula: phase = 256 - (current_material * 256 / 24)
        - More material → lower phase (opening)
        - Less material → higher phase (endgame)
        
        Tapered eval uses: (mg * (256 - phase) + eg * phase) / 256
        
        Returns:
            Phase value 0-256 (endgame weight)
        """
        current_phase = 0
        
        # Count material for both sides
        for side in [WHITE, BLACK]:
            current_phase += popcount(board.pieces[side][KNIGHT]) * PHASE_VALUES[KNIGHT]
            current_phase += popcount(board.pieces[side][BISHOP]) * PHASE_VALUES[BISHOP]
            current_phase += popcount(board.pieces[side][ROOK]) * PHASE_VALUES[ROOK]
            current_phase += popcount(board.pieces[side][QUEEN]) * PHASE_VALUES[QUEEN]
        
        # Convert to 0-256 scale (inverted: 256 = endgame)
        phase = 256 - (current_phase * 256 // TOTAL_PHASE)
        
        # Clamp to 0-256 range
        return max(0, min(phase, 256))
    
    def _evaluate_material(self, board: ChessBoard) -> int:
        """
        Evaluate material balance.
        
        Simple piece counting with standard values:
        - Pawn: 100 cp
        - Knight: 320 cp
        - Bishop: 330 cp
        - Rook: 500 cp
        - Queen: 900 cp
        
        Returns:
            Material score from white's perspective
        """
        score = 0
        
        # White material (positive)
        for piece_type in [PAWN, KNIGHT, BISHOP, ROOK, QUEEN]:
            count = popcount(board.pieces[WHITE][piece_type])
            score += count * MATERIAL_VALUES[piece_type]
        
        # Black material (negative)
        for piece_type in [PAWN, KNIGHT, BISHOP, ROOK, QUEEN]:
            count = popcount(board.pieces[BLACK][piece_type])
            score -= count * MATERIAL_VALUES[piece_type]
        
        return score
    
    def _evaluate_psqt(self, board: ChessBoard) -> Tuple[int, int]:
        """
        Evaluate piece-square tables (PeSTO's tables).
        
        Assigns bonuses/penalties based on piece placement.
        Uses separate tables for middlegame and endgame.
        
        Note: Pawns are NOT included here - they are cached in pawn hash table.
        Only evaluates Knights, Bishops, Rooks, Queens, Kings.
        
        Note: Tables are indexed from white's perspective (a1=0, h8=63).
        For black pieces, we need to flip the square vertically.
        
        Returns:
            Tuple of (middlegame_score, endgame_score)
        """
        mg_score = 0
        eg_score = 0
        
        # Evaluate white pieces (SKIP PAWNS - they're cached!)
        for piece_type in range(1, 6):  # KNIGHT to KING (skip PAWN)
            pieces = board.pieces[WHITE][piece_type]
            mg_table = PSQ_TABLES_MG[piece_type]
            eg_table = PSQ_TABLES_EG[piece_type]
            
            while pieces:
                square = (pieces & -pieces).bit_length() - 1  # Get LSB
                mg_score += mg_table[square]
                eg_score += eg_table[square]
                pieces &= pieces - 1  # Clear LSB
        
        # Evaluate black pieces (SKIP PAWNS - they're cached!, flip square vertically)
        for piece_type in range(1, 6):  # KNIGHT to KING (skip PAWN)
            pieces = board.pieces[BLACK][piece_type]
            mg_table = PSQ_TABLES_MG[piece_type]
            eg_table = PSQ_TABLES_EG[piece_type]
            
            while pieces:
                square = (pieces & -pieces).bit_length() - 1  # Get LSB
                # Flip square: rank 0 ↔ 7, rank 1 ↔ 6, etc.
                flipped_square = square ^ 56  # XOR with 56 flips the rank
                mg_score -= mg_table[flipped_square]
                eg_score -= eg_table[flipped_square]
                pieces &= pieces - 1  # Clear LSB
        
        return (mg_score, eg_score)
    
    def _evaluate_pawn_structure(self, board: ChessBoard) -> Tuple[int, int, int, int]:
        """
        Evaluate pawn structure AND pawn PSQT (EXPENSIVE - that's why we cache it!).
        
        Evaluates:
        - Doubled pawns (same file) - PENALTY
        - Isolated pawns (no adjacent pawns) - PENALTY
        - Passed pawns (no enemy pawns ahead) - BONUS
        - Backward pawns (TODO) - PENALTY
        - Pawn piece-square table bonuses (PeSTO's tables)
        
        Returns:
            Tuple of (mg_structure, eg_structure, mg_psqt, eg_psqt)
        """
        mg_score = 0
        eg_score = 0
        
        # Evaluate white pawns (structure)
        mg_white, eg_white = self._evaluate_pawn_structure_side(
            board.white_pawns,
            board.black_pawns,
            WHITE
        )
        mg_score += mg_white
        eg_score += eg_white
        
        # Evaluate black pawns (structure)
        mg_black, eg_black = self._evaluate_pawn_structure_side(
            board.black_pawns,
            board.white_pawns,
            BLACK
        )
        mg_score -= mg_black  # Subtract for black
        eg_score -= eg_black
        
        # Evaluate pawn PSQT (piece-square tables)
        mg_psqt = 0
        eg_psqt = 0
        
        # White pawns PSQT
        pawns = board.white_pawns
        mg_table = PSQ_TABLES_MG[PAWN]
        eg_table = PSQ_TABLES_EG[PAWN]
        while pawns:
            square = (pawns & -pawns).bit_length() - 1  # Get LSB
            mg_psqt += mg_table[square]
            eg_psqt += eg_table[square]
            pawns &= pawns - 1  # Clear LSB
        
        # Black pawns PSQT (flip square vertically)
        pawns = board.black_pawns
        while pawns:
            square = (pawns & -pawns).bit_length() - 1  # Get LSB
            flipped_square = square ^ 56  # XOR with 56 flips the rank
            mg_psqt -= mg_table[flipped_square]
            eg_psqt -= eg_table[flipped_square]
            pawns &= pawns - 1  # Clear LSB
        
        return (mg_score, eg_score, mg_psqt, eg_psqt)
    
    def _evaluate_pawn_structure_side(
        self,
        our_pawns: int,
        enemy_pawns: int,
        side: int
    ) -> Tuple[int, int]:
        """
        Evaluate pawn structure for one side.
        
        Args:
            our_pawns: Bitboard of our pawns
            enemy_pawns: Bitboard of enemy pawns
            side: WHITE or BLACK
        
        Returns:
            Tuple of (middlegame_score, endgame_score)
        """
        mg_score = 0
        eg_score = 0
        
        # Check each file for pawns
        for file in range(8):
            file_mask = FILE_MASKS[file]
            our_pawns_on_file = our_pawns & file_mask
            
            if not our_pawns_on_file:
                continue
            
            pawn_count = popcount(our_pawns_on_file)
            
            # Doubled pawns: More than one pawn on same file
            # CRITICAL: "Doubled" means same FILE, not side-by-side!
            if pawn_count > 1:
                # Penalty for each extra pawn beyond the first
                penalty = (pawn_count - 1) * DOUBLED_PAWN_PENALTY
                mg_score -= penalty
                eg_score -= penalty
            
            # Isolated pawns: No friendly pawns on adjacent files
            adjacent_mask = ADJACENT_FILE_MASKS[file]
            has_adjacent_pawns = (our_pawns & adjacent_mask) != 0
            
            if not has_adjacent_pawns:
                # Isolated pawn penalty
                mg_score -= ISOLATED_PAWN_PENALTY
                eg_score -= ISOLATED_PAWN_PENALTY
            
            # Passed pawns: No enemy pawns ahead on same or adjacent files
            # This is more complex and depends on side
            passed_bonus = self._evaluate_passed_pawns(
                our_pawns_on_file,
                enemy_pawns,
                file,
                side
            )
            mg_score += passed_bonus
            eg_score += passed_bonus * 2  # Passed pawns more valuable in endgame
        
        return (mg_score, eg_score)
    
    def _evaluate_passed_pawns(
        self,
        our_pawns_on_file: int,
        enemy_pawns: int,
        file: int,
        side: int
    ) -> int:
        """
        Evaluate passed pawns on a file.
        
        A passed pawn has no enemy pawns:
        - On the same file ahead
        - On adjacent files ahead
        
        Optimized for PyPy JIT: uses bitwise operations instead of loops.
        
        Args:
            our_pawns_on_file: Our pawns on this file (bitboard)
            enemy_pawns: All enemy pawns (bitboard)
            file: File number (0-7)
            side: WHITE or BLACK
        
        Returns:
            Bonus score for passed pawns
        """
        if not our_pawns_on_file:
            return 0
        
        bonus = 0
        
        # Create mask for "ahead" squares on this file and adjacent files
        file_mask = FILE_MASKS[file]
        adjacent_mask = ADJACENT_FILE_MASKS[file]
        check_mask = file_mask | adjacent_mask
        
        # Check each pawn on this file
        pawns = our_pawns_on_file
        while pawns:
            square = (pawns & -pawns).bit_length() - 1  # Get LSB
            rank = square // 8
            
            # Create "ahead" mask based on side using bitwise operations (no loops!)
            if side == WHITE:
                # White pawns move up (toward rank 7)
                # Ahead = all squares on ranks above current rank
                if rank < 7:
                    # All bits from (rank+1)*8 onwards
                    ahead_mask = (0xFFFFFFFFFFFFFFFF << ((rank + 1) * 8)) & check_mask
                    
                    # Check if any enemy pawns ahead
                    if not (enemy_pawns & ahead_mask):
                        # Passed pawn! Bonus based on rank
                        bonus += PASSED_PAWN_BONUS[rank]
            else:
                # Black pawns move down (toward rank 0)
                # Ahead = all squares on ranks below current rank
                if rank > 0:
                    # All bits from 0 to rank*8 - 1
                    ahead_mask = ((1 << (rank * 8)) - 1) & check_mask
                    
                    # Check if any enemy pawns ahead
                    if not (enemy_pawns & ahead_mask):
                        # Passed pawn! Bonus based on rank (inverted for black)
                        bonus += PASSED_PAWN_BONUS[7 - rank]
            
            # Clear this pawn and continue
            pawns &= pawns - 1
        
        return bonus
    
    def _evaluate_king_safety(self, board: ChessBoard, phase: int) -> int:
        """
        Evaluate king safety for both sides.
        
        Components:
        1. Pawn shield bonus (pawns near king provide protection)
        2. Open/semi-open file penalties (exposed to rook attacks)
        3. King exposure penalty (enemy pieces attacking king zone)
        
        King zone = 8 squares adjacent to king (not including king square itself)
        
        King safety affects ONLY middlegame score. Phase weighting is applied
        by the taper formula, so this function returns unweighted raw scores.
        - Added to mg_score (not eg_score)
        - Taper applies: (mg_score * (256 - phase) + eg_score * phase) / 256
        - Result: King safety naturally fades as phase increases
        
        Args:
            board: ChessBoard instance
            phase: Game phase (0-256)
        
        Returns:
            King safety score from white's perspective (centipawns)
        """
        # Calculate for both sides
        white_safety = self._evaluate_king_safety_side(board, WHITE)
        black_safety = self._evaluate_king_safety_side(board, BLACK)
        
        # Return raw difference - phase weighting will be applied by taper
        # (no need to weight here, otherwise it gets weighted twice!)
        safety_score = white_safety - black_safety
        
        return safety_score
    
    def _evaluate_king_safety_side(self, board: ChessBoard, side: int) -> int:
        """
        Evaluate king safety for one side.
        
        Args:
            board: ChessBoard instance
            side: WHITE or BLACK
        
        Returns:
            King safety score (positive = safer)
        """
        # Find king position
        king_bb = board.pieces[side][KING]
        if not king_bb:
            return 0  # No king (shouldn't happen in valid position)
        
        # Get king square
        king_square = (king_bb & -king_bb).bit_length() - 1
        king_rank = king_square // 8
        king_file = king_square % 8
        
        safety = 0
        
        # 1. Pawn shield evaluation
        safety += self._evaluate_pawn_shield(board, side, king_square)
        
        # 2. Open/semi-open file penalties
        safety -= self._evaluate_open_files_near_king(board, side, king_file)
        
        # 3. King exposure (enemy attacks on king zone)
        safety -= self._evaluate_king_exposure(board, side, king_square)
        
        return safety
    
    def _evaluate_pawn_shield(self, board: ChessBoard, side: int, king_square: int) -> int:
        """
        Evaluate pawn shield around king using precomputed masks.
        
        Checks for friendly pawns:
        - Close shield: 1 square in front (3 squares)
        - Far shield: 2 squares in front (3 squares)
        
        OPTIMIZATION: Uses precomputed masks (stored in __init__).
        Kings rarely move in opening/middlegame, so we precompute all
        64 possible shield masks (close + far) for both colors.
        
        This reduces computation from ~40 cycles to ~8 cycles!
        
        Args:
            board: ChessBoard instance
            side: WHITE or BLACK
            king_square: King square index (0-63)
        
        Returns:
            Pawn shield bonus (positive value)
        """
        friendly_pawns = board.pieces[side][PAWN]
        
        # Use precomputed masks (MUCH faster - no computation needed!)
        close_mask, far_mask = self.pawn_shield_masks[side][king_square]
        
        # Count pawns in shield zones
        close_pawns = popcount(friendly_pawns & close_mask)
        far_pawns = popcount(friendly_pawns & far_mask)
        
        # Calculate bonus
        bonus = close_pawns * PAWN_SHIELD_BONUS + far_pawns * PAWN_SHIELD_FAR_BONUS
        
        return bonus
    
    def _evaluate_open_files_near_king(self, board: ChessBoard, side: int, king_file: int) -> int:
        """
        Evaluate open and semi-open files near king.
        
        Open file = no pawns of either color
        Semi-open file = no friendly pawns (but enemy pawns present)
        
        Args:
            board: ChessBoard instance
            side: WHITE or BLACK
            king_file: King's file (0-7)
        
        Returns:
            Penalty for exposed files (positive value = bad for king)
        """
        friendly_pawns = board.pieces[side][PAWN]
        enemy_pawns = board.pieces[1 - side][PAWN]
        
        penalty = 0
        
        # Check king's file and adjacent files
        for file_offset in [-1, 0, 1]:
            check_file = king_file + file_offset
            if 0 <= check_file < 8:
                file_mask = FILE_MASKS[check_file]
                
                has_friendly_pawn = bool(friendly_pawns & file_mask)
                has_enemy_pawn = bool(enemy_pawns & file_mask)
                
                if not has_friendly_pawn and not has_enemy_pawn:
                    # Open file (very dangerous)
                    penalty += OPEN_FILE_NEAR_KING_PENALTY
                elif not has_friendly_pawn and has_enemy_pawn:
                    # Semi-open file (moderately dangerous)
                    penalty += SEMI_OPEN_FILE_NEAR_KING_PENALTY
        
        return penalty
    
    def _evaluate_king_exposure(self, board: ChessBoard, side: int, king_square: int) -> int:
        """
        Evaluate king exposure to enemy attacks.
        
        King zone = 8 squares adjacent to king (not the king square itself).
        Count how many enemy pieces can attack these squares.
        
        Uses attack bitboards for speed:
        - Knight attacks (pre-calculated)
        - Bishop/Rook/Queen attacks (magic bitboards)
        - Pawn attacks (pre-calculated)
        - King attacks not counted (kings can't attack each other)
        
        TENTATIVE WEIGHT: Each attacking piece counts as -20 cp penalty.
        This will be tuned later based on testing.
        
        Args:
            board: ChessBoard instance
            side: WHITE or BLACK (side we're evaluating safety for)
            king_square: King square index (0-63)
        
        Returns:
            Exposure penalty (positive value = more exposed = worse)
        """
        enemy = 1 - side
        
        # Get king zone (8 adjacent squares, not the king square itself)
        king_zone = self.pre_calc_attacks.king_attacks[king_square]
        
        # Count enemy pieces attacking king zone
        attack_count = 0
        occupancy = board.all_pieces
        
        # Enemy knights
        enemy_knights = board.pieces[enemy][KNIGHT]
        while enemy_knights:
            knight_sq = (enemy_knights & -enemy_knights).bit_length() - 1
            knight_attacks = self.pre_calc_attacks.knight_attacks[knight_sq]
            if knight_attacks & king_zone:
                attack_count += 1
            enemy_knights &= enemy_knights - 1
        
        # Enemy bishops
        enemy_bishops = board.pieces[enemy][BISHOP]
        while enemy_bishops:
            bishop_sq = (enemy_bishops & -enemy_bishops).bit_length() - 1
            bishop_attacks = self.magic_bb.get_bishop_attacks(bishop_sq, occupancy)
            if bishop_attacks & king_zone:
                attack_count += 1
            enemy_bishops &= enemy_bishops - 1
        
        # Enemy rooks
        enemy_rooks = board.pieces[enemy][ROOK]
        while enemy_rooks:
            rook_sq = (enemy_rooks & -enemy_rooks).bit_length() - 1
            rook_attacks = self.magic_bb.get_rook_attacks(rook_sq, occupancy)
            if rook_attacks & king_zone:
                attack_count += 1
            enemy_rooks &= enemy_rooks - 1
        
        # Enemy queens
        enemy_queens = board.pieces[enemy][QUEEN]
        while enemy_queens:
            queen_sq = (enemy_queens & -enemy_queens).bit_length() - 1
            queen_attacks = self.magic_bb.get_queen_attacks(queen_sq, occupancy)
            if queen_attacks & king_zone:
                attack_count += 1
            enemy_queens &= enemy_queens - 1
        
        # Enemy pawns (they can also attack king zone)
        enemy_pawns = board.pieces[enemy][PAWN]
        if side == WHITE:
            # Black pawns attack diagonally downward
            # >> 7 goes right (towards h-file), >> 9 goes left (towards a-file)
            pawn_attacks_right = (enemy_pawns >> 7) & ~FILE_MASKS[7]  # Mask h-file
            pawn_attacks_left = (enemy_pawns >> 9) & ~FILE_MASKS[0]   # Mask a-file
        else:
            # White pawns attack diagonally upward
            # << 7 goes left (towards a-file), << 9 goes right (towards h-file)
            pawn_attacks_left = (enemy_pawns << 7) & ~FILE_MASKS[0]   # Mask a-file
            pawn_attacks_right = (enemy_pawns << 9) & ~FILE_MASKS[7]  # Mask h-file
        
        pawn_attacks = pawn_attacks_left | pawn_attacks_right
        if pawn_attacks & king_zone:
            # Count number of pawns attacking (approximate)
            attack_count += popcount(pawn_attacks & king_zone)
        
        # Calculate penalty
        penalty = attack_count * KING_ZONE_ATTACK_PENALTY
        
        return penalty
    
    def _evaluate_mobility(self, board: ChessBoard, phase: int) -> Tuple[int, int]:
        """
        Evaluate piece mobility for both sides.
        
        Mobility = number of SAFE squares each piece can move to:
        - Reachable by the piece (using magic bitboards for sliders)
        - NOT attacked by enemy pieces
        - NOT occupied by friendly pieces
        - NOT occupied by enemy pieces (excludes captures)
        
        Weight ratios: Knight/Bishop constant, Queen/Rook scale with phase
        Queens and rooks more valuable in endgame (open files, active pieces)
        
        Optimized: Compute attack maps once and reuse for both sides.
        
        Args:
            board: ChessBoard instance
            phase: Game phase (0=opening, 256=endgame)
        
        Returns:
            Tuple of (middlegame_mobility, endgame_mobility)
        """
        # Get occupancy once
        all_pieces = board.white_pieces | board.black_pieces
        
        # Compute attack maps once for both sides
        white_attacks = self._generate_attack_map(board, WHITE, all_pieces)
        black_attacks = self._generate_attack_map(board, BLACK, all_pieces)
        
        # Evaluate white mobility (pass pre-computed black attacks)
        mg_white, eg_white = self._evaluate_mobility_side(
            board, WHITE, phase, all_pieces, black_attacks
        )
        
        # Evaluate black mobility (pass pre-computed white attacks)
        mg_black, eg_black = self._evaluate_mobility_side(
            board, BLACK, phase, all_pieces, white_attacks
        )
        
        # Calculate difference (weights are already in centipawns)
        mg_mobility = mg_white - mg_black
        eg_mobility = eg_white - eg_black
        
        return (mg_mobility, eg_mobility)
    
    def _evaluate_mobility_side(self, board: ChessBoard, side: int, phase: int,
                                 all_pieces: int, enemy_attacks: int) -> Tuple[int, int]:
        """
        Evaluate mobility for one side.
        
        Queens and rooks use phase-dependent weights to encourage
        activity in late middlegame and endgame.
        
        Optimized: Takes pre-computed occupancy and enemy attacks.
        Inlines frequently accessed attributes for PyPy JIT.
        
        Args:
            board: ChessBoard instance
            side: WHITE or BLACK
            phase: Game phase (0=opening, 256=endgame)
            all_pieces: Pre-computed occupancy bitboard
            enemy_attacks: Pre-computed enemy attack map
        
        Returns:
            Tuple of (middlegame_score, endgame_score)
        """
        # Inline frequently accessed attributes for PyPy JIT
        magic_bb = self.magic_bb
        pre_calc = self.pre_calc_attacks
        
        # Safe squares = not occupied AND not attacked by enemy
        # Mask with 0xFFFFFFFFFFFFFFFF to prevent Python big-int overhead
        MASK_64 = 0xFFFFFFFFFFFFFFFF
        safe_empty_squares = ((~all_pieces) & (~enemy_attacks)) & MASK_64
        
        mg_score = 0
        eg_score = 0
        
        # 1. Knight mobility (constant weight: 11 cp)
        knights = board.pieces[side][KNIGHT]
        knight_mobility = 0
        while knights:
            square = (knights & -knights).bit_length() - 1
            # Get knight attacks from pre-calculated table (inlined)
            attacks = pre_calc.knight_attacks[square]
            # Count safe empty squares
            safe_moves = attacks & safe_empty_squares
            knight_mobility += popcount(safe_moves)
            knights &= knights - 1
        
        mg_score += knight_mobility * MOBILITY_KNIGHT_WEIGHT
        eg_score += knight_mobility * MOBILITY_KNIGHT_WEIGHT
        
        # 2. Bishop mobility (constant weight: 7 cp)
        bishops = board.pieces[side][BISHOP]
        bishop_mobility = 0
        while bishops:
            square = (bishops & -bishops).bit_length() - 1
            # Get bishop attacks using magic bitboards (inlined)
            attacks = magic_bb.get_bishop_attacks(square, all_pieces)
            # Count safe empty squares
            safe_moves = attacks & safe_empty_squares
            bishop_mobility += popcount(safe_moves)
            bishops &= bishops - 1
        
        mg_score += bishop_mobility * MOBILITY_BISHOP_WEIGHT
        eg_score += bishop_mobility * MOBILITY_BISHOP_WEIGHT
        
        # 3. Rook mobility (phase-dependent: 3 in MG, 8 in EG)
        rooks = board.pieces[side][ROOK]
        rook_mobility = 0
        while rooks:
            square = (rooks & -rooks).bit_length() - 1
            # Get rook attacks using magic bitboards (inlined)
            attacks = magic_bb.get_rook_attacks(square, all_pieces)
            # Count safe empty squares
            safe_moves = attacks & safe_empty_squares
            rook_mobility += popcount(safe_moves)
            rooks &= rooks - 1
        
        # FIXED: Use separate MG and EG weights (no longer interpolating)
        # Tapered eval will handle the phase blending automatically
        mg_score += rook_mobility * MOBILITY_ROOK_WEIGHT_MG
        eg_score += rook_mobility * MOBILITY_ROOK_WEIGHT_EG
        
        # 4. Queen mobility (phase-dependent: 4 in MG, 10 in EG)
        queens = board.pieces[side][QUEEN]
        queen_mobility = 0
        while queens:
            square = (queens & -queens).bit_length() - 1
            # Queen = rook + bishop attacks (inlined magic)
            rook_attacks = magic_bb.get_rook_attacks(square, all_pieces)
            bishop_attacks = magic_bb.get_bishop_attacks(square, all_pieces)
            attacks = rook_attacks | bishop_attacks
            # Count safe empty squares
            safe_moves = attacks & safe_empty_squares
            queen_mobility += popcount(safe_moves)
            queens &= queens - 1
        
        # FIXED: Use separate MG and EG weights (no longer interpolating)
        # Tapered eval will handle the phase blending automatically
        mg_score += queen_mobility * MOBILITY_QUEEN_WEIGHT_MG
        eg_score += queen_mobility * MOBILITY_QUEEN_WEIGHT_EG
        
        # Return weighted mobility scores (already in centipawns)
        return (mg_score, eg_score)
    
    def _generate_attack_map(self, board: ChessBoard, side: int, all_pieces: int) -> int:
        """
        Generate a bitboard of all squares attacked by a given side.
        
        Used for mobility calculation to identify unsafe squares.
        Optimized with bitwise operations for PyPy JIT.
        
        Args:
            board: ChessBoard instance
            side: WHITE or BLACK
            all_pieces: Bitboard of all pieces on the board
        
        Returns:
            Bitboard of all attacked squares
        """
        attacks = 0
        
        # 1. Pawn attacks (special case - don't need occupancy)
        pawns = board.pieces[side][PAWN]
        if side == WHITE:
            # White pawns attack diagonally upward
            pawn_attacks_left = (pawns << 7) & ~FILE_MASKS[0]   # Mask a-file
            pawn_attacks_right = (pawns << 9) & ~FILE_MASKS[7]  # Mask h-file
            attacks |= pawn_attacks_left | pawn_attacks_right
        else:
            # Black pawns attack diagonally downward
            pawn_attacks_right = (pawns >> 7) & ~FILE_MASKS[7]  # Mask h-file
            pawn_attacks_left = (pawns >> 9) & ~FILE_MASKS[0]   # Mask a-file
            attacks |= pawn_attacks_left | pawn_attacks_right
        
        # 2. Knight attacks
        knights = board.pieces[side][KNIGHT]
        while knights:
            square = (knights & -knights).bit_length() - 1
            attacks |= self.pre_calc_attacks.knight_attacks[square]
            knights &= knights - 1
        
        # 3. Bishop attacks
        bishops = board.pieces[side][BISHOP]
        while bishops:
            square = (bishops & -bishops).bit_length() - 1
            attacks |= self.magic_bb.get_bishop_attacks(square, all_pieces)
            bishops &= bishops - 1
        
        # 4. Rook attacks
        rooks = board.pieces[side][ROOK]
        while rooks:
            square = (rooks & -rooks).bit_length() - 1
            attacks |= self.magic_bb.get_rook_attacks(square, all_pieces)
            rooks &= rooks - 1
        
        # 5. Queen attacks
        queens = board.pieces[side][QUEEN]
        while queens:
            square = (queens & -queens).bit_length() - 1
            rook_attacks = self.magic_bb.get_rook_attacks(square, all_pieces)
            bishop_attacks = self.magic_bb.get_bishop_attacks(square, all_pieces)
            attacks |= rook_attacks | bishop_attacks
            queens &= queens - 1
        
        # 6. King attacks
        kings = board.pieces[side][KING]
        if kings:
            king_square = (kings & -kings).bit_length() - 1
            attacks |= self.pre_calc_attacks.king_attacks[king_square]
        
        return attacks
    
    def get_stats(self) -> dict:
        """
        Get evaluator statistics.
        
        Returns:
            Dictionary with evaluation and hash table stats
        """
        pawn_stats = self.pawn_hash_table.get_stats()
        
        return {
            'evaluations': self.eval_count,
            'pawn_hash': pawn_stats
        }
    
    def clear_cache(self):
        """Clear pawn hash table and reset statistics."""
        self.pawn_hash_table.clear()
        self.eval_count = 0
