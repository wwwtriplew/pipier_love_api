#!/usr/bin/env python3
"""Debug Polyglot hash computation step by step."""

import sys
import os
import chess
import chess.polyglot

sys.path.insert(0, os.path.dirname(__file__))

from src.chess_engine import ChessBoard
from src.opening_book import PolyglotZobrist

def debug_hash_computation(fen: str):
    """Compare hash computation step by step."""
    print(f"\nFEN: {fen}")
    print("=" * 60)
    
    # Reference board
    chess_board = chess.Board(fen)
    reference_hash = chess.polyglot.zobrist_hash(chess_board)
    print(f"Reference hash: {reference_hash:016x}")
    
    # Our board
    our_board = ChessBoard()
    our_board.setup_from_fen(fen)
    
    # Compute hash step by step
    print("\nStep-by-step computation:")
    hash_val = 0
    
    # Our piece map
    polyglot_piece_map = {
        (1, 0): 0,  (0, 0): 1,  # Pawns
        (1, 1): 2,  (0, 1): 3,  # Knights
        (1, 2): 4,  (0, 2): 5,  # Bishops
        (1, 3): 6,  (0, 3): 7,  # Rooks
        (1, 4): 8,  (0, 4): 9,  # Queens
        (1, 5): 10, (0, 5): 11, # Kings
    }
    
    piece_names = ["Pawn", "Knight", "Bishop", "Rook", "Queen", "King"]
    color_names = ["White", "Black"]
    
    # Hash pieces
    print("\n1. Pieces:")
    for color in range(2):
        for piece_type in range(6):
            bitboard = our_board.pieces[color][piece_type]
            if bitboard:
                print(f"  {color_names[color]} {piece_names[piece_type]}:")
                while bitboard:
                    square = (bitboard & -bitboard).bit_length() - 1
                    bitboard &= bitboard - 1
                    
                    polyglot_piece = polyglot_piece_map[(color, piece_type)]
                    key = PolyglotZobrist.KEYS['pieces'][square][polyglot_piece]
                    hash_val ^= key
                    
                    file = square % 8
                    rank = square // 8
                    print(f"    {chr(ord('a') + file)}{rank + 1} (sq={square}): piece_idx={polyglot_piece}, key={key:016x}")
    
    print(f"\n  Hash after pieces: {hash_val:016x}")
    
    # Hash castling
    print("\n2. Castling rights:")
    print(f"  Our castling_rights = {our_board.castling_rights} (binary: {our_board.castling_rights:04b})")
    if our_board.castling_rights & 1:
        key = PolyglotZobrist.KEYS['castling'][0]
        hash_val ^= key
        print(f"  White kingside: {key:016x}")
    if our_board.castling_rights & 2:
        key = PolyglotZobrist.KEYS['castling'][1]
        hash_val ^= key
        print(f"  White queenside: {key:016x}")
    if our_board.castling_rights & 4:
        key = PolyglotZobrist.KEYS['castling'][2]
        hash_val ^= key
        print(f"  Black kingside: {key:016x}")
    if our_board.castling_rights & 8:
        key = PolyglotZobrist.KEYS['castling'][3]
        hash_val ^= key
        print(f"  Black queenside: {key:016x}")
    
    print(f"\n  Hash after castling: {hash_val:016x}")
    
    # Hash en passant
    print("\n3. En passant:")
    if our_board.en_passant_square is not None:
        print(f"  EP square: {our_board.en_passant_square}")
        ep_file = our_board.en_passant_square % 8
        print(f"  EP file: {ep_file}")
        # Check for capturer (simplified - just check if EP should be hashed)
        key = PolyglotZobrist.KEYS['en_passant'][ep_file]
        print(f"  EP key: {key:016x}")
    else:
        print(f"  No en passant")
    
    print(f"\n  Hash after EP: {hash_val:016x}")
    
    # Hash side to move
    print("\n4. Side to move:")
    print(f"  side_to_move = {our_board.side_to_move} ({'White' if our_board.side_to_move == 0 else 'Black'})")
    if our_board.side_to_move == 0:
        key = PolyglotZobrist.KEYS['side_to_move']
        hash_val ^= key
        print(f"  XOR side key (White): {key:016x}")
    else:
        print(f"  No XOR for Black to move")
    
    print(f"\n  Final hash: {hash_val:016x}")
    
    # Compare
    print("\n" + "=" * 60)
    print(f"Reference: {reference_hash:016x}")
    print(f"Ours:      {hash_val:016x}")
    if reference_hash == hash_val:
        print("✓ MATCH!")
    else:
        print(f"✗ MISMATCH - XOR diff: {(reference_hash ^ hash_val):016x}")

if __name__ == "__main__":
    debug_hash_computation("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
