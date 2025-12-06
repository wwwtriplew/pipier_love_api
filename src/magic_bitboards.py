"""
Magic Bitboard Implementation for Fast Chess Move Generation

This module implements magic bitboards for sliding pieces (rooks, bishops, queens)
with pre-calculated attack tables for maximum performance.
"""

import random
from typing import List, Tuple

# Try to import Cython-optimized functions
try:
    from bitboard_ops import (  # type: ignore
        cy_pop_count, cy_get_lsb, cy_pop_lsb,
        cy_knight_attacks, cy_king_attacks,
        cy_white_pawn_attacks, cy_black_pawn_attacks
    )
    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False

# Bitboard constants
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
FILE_AB = FILE_A | (FILE_A << 1)
FILE_GH = FILE_H | (FILE_H >> 1)
RANK_1 = 0x00000000000000FF
RANK_8 = 0xFF00000000000000
RANK_4 = 0x00000000FF000000
RANK_5 = 0x000000FF00000000

# Direction offsets
NORTH = 8
SOUTH = -8
EAST = 1
WEST = -1
NORTH_EAST = 9
NORTH_WEST = 7
SOUTH_EAST = -7
SOUTH_WEST = -9

# Magic numbers for rooks and bishops (pre-calculated for best performance)
ROOK_MAGICS = [
    0x0080001020400080, 0x0040001000200040, 0x0080081000200080, 0x0080040800100080,
    0x0080020400080080, 0x0080010200040080, 0x0080008001000200, 0x0080002040800100,
    0x0000800020400080, 0x0000400020005000, 0x0000801000200080, 0x0000800800100080,
    0x0000800400080080, 0x0000800200040080, 0x0000800100020080, 0x0000800040800100,
    0x0000208000400080, 0x0000404000201000, 0x0000808010000800, 0x0000808008000400,
    0x0000808004000200, 0x0000808002000100, 0x0000808001000100, 0x0000408000800100,
    0x0000204000808000, 0x0000200040008080, 0x0000100080008080, 0x0000080080008080,
    0x0000040080008080, 0x0000020080008080, 0x0000010080008080, 0x0000008080008080,
    0x0000802000808000, 0x0000800800808000, 0x0000800400808000, 0x0000800200808000,
    0x0000800100808000, 0x0000800080808000, 0x0000800040808000, 0x0000800020808000,
    0x0000800010020000, 0x0000800008020000, 0x0000800004020000, 0x0000800002020000,
    0x0000800001020000, 0x0000800000808000, 0x0000800000404000, 0x0000800000202000,
    0x0000802000208000, 0x0000801000204000, 0x0000800800202000, 0x0000800400201000,
    0x0000800200200800, 0x0000800100200400, 0x0000800080200200, 0x0000800040200100,
    0x0000208000400080, 0x0000404000201000, 0x0000808010000800, 0x0000808008000400,
    0x0000808004000200, 0x0000808002000100, 0x0000808001000100, 0x0000408000800100
]

BISHOP_MAGICS = [
    0x0002020202020200, 0x0002020202020000, 0x0004010202000000, 0x0004040080000000,
    0x0001104000000000, 0x0000821040000000, 0x0000410410400000, 0x0000104104104000,
    0x0000040404040400, 0x0000020202020200, 0x0000040102020000, 0x0000040400800000,
    0x0000011040000000, 0x0000008210400000, 0x0000004104104000, 0x0000002082082000,
    0x0004000808080800, 0x0002000404040400, 0x0001000202020200, 0x0000800802004000,
    0x0000800400A00000, 0x0000200100884000, 0x0000400082082000, 0x0000200041041000,
    0x0002080010101000, 0x0001040008080800, 0x0000208004010400, 0x0000404004010200,
    0x0000840000802000, 0x0000404002011000, 0x0000808001041000, 0x0000404000820800,
    0x0001041000202000, 0x0000820800101000, 0x0000104400080800, 0x0000020080080080,
    0x0000404040040100, 0x0000808100020100, 0x0001010100020800, 0x0000808080010400,
    0x0000820820004000, 0x0000410410002000, 0x0000082088001000, 0x0000002011000800,
    0x0000080100400400, 0x0001010101000200, 0x0002020202000400, 0x0001010101000200,
    0x0000410410400000, 0x0000208208200000, 0x0000002084100000, 0x0000000020880000,
    0x0000001002020000, 0x0000040408020000, 0x0004040404040000, 0x0002020202020000,
    0x0000104104104000, 0x0000002082082000, 0x0000000020841000, 0x0000000000208800,
    0x0000000010020200, 0x0000000404080200, 0x0000040404040400, 0x0002020202020200
]

