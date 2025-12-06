"""
Polyglot Opening Book Support

Polyglot is a standard opening book format for chess engines:
- Binary format with 16-byte entries
- Each entry: 8 bytes (hash) + 2 bytes (move) + 2 bytes (weight) + 2 bytes (learn) + 2 bytes (padding)
- Entries sorted by Polyglot hash key for binary search
- Uses specific Polyglot Zobrist hashing scheme (different from engine's internal hashing)

Safety Features:
- Read-only access (never modifies book file)
- Validates file format before loading
- Validates moves are legal before returning
- Handles missing book files gracefully
- Thread-safe (no shared mutable state)
- Proper error handling and logging

Usage:
    book = OpeningBook("path/to/book.bin")
    if book.is_loaded():
        move = book.probe(board)  # Returns move tuple or None
"""

import struct
import os
import random
from typing import Optional, Tuple, List

# Polyglot uses specific Zobrist keys (must match Polyglot standard)
# These are different from our engine's internal Zobrist keys
# Source: PolyGlot specification by Fabien Letouzey

class PolyglotZobrist:
    """
    Polyglot-compatible Zobrist keys.
    
    CRITICAL: These keys must match the PolyGlot specification exactly.
    The Polyglot standard uses a specific 64-bit random number generator
    to ensure all engines produce the same hash keys.
    
    Reference: PolyGlot specification by Fabien Letouzey
    """
    
    @staticmethod
    def _polyglot_random():
        """
        Polyglot random number generator.
        
        This is a 64-bit linear congruential generator used by Polyglot.
        It must match the reference implementation exactly.
        """
        # Initialize with Polyglot seed
        seed = 1070372
        
        def next_rand():
            nonlocal seed
            seed = (seed * 1103515245 + 12345) & 0xFFFFFFFFFFFFFFFF
            return seed
        
        return next_rand
    
    @staticmethod
    def _init_keys():
        """Initialize Polyglot Zobrist keys with standard seed."""
        # Use the proven Polyglot random array (pure Python implementation)
        # This ensures 100% compatibility with Polyglot books
        from .polyglot_constants import POLYGLOT_RANDOM_ARRAY
        
        keys = {}
        
        # Piece keys: [square][piece]
        # The array is indexed as: piece * 64 + square
        # Piece encoding: 0=BP, 1=WP, 2=BN, 3=WN, 4=BB, 5=WB, 6=BR, 7=WR, 8=BQ, 9=WQ, 10=BK, 11=WK
        keys['pieces'] = []
        for square in range(64):
            keys['pieces'].append([])
            for piece in range(12):
                idx = piece * 64 + square
                keys['pieces'][square].append(POLYGLOT_RANDOM_ARRAY[idx])
        
        # Castling keys [4]: WK, WQ, BK, BQ (indices 768-771)
        keys['castling'] = [POLYGLOT_RANDOM_ARRAY[768 + i] for i in range(4)]
        
        # En passant keys [8]: files a-h (indices 772-779)
        keys['en_passant'] = [POLYGLOT_RANDOM_ARRAY[772 + i] for i in range(8)]
        
        # Side to move key (index 780)
        keys['side_to_move'] = POLYGLOT_RANDOM_ARRAY[780]
        
        return keys
    
    KEYS = _init_keys.__func__()  # Pre-compute keys
    
    @classmethod
    def compute_hash(cls, board) -> int:
        """
        Compute Polyglot hash for board position.
        
        Args:
            board: ChessBoard instance
            
        Returns:
            64-bit Polyglot hash key
        """
        hash_val = 0
        
        # Polyglot piece encoding (different from our engine)
        # Our engine: WHITE=0, BLACK=1, PAWN=0, KNIGHT=1, BISHOP=2, ROOK=3, QUEEN=4, KING=5
        # Polyglot: BP=0, WP=1, BN=2, WN=3, BB=4, WB=5, BR=6, WR=7, BQ=8, WQ=9, BK=10, WK=11
        
        polyglot_piece_map = {
            # (color, piece_type) -> polyglot_piece
            (1, 0): 0,  # Black pawn
            (0, 0): 1,  # White pawn
            (1, 1): 2,  # Black knight
            (0, 1): 3,  # White knight
            (1, 2): 4,  # Black bishop
            (0, 2): 5,  # White bishop
            (1, 3): 6,  # Black rook
            (0, 3): 7,  # White rook
            (1, 4): 8,  # Black queen
            (0, 4): 9,  # White queen
            (1, 5): 10, # Black king
            (0, 5): 11, # White king
        }
        
        # Hash pieces
        for color in range(2):
            for piece_type in range(6):
                bitboard = board.pieces[color][piece_type]
                while bitboard:
                    square = (bitboard & -bitboard).bit_length() - 1
                    bitboard &= bitboard - 1
                    
                    polyglot_piece = polyglot_piece_map[(color, piece_type)]
                    hash_val ^= cls.KEYS['pieces'][square][polyglot_piece]
        
        # Hash castling rights
        # Polyglot: WK=0, WQ=1, BK=2, BQ=3
        if board.castling_rights & 1:  # White kingside
            hash_val ^= cls.KEYS['castling'][0]
        if board.castling_rights & 2:  # White queenside
            hash_val ^= cls.KEYS['castling'][1]
        if board.castling_rights & 4:  # Black kingside
            hash_val ^= cls.KEYS['castling'][2]
        if board.castling_rights & 8:  # Black queenside
            hash_val ^= cls.KEYS['castling'][3]
        
        # Hash en passant (only if EP capture is legal)
        if board.en_passant_square is not None:
            # Check if there's actually a pawn that can capture EP
            ep_file = board.en_passant_square % 8
            ep_rank = board.en_passant_square // 8
            
            # Calculate the rank where capturing pawns would be
            # For white (moving up), pawns are one rank below the EP square
            # For black (moving down), pawns are one rank above the EP square
            has_ep_capturer = False
            if board.side_to_move == 0:  # White to move
                # White pawns would be on rank below EP target (ep_rank - 1)
                capture_rank = ep_rank - 1
                # Check for white pawns on adjacent files at the capture rank
                if ep_file > 0:
                    left_square = capture_rank * 8 + (ep_file - 1)
                    if board.pieces[0][0] & (1 << left_square):
                        has_ep_capturer = True
                if ep_file < 7:
                    right_square = capture_rank * 8 + (ep_file + 1)
                    if board.pieces[0][0] & (1 << right_square):
                        has_ep_capturer = True
            else:  # Black to move
                # Black pawns would be on rank above EP target (ep_rank + 1)
                capture_rank = ep_rank + 1
                # Check for black pawns on adjacent files at the capture rank
                if ep_file > 0:
                    left_square = capture_rank * 8 + (ep_file - 1)
                    if board.pieces[1][0] & (1 << left_square):
                        has_ep_capturer = True
                if ep_file < 7:
                    right_square = capture_rank * 8 + (ep_file + 1)
                    if board.pieces[1][0] & (1 << right_square):
                        has_ep_capturer = True
            
            if has_ep_capturer:
                hash_val ^= cls.KEYS['en_passant'][ep_file]
        
        # Hash side to move
        # NOTE: Polyglot XORs when WHITE to move, opposite of most implementations!
        # This matches python-chess behavior
        if board.side_to_move == 0:  # White to move
            hash_val ^= cls.KEYS['side_to_move']
        
        return hash_val


