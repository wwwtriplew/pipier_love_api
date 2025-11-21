"""
Full-Board Zobrist Hashing for Chess Positions

Zobrist hashing creates unique 64-bit hash keys for complete chess positions.
This is used for:
- Transposition table lookups (position caching)
- Repetition detection (threefold repetition rule)
- Hash move ordering (PV moves from previous iterations)

Hash Components:
- Piece-square keys: [color][piece_type][square] (12 * 64 = 768 keys)
- Side-to-move key: 1 key (XOR when black to move)
- Castling rights keys: 4 keys (white kingside, white queenside, black kingside, black queenside)
- En passant file keys: 8 keys (only XOR when EP capture is actually legal)

Critical Invariant:
- En passant key is ONLY included when an en passant capture is actually legal
  (i.e., opponent has a pawn that can capture en passant)
  This prevents TT fragmentation from phantom EP rights

Incremental Updates:
- XOR out old piece-square, XOR in new piece-square on moves
- XOR side-to-move key after every move
- XOR castling rights when they change
- XOR EP file when EP square appears/disappears (and EP capture is legal)
"""

import random

# Seed for reproducibility (different from pawn hash)
ZOBRIST_FULL_SEED = 0x1A2B3C4D  # Different seed for full-board hashing

def generate_full_zobrist_keys():
    """
    Generate all Zobrist keys for full-board hashing.
    
    Returns:
        Dictionary with keys:
        - 'pieces': [color][piece_type][square] 
        - 'side_to_move': single key for black to move
        - 'castling': [4] keys for castling rights (WK, WQ, BK, BQ)
        - 'en_passant': [8] keys for en passant files (a-h)
    """
    random.seed(ZOBRIST_FULL_SEED)
    
    keys = {}
    
    # Piece-square keys: [color][piece_type][square]
    # color: 0=white, 1=black
    # piece_type: 0=pawn, 1=knight, 2=bishop, 3=rook, 4=queen, 5=king
    # square: 0-63
    keys['pieces'] = []
    for color in range(2):
        color_keys = []
        for piece_type in range(6):
            piece_keys = [random.getrandbits(64) for _ in range(64)]
            color_keys.append(piece_keys)
        keys['pieces'].append(color_keys)
    
    # Side-to-move key (XOR when black to move)
    keys['side_to_move'] = random.getrandbits(64)
    
    # Castling rights keys [white_kingside, white_queenside, black_kingside, black_queenside]
    keys['castling'] = [random.getrandbits(64) for _ in range(4)]
    
    # En passant file keys (a-h = files 0-7)
    # Only XOR when EP capture is actually legal
    keys['en_passant'] = [random.getrandbits(64) for _ in range(8)]
    
    return keys

# Pre-generated Zobrist keys
ZOBRIST_KEYS = generate_full_zobrist_keys()

# Convenience accessors
PIECE_KEYS = ZOBRIST_KEYS['pieces']
SIDE_KEY = ZOBRIST_KEYS['side_to_move']
CASTLING_KEYS = ZOBRIST_KEYS['castling']
EP_KEYS = ZOBRIST_KEYS['en_passant']

# Castling rights indices
WHITE_KINGSIDE_IDX = 0
WHITE_QUEENSIDE_IDX = 1
BLACK_KINGSIDE_IDX = 2
BLACK_QUEENSIDE_IDX = 3


