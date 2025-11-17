"""
Ultra-Fast Bitboard Operations - Inline Optimized
All critical hot-path functions optimized for maximum speed.
"""

# Inline-optimized pop_lsb - most called function in move generation
def pop_lsb_fast(bb: int) -> tuple:
    """
    Ultra-fast LSB extraction and removal.
    Inline-optimized to avoid function call overhead.
    Returns (square_index, remaining_bitboard).
    """
    # Isolate LSB: bb & -bb
    # Get square: (lsb).bit_length() - 1
    # Remove LSB: bb & (bb - 1)
    # All in one expression to maximize speed
    lsb = bb & -bb
    return (lsb.bit_length() - 1, bb ^ lsb)


# Pre-computed bit_length lookup for small values (faster than .bit_length())
_BIT_LENGTH = [0] * 256
for _i in range(256):
    _BIT_LENGTH[_i] = _i.bit_length()


def get_lsb_fast(bb: int) -> int:
    """
    Ultra-fast LSB index retrieval.
    Returns the index of the least significant bit.
    """
    return (bb & -bb).bit_length() - 1


def count_bits_fast(bb: int) -> int:
    """
    Ultra-fast bit counting using Brian Kernighan's algorithm.
    Optimized for typical chess piece counts (1-16 pieces).
    """
    count = 0
    while bb:
        bb &= bb - 1  # Clear the lowest set bit
        count += 1
    return count


# Alternative using Python 3.10+ bit_count (even faster if available)
try:
    def count_bits_builtin(bb: int) -> int:
        return bb.bit_count()
    # Test if bit_count is available
    count_bits_builtin(1)
    count_bits_fast = count_bits_builtin
except AttributeError:
    pass  # Keep the manual version


# Inline helpers for move generation
def _white_pawn_push_one(pawns: int, empty: int) -> int:
    """Inline: Generate single pawn pushes for white."""
    return (pawns << 8) & empty


def _white_pawn_push_two(pawns: int, empty: int) -> int:
    """Inline: Generate double pawn pushes for white."""
    # Rank 2 pawns, push twice, both squares must be empty
    rank_2 = 0x000000000000FF00
    single_push = (pawns & rank_2) << 8
    return (single_push << 8) & empty & (empty >> 8)


def _black_pawn_push_one(pawns: int, empty: int) -> int:
    """Inline: Generate single pawn pushes for black."""
    return (pawns >> 8) & empty


def _black_pawn_push_two(pawns: int, empty: int) -> int:
    """Inline: Generate double pawn pushes for black."""
    # Rank 7 pawns, push twice, both squares must be empty
    rank_7 = 0x00FF000000000000
    single_push = (pawns & rank_7) >> 8
    return (single_push >> 8) & empty & (empty << 8)


# Bitboard rank masks for fast promotion detection
RANK_7_BB = 0x00FF000000000000  # White promotion rank (pawns on rank 7)
RANK_2_BB = 0x000000000000FF00  # Black promotion rank (pawns on rank 2)
RANK_2_WHITE = 0x000000000000FF00  # White starting rank
RANK_7_BLACK = 0x00FF000000000000  # Black starting rank

# File masks for boundary checking
NOT_A_FILE = 0xFEFEFEFEFEFEFEFE
NOT_H_FILE = 0x7F7F7F7F7F7F7F7F


def is_promotion_square(square: int, side: int) -> bool:
    """Fast promotion check using bitboard."""
    bb = 1 << square
    if side == 0:  # WHITE
        return bb & 0xFF00000000000000  # Rank 8
    else:  # BLACK
        return bb & 0x00000000000000FF  # Rank 1


# ============================================================================
# PHASE 2: Pre-computed Lookup Tables for Maximum Speed
# ============================================================================

# Pre-compute all single bit positions (used constantly)
_SINGLE_BIT = tuple(1 << i for i in range(64))

def get_bit(square: int) -> int:
    """Get single bit at square position - O(1) lookup."""
    return _SINGLE_BIT[square]


# Pre-compute squares by rank and file for fast access
_SQUARES_BY_RANK = tuple(tuple(rank * 8 + file for file in range(8)) for rank in range(8))
_SQUARES_BY_FILE = tuple(tuple(rank * 8 + file for rank in range(8)) for file in range(8))


