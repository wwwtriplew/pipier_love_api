"""
Fast Chess Engine with Bitboard Representation

A high-performance, platform-independent chess engine using:
- 64-bit bitboards for board representation (O(1) operations)
- Magic bitboards for sliding piece attacks (O(1) lookup)
- Pre-calculated attack tables for knights, kings, pawns
- Check-aware move generation (optimized for check scenarios)
- Proper move making/unmaking for accurate search algorithms

Platform Independence:
- Pure Python with optional Cython optimization
- No platform-specific dependencies
- Works on Windows, macOS, Linux (any Python 3.7+)

Chess engine implementation with bitboards and legal move generation.
"""

from typing import List, Tuple, Optional, Set

try:  # Support package imports
    from .magic_bitboards import (
        MagicBitboards,
        PreCalculatedAttacks,
        pop_lsb as _pop_lsb_orig,
        get_lsb as _get_lsb_orig,
        count_bits as _count_bits_orig,
    )
except ImportError:  # Fallback when run as a standalone module
    import os
    import sys

    _SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    if _SRC_DIR not in sys.path:
        sys.path.append(_SRC_DIR)

    from magic_bitboards import (  # type: ignore
        MagicBitboards,
        PreCalculatedAttacks,
        pop_lsb as _pop_lsb_orig,
        get_lsb as _get_lsb_orig,
        count_bits as _count_bits_orig,
    )

try:
    from .zobrist_keys import compute_pawn_hash
    from .zobrist_full import compute_full_hash
except ImportError:  # pragma: no cover - fallback for standalone execution
    from zobrist_keys import compute_pawn_hash  # type: ignore
    from zobrist_full import compute_full_hash  # type: ignore

# CRITICAL: Direct function names (no reassignment) for PyPy JIT optimization
# PyPy JIT cannot optimize through dynamic function references!
# We use the _orig versions directly to enable JIT inlining
pop_lsb = _pop_lsb_orig
get_lsb = _get_lsb_orig
count_bits = _count_bits_orig

# Piece constants (must be defined before importing move_generation to avoid circular import)
WHITE = 0
BLACK = 1
PAWN = 0
KNIGHT = 1
BISHOP = 2
ROOK = 3
QUEEN = 4
KING = 5

# Castling rights
WHITE_KINGSIDE = 1
WHITE_QUEENSIDE = 2
BLACK_KINGSIDE = 4
BLACK_QUEENSIDE = 8

# Square constants
A1, B1, C1, D1, E1, F1, G1, H1 = 0, 1, 2, 3, 4, 5, 6, 7
A8, B8, C8, D8, E8, F8, G8, H8 = 56, 57, 58, 59, 60, 61, 62, 63

# Import move_generation and move_execution after constants are defined (avoids circular import)
try:
    from . import move_generation as _move_generation
    from . import move_execution as _move_execution
except ImportError:  # pragma: no cover - standalone fallback
    import os
    import sys
    _SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    if _SRC_DIR not in sys.path:
        sys.path.insert(0, _SRC_DIR)
    import move_generation as _move_generation  # type: ignore
    import move_execution as _move_execution  # type: ignore