class OpeningBook:
    """
    Polyglot opening book reader.
    
    Thread-safe, read-only access to Polyglot opening books.
    """
    
    ENTRY_SIZE = 16  # Polyglot entry: 8(hash) + 2(move) + 2(weight) + 2(learn) + 2(padding)
    
    def __init__(self, book_path: str):
        """
        Initialize opening book.
        
        Args:
            book_path: Path to Polyglot .bin file
        """
        self.book_path = book_path
        self.entries: List[Tuple[int, int, int]] = []  # (hash, move, weight)
        self._loaded = False
        
        if os.path.exists(book_path):
            try:
                self._load_book()
            except Exception as e:
                print(f"Warning: Failed to load opening book {book_path}: {e}")
                self._loaded = False
        else:
            print(f"Info: Opening book not found at {book_path}")
    
    def _load_book(self):
        """Load and parse Polyglot book file."""
        with open(self.book_path, 'rb') as f:
            # Get file size
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            f.seek(0)  # Seek back to start
            
            # Validate file size
            if file_size % self.ENTRY_SIZE != 0:
                raise ValueError(f"Invalid book file size: {file_size} (not multiple of {self.ENTRY_SIZE})")
            
            num_entries = file_size // self.ENTRY_SIZE
            if num_entries == 0:
                raise ValueError("Empty opening book")
            
            print(f"Loading opening book: {num_entries} entries")
            
            # Read all entries
            for _ in range(num_entries):
                data = f.read(self.ENTRY_SIZE)
                if len(data) != self.ENTRY_SIZE:
                    raise ValueError("Incomplete entry in book file")
                
                # Unpack: big-endian format
                # Q = unsigned long long (8 bytes)
                # H = unsigned short (2 bytes)
                hash_key, move, weight, learn, _ = struct.unpack('>QHHHH', data)
                
                # Store entry
                self.entries.append((hash_key, move, weight))
            
            # Verify entries are sorted by hash (Polyglot requirement)
            for i in range(1, len(self.entries)):
                if self.entries[i][0] < self.entries[i-1][0]:
                    raise ValueError("Book entries not sorted by hash")
            
            self._loaded = True
            print(f"Opening book loaded successfully: {len(self.entries)} positions")
    
    def is_loaded(self) -> bool:
        """Check if book is loaded."""
        return self._loaded
    
    def probe(self, board, randomize: bool = True) -> Optional[Tuple[int, int, Optional[int]]]:
        """
        Probe opening book for a move.
        
        Args:
            board: ChessBoard instance
            randomize: If True, select randomly weighted by book weights
                      If False, select highest-weighted move
        
        Returns:
            Move tuple (from_sq, to_sq, promotion) or None if position not in book
        """
        if not self._loaded:
            return None
        
        # Compute Polyglot hash
        poly_hash = PolyglotZobrist.compute_hash(board)
        
        # Binary search for position
        candidates = []
        idx = self._binary_search(poly_hash)
        
        if idx < 0:
            return None  # Position not in book
        
        # Collect all moves for this position
        i = idx
        while i < len(self.entries) and self.entries[i][0] == poly_hash:
            hash_key, poly_move, weight = self.entries[i]
            candidates.append((poly_move, weight))
            i += 1
        
        if not candidates:
            return None
        
        # Decode and validate moves
        valid_moves = []
        legal_moves = set(board.generate_moves())  # Get legal moves for validation
        
        for poly_move, weight in candidates:
            move_tuple = self._decode_polyglot_move(poly_move)
            if move_tuple and move_tuple in legal_moves:
                valid_moves.append((move_tuple, weight))
        
        if not valid_moves:
            return None  # No valid moves found
        
        # Select move
        if randomize and len(valid_moves) > 1:
            # Weighted random selection
            total_weight = sum(w for _, w in valid_moves)
            if total_weight == 0:
                # All weights zero, uniform random
                return random.choice(valid_moves)[0]
            
            r = random.randint(0, total_weight - 1)
            cumulative = 0
            for move, weight in valid_moves:
                cumulative += weight
                if r < cumulative:
                    return move
            return valid_moves[-1][0]  # Fallback
        else:
            # Select highest-weighted move
            return max(valid_moves, key=lambda x: x[1])[0]
    
    def _binary_search(self, hash_key: int) -> int:
        """
        Binary search for hash key in book.
        
        Returns:
            Index of first entry with this hash, or -1 if not found
        """
        left, right = 0, len(self.entries) - 1
        result = -1
        
        while left <= right:
            mid = (left + right) // 2
            mid_hash = self.entries[mid][0]
            
            if mid_hash == hash_key:
                result = mid
                # Continue searching left for first occurrence
                right = mid - 1
            elif mid_hash < hash_key:
                left = mid + 1
            else:
                right = mid - 1
        
        return result
    
    def _decode_polyglot_move(self, poly_move: int) -> Optional[Tuple[int, int, Optional[int]]]:
        """
        Decode Polyglot move format to our move tuple.
        
        Polyglot move format (16 bits):
        - Bits 0-5: to square (0-63)
        - Bits 6-11: from square (0-63)
        - Bits 12-14: promotion piece (0=none, 1=knight, 2=bishop, 3=rook, 4=queen)
        - Bit 15: unused
        
        Args:
            poly_move: 16-bit Polyglot move
            
        Returns:
            (from_sq, to_sq, promotion) tuple, or None if invalid
        """
        to_sq = poly_move & 0x3F  # Bits 0-5
        from_sq = (poly_move >> 6) & 0x3F  # Bits 6-11
        promo = (poly_move >> 12) & 0x7  # Bits 12-14
        
        # Validate squares
        if from_sq > 63 or to_sq > 63:
            return None
        
        # Decode promotion
        # Polyglot: 1=N, 2=B, 3=R, 4=Q
        # Our engine: 1=N, 2=B, 3=R, 4=Q (same!)
        promotion = promo if promo > 0 else None
        
        return (from_sq, to_sq, promotion)


# Singleton instance for default book
_default_book: Optional[OpeningBook] = None

def get_default_book() -> Optional[OpeningBook]:
    """Get or create default opening book instance."""
    global _default_book
    if _default_book is None:
        # Try standard locations
        book_paths = [
            "openingbook/baron343/baron30.bin",
            "openingbook/baron343/book.bin",
            "openingbook/book.bin",
            "../openingbook/baron343/baron30.bin",
            "../openingbook/baron343/book.bin",
            "../openingbook/book.bin",
        ]
        
        for path in book_paths:
            if os.path.exists(path):
                _default_book = OpeningBook(path)
                if _default_book.is_loaded():
                    break
    
    return _default_book if _default_book and _default_book.is_loaded() else None


def probe_book(board, randomize: bool = True) -> Optional[Tuple[int, int, Optional[int]]]:
    """
    Convenience function to probe default opening book.
    
    Args:
        board: ChessBoard instance
        randomize: If True, select randomly weighted by book weights
        
    Returns:
        Move tuple or None
    """
    book = get_default_book()
    if book:
        return book.probe(board, randomize)
    return None
