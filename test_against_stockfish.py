#!/usr/bin/env python3
"""
Test Piper Love evaluation against Stockfish.

This script:
1. Reads positions from a PGN file (or generates test positions)
2. Evaluates each position with Stockfish
3. Evaluates each position with Piper Love
4. Compares results and calculates correlation

Usage:
    python3 test_against_stockfish.py [--pgn FILE] [--positions N] [--depth D]
"""

import sys
import os
import subprocess
import time
import random
from typing import Optional, Tuple, List

# Add src to path
sys.path.insert(0, 'src')

from board_state import Position, new_game, from_fen
from evaluation import Evaluator


class StockfishEvaluator:
    """Interface to Stockfish engine."""
    
    def __init__(self, stockfish_path: str = "stockfish", depth: int = 15):
        """
        Initialize Stockfish evaluator.
        
        Args:
            stockfish_path: Path to Stockfish binary
            depth: Search depth for evaluation
        """
        self.stockfish_path = stockfish_path
        self.depth = depth
        self.process = None
    
    def start(self):
        """Start Stockfish process."""
        try:
            self.process = subprocess.Popen(
                [self.stockfish_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            # Wait for UCI response
            self._send_command("uci")
            self._wait_for("uciok")
            self._send_command("isready")
            self._wait_for("readyok")
            print(f"✅ Stockfish started successfully")
            return True
        except FileNotFoundError:
            print(f"❌ Stockfish not found at: {self.stockfish_path}")
            print(f"   Install with: brew install stockfish")
            return False
        except Exception as e:
            print(f"❌ Failed to start Stockfish: {e}")
            return False
    
    def stop(self):
        """Stop Stockfish process."""
        if self.process:
            self._send_command("quit")
            self.process.wait()
            self.process = None
    
    def evaluate(self, fen: str) -> Optional[int]:
        """
        Evaluate position with Stockfish.
        
        Args:
            fen: FEN string
        
        Returns:
            Evaluation in centipawns (from white's perspective)
            None if evaluation fails
        """
        if not self.process:
            return None
        
        try:
            # Set position
            self._send_command(f"position fen {fen}")
            
            # Start search
            self._send_command(f"go depth {self.depth}")
            
            # Parse evaluation
            eval_cp = None
            mate_score = None
            
            while True:
                line = self.process.stdout.readline().strip()
                
                if not line:
                    continue
                
                if line.startswith("bestmove"):
                    break
                
                if "score cp" in line:
                    # Extract centipawn score
                    parts = line.split()
                    try:
                        idx = parts.index("cp")
                        eval_cp = int(parts[idx + 1])
                    except (ValueError, IndexError):
                        pass
                
                elif "score mate" in line:
                    # Extract mate score
                    parts = line.split()
                    try:
                        idx = parts.index("mate")
                        mate_in = int(parts[idx + 1])
                        # Convert mate to large score
                        if mate_in > 0:
                            mate_score = 10000 - mate_in * 10
                        else:
                            mate_score = -10000 - mate_in * 10
                    except (ValueError, IndexError):
                        pass
            
            # Return mate score if found, otherwise centipawn score
            return mate_score if mate_score is not None else eval_cp
        
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            return None
    
    def _send_command(self, cmd: str):
        """Send command to Stockfish."""
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()
    
    def _wait_for(self, text: str, timeout: float = 5.0):
        """Wait for specific text in output."""
        start = time.time()
        while time.time() - start < timeout:
            line = self.process.stdout.readline().strip()
            if text in line:
                return True
        return False


def generate_test_positions(count: int = 100) -> List[str]:
    """
    Generate test positions from random games.
    
    Args:
        count: Number of positions to generate
    
    Returns:
        List of FEN strings
    """
    positions = []
    
    # Starting position
    positions.append("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    
    print(f"Generating {count} test positions...")
    
    while len(positions) < count:
        # Play random game
        pos = new_game()
        moves_played = 0
        max_moves = random.randint(10, 40)
        
        while moves_played < max_moves and not pos.is_game_over:
            legal_moves = pos.legal_moves()
            if not legal_moves:
                break
            
            # Random move
            move = random.choice(legal_moves)
            pos.make_move(move)
            moves_played += 1
            
            # Save position every few moves
            if moves_played >= 8 and moves_played % 3 == 0:
                fen = pos.get_fen()
                if fen not in positions:
                    positions.append(fen)
                    if len(positions) >= count:
                        break
    
    print(f"✅ Generated {len(positions)} positions")
    return positions[:count]


def compare_evaluations(test_positions: List[str], stockfish_depth: int = 15):
    """
    Compare Piper Love evaluation with Stockfish.
    
    Args:
        test_positions: List of FEN strings
        stockfish_depth: Stockfish search depth
    """
    print("=" * 70)
    print("EVALUATION COMPARISON: Piper Love vs Stockfish")
    print("=" * 70)
    print()
    
    # Initialize engines
    stockfish = StockfishEvaluator(depth=stockfish_depth)
    if not stockfish.start():
        print("Cannot proceed without Stockfish.")
        print("Install with: brew install stockfish")
        return
    
    piper = Evaluator()
    
    # Results storage
    results = []
    
    print(f"Testing {len(test_positions)} positions...")
    print(f"Stockfish depth: {stockfish_depth}")
    print()
    
    # Evaluate each position
    for i, fen in enumerate(test_positions):
        # Get Stockfish evaluation
        sf_eval = stockfish.evaluate(fen)
        if sf_eval is None:
            print(f"  Position {i+1}: Stockfish evaluation failed, skipping")
            continue
        
        # Get Piper Love evaluation
        try:
            pos = from_fen(fen)
            board = pos._board
            piper_eval = piper.evaluate(board)
        except Exception as e:
            print(f"  Position {i+1}: Piper evaluation failed: {e}")
            continue
        
        # Calculate difference
        diff = abs(sf_eval - piper_eval)
        
        results.append({
            'fen': fen,
            'stockfish': sf_eval,
            'piper': piper_eval,
            'diff': diff
        })
        
        # Print progress
        if (i + 1) % 10 == 0:
            print(f"  Evaluated {i+1}/{len(test_positions)} positions...")
    
    stockfish.stop()
    
    # Analyze results
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    
    if not results:
        print("❌ No valid results")
        return
    
    # Calculate statistics
    diffs = [r['diff'] for r in results]
    mean_diff = sum(diffs) / len(diffs)
    max_diff = max(diffs)
    min_diff = min(diffs)
    
    # Calculate correlation
    sf_evals = [r['stockfish'] for r in results]
    piper_evals = [r['piper'] for r in results]
    
    # Pearson correlation
    n = len(results)
    mean_sf = sum(sf_evals) / n
    mean_piper = sum(piper_evals) / n
    
    numerator = sum((sf - mean_sf) * (p - mean_piper) for sf, p in zip(sf_evals, piper_evals))
    denom_sf = sum((sf - mean_sf) ** 2 for sf in sf_evals) ** 0.5
    denom_piper = sum((p - mean_piper) ** 2 for p in piper_evals) ** 0.5
    
    correlation = numerator / (denom_sf * denom_piper) if denom_sf * denom_piper > 0 else 0
    
    print(f"Positions evaluated: {len(results)}")
    print(f"Mean difference:     {mean_diff:.1f} cp")
    print(f"Max difference:      {max_diff:.1f} cp")
    print(f"Min difference:      {min_diff:.1f} cp")
    print(f"Correlation:         {correlation:.3f}")
    print()
    
    # Interpretation
    if correlation >= 0.8:
        print("✅ EXCELLENT: Strong correlation (≥0.8)")
    elif correlation >= 0.6:
        print("✅ GOOD: Moderate correlation (≥0.6)")
    elif correlation >= 0.4:
        print("⚠️  FAIR: Weak correlation (≥0.4)")
    else:
        print("❌ POOR: Very weak correlation (<0.4)")
    print()
    
    # Show largest deviations
    print("=" * 70)
    print("LARGEST DEVIATIONS (Top 5)")
    print("=" * 70)
    print()
    
    sorted_results = sorted(results, key=lambda r: r['diff'], reverse=True)
    
    for i, r in enumerate(sorted_results[:5]):
        print(f"{i+1}. Position: {r['fen'][:50]}...")
        print(f"   Stockfish: {r['stockfish']:6d} cp")
        print(f"   Piper:     {r['piper']:6d} cp")
        print(f"   Difference: {r['diff']:6d} cp")
        print()
    
    # Save results to file
    with open('evaluation_comparison.txt', 'w') as f:
        f.write("Evaluation Comparison: Piper Love vs Stockfish\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Positions: {len(results)}\n")
        f.write(f"Mean diff: {mean_diff:.1f} cp\n")
        f.write(f"Correlation: {correlation:.3f}\n\n")
        
        for r in sorted_results:
            f.write(f"FEN: {r['fen']}\n")
            f.write(f"  Stockfish: {r['stockfish']:6d} cp\n")
            f.write(f"  Piper:     {r['piper']:6d} cp\n")
            f.write(f"  Diff:      {r['diff']:6d} cp\n\n")
    
    print(f"📝 Detailed results saved to: evaluation_comparison.txt")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare Piper Love with Stockfish")
    parser.add_argument('--positions', type=int, default=50,
                        help='Number of test positions (default: 50)')
    parser.add_argument('--depth', type=int, default=15,
                        help='Stockfish search depth (default: 15)')
    
    args = parser.parse_args()
    
    # Generate test positions
    test_positions = generate_test_positions(args.positions)
    
    # Compare evaluations
    compare_evaluations(test_positions, args.depth)