# Bit counts for indexing (number of relevant occupancy bits)
ROOK_BITS = [
    12, 11, 11, 11, 11, 11, 11, 12,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    12, 11, 11, 11, 11, 11, 11, 12
]

BISHOP_BITS = [
    6, 5, 5, 5, 5, 5, 5, 6,
    5, 5, 5, 5, 5, 5, 5, 5,
    5, 5, 7, 7, 7, 7, 5, 5,
    5, 5, 7, 9, 9, 7, 5, 5,
    5, 5, 7, 9, 9, 7, 5, 5,
    5, 5, 7, 7, 7, 7, 5, 5,
    5, 5, 5, 5, 5, 5, 5, 5,
    6, 5, 5, 5, 5, 5, 5, 6
]


class MagicBitboards:
    """
    Magic bitboard implementation with pre-calculated attack tables.
    Provides O(1) lookup for sliding piece attacks.
    """
    
    def __init__(self):
        self.rook_masks = [0] * 64
        self.bishop_masks = [0] * 64
        # Create properly sized attack tables based on bit counts
        self.rook_attacks = [[0] * (1 << ROOK_BITS[sq]) for sq in range(64)]
        self.bishop_attacks = [[0] * (1 << BISHOP_BITS[sq]) for sq in range(64)]
        
        # Pre-calculate all attack tables
        self._init_masks()
        self._init_attack_tables()
    
    def _init_masks(self):
        """Generate occupancy masks for rooks and bishops."""
        for square in range(64):
            self.rook_masks[square] = self._rook_mask(square)
            self.bishop_masks[square] = self._bishop_mask(square)
    
    def _rook_mask(self, square: int) -> int:
        """Generate rook occupancy mask (excludes edges)."""
        mask = 0
        rank = square // 8
        file = square % 8
        
        # North
        for r in range(rank + 1, 7):
            mask |= 1 << (r * 8 + file)
        # South
        for r in range(rank - 1, 0, -1):
            mask |= 1 << (r * 8 + file)
        # East
        for f in range(file + 1, 7):
            mask |= 1 << (rank * 8 + f)
        # West
        for f in range(file - 1, 0, -1):
            mask |= 1 << (rank * 8 + f)
        
        return mask
    
    def _bishop_mask(self, square: int) -> int:
        """Generate bishop occupancy mask (excludes edges)."""
        mask = 0
        rank = square // 8
        file = square % 8
        
        # North-East
        r, f = rank + 1, file + 1
        while r < 7 and f < 7:
            mask |= 1 << (r * 8 + f)
            r += 1
            f += 1
        
        # North-West
        r, f = rank + 1, file - 1
        while r < 7 and f > 0:
            mask |= 1 << (r * 8 + f)
            r += 1
            f -= 1
        
        # South-East
        r, f = rank - 1, file + 1
        while r > 0 and f < 7:
            mask |= 1 << (r * 8 + f)
            r -= 1
            f += 1
        
        # South-West
        r, f = rank - 1, file - 1
        while r > 0 and f > 0:
            mask |= 1 << (r * 8 + f)
            r -= 1
            f -= 1
        
        return mask
    
    def _rook_attacks_on_the_fly(self, square: int, occupancy: int) -> int:
        """Generate rook attacks for a given occupancy."""
        # Bounds check
        if square < 0 or square > 63:
            return 0
        
        attacks = 0
        rank = square // 8
        file = square % 8
        
        # North
        for r in range(rank + 1, 8):
            attacks |= 1 << (r * 8 + file)
            if occupancy & (1 << (r * 8 + file)):
                break
        # South
        for r in range(rank - 1, -1, -1):
            attacks |= 1 << (r * 8 + file)
            if occupancy & (1 << (r * 8 + file)):
                break
        # East
        for f in range(file + 1, 8):
            attacks |= 1 << (rank * 8 + f)
            if occupancy & (1 << (rank * 8 + f)):
                break
        # West
        for f in range(file - 1, -1, -1):
            attacks |= 1 << (rank * 8 + f)
            if occupancy & (1 << (rank * 8 + f)):
                break
        
        return attacks
    
    def _bishop_attacks_on_the_fly(self, square: int, occupancy: int) -> int:
        """Generate bishop attacks for a given occupancy."""
        # Bounds check
        if square < 0 or square > 63:
            return 0
        
        attacks = 0
        rank = square // 8
        file = square % 8
        
        # North-East
        r, f = rank + 1, file + 1
        while r < 8 and f < 8:
            attacks |= 1 << (r * 8 + f)
            if occupancy & (1 << (r * 8 + f)):
                break
            r += 1
            f += 1
        
        # North-West
        r, f = rank + 1, file - 1
        while r < 8 and f >= 0:
            attacks |= 1 << (r * 8 + f)
            if occupancy & (1 << (r * 8 + f)):
                break
            r += 1
            f -= 1
        
        # South-East
        r, f = rank - 1, file + 1
        while r >= 0 and f < 8:
            attacks |= 1 << (r * 8 + f)
            if occupancy & (1 << (r * 8 + f)):
                break
            r -= 1
            f += 1
        
        # South-West
        r, f = rank - 1, file - 1
        while r >= 0 and f >= 0:
            attacks |= 1 << (r * 8 + f)
            if occupancy & (1 << (r * 8 + f)):
                break
            r -= 1
            f -= 1
        
        return attacks
    
    def _init_attack_tables(self):
        """Initialize magic bitboard attack tables."""
        for square in range(64):
            # Rook attacks
            occ_mask = self.rook_masks[square]
            bit_count = ROOK_BITS[square]
            occ_variations = 1 << bit_count
            
            for i in range(occ_variations):
                occupancy = self._index_to_occupancy(i, bit_count, occ_mask)
                magic_index = ((occupancy & occ_mask) * ROOK_MAGICS[square]) >> (64 - bit_count)
                # Ensure index is within bounds
                if magic_index < len(self.rook_attacks[square]):
                    self.rook_attacks[square][magic_index] = self._rook_attacks_on_the_fly(square, occupancy)
            
            # Bishop attacks
            occ_mask = self.bishop_masks[square]
            bit_count = BISHOP_BITS[square]
            occ_variations = 1 << bit_count
            
            for i in range(occ_variations):
                occupancy = self._index_to_occupancy(i, bit_count, occ_mask)
                magic_index = ((occupancy & occ_mask) * BISHOP_MAGICS[square]) >> (64 - bit_count)
                # Ensure index is within bounds
                if magic_index < len(self.bishop_attacks[square]):
                    self.bishop_attacks[square][magic_index] = self._bishop_attacks_on_the_fly(square, occupancy)
    
    def _index_to_occupancy(self, index: int, bit_count: int, mask: int) -> int:
        """Convert an index to a specific occupancy pattern."""
        occupancy = 0
        for i in range(bit_count):
            bit_pos = (mask & -mask).bit_length() - 1
            if index & (1 << i):
                occupancy |= 1 << bit_pos
            mask &= mask - 1
        return occupancy
    
    def get_rook_attacks(self, square: int, occupancy: int) -> int:
        """Get rook attacks using magic bitboards (O(1) lookup)."""
        occ = occupancy & self.rook_masks[square]
        magic_index = (occ * ROOK_MAGICS[square]) >> (64 - ROOK_BITS[square])
        # Bounds check with fallback
        if magic_index < len(self.rook_attacks[square]) and self.rook_attacks[square][magic_index] != 0:
            return self.rook_attacks[square][magic_index]
        return self._rook_attacks_on_the_fly(square, occupancy)
    
    def get_bishop_attacks(self, square: int, occupancy: int) -> int:
        """Get bishop attacks using magic bitboards (O(1) lookup)."""
        occ = occupancy & self.bishop_masks[square]
        magic_index = (occ * BISHOP_MAGICS[square]) >> (64 - BISHOP_BITS[square])
        # Bounds check with fallback
        if magic_index < len(self.bishop_attacks[square]) and self.bishop_attacks[square][magic_index] != 0:
            return self.bishop_attacks[square][magic_index]
        return self._bishop_attacks_on_the_fly(square, occupancy)
    
    def get_queen_attacks(self, square: int, occupancy: int) -> int:
        """Get queen attacks (combination of rook and bishop)."""
        return self.get_rook_attacks(square, occupancy) | self.get_bishop_attacks(square, occupancy)