class ChessBoard:
    """
    Fast chess board representation using bitboards.
    
    Core Features:
    - Separate bitboards for each piece type and color (12 bitboards total)
    - Combined occupancy bitboards for efficient move generation
    - Move history for proper unmake (essential for search algorithms)
    - Pre-calculated attack tables (loaded once at initialization)
    - Check state caching for optimized move generation
    
    Essential Functions for Users:
    - generate_moves() -> Get all legal moves
    - make_move(from, to, promotion) -> Execute a move
    - unmake_move() -> Undo last move  
    - print_board() -> Display board
    - str_to_square('e4') -> Convert notation to index
    - square_to_str(28) -> Convert index to notation
    
    Internal State (Encapsulated):
    - pieces[color][type]: 12 bitboards for pieces
    - all_pieces, white_pieces, black_pieces: Combined occupancy
    - magic_bb, precalc_attacks: Pre-calculated tables (hidden from user)
    - in_check, checkers: Check detection cache
    """
    
    def __init__(self):
        # Bitboards: [color][piece_type]
        self.pieces = [[0] * 6 for _ in range(2)]
        
        # Separate pawn bitboards for speed
        self.white_pawns = 0
        self.black_pawns = 0
        
        # Combined bitboards
        self.white_pieces = 0
        self.black_pieces = 0
        self.all_pieces = 0
        
        # Game state
        self.side_to_move = WHITE
        self.castling_rights = 0
        self.en_passant_square = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        
        # Move history for unmake
        self.move_history = []
        
        # Pre-calculated attack tables
        self.magic_bb = MagicBitboards()
        self.precalc_attacks = PreCalculatedAttacks()
        
        # Check state cache
        self.in_check = False
        self.checkers = 0
        self.num_checkers = 0
        
        # Zobrist hashes
        self.pawn_hash = 0  # Pawn structure hash for evaluation cache
        self.zobrist_key = 0  # Full position hash for transposition table
        
        self.setup_starting_position()
    
    def setup_from_fen(self, fen: str):
        """
        Set up position from FEN (Forsyth-Edwards Notation) string.
        Example: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        """
        # Clear board
        for color in range(2):
            for piece in range(6):
                self.pieces[color][piece] = 0
        
        parts = fen.split()
        board_str = parts[0]
        
        # Parse piece positions
        square = 56  # Start at a8
        for char in board_str:
            if char == '/':
                square -= 16  # Move to next rank
            elif char.isdigit():
                square += int(char)  # Empty squares
            else:
                # Place piece
                piece_map = {
                    'P': (WHITE, PAWN), 'N': (WHITE, KNIGHT), 'B': (WHITE, BISHOP),
                    'R': (WHITE, ROOK), 'Q': (WHITE, QUEEN), 'K': (WHITE, KING),
                    'p': (BLACK, PAWN), 'n': (BLACK, KNIGHT), 'b': (BLACK, BISHOP),
                    'r': (BLACK, ROOK), 'q': (BLACK, QUEEN), 'k': (BLACK, KING)
                }
                color, piece = piece_map[char]
                self.pieces[color][piece] |= 1 << square
                square += 1
        
        # Parse side to move
        self.side_to_move = WHITE if parts[1] == 'w' else BLACK
        
        # Parse castling rights
        self.castling_rights = 0
        if 'K' in parts[2]: self.castling_rights |= WHITE_KINGSIDE
        if 'Q' in parts[2]: self.castling_rights |= WHITE_QUEENSIDE
        if 'k' in parts[2]: self.castling_rights |= BLACK_KINGSIDE
        if 'q' in parts[2]: self.castling_rights |= BLACK_QUEENSIDE
        
        # Parse en passant
        if parts[3] != '-':
            self.en_passant_square = self.str_to_square(parts[3])
        else:
            self.en_passant_square = None
        
        # Parse halfmove clock and fullmove number
        if len(parts) >= 5:
            self.halfmove_clock = int(parts[4])
        if len(parts) >= 6:
            self.fullmove_number = int(parts[5])
        
        # Update derived bitboards
        self.white_pawns = self.pieces[WHITE][PAWN]
        self.black_pawns = self.pieces[BLACK][PAWN]
        self._update_occupancy()
        self._update_check_status()
        
        # Compute Zobrist hashes - CRITICAL for search and TT
        self.pawn_hash = compute_pawn_hash(self.white_pawns, self.black_pawns)
        self.zobrist_key = compute_full_hash(self)
    
    def setup_starting_position(self):
        """Set up the standard chess starting position."""
        # White pieces
        self.pieces[WHITE][PAWN] = 0x000000000000FF00
        self.pieces[WHITE][KNIGHT] = 0x0000000000000042
        self.pieces[WHITE][BISHOP] = 0x0000000000000024
        self.pieces[WHITE][ROOK] = 0x0000000000000081
        self.pieces[WHITE][QUEEN] = 0x0000000000000008
        self.pieces[WHITE][KING] = 0x0000000000000010
        
        # Black pieces
        self.pieces[BLACK][PAWN] = 0x00FF000000000000
        self.pieces[BLACK][KNIGHT] = 0x4200000000000000
        self.pieces[BLACK][BISHOP] = 0x2400000000000000
        self.pieces[BLACK][ROOK] = 0x8100000000000000
        self.pieces[BLACK][QUEEN] = 0x0800000000000000
        self.pieces[BLACK][KING] = 0x1000000000000000
        
        self.white_pawns = self.pieces[WHITE][PAWN]
        self.black_pawns = self.pieces[BLACK][PAWN]
        self._update_occupancy()
        
        self.castling_rights = WHITE_KINGSIDE | WHITE_QUEENSIDE | BLACK_KINGSIDE | BLACK_QUEENSIDE
        self.en_passant_square = None
        self.side_to_move = WHITE
        self._update_check_status()
        
        # Compute Zobrist hashes - CRITICAL for search and TT
        self.pawn_hash = compute_pawn_hash(self.white_pawns, self.black_pawns)
        self.zobrist_key = compute_full_hash(self)
    
    def _update_occupancy(self):
        """Update combined occupancy bitboards."""
        self.white_pieces = 0
        self.black_pieces = 0
        for piece in range(6):
            self.white_pieces |= self.pieces[WHITE][piece]
            self.black_pieces |= self.pieces[BLACK][piece]
        self.all_pieces = self.white_pieces | self.black_pieces
    
    def _update_check_status(self):
        """Update check status and identify checkers."""
        king_bb = self.pieces[self.side_to_move][KING]
        if not king_bb:
            # No king - illegal position (shouldn't happen with legal moves)
            self.checkers = 0
            self.num_checkers = 0
            self.in_check = False
            return
        
        king_square = get_lsb(king_bb)
        self.checkers = self._get_attackers_to_square(king_square, 1 - self.side_to_move)
        self.num_checkers = count_bits(self.checkers)
        self.in_check = self.num_checkers > 0
    
    def _get_attackers_to_square(self, square: int, attacking_side: int) -> int:
        """Get all pieces of attacking_side that attack the given square."""
        attackers = 0
        
        # Pawn attacks
        if attacking_side == WHITE:
            attackers |= self.precalc_attacks.black_pawn_attacks[square] & self.pieces[WHITE][PAWN]
        else:
            attackers |= self.precalc_attacks.white_pawn_attacks[square] & self.pieces[BLACK][PAWN]
        
        # Knight attacks
        attackers |= self.precalc_attacks.knight_attacks[square] & self.pieces[attacking_side][KNIGHT]
        
        # King attacks
        attackers |= self.precalc_attacks.king_attacks[square] & self.pieces[attacking_side][KING]
        
        # Sliding pieces
        bishop_attacks = self.magic_bb.get_bishop_attacks(square, self.all_pieces)
        attackers |= bishop_attacks & (self.pieces[attacking_side][BISHOP] | self.pieces[attacking_side][QUEEN])
        
        rook_attacks = self.magic_bb.get_rook_attacks(square, self.all_pieces)
        attackers |= rook_attacks & (self.pieces[attacking_side][ROOK] | self.pieces[attacking_side][QUEEN])
        
        return attackers
    
    def is_square_attacked(self, square: int, attacking_side: int) -> bool:
        """
        ULTRA-OPTIMIZED attack checking in pure Python.
        Aggressive inlining and caching for maximum speed.
        """
        # Cache frequently accessed attributes in local variables (faster lookup)
        pieces = self.pieces[attacking_side]
        precalc = self.precalc_attacks
        
        # Pawns - most common attackers, check first for early exit
        if attacking_side == 0:  # WHITE
            if precalc.black_pawn_attacks[square] & pieces[0]:
                return True
        else:  # BLACK
            if precalc.white_pawn_attacks[square] & pieces[0]:
                return True
        
        # Knights - second most common
        if precalc.knight_attacks[square] & pieces[1]:
            return True
        
        # King
        if precalc.king_attacks[square] & pieces[5]:
            return True
        
        # Bishops and Queens (diagonal) - only compute if pieces exist
        diagonal_attackers = pieces[2] | pieces[4]
        if diagonal_attackers:
            if self.magic_bb.get_bishop_attacks(square, self.all_pieces) & diagonal_attackers:
                return True
        
        # Rooks and Queens (orthogonal) - only compute if pieces exist
        orthogonal_attackers = pieces[3] | pieces[4]
        if orthogonal_attackers:
            if self.magic_bb.get_rook_attacks(square, self.all_pieces) & orthogonal_attackers:
                return True
        
        return False
    
    def generate_moves(self) -> List[Tuple[int, int, Optional[int]]]:
        """
        Generate all legal moves for the current position.
        
        Optimized for check situations:
        - Double check: only king moves
        - Single check: king moves, captures of checker, or blocking moves
        - Not in check: all legal moves
        
        Returns: List of (from_square, to_square, promotion_piece)
        """
        if self.num_checkers >= 2:
            return self._generate_king_moves()
        elif self.num_checkers == 1:
            return self._generate_king_moves() + self._generate_check_evasions()
        else:
            return self._generate_all_moves()
    
    def square_to_str(self, square: int) -> str:
        """Convert square index to algebraic notation."""
        return chr(ord('a') + square % 8) + str(square // 8 + 1)
    
    def str_to_square(self, s: str) -> int:
        """Convert algebraic notation to square index."""
        return (ord(s[0]) - ord('a')) + (int(s[1]) - 1) * 8
    
    def print_board(self):
        """Print the current board state."""
        piece_chars = {
            (WHITE, PAWN): 'P', (WHITE, KNIGHT): 'N', (WHITE, BISHOP): 'B',
            (WHITE, ROOK): 'R', (WHITE, QUEEN): 'Q', (WHITE, KING): 'K',
            (BLACK, PAWN): 'p', (BLACK, KNIGHT): 'n', (BLACK, BISHOP): 'b',
            (BLACK, ROOK): 'r', (BLACK, QUEEN): 'q', (BLACK, KING): 'k'
        }
        
        print("\n  a b c d e f g h")
        for rank in range(7, -1, -1):
            print(f"{rank + 1} ", end="")
            for file in range(8):
                square = rank * 8 + file
                piece_found = False
                for color in [WHITE, BLACK]:
                    for piece in range(6):
                        if self.pieces[color][piece] & (1 << square):
                            print(piece_chars[(color, piece)] + " ", end="")
                            piece_found = True
                            break
                    if piece_found:
                        break
                if not piece_found:
                    print(". ", end="")
            print(f"{rank + 1}")
        print("  a b c d e f g h\n")
        print(f"Side to move: {'White' if self.side_to_move == WHITE else 'Black'}")
        print(f"In check: {self.in_check}")
    
    # Essential simplified functions for move generation
    def _generate_king_moves(self) -> List:
        """Generate king moves including castling."""
        return _move_generation.generate_king_moves(self)
    
    def _generate_check_evasions(self) -> List:
        """Generate moves that evade check."""
        return _move_generation.generate_check_evasions(self)
    
    def _generate_all_moves(self) -> List:
        """Generate all legal moves."""
        return _move_generation.generate_all_legal_moves(self)
    
    def make_move(self, from_square: int, to_square: int, promotion: Optional[int] = None) -> bool:
        """
        Make a move on the board and save complete state for unmake.
        
        OPTIMIZED VERSION: Uses tuple instead of dict for 10x+ speedup.
        PyPy JIT can optimize tuples much better than dicts with list comprehensions.
        
        Args:
            from_square: Source square (0-63)
            to_square: Destination square (0-63)
            promotion: Piece type to promote to (QUEEN, ROOK, BISHOP, KNIGHT)
        
        Returns:
            True if move was legal and executed, False otherwise
        """
        # Save state as tuple (much faster than dict for PyPy JIT)
        # Flat tuple avoids nested list comprehensions
        state = (
            # Piece bitboards (12 values)
            self.pieces[0][0], self.pieces[0][1], self.pieces[0][2],
            self.pieces[0][3], self.pieces[0][4], self.pieces[0][5],
            self.pieces[1][0], self.pieces[1][1], self.pieces[1][2],
            self.pieces[1][3], self.pieces[1][4], self.pieces[1][5],
            # Combined bitboards (5 values)
            self.white_pawns, self.black_pawns,
            self.white_pieces, self.black_pieces, self.all_pieces,
            # Game state (9 values)
            self.side_to_move, self.castling_rights, self.en_passant_square,
            self.halfmove_clock, self.fullmove_number,
            self.in_check, self.checkers, self.num_checkers,
            self.pawn_hash, self.zobrist_key,
        )
        
        # Execute the move
        result = _move_execution.execute_move(self, from_square, to_square, promotion)
        
        # Only save state if move was successful
        if result:
            self.move_history.append(state)
        
        return result
    
    def unmake_move(self) -> bool:
        """
        Unmake the last move and restore previous board state.
        
        OPTIMIZED VERSION: Restores from tuple (10x+ faster than dict access).
        
        Returns:
            True if unmake successful, False if no move history
        """
        if not self.move_history:
            return False
        
        # Restore from tuple (indices match make_move order)
        state = self.move_history.pop()
        
        # Piece bitboards (indices 0-11)
        self.pieces[0][0] = state[0]
        self.pieces[0][1] = state[1]
        self.pieces[0][2] = state[2]
        self.pieces[0][3] = state[3]
        self.pieces[0][4] = state[4]
        self.pieces[0][5] = state[5]
        self.pieces[1][0] = state[6]
        self.pieces[1][1] = state[7]
        self.pieces[1][2] = state[8]
        self.pieces[1][3] = state[9]
        self.pieces[1][4] = state[10]
        self.pieces[1][5] = state[11]
        
        # Combined bitboards (indices 12-16)
        self.white_pawns = state[12]
        self.black_pawns = state[13]
        self.white_pieces = state[14]
        self.black_pieces = state[15]
        self.all_pieces = state[16]
        
        # Game state (indices 17-25)
        self.side_to_move = state[17]
        self.castling_rights = state[18]
        self.en_passant_square = state[19]
        self.halfmove_clock = state[20]
        self.fullmove_number = state[21]
        self.in_check = state[22]
        self.checkers = state[23]
        self.num_checkers = state[24]
        self.pawn_hash = state[25]
        self.zobrist_key = state[26]
        
        return True
