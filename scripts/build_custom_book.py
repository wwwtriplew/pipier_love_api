#!/usr/bin/env python3
"""
Custom Opening Book Builder for Piper Love (Black Repertoire)

Builds a Polyglot opening book from PGN variations using python-chess library
for correct SAN parsing (handles disambiguation like Nbd7 vs Nfd7).
"""

import struct
import sys
import os
from typing import List, Dict
import chess
import chess.pgn
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chess_engine import ChessBoard
from src.opening_book import PolyglotZobrist


class BookEntry:
    """Single opening book entry."""
    def __init__(self, hash_key: int, move: int, weight: int = 1):
        self.hash_key = hash_key
        self.move = move
        self.weight = weight
    
    def __lt__(self, other):
        """Sort by hash key for Polyglot format."""
        return self.hash_key < other.hash_key


def chess_to_internal_move(chess_move: chess.Move) -> tuple:
    """Convert python-chess Move to internal format (from_sq, to_sq, promo)."""
    from_sq = chess_move.from_square
    to_sq = chess_move.to_square
    
    # Handle promotion
    promo = None
    if chess_move.promotion:
        # chess.KNIGHT=2, BISHOP=3, ROOK=4, QUEEN=5
        # Internal: KNIGHT=1, BISHOP=2, ROOK=3, QUEEN=4
        promo = chess_move.promotion - 1
    
    return from_sq, to_sq, promo


def encode_polyglot_move(from_sq: int, to_sq: int, promotion) -> int:
    """
    Encode move in Polyglot format.
    
    Format (16 bits):
    - Bits 0-5: to square (0-63)
    - Bits 6-11: from square (0-63)  
    - Bits 12-14: promotion (0=none, 1=N, 2=B, 3=R, 4=Q)
    """
    promo_val = promotion if promotion else 0
    return to_sq | (from_sq << 6) | (promo_val << 12)


def extract_all_variations(game_node) -> List[List[chess.Move]]:
    """Recursively extract all variations from a chess.pgn game tree."""
    variations = []
    
    def walk(node, current_line):
        """Walk through game tree and collect all lines."""
        if node.move:
            current_line.append(node.move)
        
        # If this node has no more moves, save the line
        if not node.variations:
            if current_line:
                variations.append(current_line.copy())
            return
        
        # Main variation
        walk(node.variations[0], current_line.copy())
        
        # Alternative variations (if any)
        for var in node.variations[1:]:
            walk(var, current_line.copy())
    
    walk(game_node, [])
    return variations


