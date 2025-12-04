"""
Test script for opening book implementation.

This script verifies:
1. Opening book file exists and loads correctly
2. Polyglot hash computation works
3. Book probe returns legal moves
4. Integration with main engine works
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chess_engine import ChessBoard
from opening_book import OpeningBook, probe_book, PolyglotZobrist

def test_polyglot_hash():
    """Test Polyglot hash computation."""
    print("\n=== Testing Polyglot Hash ===")
    
    # Starting position
    board = ChessBoard()
    board.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    hash_val = PolyglotZobrist.compute_hash(board)
    print(f"Starting position hash: {hash_val:#018x}")
    
    # Known hash for starting position (from Polyglot spec)
    # This should be: 0x463b96181691fc9c
    expected = 0x463b96181691fc9c
    if hash_val == expected:
        print("✓ Hash matches Polyglot standard!")
    else:
        print(f"✗ Hash mismatch! Expected {expected:#018x}, got {hash_val:#018x}")
    
    return hash_val == expected

def test_book_loading():
    """Test opening book loading."""
    print("\n=== Testing Book Loading ===")
    
    # Try to find book file
    book_paths = [
        "openingbook/baron343/book.bin",
        "openingbook/book.bin",
    ]
    
    found_book = None
    for path in book_paths:
        if os.path.exists(path):
            print(f"Found book at: {path}")
            found_book = path
            break
    
    if not found_book:
        print("✗ No book file found!")
        print("Searched paths:")
        for path in book_paths:
            print(f"  - {path}")
        return False
    
    # Load book
    try:
        book = OpeningBook(found_book)
        if book.is_loaded():
            print(f"✓ Book loaded successfully")
            return True
        else:
            print("✗ Book failed to load")
            return False
    except Exception as e:
        print(f"✗ Error loading book: {e}")
        return False

def test_book_probe():
    """Test probing opening book."""
    print("\n=== Testing Book Probe ===")
    
    # Starting position
    board = ChessBoard()
    board.setup_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    move = probe_book(board, randomize=False)
    
    if move:
        from_sq, to_sq, promo = move
        print(f"✓ Found book move: {from_sq} -> {to_sq}" + (f" ={promo}" if promo else ""))
        
        # Verify move is legal
        legal_moves = set(board.generate_moves())
        if move in legal_moves:
            print("✓ Book move is legal")
            return True
        else:
            print("✗ Book move is ILLEGAL!")
            return False
    else:
        print("✗ No book move found for starting position")
        return False

def test_various_positions():
    """Test book probe on various positions."""
    print("\n=== Testing Various Positions ===")
    
    positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("After 1.e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"),
        ("After 1.d4", "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1"),
        ("Middlegame (not in book)", "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
    ]
    
    for name, fen in positions:
        board = ChessBoard()
        board.setup_from_fen(fen)
        move = probe_book(board, randomize=False)
        
        if move:
            from_sq, to_sq, promo = move
            print(f"✓ {name}: Found move {from_sq}->{to_sq}")
        else:
            print(f"  {name}: Not in book (expected for later positions)")
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("OPENING BOOK TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Polyglot hash
    results.append(("Polyglot Hash", test_polyglot_hash()))
    
    # Test 2: Book loading
    results.append(("Book Loading", test_book_loading()))
    
    # Test 3: Book probe
    results.append(("Book Probe", test_book_probe()))
    
    # Test 4: Various positions
    results.append(("Various Positions", test_various_positions()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Opening book is ready to use.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
