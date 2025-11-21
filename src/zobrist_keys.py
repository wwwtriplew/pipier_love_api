"""
Zobrist Hashing for Pawn structure evaluation

Zobrist hashing is a technique to create unique hash keys for chess positions.
For pawn structure evaluation, we only need to hash pawn positions.

This module provides pre-generated random 64-bit numbers for:
- White pawns on each square (64 values)
- Black pawns on each square (64 values)
"""

import random

# Seed for reproducibility (change this to generate different keys)
ZOBRIST_SEED = 0x5f3759df  # Famous fast inverse square root magic number

def generate_zobrist_keys():
    """Generate Zobrist keys for pawn hashing."""
    random.seed(ZOBRIST_SEED)
    
    # Generate 64-bit random numbers for each pawn position
    # [color][square] where color 0=white, 1=black
    pawn_keys = []
    for color in range(2):
        keys = []
        for square in range(64):
            # Generate random 64-bit number
            keys.append(random.getrandbits(64))
        pawn_keys.append(keys)
    
    return pawn_keys

# Pre-generated Zobrist keys for pawn positions
# Access as: PAWN_ZOBRIST[color][square]
# where color is 0 (WHITE) or 1 (BLACK), square is 0-63
PAWN_ZOBRIST = generate_zobrist_keys()


def compute_pawn_hash(white_pawns_bb, black_pawns_bb):
    """
    Compute pawn hash from pawn bitboards.
    
    Args:
        white_pawns_bb: Bitboard of white pawns
        black_pawns_bb: Bitboard of black pawns
    
    Returns:
        64-bit hash representing pawn structure
    """
    hash_value = 0
    
    # XOR in white pawns
    bb = white_pawns_bb
    while bb:
        square = (bb & -bb).bit_length() - 1  # Get LSB
        hash_value ^= PAWN_ZOBRIST[0][square]
        bb &= bb - 1  # Clear LSB
    
    # XOR in black pawns
    bb = black_pawns_bb
    while bb:
        square = (bb & -bb).bit_length() - 1  # Get LSB
        hash_value ^= PAWN_ZOBRIST[1][square]
        bb &= bb - 1  # Clear LSB
    
    return hash_value


def update_pawn_hash_add(current_hash, color, square):
    """
    Update pawn hash when adding a pawn.
    
    Args:
        current_hash: Current pawn hash
        color: 0 for white, 1 for black
        square: Square index (0-63)
    
    Returns:
        Updated hash
    """
    return current_hash ^ PAWN_ZOBRIST[color][square]


def update_pawn_hash_remove(current_hash, color, square):
    """
    Update pawn hash when removing a pawn.
    
    Args:
        current_hash: Current pawn hash
        color: 0 for white, 1 for black
        square: Square index (0-63)
    
    Returns:
        Updated hash
    """
    # XOR is its own inverse, so removing is same as adding
    return current_hash ^ PAWN_ZOBRIST[color][square]


def update_pawn_hash_move(current_hash, color, from_square, to_square):
    """
    Update pawn hash when moving a pawn.
    
    Args:
        current_hash: Current pawn hash
        color: 0 for white, 1 for black
        from_square: Source square (0-63)
        to_square: Destination square (0-63)
    
    Returns:
        Updated hash
    """
    # Remove from old square, add to new square
    hash_value = current_hash ^ PAWN_ZOBRIST[color][from_square]
    hash_value ^= PAWN_ZOBRIST[color][to_square]
    return hash_value
