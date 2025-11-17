#!/usr/bin/env python3
"""
Extract positions from PGN file for evaluation testing.

Handles both regular PGN and compressed .pgn.zst files.

Usage:
    python3 extract_pgn_positions.py <pgn_file> [--output positions.txt] [--count 1000]
"""

import sys
import re
from typing import List, Optional


def decompress_zst_file(zst_path: str, output_path: str) -> bool:
    """
    Decompress .zst file using zstandard library.
    
    Args:
        zst_path: Path to .zst file
        output_path: Path for decompressed output
    
    Returns:
        True if successful
    """
    try:
        import zstandard as zstd
    except ImportError:
        print("❌ zstandard library not installed")
        print("   Install with: pip install zstandard")
        return False
    
    print(f"Decompressing {zst_path}...")
    
    try:
        with open(zst_path, 'rb') as compressed:
            dctx = zstd.ZstdDecompressor()
            with open(output_path, 'wb') as destination:
                dctx.copy_stream(compressed, destination)
        
        print(f"✅ Decompressed to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Decompression failed: {e}")
        return False


def parse_pgn_moves(movetext: str) -> List[str]:
    """
    Parse moves from PGN movetext.
    
    Args:
        movetext: PGN movetext string (e.g., "1. e4 e5 2. Nf3 Nc6")
    
    Returns:
        List of moves in algebraic notation
    """
    # Remove comments
    movetext = re.sub(r'\{[^}]*\}', '', movetext)
    movetext = re.sub(r'\([^)]*\)', '', movetext)
    
    # Remove move numbers
    movetext = re.sub(r'\d+\.+', '', movetext)
    
    # Remove game result
    movetext = re.sub(r'(1-0|0-1|1/2-1/2|\*)', '', movetext)
    
    # Split into moves
    moves = movetext.split()
    
    return [m.strip() for m in moves if m.strip()]


def extract_positions_from_pgn(pgn_path: str, max_positions: int = 1000, 
                                 games_to_process: int = 100) -> List[str]:
    """
    Extract positions from PGN file.
    
    Args:
        pgn_path: Path to PGN file
        max_positions: Maximum positions to extract
        games_to_process: Number of games to process
    
    Returns:
        List of FEN strings
    """
    print(f"Reading PGN file: {pgn_path}")
    
    positions = []
    games_processed = 0
    current_game = []
    in_movetext = False
    
    try:
        with open(pgn_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    if in_movetext and current_game:
                        # End of game
                        games_processed += 1
                        
                        # Process this game
                        movetext = ' '.join(current_game)
                        # TODO: Parse moves and generate FENs
                        # For now, we skip move parsing (would need chess library)
                        
                        current_game = []
                        in_movetext = False
                        
                        if games_processed >= games_to_process:
                            break
                        
                        if games_processed % 10 == 0:
                            print(f"  Processed {games_processed} games...")
                    continue
                
                # Skip headers (lines starting with [)
                if line.startswith('['):
                    continue
                
                # Movetext
                in_movetext = True
                current_game.append(line)
        
        print(f"✅ Processed {games_processed} games")
    
    except Exception as e:
        print(f"❌ Error reading PGN: {e}")
    
    return positions


def main():
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Extract positions from PGN")
    parser.add_argument('pgn_file', help='PGN file (or .pgn.zst)')
    parser.add_argument('--output', default='positions.txt', help='Output file')
    parser.add_argument('--count', type=int, default=1000, help='Max positions')
    parser.add_argument('--games', type=int, default=100, help='Games to process')
    
    args = parser.parse_args()
    
    pgn_path = args.pgn_file
    
    # Check if file needs decompression
    if pgn_path.endswith('.zst'):
        decompressed_path = pgn_path[:-4]  # Remove .zst
        
        if not os.path.exists(decompressed_path):
            if not decompress_zst_file(pgn_path, decompressed_path):
                print("Cannot proceed without decompressed file")
                print()
                print("Alternative: Use pre-generated positions with test_against_stockfish.py")
                return
        else:
            print(f"✅ Using existing decompressed file: {decompressed_path}")
        
        pgn_path = decompressed_path
    
    # Extract positions
    print()
    print("=" * 70)
    print("NOTE: Full PGN parsing requires chess library")
    print("=" * 70)
    print()
    print("The Lichess PGN file is very large (hundreds of MB when decompressed).")
    print("For evaluation testing, it's better to use:")
    print()
    print("  python3 test_against_stockfish.py --positions 100 --depth 15")
    print()
    print("This generates diverse test positions automatically!")
    print()


if __name__ == "__main__":
    main()
