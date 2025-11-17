"""
Piper Love Chess Engine

A professional-grade chess engine with clean API and optimized performance.

Quick Start:
    >>> from board_state import new_game
    >>> pos = new_game()
    >>> pos.make_move('e2e4')
    >>> print(pos)

Performance:
    - 77,000+ NPS with CPython
    - 155,000-235,000 NPS with PyPy (2-3x faster)
    - 100% perft correctness
"""

# High-level API (recommended for most users)
from .board_state import Position, new_game, from_fen, quick_perft

# Low-level core (for advanced users)
from .chess_engine import ChessBoard, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
from .magic_bitboards import MagicBitboards, PreCalculatedAttacks
from .move_execution import execute_move
from .move_generation import (
    generate_king_moves, generate_pawn_moves, generate_knight_moves,
    generate_bishop_moves, generate_rook_moves, generate_queen_moves,
    generate_all_legal_moves
)

# Fast operations (for optimization)
from .fast_ops import (
    pop_lsb_fast, get_lsb_fast, count_bits_fast,
    FastBitboard
)

__version__ = '1.0.0'

__all__ = [
    # High-level API (START HERE!)
    'Position', 'new_game', 'from_fen', 'quick_perft',
    
    # Low-level core
    'ChessBoard', 'WHITE', 'BLACK', 'PAWN', 'KNIGHT', 'BISHOP', 'ROOK', 'QUEEN', 'KING',
    'MagicBitboards', 'PreCalculatedAttacks',
    
    # Move operations
    'execute_move',
    'generate_king_moves', 'generate_pawn_moves', 'generate_knight_moves',
    'generate_bishop_moves', 'generate_rook_moves', 'generate_queen_moves',
    'generate_all_legal_moves',
    
    # Fast operations
    'pop_lsb_fast', 'get_lsb_fast', 'count_bits_fast', 'FastBitboard',
]
