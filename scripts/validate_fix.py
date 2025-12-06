#!/usr/bin/env python3
"""
Quick validation of the castling bug fix.
Run this to verify the fix prevents illegal castling moves.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chess_engine import ChessBoard

def validate_fix():
    print("=" * 70)
    print("CASTLING BUG FIX VALIDATION")
    print("=" * 70)
    
    # Test 1: The exact bug from user's report
    print("\n1. User's reported bug position:")
    print("   FEN: 8/2P3k1/8/P7/3n4/8/8/4K3 b KQkq - 0 61")
    print("   (No rooks, but castling rights = KQkq)")
    
    board = ChessBoard()
    board.setup_from_fen("8/2P3k1/8/P7/3n4/8/8/4K3 b KQkq - 0 61")
    moves = board.generate_moves()
    
    # Check for illegal e8g8 or e8c8
    illegal_found = False
    for move in moves:
        from_sq, to_sq = move[0], move[1]
        # e8=60, g8=62, c8=58
        if (from_sq == 60 and to_sq == 62) or (from_sq == 60 and to_sq == 58):
            illegal_found = True
            print(f"   ❌ ILLEGAL MOVE FOUND: {from_sq} -> {to_sq}")
    
    if not illegal_found:
        print("   ✅ No illegal castling moves generated!")
    
    # Test 2: Valid castling should still work
    print("\n2. Valid castling (Black to move with rooks):")
    print("   FEN: r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    
    board = ChessBoard()
    board.setup_from_fen("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    moves = board.generate_moves()
    
    e8g8_found = False
    e8c8_found = False
    for move in moves:
        from_sq, to_sq = move[0], move[1]
        if from_sq == 60 and to_sq == 62:  # e8g8
            e8g8_found = True
        if from_sq == 60 and to_sq == 58:  # e8c8
            e8c8_found = True
    
    if e8g8_found and e8c8_found:
        print("   ✅ Both Black castling moves work (e8g8, e8c8)")
    else:
        print(f"   ❌ Missing moves: e8g8={e8g8_found}, e8c8={e8c8_found}")
    
    # Test 3: Partial rooks - the critical test
    print("\n3. Critical test (Black to move, only h8 rook, but FEN says 'kq'):")
    print("   FEN: 4k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    print("   Expected: Only e8g8 (kingside), NOT e8c8 (no rook on a8)")
    
    board = ChessBoard()
    board.setup_from_fen("4k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    moves = board.generate_moves()
    
    e8g8_found = False
    e8c8_found = False
    for move in moves:
        from_sq, to_sq = move[0], move[1]
        if from_sq == 60 and to_sq == 62:
            e8g8_found = True
        if from_sq == 60 and to_sq == 58:
            e8c8_found = True
    
    if e8g8_found and not e8c8_found:
        print("   ✅ PERFECT! Only e8g8 generated, no illegal e8c8")
    elif e8c8_found:
        print("   ❌ CRITICAL BUG: e8c8 generated without rook on a8!")
    else:
        print(f"   ⚠️  e8g8={e8g8_found}, e8c8={e8c8_found}")
    
    print("\n" + "=" * 70)
    if not illegal_found and e8g8_found and e8c8_found:
        print("✅ ALL VALIDATIONS PASSED - Bug is fixed!")
        print("=" * 70)
        return True
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = validate_fix()
    sys.exit(0 if success else 1)
