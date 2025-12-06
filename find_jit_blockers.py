#!/usr/bin/env python
"""
Systematic check for known PyPy JIT blockers in our codebase.

Known JIT blockers:
1. Large functions (>200-300 lines)
2. Complex functions (>100-150 branches)
3. Try/except in hot loops
4. Frame introspection (sys._getframe, inspect module)
5. eval/exec
6. Too many instance variables (>50)
7. Deeply nested loops (>4 levels)
8. String formatting in loops
9. Large constant dictionaries
10. Attribute lookups in tight loops
"""
import sys
import os
import ast
import inspect

print("="*80)
print("SYSTEMATIC JIT BLOCKER DETECTION")
print("="*80)

def count_lines(func):
    """Count lines in a function."""
    try:
        source = inspect.getsource(func)
        return len([l for l in source.split('\n') if l.strip() and not l.strip().startswith('#')])
    except:
        return 0

def analyze_function_ast(func):
    """Analyze function AST for complexity."""
    try:
        source = inspect.getsource(func)
        tree = ast.parse(source)
        
        # Count different node types
        branches = 0
        loops = 0
        try_except = 0
        dict_lookups = 0
        attr_lookups = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp)):
                branches += 1
            elif isinstance(node, (ast.For, ast.While)):
                loops += 1
            elif isinstance(node, ast.Try):
                try_except += 1
            elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                dict_lookups += 1
            elif isinstance(node, ast.Attribute):
                attr_lookups += 1
        
        return {
            'branches': branches,
            'loops': loops,
            'try_except': try_except,
            'dict_lookups': dict_lookups,
            'attr_lookups': attr_lookups
        }
    except:
        return None

print("\n1. Checking evaluation.py")
print("-" * 80)

from src.evaluation import Evaluator

evaluator = Evaluator()

# Check Evaluator.evaluate
lines = count_lines(evaluator.evaluate)
print(f"Evaluator.evaluate: {lines} lines")
if lines > 200:
    print(f"  ⚠️  WARNING: >200 lines may block JIT compilation")

ast_info = analyze_function_ast(evaluator.evaluate)
if ast_info:
    print(f"  Branches: {ast_info['branches']}")
    print(f"  Loops: {ast_info['loops']}")
    print(f"  Try/except: {ast_info['try_except']}")
    print(f"  Dict lookups: {ast_info['dict_lookups']}")
    print(f"  Attr lookups: {ast_info['attr_lookups']}")
    
    if ast_info['branches'] > 100:
        print(f"  ⚠️  WARNING: >{ast_info['branches']} branches may block JIT")
    if ast_info['attr_lookups'] > 50:
        print(f"  ⚠️  WARNING: {ast_info['attr_lookups']} attribute lookups in hot path")

# Check helper methods
print("\nHelper methods:")
for method_name in ['_evaluate_material', '_evaluate_psqt', '_calculate_phase', '_evaluate_pawn_structure']:
    try:
        method = getattr(evaluator, method_name)
        lines = count_lines(method)
        print(f"  {method_name}: {lines} lines")
        if lines > 150:
            print(f"    ⚠️  WARNING: May be too large for JIT")
    except:
        pass

print("\n2. Checking search.py")
print("-" * 80)

from src.search import alpha_beta, quiescence

# Check alpha_beta
lines = count_lines(alpha_beta)
print(f"alpha_beta: {lines} lines")
if lines > 200:
    print(f"  ⚠️  WARNING: {lines} lines may block JIT compilation")

ast_info = analyze_function_ast(alpha_beta)
if ast_info:
    print(f"  Branches: {ast_info['branches']}")
    print(f"  Loops: {ast_info['loops']}")
    if ast_info['branches'] > 100:
        print(f"  ⚠️  WARNING: Too many branches may block JIT")

# Check quiescence
lines = count_lines(quiescence)
print(f"\nquiescence: {lines} lines")
if lines > 200:
    print(f"  ⚠️  WARNING: {lines} lines may block JIT compilation")

print("\n3. Checking move_generation.py")
print("-" * 80)

from src.chess_engine import ChessBoard

board = ChessBoard()

# Check generate_moves
lines = count_lines(board.generate_moves)
print(f"ChessBoard.generate_moves: {lines} lines")
if lines > 200:
    print(f"  ⚠️  WARNING: May block JIT")

print("\n4. Checking for specific blockers")
print("-" * 80)

# Check evaluation.py source for known blockers
eval_source = inspect.getsource(Evaluator)

checks = [
    ('eval() or exec()', 'eval(' in eval_source or 'exec(' in eval_source),
    ('sys._getframe', 'sys._getframe' in eval_source or 'inspect.currentframe' in eval_source),
    ('Too many instance vars', len([l for l in eval_source.split('\n') if 'self.' in l and '=' in l]) > 50),
]

for name, has_blocker in checks:
    if has_blocker:
        print(f"  ❌ FOUND: {name}")
    else:
        print(f"  ✅ OK: No {name}")

print("\n5. Checking MATERIAL_VALUES usage")
print("-" * 80)

# This is a critical check - dict lookups in hot loops
from src.evaluation import MATERIAL_VALUES

print(f"MATERIAL_VALUES type: {type(MATERIAL_VALUES)}")
print(f"MATERIAL_VALUES: {MATERIAL_VALUES}")

if isinstance(MATERIAL_VALUES, dict):
    print("  ⚠️  WARNING: Dictionary used for material values")
    print("  Recommendation: Use array/tuple for constant lookups")
else:
    print("  ✅ OK: Not a dictionary")

print("\n6. File-level analysis")
print("-" * 80)

files_to_check = [
    'src/evaluation.py',
    'src/search.py', 
    'src/move_generation.py',
    'src/chess_engine.py'
]

for filepath in files_to_check:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = len(content.split('\n'))
            
        # Count functions
        tree = ast.parse(content)
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        print(f"\n{filepath}:")
        print(f"  Total lines: {lines}")
        print(f"  Functions: {len(functions)}")
        print(f"  Classes: {len(classes)}")
        
        # Find largest functions
        large_funcs = []
        for func in functions:
            func_lines = func.end_lineno - func.lineno if hasattr(func, 'end_lineno') else 0
            if func_lines > 150:
                large_funcs.append((func.name, func_lines))
        
        if large_funcs:
            print(f"  ⚠️  Large functions (>150 lines):")
            for name, size in sorted(large_funcs, key=lambda x: -x[1])[:5]:
                print(f"    - {name}: {size} lines")
    except Exception as e:
        print(f"\n{filepath}: Error analyzing - {e}")

print("\n" + "="*80)
print("SUMMARY & RECOMMENDATIONS")
print("="*80)

print("""
Based on the analysis above, the likely JIT blockers are:

1. If Evaluator.evaluate has >50 attribute lookups:
   → Move constants to module level
   → Use local variables for repeated lookups

2. If _evaluate_material uses MATERIAL_VALUES dict:
   → Replace with array indexing
   → Use: MATERIAL_VALUES = [0, 100, 320, 330, 500, 900, 0]

3. If any function >200 lines:
   → Split into smaller functions (<100 lines each)
   → Extract helper functions

4. If many branches in evaluate():
   → Simplify conditionals
   → Use lookup tables instead of if/elif chains

Run this script and share the output to identify the exact blockers!
""")