def compute_full_hash(board):
    """
    Compute full Zobrist hash from board position.
    
    Args:
        board: ChessBoard instance with pieces, side_to_move, castling_rights, en_passant_square
    
    Returns:
        64-bit Zobrist hash representing complete position
    """
    hash_value = 0
    
    # Hash all pieces
    for color in range(2):
        for piece_type in range(6):
            bb = board.pieces[color][piece_type]
            while bb:
                square = (bb & -bb).bit_length() - 1  # Get LSB
                hash_value ^= PIECE_KEYS[color][piece_type][square]
                bb &= bb - 1  # Clear LSB
    
    # Hash side to move (XOR if black to move)
    if board.side_to_move == 1:  # BLACK
        hash_value ^= SIDE_KEY
    
    # Hash castling rights
    # Castling rights format: bits 0-3 for WK, WQ, BK, BQ
    if board.castling_rights & 1:  # WHITE_KINGSIDE
        hash_value ^= CASTLING_KEYS[WHITE_KINGSIDE_IDX]
    if board.castling_rights & 2:  # WHITE_QUEENSIDE
        hash_value ^= CASTLING_KEYS[WHITE_QUEENSIDE_IDX]
    if board.castling_rights & 4:  # BLACK_KINGSIDE
        hash_value ^= CASTLING_KEYS[BLACK_KINGSIDE_IDX]
    if board.castling_rights & 8:  # BLACK_QUEENSIDE
        hash_value ^= CASTLING_KEYS[BLACK_QUEENSIDE_IDX]
    
    # Hash en passant file (ONLY if EP capture is actually legal)
    if board.en_passant_square is not None:
        # Check if opponent has a pawn that can capture en passant
        if is_ep_capture_legal(board, board.en_passant_square):
            ep_file = board.en_passant_square % 8
            hash_value ^= EP_KEYS[ep_file]
    
    return hash_value


def is_ep_capture_legal(board, ep_square, side_to_check=None):
    """
    Check if an en passant capture is actually legal.
    
    This prevents TT key fragmentation from phantom EP rights.
    Only include EP in hash if opponent can actually capture en passant.
    
    Args:
        board: ChessBoard instance
        ep_square: En passant square (0-63)
        side_to_check: Optional override for which side can capture (0=white, 1=black)
                      If None, uses board.side_to_move
    
    Returns:
        True if specified side has a pawn that can legally capture en passant
    """
    if ep_square is None:
        return False
    
    # Side to move is the one who can capture (opponent of the pawn that just moved)
    capturing_color = board.side_to_move if side_to_check is None else side_to_check
    ep_file = ep_square % 8
    ep_rank = ep_square // 8
    
    # For white capturing (ep_rank = 5), check files ep_file-1 and ep_file+1 on rank 4
    # For black capturing (ep_rank = 2), check files ep_file-1 and ep_file+1 on rank 3
    if capturing_color == 0:  # WHITE capturing
        pawn_rank = 4
        if ep_rank != 5:
            return False
    else:  # BLACK capturing
        pawn_rank = 3
        if ep_rank != 2:
            return False
    
    # Check if capturing side has pawns on adjacent files
    pawn_bb = board.pieces[capturing_color][0]  # PAWN = 0
    
    # Check left file
    if ep_file > 0:
        left_square = pawn_rank * 8 + (ep_file - 1)
        if pawn_bb & (1 << left_square):
            return True
    
    # Check right file
    if ep_file < 7:
        right_square = pawn_rank * 8 + (ep_file + 1)
        if pawn_bb & (1 << right_square):
            return True
    
    return False


def update_hash_piece_move(current_hash, color, piece_type, from_square, to_square):
    """
    Update hash when moving a piece (non-capture).
    
    Args:
        current_hash: Current Zobrist hash
        color: 0=white, 1=black
        piece_type: 0=pawn, 1=knight, 2=bishop, 3=rook, 4=queen, 5=king
        from_square: Source square (0-63)
        to_square: Destination square (0-63)
    
    Returns:
        Updated hash
    """
    # XOR out piece from source square
    hash_value = current_hash ^ PIECE_KEYS[color][piece_type][from_square]
    # XOR in piece at destination square
    hash_value ^= PIECE_KEYS[color][piece_type][to_square]
    return hash_value


def update_hash_capture(current_hash, moving_color, moving_piece, victim_color, victim_piece,
                       from_square, to_square):
    """
    Update hash when capturing a piece.
    
    Args:
        current_hash: Current Zobrist hash
        moving_color: Color of capturing piece (0=white, 1=black)
        moving_piece: Type of capturing piece (0-5)
        victim_color: Color of captured piece (0=white, 1=black)
        victim_piece: Type of captured piece (0-5)
        from_square: Source square of capturing piece (0-63)
        to_square: Destination square (where capture happens) (0-63)
    
    Returns:
        Updated hash
    """
    # XOR out victim piece from destination
    hash_value = current_hash ^ PIECE_KEYS[victim_color][victim_piece][to_square]
    # XOR out capturing piece from source
    hash_value ^= PIECE_KEYS[moving_color][moving_piece][from_square]
    # XOR in capturing piece at destination
    hash_value ^= PIECE_KEYS[moving_color][moving_piece][to_square]
    return hash_value