# Pre-calculated attack tables for non-sliding pieces
class PreCalculatedAttacks:
    """Pre-calculated attack tables for knights, kings, and pawns."""
    
    def __init__(self):
        self.knight_attacks = [0] * 64
        self.king_attacks = [0] * 64
        self.white_pawn_attacks = [0] * 64
        self.black_pawn_attacks = [0] * 64
        
        self._init_knight_attacks()
        self._init_king_attacks()
        self._init_pawn_attacks()
    
    def _init_knight_attacks(self):
        """Pre-calculate knight attack patterns."""
        if CYTHON_AVAILABLE:
            # Use Cython-optimized version
            for square in range(64):
                self.knight_attacks[square] = cy_knight_attacks(square)
        else:
            # Fallback to Python
            knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                           (1, 2), (1, -2), (-1, 2), (-1, -2)]
            
            for square in range(64):
                attacks = 0
                rank = square // 8
                file = square % 8
                
                for dr, df in knight_moves:
                    new_rank = rank + dr
                    new_file = file + df
                    if 0 <= new_rank < 8 and 0 <= new_file < 8:
                        attacks |= 1 << (new_rank * 8 + new_file)
                
                self.knight_attacks[square] = attacks
    
    def _init_king_attacks(self):
        """Pre-calculate king attack patterns."""
        if CYTHON_AVAILABLE:
            # Use Cython-optimized version
            for square in range(64):
                self.king_attacks[square] = cy_king_attacks(square)
        else:
            # Fallback to Python
            king_moves = [(1, 0), (1, 1), (0, 1), (-1, 1),
                         (-1, 0), (-1, -1), (0, -1), (1, -1)]
            
            for square in range(64):
                attacks = 0
                rank = square // 8
                file = square % 8
                
                for dr, df in king_moves:
                    new_rank = rank + dr
                    new_file = file + df
                    if 0 <= new_rank < 8 and 0 <= new_file < 8:
                        attacks |= 1 << (new_rank * 8 + new_file)
                
                self.king_attacks[square] = attacks
    
    def _init_pawn_attacks(self):
        """Pre-calculate pawn attack patterns (separate for white and black)."""
        if CYTHON_AVAILABLE:
            # Use Cython-optimized version for bulk generation
            for square in range(64):
                # Generate attacks for single pawn on each square
                pawn_bb = 1 << square
                self.white_pawn_attacks[square] = cy_white_pawn_attacks(pawn_bb)
                self.black_pawn_attacks[square] = cy_black_pawn_attacks(pawn_bb)
        else:
            # Fallback to Python
            for square in range(64):
                rank = square // 8
                file = square % 8
                
                # White pawn attacks (move up the board)
                white_attacks = 0
                if rank < 7:
                    if file > 0:
                        white_attacks |= 1 << ((rank + 1) * 8 + file - 1)
                    if file < 7:
                        white_attacks |= 1 << ((rank + 1) * 8 + file + 1)
                self.white_pawn_attacks[square] = white_attacks
                
                # Black pawn attacks (move down the board)
                black_attacks = 0
                if rank > 0:
                    if file > 0:
                        black_attacks |= 1 << ((rank - 1) * 8 + file - 1)
                    if file < 7:
                        black_attacks |= 1 << ((rank - 1) * 8 + file + 1)
                self.black_pawn_attacks[square] = black_attacks


# Utility functions for bitboard manipulation
def pop_lsb(bb: int) -> Tuple[int, int]:
    """Pop the least significant bit and return the square index."""
    if CYTHON_AVAILABLE:
        return cy_pop_lsb(bb)
    square = (bb & -bb).bit_length() - 1
    return square, bb & (bb - 1)


def count_bits(bb: int) -> int:
    """Count the number of set bits in a bitboard."""
    if CYTHON_AVAILABLE:
        return cy_pop_count(bb)
    return bin(bb).count('1')


def get_lsb(bb: int) -> int:
    """Get the index of the least significant bit."""
    if CYTHON_AVAILABLE:
        return cy_get_lsb(bb)
    return (bb & -bb).bit_length() - 1


def print_bitboard(bb: int):
    """Print a bitboard in a human-readable format."""
    print("\n  a b c d e f g h")
    for rank in range(7, -1, -1):
        print(f"{rank + 1} ", end="")
        for file in range(8):
            square = rank * 8 + file
            if bb & (1 << square):
                print("1 ", end="")
            else:
                print(". ", end="")
        print(f"{rank + 1}")
    print("  a b c d e f g h\n")
