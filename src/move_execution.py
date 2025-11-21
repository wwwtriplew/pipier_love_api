"""
Move execution module for making and unmaking moves.
"""

from typing import Optional

try:  # Package import
    from .chess_engine import (
        WHITE,
        BLACK,
        PAWN,
        KNIGHT,
        BISHOP,
        ROOK,
        QUEEN,
        KING,
        WHITE_KINGSIDE,
        WHITE_QUEENSIDE,
        BLACK_KINGSIDE,
        BLACK_QUEENSIDE,
    )
    from .zobrist_keys import compute_pawn_hash
    from .zobrist_full import (
        compute_full_hash,
        update_hash_piece_move,
        update_hash_capture,
        update_hash_promotion,
        update_hash_promotion_capture,
        update_hash_castling,
        update_hash_en_passant_capture,
        update_hash_side_to_move,
        update_hash_castling_rights,
        update_hash_en_passant_square,
        is_ep_capture_legal,
    )
except ImportError:  # Standalone fallback
    import os
    import sys

    _SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    if _SRC_DIR not in sys.path:
        sys.path.append(_SRC_DIR)

    from chess_engine import (  # type: ignore
        WHITE,
        BLACK,
        PAWN,
        KNIGHT,
        BISHOP,
        ROOK,
        QUEEN,
        KING,
        WHITE_KINGSIDE,
        WHITE_QUEENSIDE,
        BLACK_KINGSIDE,
        BLACK_QUEENSIDE,
    )
    from zobrist_keys import compute_pawn_hash  # type: ignore
    from zobrist_full import (  # type: ignore
        compute_full_hash,
        update_hash_piece_move,
        update_hash_capture,
        update_hash_promotion,
        update_hash_promotion_capture,
        update_hash_castling,
        update_hash_en_passant_capture,
        update_hash_side_to_move,
        update_hash_castling_rights,
        update_hash_en_passant_square,
        is_ep_capture_legal,
    )