def update_hash_promotion(current_hash, color, from_square, to_square, promoted_piece):
    """
    Update hash for pawn promotion.
    
    Args:
        current_hash: Current Zobrist hash
        color: Color of promoting pawn (0=white, 1=black)
        from_square: Source square of pawn (0-63)
        to_square: Destination square (0-63)
        promoted_piece: Piece type promoted to (1=knight, 2=bishop, 3=rook, 4=queen)
    
    Returns:
        Updated hash
    """
    # XOR out pawn from source
    hash_value = current_hash ^ PIECE_KEYS[color][0][from_square]  # PAWN = 0
    # XOR in promoted piece at destination
    hash_value ^= PIECE_KEYS[color][promoted_piece][to_square]
    return hash_value


def update_hash_promotion_capture(current_hash, moving_color, victim_color, victim_piece,
                                  from_square, to_square, promoted_piece):
    """
    Update hash for pawn promotion with capture.
    
    Args:
        current_hash: Current Zobrist hash
        moving_color: Color of promoting pawn (0=white, 1=black)
        victim_color: Color of captured piece (0=white, 1=black)
        victim_piece: Type of captured piece (0-5)
        from_square: Source square of pawn (0-63)
        to_square: Destination square (0-63)
        promoted_piece: Piece type promoted to (1-4)
    
    Returns:
        Updated hash
    """
    # XOR out victim piece
    hash_value = current_hash ^ PIECE_KEYS[victim_color][victim_piece][to_square]
    # XOR out pawn from source
    hash_value ^= PIECE_KEYS[moving_color][0][from_square]  # PAWN = 0
    # XOR in promoted piece at destination
    hash_value ^= PIECE_KEYS[moving_color][promoted_piece][to_square]
    return hash_value


def update_hash_castling(current_hash, color, is_kingside):
    """
    Update hash for castling move.
    
    Castling moves both king and rook.
    
    Args:
        current_hash: Current Zobrist hash
        color: 0=white, 1=black
        is_kingside: True for O-O, False for O-O-O
    
    Returns:
        Updated hash
    """
    KING = 5
    ROOK = 3
    
    if color == 0:  # WHITE
        if is_kingside:
            # King e1->g1 (4->6), Rook h1->f1 (7->5)
            hash_value = current_hash ^ PIECE_KEYS[0][KING][4]
            hash_value ^= PIECE_KEYS[0][KING][6]
            hash_value ^= PIECE_KEYS[0][ROOK][7]
            hash_value ^= PIECE_KEYS[0][ROOK][5]
        else:
            # King e1->c1 (4->2), Rook a1->d1 (0->3)
            hash_value = current_hash ^ PIECE_KEYS[0][KING][4]
            hash_value ^= PIECE_KEYS[0][KING][2]
            hash_value ^= PIECE_KEYS[0][ROOK][0]
            hash_value ^= PIECE_KEYS[0][ROOK][3]
    else:  # BLACK
        if is_kingside:
            # King e8->g8 (60->62), Rook h8->f8 (63->61)
            hash_value = current_hash ^ PIECE_KEYS[1][KING][60]
            hash_value ^= PIECE_KEYS[1][KING][62]
            hash_value ^= PIECE_KEYS[1][ROOK][63]
            hash_value ^= PIECE_KEYS[1][ROOK][61]
        else:
            # King e8->c8 (60->58), Rook a8->d8 (56->59)
            hash_value = current_hash ^ PIECE_KEYS[1][KING][60]
            hash_value ^= PIECE_KEYS[1][KING][58]
            hash_value ^= PIECE_KEYS[1][ROOK][56]
            hash_value ^= PIECE_KEYS[1][ROOK][59]
    
    return hash_value


