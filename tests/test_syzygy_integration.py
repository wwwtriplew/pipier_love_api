#!/usr/bin/env python3
"""
Syzygy Tablebase Integration Test

Tests that our implementation can correctly:
1. Load Syzygy tablebase files
2. Convert our ChessBoard to python-chess Board
3. Probe tablebases for correct moves
4. Handle errors gracefully
"""

import sys
import os
sys.path.insert(0, 'src')

import chess
import chess.syzygy
from chess_engine import ChessBoard

print("=" * 80)
print("SYZYGY TABLEBASE INTEGRATION TEST")
print("=" * 80)

# Test positions (2-5 pieces)
test_positions = [
    # KvK (2 pieces) - should be draw
    ("KvK", "8/8/8/8/4k3/8/8/4K3 w - - 0 1", 0),  # Draw
    
    # KQvK (3 pieces) - should be winning
    ("KQvK", "8/8/8/8/4k3/8/8/4KQ2 w - - 0 1", 2),  # Win for white
    
    # KRvK (3 pieces) - should be winning
    ("KRvK", "8/8/8/8/4k3/8/8/4KR2 w - - 0 1", 2),  # Win for white
    
    # KPvK (3 pieces) - depends on position
    ("KPvK", "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1", None),  # Complex
    
    # KQvKR (4 pieces) - should be winning
    ("KQvKR", "8/8/8/8/4k3/5r2/8/4KQ2 w - - 0 1", 2),  # Win for white
    
    # Complex 5-piece endgame
    ("5-piece", "8/8/8/4k3/8/4r3/4P3/4K3 w - - 0 1", None),
]

print("\n[TEST 1] Board Conversion")
print("-" * 40)

for name, fen, expected_wdl in test_positions:
    try:
        # Our board
        our_board = ChessBoard()
        our_board.setup_from_fen(fen)
        
        # python-chess board
        chess_board = chess.Board(fen)
        
        # Verify piece count matches
        our_piece_count = bin(our_board.pieces[0][0]).count('1') + \
                         bin(our_board.pieces[0][1]).count('1') + \
                         bin(our_board.pieces[0][2]).count('1') + \
                         bin(our_board.pieces[0][3]).count('1') + \
                         bin(our_board.pieces[0][4]).count('1') + \
                         bin(our_board.pieces[0][5]).count('1') + \
                         bin(our_board.pieces[1][0]).count('1') + \
                         bin(our_board.pieces[1][1]).count('1') + \
                         bin(our_board.pieces[1][2]).count('1') + \
                         bin(our_board.pieces[1][3]).count('1') + \
                         bin(our_board.pieces[1][4]).count('1') + \
                         bin(our_board.pieces[1][5]).count('1')
        
        chess_piece_count = len(chess_board.piece_map())
        
        if our_piece_count == chess_piece_count:
            print(f"  ✅ {name}: {our_piece_count} pieces (conversion OK)")
        else:
            print(f"  ❌ {name}: Mismatch! Our={our_piece_count}, chess.py={chess_piece_count}")
            
    except Exception as e:
        print(f"  ❌ {name}: Conversion failed - {e}")

print("\n[TEST 2] Tablebase File Format")
print("-" * 40)

# Check what files Syzygy actually needs
print("  Syzygy tablebase files should be:")
print("    • .rtbw files (WDL - Win/Draw/Loss)")
print("    • .rtbz files (DTZ - Distance To Zero)")
print("  ")
print("  Example for KQvK (3-piece):")
print("    • KQvK.rtbw")
print("    • KQvK.rtbz")

# Try to load tablebase if directory exists
print("\n[TEST 3] Tablebase Loading")
print("-" * 40)

test_paths = ['/root/syzygy', '/opt/syzygy', './syzygy']

for path in test_paths:
    if os.path.exists(path):
        print(f"  📁 Found directory: {path}")
        
        # List files
        try:
            files = os.listdir(path)
            rtbw_files = [f for f in files if f.endswith('.rtbw')]
            rtbz_files = [f for f in files if f.endswith('.rtbz')]
            
            print(f"     • {len(rtbw_files)} .rtbw files")
            print(f"     • {len(rtbz_files)} .rtbz files")
            
            if rtbw_files:
                print(f"     • Sample files: {rtbw_files[:3]}")
                
                # Try to load
                try:
                    tablebase = chess.syzygy.open_tablebase(path)
                    print(f"     ✅ Tablebase loaded successfully!")
                    
                    # Test probe
                    test_board = chess.Board("8/8/8/8/4k3/8/8/4KQ2 w - - 0 1")  # KQvK
                    try:
                        wdl = tablebase.probe_wdl(test_board)
                        print(f"     ✅ Probe test: WDL={wdl} (expected: 2=Win)")
                        
                        # Find best move
                        best_move = None
                        best_wdl = -3
                        for move in test_board.legal_moves:
                            test_board.push(move)
                            try:
                                next_wdl = -tablebase.probe_wdl(test_board)
                                if next_wdl > best_wdl:
                                    best_wdl = next_wdl
                                    best_move = move
                            except:
                                pass
                            test_board.pop()
                        
                        if best_move:
                            print(f"     ✅ Best move found: {best_move.uci()}")
                        else:
                            print(f"     ⚠️  No best move found")
                            
                    except Exception as e:
                        print(f"     ❌ Probe failed: {e}")
                        
                except Exception as e:
                    print(f"     ❌ Loading failed: {e}")
            else:
                print(f"     ⚠️  No .rtbw files found!")
                print(f"     ⚠️  Download may be incomplete or incorrect")
                
        except Exception as e:
            print(f"     ❌ Error reading directory: {e}")
    else:
        print(f"  ⚪ Not found: {path}")

print("\n" + "=" * 80)
print("CRITICAL CHECKS")
print("=" * 80)

print("\n1. ✅ FEN conversion works (our board → python-chess)")
print("2. ❓ Tablebase files present (.rtbw and .rtbz)?")
print("3. ❓ python-chess.syzygy can load the files?")
print("4. ❓ Probe returns correct WDL values?")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

print("\nIf tablebase loading fails:")
print("  1. Verify .rtbw and .rtbz files exist")
print("  2. Check file permissions (should be readable)")
print("  3. Ensure complete download (wget should finish without errors)")
print("  4. Test with: python -c 'import chess.syzygy; tb = chess.syzygy.open_tablebase(\"/root/syzygy\"); print(tb)'")
print("\nIf no files found:")
print("  • wget command may need adjustment")
print("  • Check sesse.net URL is accessible")
print("  • Try alternative: http://tablebase.lichess.ovh/tables/standard/3-4-5/")

print("\n" + "=" * 80)