# Pre-compute promotion squares for each side
_WHITE_PROMOTION_SQUARES = frozenset(range(56, 64))  # Rank 8
_BLACK_PROMOTION_SQUARES = frozenset(range(0, 8))    # Rank 1

def is_promotion_square_lookup(square: int, side: int) -> bool:
    """O(1) promotion check using pre-computed sets."""
    return square in (_WHITE_PROMOTION_SQUARES if side == 0 else _BLACK_PROMOTION_SQUARES)


# Pre-compute double push source squares
_WHITE_DOUBLE_PUSH_SQUARES = frozenset(range(8, 16))   # Rank 2
_BLACK_DOUBLE_PUSH_SQUARES = frozenset(range(48, 56))  # Rank 7

def can_double_push(square: int, side: int) -> bool:
    """O(1) check if pawn can double push."""
    return square in (_WHITE_DOUBLE_PUSH_SQUARES if side == 0 else _BLACK_DOUBLE_PUSH_SQUARES)


# Pre-compute all pawn push destinations
_WHITE_PAWN_SINGLE_PUSH = tuple((sq + 8 if sq < 56 else -1) for sq in range(64))
_BLACK_PAWN_SINGLE_PUSH = tuple((sq - 8 if sq >= 8 else -1) for sq in range(64))
_WHITE_PAWN_DOUBLE_PUSH = tuple((sq + 16 if 8 <= sq < 16 else -1) for sq in range(64))
_BLACK_PAWN_DOUBLE_PUSH = tuple((sq - 16 if 48 <= sq < 56 else -1) for sq in range(64))

def get_pawn_single_push(square: int, side: int) -> int:
    """Get single push destination - O(1) lookup."""
    return _WHITE_PAWN_SINGLE_PUSH[square] if side == 0 else _BLACK_PAWN_SINGLE_PUSH[square]

def get_pawn_double_push(square: int, side: int) -> int:
    """Get double push destination - O(1) lookup."""
    return _WHITE_PAWN_DOUBLE_PUSH[square] if side == 0 else _BLACK_PAWN_DOUBLE_PUSH[square]


# ============================================================================
# PHASE 3: Ultra-aggressive inlining for maximum speed
# ============================================================================

# Pre-compute LSB lookup table for ultra-fast operations
_LSB_TABLE = tuple((1 << i).bit_length() - 1 for i in range(64))

# Cache commonly used bitboard operations
def has_single_bit(bb: int) -> bool:
    """Check if bitboard has exactly one bit set."""
    return bb != 0 and (bb & (bb - 1)) == 0

def more_than_one_bit(bb: int) -> bool:
    """Check if bitboard has more than one bit set."""
    return (bb & (bb - 1)) != 0


# Ultra-fast square operations (no function call overhead)
class FastBitboard:
    """
    Namespace for ultra-fast bitboard operations.
    All methods are static and optimized for speed.
    """
    
    __slots__ = ()
    
    @staticmethod
    def pop_lsb(bb: int) -> tuple:
        """Ultra-fast pop LSB."""
        lsb = bb & -bb
        return lsb.bit_length() - 1, bb ^ lsb
    
    @staticmethod
    def get_lsb(bb: int) -> int:
        """Ultra-fast get LSB index."""
        return (bb & -bb).bit_length() - 1
    
    @staticmethod
    def count_bits(bb: int) -> int:
        """Ultra-fast bit count."""
        try:
            return bb.bit_count()  # Python 3.10+
        except AttributeError:
            count = 0
            while bb:
                bb &= bb - 1
                count += 1
            return count
    
    @staticmethod
    def get_bit(square: int) -> int:
        """Get bit at square."""
        return 1 << square
    
    @staticmethod
    def is_set(bb: int, square: int) -> bool:
        """Check if bit at square is set."""
        return bool(bb & (1 << square))


# Export optimized operations
fast_pop_lsb = FastBitboard.pop_lsb
fast_get_lsb = FastBitboard.get_lsb
fast_count_bits = FastBitboard.count_bits
fast_get_bit = FastBitboard.get_bit
fast_is_set = FastBitboard.is_set
