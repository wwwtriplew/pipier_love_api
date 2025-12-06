#!/usr/bin/env python3
"""
Comprehensive validation suite for opening book implementation.
Tests correctness, performance, thread safety, and edge cases.
"""

import sys
sys.path.insert(0, 'src')

import chess
import chess.polyglot
from opening_book import PolyglotZobrist, OpeningBook, probe_book
from chess_engine import ChessBoard
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict

class ValidationSuite:
    def __init__(self):
        self.results = {
            'hash_correctness': [],
            'move_legality': [],
            'edge_cases': [],
            'performance': [],
            'thread_safety': []
        }
        
    def print_section(self, title: str):
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)
    
    def print_test(self, name: str, passed: bool, details: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if details:
            print(f"         {details}")
    
    # ========================================================================
    # SECTION 1: HASH CORRECTNESS
    # ========================================================================
    
    def test_hash_correctness(self):
        """Verify hash computation matches python-chess for various positions"""
        self.print_section("1. HASH CORRECTNESS TESTS")
        
        test_positions = [
            # Basic positions
            ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
            ("After 1.e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"),
            ("After 1.d4", "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"),
            ("After 1.Nf3", "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 0 1"),
            
            # Castling variations
            ("White loses kingside", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w Qkq - 0 1"),
            ("White loses queenside", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w Kkq - 0 1"),
            ("Black loses kingside", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQq - 0 1"),
            ("Black loses queenside", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQk - 0 1"),
            ("No castling rights", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"),
            ("After white castles kingside", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQ1RK1 w kq - 0 1"),
            ("After black castles queenside", "2kr1bnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQ - 0 1"),
            
            # En passant - CRITICAL tests
            ("EP d6 white to move", "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2"),
            ("EP e6 white to move", "rnbqkbnr/pppp1ppp/8/4pP2/8/8/PPPPP1PP/RNBQKBNR w KQkq e6 0 2"),
            ("EP d3 black to move", "rnbqkbnr/ppp1pppp/8/8/8/3p4/PPPPPPPP/RNBQKBNR b KQkq d3 0 2"),
            ("EP a6 (edge file)", "rnbqkbnr/1ppppppp/8/pP6/8/8/P1PPPPPP/RNBQKBNR w KQkq a6 0 2"),
            ("EP h6 (edge file)", "rnbqkbnr/ppppppp1/8/6Pp/8/8/PPPPPP1P/RNBQKBNR w KQkq h6 0 2"),
            ("EP square no capturer", "rnbqkbnr/pppp1ppp/8/3Pp3/8/8/PPP1PPPP/RNBQKBNR b KQkq - 0 2"),
            
            # Side to move
            ("White to move midgame", "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
            ("Black to move midgame", "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 2 3"),
            
            # Piece configurations
            ("Ruy Lopez", "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"),
            ("Sicilian Najdorf", "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"),
            ("French Defense", "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
            ("Caro-Kann", "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
            ("King's Indian", "rnbqkb1r/pppppp1p/5np1/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3"),
            
            # Edge cases
            ("Empty board except kings", "4k3/8/8/8/8/8/8/4K3 w - - 0 1"),
            ("All pawns promoted", "RNBQKBNR/8/8/8/8/8/8/rnbqkbnr w - - 0 1"),
            ("Pawn endgame", "8/pppppppp/8/8/8/8/PPPPPPPP/8 w - - 0 1"),
        ]
        
        passed = 0
        failed = []
        
        for name, fen in test_positions:
            try:
                py_board = chess.Board(fen)
                my_board = ChessBoard()
                my_board.setup_from_fen(fen)
                
                py_hash = chess.polyglot.zobrist_hash(py_board)
                my_hash = PolyglotZobrist.compute_hash(my_board)
                
                if py_hash == my_hash:
                    passed += 1
                    self.print_test(name, True, f"Hash: {hex(my_hash)}")
                else:
                    failed.append(name)
                    self.print_test(name, False, 
                        f"Expected {hex(py_hash)}, got {hex(my_hash)}")
                    
            except Exception as e:
                failed.append(name)
                self.print_test(name, False, f"Exception: {e}")
        
        total = len(test_positions)
        print(f"\n📊 Hash Correctness: {passed}/{total} passed")
        self.results['hash_correctness'] = (passed, total, failed)
        return len(failed) == 0
    
    # ========================================================================
    # SECTION 2: MOVE LEGALITY
    # ========================================================================
    
    def test_move_legality(self):
        """Verify all book moves are legal in their positions"""
        self.print_section("2. MOVE LEGALITY TESTS")
        
        test_positions = [
            ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
            ("After 1.e4", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"),
            ("After 1.d4", "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"),
            ("After 1.e4 e5", "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
            ("After 1.d4 Nf6", "rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 1 2"),
        ]
        
        passed = 0
        failed = []
        
        for name, fen in test_positions:
            try:
                board = ChessBoard()
                board.setup_from_fen(fen)
                
                book_move = probe_book(board)
                
                if book_move is None:
                    self.print_test(name, True, "Not in book (acceptable)")
                    passed += 1
                    continue
                
                # Verify move is legal
                from_sq, to_sq, promo = book_move
                
                # Check basic validity
                if not (0 <= from_sq < 64 and 0 <= to_sq < 64):
                    failed.append(name)
                    self.print_test(name, False, f"Invalid squares: {from_sq}->{to_sq}")
                    continue
                
                # Generate legal moves and check if book move is in them
                from move_generation import generate_moves
                legal_moves = generate_moves(board)
                
                move_found = False
                for move in legal_moves:
                    if move[0] == from_sq and move[1] == to_sq:
                        if promo is None or move[2] == promo:
                            move_found = True
                            break
                
                if move_found:
                    file_from = chr(from_sq % 8 + ord('a'))
                    rank_from = from_sq // 8 + 1
                    file_to = chr(to_sq % 8 + ord('a'))
                    rank_to = to_sq // 8 + 1
                    move_str = f"{file_from}{rank_from}{file_to}{rank_to}"
                    if promo:
                        move_str += ['n', 'b', 'r', 'q'][promo - 1]
                    
                    self.print_test(name, True, f"Legal move: {move_str}")
                    passed += 1
                else:
                    failed.append(name)
                    self.print_test(name, False, f"Move {from_sq}->{to_sq} not legal")
                    
            except Exception as e:
                failed.append(name)
                self.print_test(name, False, f"Exception: {e}")
        
        total = len(test_positions)
        print(f"\n📊 Move Legality: {passed}/{total} passed")
        self.results['move_legality'] = (passed, total, failed)
        return len(failed) == 0
    
    # ========================================================================
    # SECTION 3: EDGE CASES
    # ========================================================================
    
    def test_edge_cases(self):
        """Test boundary conditions and error handling"""
        self.print_section("3. EDGE CASE TESTS")
        
        tests_passed = 0
        tests_failed = []
        
        # Test 1: Invalid FEN handling
        try:
            board = ChessBoard()
            # This should either handle gracefully or raise exception
            result = probe_book(board)  # Default position should work
            self.print_test("Default board probe", True, f"Result: {result}")
            tests_passed += 1
        except Exception as e:
            tests_failed.append("Default board probe")
            self.print_test("Default board probe", False, f"Exception: {e}")
        
        # Test 2: Position definitely not in book
        try:
            board = ChessBoard()
            # Random endgame position unlikely to be in opening book
            board.setup_from_fen("8/8/8/8/8/k7/8/K7 w - - 0 1")
            result = probe_book(board)
            if result is None:
                self.print_test("Non-book position", True, "Correctly returns None")
                tests_passed += 1
            else:
                tests_failed.append("Non-book position")
                self.print_test("Non-book position", False, f"Expected None, got {result}")
        except Exception as e:
            tests_failed.append("Non-book position")
            self.print_test("Non-book position", False, f"Exception: {e}")
        
        # Test 3: Multiple probes of same position (caching)
        try:
            board = ChessBoard()
            result1 = probe_book(board)
            result2 = probe_book(board)
            if result1 == result2:
                self.print_test("Consistent results", True, "Same move returned")
                tests_passed += 1
            else:
                tests_failed.append("Consistent results")
                self.print_test("Consistent results", False, f"{result1} != {result2}")
        except Exception as e:
            tests_failed.append("Consistent results")
            self.print_test("Consistent results", False, f"Exception: {e}")
        
        # Test 4: Book file integrity
        try:
            from opening_book import get_default_book
            book = get_default_book()
            entries = len(book.entries) if book else 0
            if entries > 0:
                self.print_test("Book file loaded", True, f"{entries} entries")
                tests_passed += 1
            else:
                tests_failed.append("Book file loaded")
                self.print_test("Book file loaded", False, "No entries")
        except Exception as e:
            tests_failed.append("Book file loaded")
            self.print_test("Book file loaded", False, f"Exception: {e}")
        
        # Test 5: Hash uniqueness (different positions should have different hashes)
        try:
            positions = [
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            ]
            hashes = []
            for fen in positions:
                board = ChessBoard()
                board.setup_from_fen(fen)
                hashes.append(PolyglotZobrist.compute_hash(board))
            
            if len(set(hashes)) == len(hashes):
                self.print_test("Hash uniqueness", True, "All hashes unique")
                tests_passed += 1
            else:
                tests_failed.append("Hash uniqueness")
                self.print_test("Hash uniqueness", False, "Duplicate hashes found")
        except Exception as e:
            tests_failed.append("Hash uniqueness")
            self.print_test("Hash uniqueness", False, f"Exception: {e}")
        
        total = 5
        print(f"\n📊 Edge Cases: {tests_passed}/{total} passed")
        self.results['edge_cases'] = (tests_passed, total, tests_failed)
        return len(tests_failed) == 0
    
    # ========================================================================
    # SECTION 4: PERFORMANCE
    # ========================================================================
    
    def test_performance(self):
        """Test hash computation and book lookup performance"""
        self.print_section("4. PERFORMANCE TESTS")
        
        tests_passed = 0
        tests_failed = []
        
        # Test 1: Hash computation speed
        try:
            board = ChessBoard()
            iterations = 10000
            
            start = time.time()
            for _ in range(iterations):
                PolyglotZobrist.compute_hash(board)
            elapsed = time.time() - start
            
            rate = iterations / elapsed
            if rate > 10000:  # Should be very fast (>10k/sec)
                self.print_test("Hash computation speed", True, 
                    f"{rate:.0f} hashes/sec")
                tests_passed += 1
            else:
                tests_failed.append("Hash computation speed")
                self.print_test("Hash computation speed", False, 
                    f"Too slow: {rate:.0f} hashes/sec")
        except Exception as e:
            tests_failed.append("Hash computation speed")
            self.print_test("Hash computation speed", False, f"Exception: {e}")
        
        # Test 2: Book lookup speed
        try:
            board = ChessBoard()
            iterations = 1000
            
            start = time.time()
            for _ in range(iterations):
                probe_book(board)
            elapsed = time.time() - start
            
            rate = iterations / elapsed
            if rate > 1000:  # Should be fast (>1k/sec with binary search)
                self.print_test("Book lookup speed", True, 
                    f"{rate:.0f} lookups/sec")
                tests_passed += 1
            else:
                tests_failed.append("Book lookup speed")
                self.print_test("Book lookup speed", False, 
                    f"Too slow: {rate:.0f} lookups/sec")
        except Exception as e:
            tests_failed.append("Book lookup speed")
            self.print_test("Book lookup speed", False, f"Exception: {e}")
        
        # Test 3: Memory usage (basic check)
        try:
            import sys
            from opening_book import get_default_book
            book = get_default_book()
            size_bytes = sys.getsizeof(book.entries) if book else 0
            size_mb = size_bytes / (1024 * 1024)
            
            # Book should be reasonably sized (< 10MB for 163k entries)
            if size_mb < 10:
                self.print_test("Memory usage", True, f"{size_mb:.2f} MB")
                tests_passed += 1
            else:
                tests_failed.append("Memory usage")
                self.print_test("Memory usage", False, f"Too large: {size_mb:.2f} MB")
        except Exception as e:
            tests_failed.append("Memory usage")
            self.print_test("Memory usage", False, f"Exception: {e}")
        
        total = 3
        print(f"\n📊 Performance: {tests_passed}/{total} passed")
        self.results['performance'] = (tests_passed, total, tests_failed)
        return len(tests_failed) == 0
    
    # ========================================================================
    # SECTION 5: THREAD SAFETY
    # ========================================================================
    
    def test_thread_safety(self):
        """Test concurrent access to opening book"""
        self.print_section("5. THREAD SAFETY TESTS")
        
        tests_passed = 0
        tests_failed = []
        
        # Test 1: Concurrent reads
        try:
            positions = [
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            ] * 100  # 300 total lookups
            
            def lookup_position(fen):
                board = ChessBoard()
                board.setup_from_fen(fen)
                return probe_book(board)
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(lookup_position, fen) for fen in positions]
                results = [f.result() for f in as_completed(futures)]
            
            # All lookups should complete without exception
            self.print_test("Concurrent book lookups", True, 
                f"{len(results)} lookups completed")
            tests_passed += 1
            
        except Exception as e:
            tests_failed.append("Concurrent book lookups")
            self.print_test("Concurrent book lookups", False, f"Exception: {e}")
        
        # Test 2: Concurrent hash computations
        try:
            def compute_hash_random():
                board = ChessBoard()
                fen = random.choice([
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                ])
                board.setup_from_fen(fen)
                return PolyglotZobrist.compute_hash(board)
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(compute_hash_random) for _ in range(1000)]
                results = [f.result() for f in as_completed(futures)]
            
            self.print_test("Concurrent hash computation", True, 
                f"{len(results)} hashes computed")
            tests_passed += 1
            
        except Exception as e:
            tests_failed.append("Concurrent hash computation")
            self.print_test("Concurrent hash computation", False, f"Exception: {e}")
        
        total = 2
        print(f"\n📊 Thread Safety: {tests_passed}/{total} passed")
        self.results['thread_safety'] = (tests_passed, total, tests_failed)
        return len(tests_failed) == 0
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    
    def print_final_summary(self):
        """Print comprehensive summary of all tests"""
        self.print_section("FINAL VALIDATION SUMMARY")
        
        total_passed = 0
        total_tests = 0
        all_failed = []
        
        for category, (passed, total, failed) in self.results.items():
            total_passed += passed
            total_tests += total
            all_failed.extend(failed)
            
            status = "✅" if passed == total else "⚠️"
            percentage = (passed / total * 100) if total > 0 else 0
            print(f"{status} {category.replace('_', ' ').title()}: {passed}/{total} ({percentage:.1f}%)")
        
        print("\n" + "-" * 80)
        percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"OVERALL: {total_passed}/{total_tests} tests passed ({percentage:.1f}%)")
        
        if len(all_failed) == 0:
            print("\n🎉 ALL TESTS PASSED! Opening book is production-ready.")
            return True
        else:
            print(f"\n⚠️  {len(all_failed)} test(s) failed:")
            for test_name in all_failed:
                print(f"   - {test_name}")
            return False
    
    def run_all(self):
        """Run complete validation suite"""
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + " " * 20 + "OPENING BOOK VALIDATION SUITE" + " " * 29 + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
        
        self.test_hash_correctness()
        self.test_move_legality()
        self.test_edge_cases()
        self.test_performance()
        self.test_thread_safety()
        
        return self.print_final_summary()


def main():
    validator = ValidationSuite()
    success = validator.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
