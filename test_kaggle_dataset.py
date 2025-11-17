#!/usr/bin/env python3
"""
Test Piper Love evaluation against Kaggle chess dataset.

Reads CSV file with FEN and evaluation columns, compares with Piper Love.

Usage:
    python3 test_kaggle_dataset.py ~/downloads/chessData.csv
"""

import sys
import csv
import os
from typing import List, Tuple, Optional

# Add src to path
sys.path.insert(0, 'src')

from board_state import from_fen
from evaluation import Evaluator


def read_kaggle_dataset(csv_path: str, max_positions: int = 1000) -> List[Tuple[str, int]]:
    """
    Read positions and evaluations from Kaggle CSV.
    
    Args:
        csv_path: Path to CSV file
        max_positions: Maximum positions to load
    
    Returns:
        List of (fen, evaluation_cp) tuples
    """
    positions = []
    
    print(f"Reading {csv_path}...")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Try to detect column names
            fieldnames = reader.fieldnames
            print(f"CSV columns: {fieldnames}")
            
            # Common column name variations
            fen_cols = ['FEN', 'fen', 'position', 'Position']
            eval_cols = ['Evaluation', 'evaluation', 'eval', 'score', 'Score', 'cp']
            
            fen_col = None
            eval_col = None
            
            # Find FEN column
            for col in fen_cols:
                if col in fieldnames:
                    fen_col = col
                    break
            
            # Find evaluation column
            for col in eval_cols:
                if col in fieldnames:
                    eval_col = col
                    break
            
            if not fen_col or not eval_col:
                print(f"❌ Could not detect columns automatically")
                print(f"   Available columns: {fieldnames}")
                print(f"   Please specify FEN and evaluation column names")
                return []
            
            print(f"✅ Using columns: FEN='{fen_col}', Evaluation='{eval_col}'")
            print()
            
            for i, row in enumerate(reader):
                if len(positions) >= max_positions:
                    break
                
                try:
                    fen = row[fen_col].strip()
                    eval_str = row[eval_col].strip()
                    
                    # Parse evaluation (handle different formats)
                    # Could be: "150", "+150", "#3" (mate), "M3" (mate)
                    if eval_str.startswith('#') or eval_str.startswith('M'):
                        # Mate score - skip for now (hard to compare)
                        continue
                    
                    # Remove + sign if present
                    eval_str = eval_str.replace('+', '')
                    
                    eval_cp = int(float(eval_str))
                    
                    positions.append((fen, eval_cp))
                    
                    if len(positions) % 100 == 0:
                        print(f"  Loaded {len(positions)} positions...")
                
                except (ValueError, KeyError) as e:
                    # Skip malformed rows
                    continue
        
        print(f"✅ Loaded {len(positions)} positions")
        print()
    
    except FileNotFoundError:
        print(f"❌ File not found: {csv_path}")
        print(f"   Make sure the file exists in ~/downloads/")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
    
    return positions


