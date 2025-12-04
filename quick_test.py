#!/usr/bin/env python3
"""
QUICK TEST - Opening Book Verification
Run this first to verify opening book is working.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def quick_test():
    """Quick test of opening book functionality."""
    
    print("="*60)
    print("QUICK OPENING BOOK TEST")
    print("="*60)
    
    # Test 1: File exists
    print("\n1. Checking for book file...")
    book_found = False
    for path in ["openingbook/baron343/baron30.bin", "openingbook/book.bin"]:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"   ✅ Found: {path} ({size:,} bytes)")
            book_found = True
            break
    
    if not book_found:
        print("   ⚠️  No book file found")
        print("   ✅ OK - Engine will work without book")
        return
    
    # Test 2: Import and load
    print("\n2. Loading opening book...")
    try:
        from opening_book import get_default_book, probe_book, PolyglotZobrist
        from chess_engine import ChessBoard
        print("   ✅ Imports successful")
        
        book = get_default_book()
        if book and book.is_loaded():
            print(f"   ✅ Book loaded: {len(book.entries):,} entries")
        else:
            print("   ⚠️  Book failed to load")
            print("   ✅ OK - Engine will work without book")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   ✅ OK - Engine will work without book")
        return
    
    # Test 3: Hash correctness
    print("\n3. Verifying Polyglot hash...")
    try:
        board = ChessBoard()
        board.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        hash_val = PolyglotZobrist.compute_hash(board)
        expected = 0x463b96181691fc9c
        
        if hash_val == expected:
            print(f"   ✅ Hash correct: {hash_val:#018x}")
        else:
            print(f"   ❌ Hash mismatch!")
            print(f"      Got:      {hash_val:#018x}")
            print(f"      Expected: {expected:#018x}")
            print("   ⚠️  DO NOT DEPLOY - critical error")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 4: Query starting position
    print("\n4. Testing book query...")
    try:
        move = probe_book(board, randomize=False)
        
        if move:
            from_sq, to_sq, promo = move
            move_str = f"{chr(from_sq%8 + ord('a'))}{from_sq//8 + 1}"
            move_str += f"{chr(to_sq%8 + ord('a'))}{to_sq//8 + 1}"
            if promo:
                move_str += {1: 'n', 2: 'b', 3: 'r', 4: 'q'}.get(promo, '?')
            
            # Check if legal
            legal_moves = list(board.generate_moves())
            is_legal = any(m[0] == from_sq and m[1] == to_sq and m[2] == promo for m in legal_moves)
            
            if is_legal:
                print(f"   ✅ Found legal move: {move_str}")
            else:
                print(f"   ❌ ILLEGAL move returned: {move_str}")
                print("   ⚠️  Critical error - validation failed")
                return
        else:
            print("   ⚠️  Starting position not in book")
            print("   ✅ OK - Engine will search normally")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   ✅ OK - Engine will work without book")
        return
    
    # Success!
    print("\n" + "="*60)
    print("✅ ALL CHECKS PASSED")
    print("Opening book is ready for deployment!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run full tests: python test_book_manual.py")
    print("2. Start API: uvicorn main:app --reload")
    print("3. Test API: python test_api_book.py")
    print("="*60)

if __name__ == "__main__":
    try:
        quick_test()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("✅ But engine will still work with graceful fallback")
        import traceback
        traceback.print_exc()
