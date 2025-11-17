#!/usr/bin/env python3
"""
UCI Implementation Test Suite

Tests the Piper Love Chess Engine UCI implementation to ensure
it responds correctly to all UCI commands.

Usage:
    python3 test_uci.py
"""

import subprocess
import sys
import time


class UCITester:
    """Test suite for UCI protocol implementation."""
    
    def __init__(self, engine_path="uci.py"):
        """Initialize tester with path to UCI engine."""
        self.engine_path = engine_path
        self.tests_passed = 0
        self.tests_failed = 0
    
    def run_all_tests(self):
        """Run all UCI tests."""
        print("=" * 70)
        print("UCI IMPLEMENTATION TEST SUITE")
        print("=" * 70)
        print()
        
        # Run tests
        self.test_uci_init()
        self.test_isready()
        self.test_position_startpos()
        self.test_position_with_moves()
        self.test_position_fen()
        self.test_go_depth()
        self.test_display_board()
        self.test_perft()
        self.test_options()
        
        # Summary
        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Total: {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed == 0:
            print()
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print()
            print("⚠️  SOME TESTS FAILED")
            return 1
    
    def send_commands(self, commands):
        """
        Send commands to UCI engine and get response.
        
        Args:
            commands: List of command strings
        
        Returns:
            Output from engine as string
        """
        # Join commands with newlines
        input_str = "\n".join(commands) + "\n"
        
        # Run engine process
        try:
            result = subprocess.run(
                ["python3", self.engine_path],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=10  # 10 second timeout
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "ERROR: Engine timeout"
        except Exception as e:
            return f"ERROR: {e}"
    
    def check_output(self, output, expected_strings, test_name):
        """
        Check if output contains expected strings.
        
        Args:
            output: Engine output
            expected_strings: List of strings that should be in output
            test_name: Name of test for reporting
        
        Returns:
            True if all expected strings found, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"Test: {test_name}")
        print(f"{'='*70}")
        
        all_found = True
        for expected in expected_strings:
            if expected in output:
                print(f"✅ Found: '{expected}'")
            else:
                print(f"❌ Missing: '{expected}'")
                all_found = False
        
        if all_found:
            print(f"✅ TEST PASSED: {test_name}")
            self.tests_passed += 1
        else:
            print(f"❌ TEST FAILED: {test_name}")
            print(f"\nEngine output:\n{output}")
            self.tests_failed += 1
        
        return all_found
    
    def test_uci_init(self):
        """Test UCI initialization."""
        output = self.send_commands(["uci", "quit"])
        
        expected = [
            "id name Piper Love",
            "id author",
            "option name Hash",
            "uciok"
        ]
        
        self.check_output(output, expected, "UCI Initialization")
    
    def test_isready(self):
        """Test isready command."""
        output = self.send_commands(["uci", "isready", "quit"])
        
        expected = ["readyok"]
        
        self.check_output(output, expected, "IsReady Command")
    
    def test_position_startpos(self):
        """Test position startpos command."""
        output = self.send_commands([
            "uci",
            "isready",
            "position startpos",
            "d",
            "quit"
        ])
        
        expected = [
            "White to move"
        ]
        
        self.check_output(output, expected, "Position Startpos")
    
    def test_position_with_moves(self):
        """Test position with moves."""
        output = self.send_commands([
            "uci",
            "isready",
            "position startpos moves e2e4 e7e5",
            "d",
            "quit"
        ])
        
        expected = [
            "White to move"
        ]
        
        self.check_output(output, expected, "Position with Moves")
    
    def test_position_fen(self):
        """Test position from FEN."""
        output = self.send_commands([
            "uci",
            "isready",
            "position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            "d",
            "quit"
        ])
        
        expected = [
            "Black to move"
        ]
        
        self.check_output(output, expected, "Position from FEN")
    
    def test_go_depth(self):
        """Test go depth command."""
        output = self.send_commands([
            "uci",
            "isready",
            "position startpos",
            "go depth 1",
            "quit"
        ])
        
        expected = [
            "info depth 1",
            "bestmove"
        ]
        
        self.check_output(output, expected, "Go Depth Command")
    
    def test_display_board(self):
        """Test display board command."""
        output = self.send_commands([
            "uci",
            "isready",
            "position startpos",
            "d",
            "quit"
        ])
        
        expected = [
            "Current position",
            "a b c d e f g h",
            "White to move"
        ]
        
        self.check_output(output, expected, "Display Board")
    
    def test_perft(self):
        """Test perft command."""
        output = self.send_commands([
            "uci",
            "isready",
            "position startpos",
            "perft 3",
            "quit"
        ])
        
        expected = [
            "Running perft(3)",
            "Nodes: 8,902"
        ]
        
        self.check_output(output, expected, "Perft Command")
    
    def test_options(self):
        """Test setoption command."""
        output = self.send_commands([
            "uci",
            "isready",
            "debug on",
            "setoption name Hash value 256",
            "setoption name Threads value 4",
            "quit"
        ])
        
        expected = [
            "Hash size set to 256",
            "Threads set to 4"
        ]
        
        self.check_output(output, expected, "Set Options")


def main():
    """Main test runner."""
    tester = UCITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