def compare_evaluations(dataset: List[Tuple[str, int]]):
    """
    Compare Piper Love evaluation with dataset evaluations.
    
    Args:
        dataset: List of (fen, evaluation_cp) tuples
    """
    print("=" * 70)
    print("EVALUATION COMPARISON: Piper Love vs Dataset")
    print("=" * 70)
    print()
    
    if not dataset:
        print("❌ No data to compare")
        return
    
    # Initialize evaluator
    piper = Evaluator()
    
    # Results storage
    results = []
    failed = 0
    
    print(f"Evaluating {len(dataset)} positions...")
    print()
    
    # Evaluate each position
    for i, (fen, dataset_eval) in enumerate(dataset):
        try:
            # Get Piper Love evaluation
            pos = from_fen(fen)
            board = pos._board
            piper_eval = piper.evaluate(board)
            
            # Calculate difference
            diff = abs(dataset_eval - piper_eval)
            
            results.append({
                'fen': fen,
                'dataset': dataset_eval,
                'piper': piper_eval,
                'diff': diff
            })
        
        except Exception as e:
            failed += 1
            if failed <= 5:  # Only print first few errors
                print(f"  ⚠️  Position {i+1} failed: {e}")
            continue
        
        # Print progress
        if (i + 1) % 100 == 0:
            print(f"  Evaluated {i+1}/{len(dataset)} positions...")
    
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
    dataset_evals = [r['dataset'] for r in results]
    piper_evals = [r['piper'] for r in results]
    
    mean_diff = sum(diffs) / len(diffs)
    max_diff = max(diffs)
    min_diff = min(diffs)
    median_diff = sorted(diffs)[len(diffs) // 2]
    
    # Calculate correlation (Pearson)
    n = len(results)
    mean_dataset = sum(dataset_evals) / n
    mean_piper = sum(piper_evals) / n
    
    numerator = sum((d - mean_dataset) * (p - mean_piper) 
                    for d, p in zip(dataset_evals, piper_evals))
    denom_dataset = sum((d - mean_dataset) ** 2 for d in dataset_evals) ** 0.5
    denom_piper = sum((p - mean_piper) ** 2 for p in piper_evals) ** 0.5
    
    correlation = numerator / (denom_dataset * denom_piper) if denom_dataset * denom_piper > 0 else 0
    
    # Print statistics
    print(f"Positions evaluated: {len(results)}")
    print(f"Failed positions:    {failed}")
    print()
    print(f"Mean difference:     {mean_diff:.1f} cp")
    print(f"Median difference:   {median_diff:.1f} cp")
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
    
    # Accuracy buckets
    print("Accuracy Distribution:")
    buckets = [
        ("Excellent (<50 cp)", 50),
        ("Good (50-100 cp)", 100),
        ("Fair (100-200 cp)", 200),
        ("Poor (200-500 cp)", 500),
        ("Very Poor (>500 cp)", float('inf'))
    ]
    
    for label, threshold in buckets:
        if threshold == float('inf'):
            count = sum(1 for d in diffs if d > 500)
        else:
            prev_threshold = buckets[buckets.index((label, threshold)) - 1][1] if buckets.index((label, threshold)) > 0 else 0
            count = sum(1 for d in diffs if prev_threshold < d <= threshold)
        
        percentage = count / len(diffs) * 100
        print(f"  {label:25s}: {count:4d} ({percentage:5.1f}%)")
    
    print()
    
    # Show largest deviations
    print("=" * 70)
    print("LARGEST DEVIATIONS (Top 10)")
    print("=" * 70)
    print()
    
    sorted_results = sorted(results, key=lambda r: r['diff'], reverse=True)
    
    for i, r in enumerate(sorted_results[:10]):
        print(f"{i+1}. FEN: {r['fen'][:55]}...")
        print(f"   Dataset: {r['dataset']:6d} cp")
        print(f"   Piper:   {r['piper']:6d} cp")
        print(f"   Diff:    {r['diff']:6d} cp")
        print()
    
    # Save detailed results
    output_file = 'kaggle_comparison.txt'
    with open(output_file, 'w') as f:
        f.write("Evaluation Comparison: Piper Love vs Kaggle Dataset\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Positions: {len(results)}\n")
        f.write(f"Mean diff: {mean_diff:.1f} cp\n")
        f.write(f"Median diff: {median_diff:.1f} cp\n")
        f.write(f"Correlation: {correlation:.3f}\n\n")
        
        f.write("All Results (sorted by difference):\n")
        f.write("=" * 70 + "\n\n")
        
        for r in sorted_results:
            f.write(f"FEN: {r['fen']}\n")
            f.write(f"  Dataset: {r['dataset']:6d} cp\n")
            f.write(f"  Piper:   {r['piper']:6d} cp\n")
            f.write(f"  Diff:    {r['diff']:6d} cp\n\n")
    
    print(f"📝 Detailed results saved to: {output_file}")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test against Kaggle dataset")
    parser.add_argument('csv_file', nargs='?', 
                        default='~/downloads/chessData.csv',
                        help='Path to CSV file')
    parser.add_argument('--max', type=int, default=1000,
                        help='Maximum positions to test (default: 1000)')
    
    args = parser.parse_args()
    
    # Expand ~ to home directory
    csv_path = os.path.expanduser(args.csv_file)
    
    # Read dataset
    dataset = read_kaggle_dataset(csv_path, args.max)
    
    if dataset:
        # Compare evaluations
        compare_evaluations(dataset)
    else:
        print()
        print("Usage:")
        print(f"  python3 test_kaggle_dataset.py ~/downloads/chessData.csv")
        print()
        print("CSV file should have columns like:")
        print("  - FEN (or 'fen', 'position')")
        print("  - Evaluation (or 'eval', 'score', 'cp')")
