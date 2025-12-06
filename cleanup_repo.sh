#!/bin/bash
# Cleanup Script - Remove Outdated Diagnostic Files

set -e

echo "🧹 Cleaning up outdated files..."
echo ""

# Remove outdated docs
echo "Removing outdated documentation..."
rm -f docs/BUG_FIX_ILLEGAL_MOVES.md
rm -f docs/CHANGES_SUMMARY.md
rm -f docs/CLEANUP_LOG.md
rm -f docs/DEPLOY.md
rm -f docs/DEPLOYMENT_CHECKLIST.md
rm -f docs/EN_PASSANT_BUG_FIX.md
rm -f docs/FIX_SUMMARY.md
rm -f docs/FRONTEND_ANALYSIS.md
rm -f docs/FRONTEND_MIGRATION_PR.md
rm -f docs/IMPLEMENTATION_SUMMARY.md
rm -f docs/OPTIMIZATION_SUMMARY.md
rm -f docs/PERFORMANCE_FIX.md
rm -f docs/PYPY_DEEP_ANALYSIS.md
rm -f docs/PYPY_JIT_OPTIMIZATION.md
rm -f docs/PYPY_QUICKSTART.md
rm -f docs/PYPY_SETUP.md
rm -f docs/REAL_DIAGNOSIS.md
rm -f docs/REAL_ROOT_CAUSE_INVESTIGATION.md
rm -f docs/RESTORE_WORKING_VERSION.md
rm -f docs/SOLUTION_JIT_DISABLED.md
rm -f docs/VPS_DEPLOYMENT_GUIDE.md
rm -f docs/VPS_FIX_GUIDE.md
rm -f docs/VPS_PERFORMANCE_ISSUE.md
rm -f docs/VPS_PYPY_GUIDE.md
rm -f docs/ZOBRIST_HASH_ANALYSIS.md

# Remove outdated scripts
echo "Removing outdated diagnostic scripts..."
rm -f scripts/check_git_history.sh
rm -f scripts/check_original_performance.sh
rm -f scripts/check_venv_python.sh
rm -f scripts/check_vps_pypy.sh
rm -f scripts/check_which_python_running.sh
rm -f scripts/clean_restart.sh
rm -f scripts/compare_venv_system.sh
rm -f scripts/comprehensive_validation.py
rm -f scripts/deep_diagnostic.py
rm -f scripts/deep_jit_investigation.sh
rm -f scripts/deep_validation.py
rm -f scripts/diagnose_pypy_slow.sh
rm -f scripts/diagnose_python_chess.sh
rm -f scripts/diagnostic.py
rm -f scripts/dig_history.py
rm -f scripts/final_safety_check.py
rm -f scripts/find_jit_blocker.sh
rm -f scripts/find_last_good_commit.sh
rm -f scripts/find_optimal_warmup.sh
rm -f scripts/find_the_difference.sh
rm -f scripts/fix_pypy_jit_disabled.sh
rm -f scripts/fix_venv_pypy.sh
rm -f scripts/install_official_pypy.sh
rm -f scripts/install_pypy.sh
rm -f scripts/investigate_real_problem.sh
rm -f scripts/quick_install_and_test.sh
rm -f scripts/reproduce_exact_test.sh
rm -f scripts/search_history.sh
rm -f scripts/switch_to_pypy.sh
rm -f scripts/test_jit_warmup.sh
rm -f scripts/test_no_dispatch.sh
rm -f scripts/test_pypy_optimizations.sh
rm -f scripts/test_vps_performance.sh
rm -f scripts/test_with_pypy.sh
rm -f scripts/validate_fix.py
rm -f scripts/verify_changes_safe.sh

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Remaining files:"
echo "  Scripts: $(ls scripts/ | wc -l) files"
echo "  Docs: $(ls docs/ | wc -l) files"
echo ""
echo "Next steps:"
echo "  1. Review PERFORMANCE_DIAGNOSIS.md"
echo "  2. Run critical_tests.py"
echo "  3. Remove python-chess dependency"
echo "  4. Deploy with PyPy"