def execute_move(board, from_square: int, to_square: int, promotion: Optional[int] = None) -> bool:
    """
    Execute a move on the board.
    Returns True if move was legal and made, False otherwise.
    """
    # Save state for incremental hash updates
    old_castling_rights = board.castling_rights
    old_ep_square = board.en_passant_square
    
    # Check if old EP square is actually in the hash (before board state changes)
    # This is needed because we only include EP in hash if it's actually legal
    old_ep_was_in_hash = (old_ep_square is not None and 
                          is_ep_capture_legal(board, old_ep_square))
    
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
        return False
    
    # Update piece bitboards
    to_bb = 1 << to_square
    board.pieces[board.side_to_move][piece_type] &= ~from_bb
    
    # Handle captures - track for hash update
    captured_piece = None
    enemy = 1 - board.side_to_move
    for pt in range(6):
        if board.pieces[enemy][pt] & to_bb:
            captured_piece = pt
            board.pieces[enemy][pt] &= ~to_bb
            board.halfmove_clock = 0
            
            # If a rook is captured, remove castling rights
            if pt == ROOK:
                if enemy == WHITE:
                    if to_square == 0:  # a1
                        board.castling_rights &= ~WHITE_QUEENSIDE
                    elif to_square == 7:  # h1
                        board.castling_rights &= ~WHITE_KINGSIDE
                else:  # BLACK
                    if to_square == 56:  # a8
                        board.castling_rights &= ~BLACK_QUEENSIDE
                    elif to_square == 63:  # h8
                        board.castling_rights &= ~BLACK_KINGSIDE
            break
    
    # Handle promotion
    if promotion is not None and piece_type == PAWN:
        board.pieces[board.side_to_move][promotion] |= to_bb
    else:
        board.pieces[board.side_to_move][piece_type] |= to_bb
    
    # Track special moves for hash updates
    is_castling = False
    is_kingside_castle = False
    is_ep_capture = False
    captured_pawn_square = None
    
    # Handle castling
    if piece_type == KING:
        if abs(to_square - from_square) == 2:
            # Castling move
            is_castling = True
            if to_square > from_square:  # Kingside
                is_kingside_castle = True
                rook_from = from_square + 3
                rook_to = from_square + 1
            else:  # Queenside
                is_kingside_castle = False
                rook_from = from_square - 4
                rook_to = from_square - 1
            
            board.pieces[board.side_to_move][ROOK] &= ~(1 << rook_from)
            board.pieces[board.side_to_move][ROOK] |= 1 << rook_to
        
        # Update castling rights
        if board.side_to_move == WHITE:
            board.castling_rights &= ~(WHITE_KINGSIDE | WHITE_QUEENSIDE)
        else:
            board.castling_rights &= ~(BLACK_KINGSIDE | BLACK_QUEENSIDE)
    
    # Handle en passant
    if piece_type == PAWN and to_square == board.en_passant_square:
        is_ep_capture = True
        if board.side_to_move == WHITE:
            captured_pawn_square = to_square - 8
            board.pieces[BLACK][PAWN] &= ~(1 << captured_pawn_square)
        else:
            captured_pawn_square = to_square + 8
            board.pieces[WHITE][PAWN] &= ~(1 << captured_pawn_square)
    
    # Update en passant square
    prev_ep = board.en_passant_square
    board.en_passant_square = None
    if piece_type == PAWN and abs(to_square - from_square) == 16:
        if board.side_to_move == WHITE:
            board.en_passant_square = from_square + 8
        else:
            board.en_passant_square = from_square - 8
    
    # Update castling rights for rook moves
    if piece_type == ROOK:
        if board.side_to_move == WHITE:
            if from_square == 0:  # a1
                board.castling_rights &= ~WHITE_QUEENSIDE
            elif from_square == 7:  # h1
                board.castling_rights &= ~WHITE_KINGSIDE
        else:
            if from_square == 56:  # a8
                board.castling_rights &= ~BLACK_QUEENSIDE
            elif from_square == 63:  # h8
                board.castling_rights &= ~BLACK_KINGSIDE
    
    # Update pawn bitboards
    board.white_pawns = board.pieces[WHITE][PAWN]
    board.black_pawns = board.pieces[BLACK][PAWN]
    
    # Incremental occupancy update (optimized)
    board.white_pieces = 0
    for pt in range(6):
        board.white_pieces |= board.pieces[WHITE][pt]
    
    board.black_pieces = 0
    for pt in range(6):
        board.black_pieces |= board.pieces[BLACK][pt]
    
    board.all_pieces = board.white_pieces | board.black_pieces
    
    # Update halfmove clock
    if piece_type == PAWN:
        board.halfmove_clock = 0
    else:
        board.halfmove_clock += 1
    
    # Update fullmove number
    if board.side_to_move == BLACK:
        board.fullmove_number += 1
    
    # ============================================================================
    # INCREMENTAL ZOBRIST HASH UPDATE (10-30% speedup vs full recomputation)
    # CRITICAL: Must be done BEFORE side_to_move changes!
    # ============================================================================
    
    # Start with current hash
    new_hash = board.zobrist_key
    
    # Update hash based on move type (using moving_color from BEFORE the move)
    if is_castling:
        # Special case: castling moves both king and rook
        new_hash = update_hash_castling(new_hash, moving_color, is_kingside_castle)
    elif is_ep_capture:
        # Special case: en passant capture
        new_hash = update_hash_en_passant_capture(
            new_hash, moving_color, from_square, to_square, captured_pawn_square
        )
    elif promotion is not None:
        # Pawn promotion (with or without capture)
        if captured_piece is not None:
            new_hash = update_hash_promotion_capture(
                new_hash, moving_color, enemy_color, captured_piece,
                from_square, to_square, promotion
            )
        else:
            new_hash = update_hash_promotion(
                new_hash, moving_color, from_square, to_square, promotion
            )
    elif captured_piece is not None:
        # Regular capture
        new_hash = update_hash_capture(
            new_hash, moving_color, piece_type, enemy_color, captured_piece,
            from_square, to_square
        )
    else:
        # Regular move (no capture, no special)
        new_hash = update_hash_piece_move(
            new_hash, moving_color, piece_type, from_square, to_square
        )
    
    # Update castling rights in hash
    new_hash = update_hash_castling_rights(new_hash, old_castling_rights, board.castling_rights)
    
    # Update en passant square in hash (only if EP capture is legal)
    new_hash = update_hash_en_passant_square(
        new_hash, board, old_ep_square, board.en_passant_square, old_ep_was_in_hash
    )
    
    # Toggle side to move in hash (ALWAYS done after every move)
    new_hash = update_hash_side_to_move(new_hash)
    
    # Store updated hash
    board.zobrist_key = new_hash
    
    # Update pawn hash (recompute only if pawn structure changed)
    # Pawn hash is much cheaper than full hash (only 8-16 pawns vs 32 pieces)
    if piece_type == PAWN or captured_piece == PAWN or is_ep_capture or promotion is not None:
        # Pawn structure changed - recompute pawn hash
        board.pawn_hash = compute_pawn_hash(board.white_pawns, board.black_pawns)
    # If no pawns moved, pawn_hash unchanged (speedup!)
    
    # NOW switch side to move (AFTER hash is computed with old side)
    board.side_to_move = 1 - board.side_to_move
    
    # Update check status (needs correct side_to_move)
    board._update_check_status()
    
    return True