def build_book_from_pgn(pgn_text: str, output_file: str):
    """Build Polyglot book from PGN text with variations."""
    book_entries: Dict[int, Dict[int, int]] = {}  # hash -> {move -> weight}
    position_sources: Dict[int, Dict[int, str]] = {}  # hash -> {move -> source_description}
    
    # Parse PGN using python-chess (handles all SAN correctly)
    pgn = StringIO(pgn_text)
    game = chess.pgn.read_game(pgn)
    
    if not game:
        print("ERROR: Could not parse PGN")
        return
    
    # Extract all variations
    print("Extracting variations from PGN...")
    variations = extract_all_variations(game)
    print(f"Found {len(variations)} distinct lines")
    
    # Track conflicts for validation (only for Black moves)
    conflicts = []
    
    # Process each variation
    for var_idx, moves in enumerate(variations):
        # Use python-chess board for move parsing
        chess_board = chess.Board()
        # Use our internal board for Polyglot hashing
        internal_board = ChessBoard()
        
        print(f"\nVariation {var_idx + 1}: {len(moves)} moves")
        
        for move_idx, chess_move in enumerate(moves):
            # Verify move is legal
            if chess_move not in chess_board.legal_moves:
                print(f"  WARNING: Illegal move at position {move_idx + 1}")
                break
            
            # Get side to move BEFORE making the move
            is_black_to_move = (chess_board.turn == chess.BLACK)
            
            # Get Polyglot hash BEFORE making the move
            poly_hash = PolyglotZobrist.compute_hash(internal_board)
            
            # Convert chess.Move to internal format
            from_sq, to_sq, promo = chess_to_internal_move(chess_move)
            poly_move = encode_polyglot_move(from_sq, to_sq, promo)
            
            # Get move description for debugging
            move_san = chess_board.san(chess_move)
            fen = chess_board.fen()
            source_desc = f"Var {var_idx + 1}, Move {move_idx + 1}: {move_san}"
            
            # Check for conflicts ONLY when Black is to move
            # White can have multiple variations from same position (opening tree)
            if is_black_to_move and poly_hash in book_entries:
                existing_moves = book_entries[poly_hash]
                if poly_move not in existing_moves and len(existing_moves) > 0:
                    # CONFLICT: Same position (Black to move), different Black moves
                    other_move = list(existing_moves.keys())[0]
                    other_source = position_sources[poly_hash][other_move]
                    conflict_msg = (
                        f"\n⚠️  BLACK MOVE CONFLICT at position:\n"
                        f"    FEN: {fen}\n"
                        f"    Existing: {other_source}\n"
                        f"    New:      {source_desc}\n"
                        f"    → Black has multiple book moves for same position!"
                    )
                    conflicts.append(conflict_msg)
                    print(conflict_msg)
                    continue  # Skip this move to avoid non-deterministic behavior
            
            # Add to book
            if poly_hash not in book_entries:
                book_entries[poly_hash] = {}
                position_sources[poly_hash] = {}
            
            if poly_move not in book_entries[poly_hash]:
                book_entries[poly_hash][poly_move] = 1
                position_sources[poly_hash][poly_move] = source_desc
            else:
                # Same position, same move from different variation = OK (transposition)
                book_entries[poly_hash][poly_move] += 1
            
            # Make the move on both boards
            chess_board.push(chess_move)
            internal_board.make_move(from_sq, to_sq, promo)
    
    # Report conflicts
    if conflicts:
        print("\n" + "="*60)
        print(f"❌ VALIDATION FAILED: {len(conflicts)} Black move conflict(s)!")
        print("="*60)
        print("\nConflicts occur when Black has multiple different responses")
        print("to the same position. Black's repertoire must be consistent.")
        print("\nWhite can have multiple variations (normal for opening tree).")
        print("="*60)
        return
    
    # Convert to list of entries
    entries = []
    for hash_key, moves_dict in book_entries.items():
        for poly_move, weight in moves_dict.items():
            entries.append(BookEntry(hash_key, poly_move, weight))
    
    # Sort by hash (required for Polyglot format)
    entries.sort()
    
    print(f"\n✓ Generated {len(entries)} unique positions")
    print(f"✓ No Black move conflicts - repertoire is consistent")
    
    # Write Polyglot book
    with open(output_file, 'wb') as f:
        for entry in entries:
            # Polyglot format: 8 bytes hash + 2 bytes move + 2 bytes weight + 4 bytes padding
            packed = struct.pack('>QHHI', entry.hash_key, entry.move, entry.weight, 0)
            f.write(packed)
    
    print(f"✓ Book written to {output_file}")
    print(f"  Size: {os.path.getsize(output_file) / 1024:.1f} KB")


def main():
    """Main entry point."""
    # Read PGN from external file for better maintainability
    pgn_file = 'openingbook/piperlove_repertoire.pgn'
    
    if not os.path.exists(pgn_file):
        print(f"ERROR: PGN file not found: {pgn_file}")
        print("Please create the file with your opening repertoire.")
        return
    
    with open(pgn_file, 'r') as f:
        pgn_text = f.read()
    
    print(f"Reading opening repertoire from: {pgn_file}")
    
    # Create output directory
    os.makedirs('openingbook', exist_ok=True)
    
    # Build book
    output_file = 'openingbook/piperlove_black.bin'
    build_book_from_pgn(pgn_text, output_file)
    
    print("\n" + "="*60)
    print("✓ Custom opening book created successfully!")
    print(f"  Location: {output_file}")
    print("\nTo use this book, it will be automatically prioritized")
    print("over baron30.bin in the opening book loader.")
    print("\nTo add more lines: Edit openingbook/piperlove_repertoire.pgn")
    print("Then run: python3 scripts/build_custom_book.py")
    print("="*60)


if __name__ == '__main__':
    main()

