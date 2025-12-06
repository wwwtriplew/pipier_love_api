"""
Clean Board State API - High-level interface hiding implementation details.

This module provides a simple, intuitive API for chess operations while
maintaining high performance through optimized low-level implementations.
"""

from typing import List, Tuple, Optional, Iterator

from .chess_engine import (
    ChessBoard,
    WHITE,
    BLACK,
    PAWN,
    KNIGHT,
    BISHOP,
    ROOK,
    QUEEN,
    KING,
)


class Position:
    """
    High-level chess position API with clean interface.
    Hides all bitboard and low-level implementation details.
    """
    
    def __init__(self, fen: Optional[str] = None):
        """
        Create a new position.
        
        Args:
            fen: FEN string (default: starting position)
        """
        self._board = ChessBoard()
        if fen:
            self._board.setup_from_fen(fen)
    
    @property
    def to_move(self) -> str:
        """Get side to move ('white' or 'black')."""
        return 'white' if self._board.side_to_move == WHITE else 'black'
    
    @property
    def in_check(self) -> bool:
        """Check if current side is in check."""
        return self._board.num_checkers > 0
    
    @property
    def is_checkmate(self) -> bool:
        """Check if current position is checkmate."""
        return self.in_check and len(self.legal_moves()) == 0
    
    @property
    def is_stalemate(self) -> bool:
        """Check if current position is stalemate."""
        return not self.in_check and len(self.legal_moves()) == 0
    
    @property
    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.is_checkmate or self.is_stalemate
    
    def legal_moves(self) -> List[str]:
        """
        Get all legal moves in algebraic notation.
        
        Returns:
            List of moves in format 'e2e4', 'e7e8q' (with promotion)
        """
        moves = []
        for from_sq, to_sq, promo in self._board.generate_moves():
            move_str = self._square_to_algebraic(from_sq) + self._square_to_algebraic(to_sq)
            if promo is not None:
                move_str += self._piece_to_char(promo).lower()
            moves.append(move_str)
        return moves
    
    def make_move(self, move: str) -> bool:
        """
        Make a move in algebraic notation.
        
        Args:
            move: Move string like 'e2e4' or 'e7e8q'
        
        Returns:
            True if move was legal and made, False otherwise
        """
        if len(move) < 4:
            return False
        
        from_sq = self._algebraic_to_square(move[0:2])
        to_sq = self._algebraic_to_square(move[2:4])
        promo = None
        
        if len(move) == 5:
            promo = self._char_to_piece(move[4].upper())
        
        # Check if move is legal
        legal = self._board.generate_moves()
        for f, t, p in legal:
            if f == from_sq and t == to_sq and p == promo:
                self._board.make_move(from_sq, to_sq, promo)
                return True
        
        return False
    
    def undo_move(self):
        """Undo the last move."""
        self._board.unmake_move()
    
    def get_fen(self) -> str:
        """Get FEN string of current position."""
        # TODO: ChessBoard doesn't have get_fen() method yet
        raise NotImplementedError("FEN export not implemented in ChessBoard")
    
    def perft(self, depth: int) -> int:
        """
        Performance test - count all positions at given depth.
        
        Args:
            depth: Search depth
        
        Returns:
            Number of leaf nodes
        """
        from .magic_bitboards import get_lsb
        
        def _perft(board, d):
            if d == 0:
                return 1
            
            nodes = 0
            for from_sq, to_sq, promo in board.generate_moves():
                board.make_move(from_sq, to_sq, promo)
                king_sq = get_lsb(board.pieces[1 - board.side_to_move][KING])
                if not board.is_square_attacked(king_sq, board.side_to_move):
                    nodes += _perft(board, d - 1)
                board.unmake_move()
            return nodes
        
        return _perft(self._board, depth)
    
    def __str__(self) -> str:
        """Return string representation of the board."""
        return self._board_to_string()
    
    # ========================================================================
    # Private helper methods
    # ========================================================================
    
    def _square_to_algebraic(self, square: int) -> str:
        """Convert square index to algebraic notation (e.g., 4 -> 'e1')."""
        file = square % 8
        rank = square // 8
        return chr(ord('a') + file) + str(rank + 1)
    
    def _algebraic_to_square(self, algebraic: str) -> int:
        """Convert algebraic notation to square index (e.g., 'e1' -> 4)."""
        file = ord(algebraic[0]) - ord('a')
        rank = int(algebraic[1]) - 1
        return rank * 8 + file
    
    def _piece_to_char(self, piece: int) -> str:
        """Convert piece constant to character."""
        return ['P', 'N', 'B', 'R', 'Q', 'K'][piece]
    
    def _char_to_piece(self, char: str) -> int:
        """Convert character to piece constant."""
        return {'P': PAWN, 'N': KNIGHT, 'B': BISHOP, 'R': ROOK, 'Q': QUEEN, 'K': KING}[char]
    
    def _board_to_string(self) -> str:
        """Generate a nice string representation of the board."""
        piece_chars = {
            (WHITE, PAWN): '♙', (WHITE, KNIGHT): '♘', (WHITE, BISHOP): '♗',
            (WHITE, ROOK): '♖', (WHITE, QUEEN): '♕', (WHITE, KING): '♔',
            (BLACK, PAWN): '♟', (BLACK, KNIGHT): '♞', (BLACK, BISHOP): '♝',
            (BLACK, ROOK): '♜', (BLACK, QUEEN): '♛', (BLACK, KING): '♚',
        }
        
        lines = ["\n  a b c d e f g h"]
        for rank in range(7, -1, -1):
            line = f"{rank + 1} "
            for file in range(8):
                square = rank * 8 + file
                piece_found = False
                
                for side in [WHITE, BLACK]:
                    for piece_type in range(6):
                        if (1 << square) & self._board.pieces[side][piece_type]:
                            line += piece_chars[(side, piece_type)] + " "
                            piece_found = True
                            break
                    if piece_found:
                        break
                
                if not piece_found:
                    line += ". "
            
            line += f"{rank + 1}"
            lines.append(line)
        
        lines.append("  a b c d e f g h")
        lines.append(f"\n{self.to_move.capitalize()} to move")
        
        if self.in_check:
            lines.append("Check!")
        if self.is_checkmate:
            lines.append("Checkmate!")
        if self.is_stalemate:
            lines.append("Stalemate!")
        
        return '\n'.join(lines)


# ============================================================================
# Convenience functions for quick access
# ============================================================================

def new_game() -> Position:
    """Create a new game in starting position."""
    return Position()


def from_fen(fen: str) -> Position:
    """Create position from FEN string."""
    return Position(fen)


def quick_perft(depth: int = 4) -> int:
    """Quick perft test from starting position."""
    pos = new_game()
    return pos.perft(depth)
