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


def execute_move(board, from_square: int, to_square: int, promotion: Optional[int] = None) -> bool:
    """
    Execute a move on the board.
    Returns True if move was legal and made, False otherwise.
    """
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
    
    # Handle captures
    enemy = 1 - board.side_to_move
    for pt in range(6):
        if board.pieces[enemy][pt] & to_bb:
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
    
    # Handle castling
    if piece_type == KING:
        if abs(to_square - from_square) == 2:
            # Castling move
            if to_square > from_square:  # Kingside
                rook_from = from_square + 3
                rook_to = from_square + 1
            else:  # Queenside
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
        if board.side_to_move == WHITE:
            board.pieces[BLACK][PAWN] &= ~(1 << (to_square - 8))
        else:
            board.pieces[WHITE][PAWN] &= ~(1 << (to_square + 8))
    
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
    
    # Switch side to move
    board.side_to_move = 1 - board.side_to_move
    
    # Update check status
    board._update_check_status()
    
    return True