def update_hash_en_passant_capture(current_hash, capturing_color, from_square, to_square, captured_pawn_square):
    """
    Update hash for en passant capture.
    
    Args:
        current_hash: Current Zobrist hash
        capturing_color: Color of capturing pawn (0=white, 1=black)
        from_square: Source square of capturing pawn (0-63)
        to_square: Destination square (ep square) (0-63)
        captured_pawn_square: Square where captured pawn is removed (0-63)
    
    Returns:
        Updated hash
    """
    PAWN = 0
    victim_color = 1 - capturing_color
    
    # XOR out capturing pawn from source
    hash_value = current_hash ^ PIECE_KEYS[capturing_color][PAWN][from_square]
    # XOR in capturing pawn at destination
    hash_value ^= PIECE_KEYS[capturing_color][PAWN][to_square]
    # XOR out captured pawn
    hash_value ^= PIECE_KEYS[victim_color][PAWN][captured_pawn_square]
    
    return hash_value


def update_hash_side_to_move(current_hash):
    """
    Toggle side to move in hash (call after every move).
    
    Args:
        current_hash: Current Zobrist hash
    
    Returns:
        Updated hash with toggled side to move
    """
    return current_hash ^ SIDE_KEY


def update_hash_castling_rights(current_hash, old_rights, new_rights):
    """
    Update hash when castling rights change.
    
    Args:
        current_hash: Current Zobrist hash
        old_rights: Previous castling rights bitfield (0-15)
        new_rights: New castling rights bitfield (0-15)
    
    Returns:
        Updated hash
    """
    hash_value = current_hash
    
    # XOR out old rights, XOR in new rights
    # Only XOR if the bit changed
    
    # White kingside (bit 0)
    if (old_rights & 1) != (new_rights & 1):
        hash_value ^= CASTLING_KEYS[WHITE_KINGSIDE_IDX]
    
    # White queenside (bit 1)
    if (old_rights & 2) != (new_rights & 2):
        hash_value ^= CASTLING_KEYS[WHITE_QUEENSIDE_IDX]
    
    # Black kingside (bit 2)
    if (old_rights & 4) != (new_rights & 4):
        hash_value ^= CASTLING_KEYS[BLACK_KINGSIDE_IDX]
    
    # Black queenside (bit 3)
    if (old_rights & 8) != (new_rights & 8):
        hash_value ^= CASTLING_KEYS[BLACK_QUEENSIDE_IDX]
    
    return hash_value


def update_hash_en_passant_square(current_hash, board, old_ep_square, new_ep_square, old_ep_was_in_hash=True):
    """
    Update hash when en passant square changes.
    
    CRITICAL: Check EP legality to prevent TT fragmentation from phantom EP rights.
    
    TIMING NOTE: Called AFTER board state is modified but BEFORE side_to_move is toggled.
    This means:
    - Board pieces are in their NEW positions
    - side_to_move is still the OLD side (the one that just moved)
    
    For old_ep_square:
    - Board state has changed, so we can't check legality anymore
    - Use old_ep_was_in_hash flag to know if it was included in hash
    - Only XOR out if it was actually in the hash
    
    For new_ep_square:
    - Board is in final state with side_to_move NOT yet toggled
    - Check if OPPOSITE side (1 - side_to_move) can capture
    
    Args:
        current_hash: Current Zobrist hash
        board: ChessBoard instance (for checking if EP is legal)
        old_ep_square: Previous EP square (None or 0-63)
        new_ep_square: New EP square (None or 0-63)
        old_ep_was_in_hash: Whether old EP square was included in hash (default True for setup_from_fen)
    
    Returns:
        Updated hash
    """
    hash_value = current_hash
    
    # XOR out old EP file only if it was in the hash
    if old_ep_square is not None and old_ep_was_in_hash:
        old_file = old_ep_square % 8
        hash_value ^= EP_KEYS[old_file]
    
    # XOR in new EP file if it's legal
    # Use OPPOSITE side (1 - side_to_move) because they will be able to capture next move
    if new_ep_square is not None and is_ep_capture_legal(board, new_ep_square, 1 - board.side_to_move):
        new_file = new_ep_square % 8
        hash_value ^= EP_KEYS[new_file]
    
    return hash_value
