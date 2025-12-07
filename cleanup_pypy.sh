#!/bin/bash
# Cleanup PyPy-specific files (optional)
# Run this AFTER switching to CPython and verifying it works

echo "PyPy File Cleanup Script"
echo "========================"
echo ""
echo "This will remove PyPy-specific test and diagnostic files."
echo "These files are NOT used in production."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "Removing PyPy-specific files..."

# Core PyPy module (no longer used)
rm -f src/jit_warmup.py && echo "✓ Removed src/jit_warmup.py"

# PyPy test files
rm -f definitive_jit_test.py && echo "✓ Removed definitive_jit_test.py"
rm -f start_with_jit.py && echo "✓ Removed start_with_jit.py"
rm -f deep_jit_investigation.py && echo "✓ Removed deep_jit_investigation.py"
rm -f check_jit_compilation.py && echo "✓ Removed check_jit_compilation.py"
rm -f show_jit_compilation.py && echo "✓ Removed show_jit_compilation.py"
rm -f find_jit_blocker.py && echo "✓ Removed find_jit_blocker.py"
rm -f find_jit_blockers.py && echo "✓ Removed find_jit_blockers.py"
rm -f diagnose_pypy_jit.py && echo "✓ Removed diagnose_pypy_jit.py"

# Comparison test files
rm -f test_cpython_vs_pypy.py && echo "✓ Removed test_cpython_vs_pypy.py"
rm -f test_dict_vs_array.py && echo "✓ Removed test_dict_vs_array.py"

# VPS diagnostic (imports jit_warmup)
rm -f vps_diagnostic.py && echo "✓ Removed vps_diagnostic.py"

# Scripts
rm -f scripts/verify_jit_problem.py && echo "✓ Removed scripts/verify_jit_problem.py"

echo ""
echo "Cleanup complete!"
echo ""
echo "Files removed: PyPy warmup module + 12 test/diagnostic files"
echo "Production code unchanged."
echo ""
