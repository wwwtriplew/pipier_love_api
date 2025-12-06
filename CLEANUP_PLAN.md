# Cleanup Plan - Remove Outdated Files

## Files to DELETE

### Diagnostic Scripts (28 files - all outdated)
```
scripts/check_git_history.sh
scripts/check_original_performance.sh
scripts/check_venv_python.sh
scripts/check_vps_pypy.sh
scripts/check_which_python_running.sh
scripts/clean_restart.sh
scripts/compare_venv_system.sh
scripts/comprehensive_validation.py
scripts/deep_diagnostic.py
scripts/deep_jit_investigation.sh
scripts/deep_validation.py
scripts/diagnose_pypy_slow.sh
scripts/diagnose_python_chess.sh
scripts/diagnostic.py
scripts/dig_history.py
scripts/final_safety_check.py
scripts/find_jit_blocker.sh
scripts/find_last_good_commit.sh
scripts/find_optimal_warmup.sh
scripts/find_the_difference.sh
scripts/fix_pypy_jit_disabled.sh
scripts/fix_venv_pypy.sh
scripts/install_official_pypy.sh
scripts/install_pypy.sh
scripts/investigate_real_problem.sh
scripts/quick_install_and_test.sh
scripts/reproduce_exact_test.sh
scripts/search_history.sh
scripts/switch_to_pypy.sh
scripts/test_jit_warmup.sh
scripts/test_no_dispatch.sh
scripts/test_pypy_optimizations.sh
scripts/test_vps_performance.sh
scripts/test_with_pypy.sh
scripts/validate_fix.py
scripts/verify_changes_safe.sh
```

### Outdated Documentation (25 files)
```
docs/BUG_FIX_ILLEGAL_MOVES.md
docs/CHANGES_SUMMARY.md
docs/CLEANUP_LOG.md
docs/DEPLOY.md
docs/DEPLOYMENT_CHECKLIST.md
docs/EN_PASSANT_BUG_FIX.md
docs/FIX_SUMMARY.md
docs/FRONTEND_ANALYSIS.md
docs/FRONTEND_MIGRATION_PR.md
docs/IMPLEMENTATION_SUMMARY.md
docs/OPTIMIZATION_SUMMARY.md
docs/PERFORMANCE_FIX.md
docs/PYPY_DEEP_ANALYSIS.md
docs/PYPY_JIT_OPTIMIZATION.md
docs/PYPY_QUICKSTART.md
docs/PYPY_SETUP.md
docs/REAL_DIAGNOSIS.md
docs/REAL_ROOT_CAUSE_INVESTIGATION.md
docs/RESTORE_WORKING_VERSION.md
docs/SOLUTION_JIT_DISABLED.md
docs/VPS_DEPLOYMENT_GUIDE.md
docs/VPS_FIX_GUIDE.md
docs/VPS_PERFORMANCE_ISSUE.md
docs/VPS_PYPY_GUIDE.md
docs/ZOBRIST_HASH_ANALYSIS.md
```

### Outdated Test Files
```
tests/test_api_book.py (if redundant)
tests/test_api_final.py (if redundant)
```

## Files to KEEP

### Essential Scripts
```
scripts/benchmark.py - Keep and improve
scripts/proper_benchmark.py - Keep
scripts/pre_commit_test.py - Keep for CI
scripts/run_tests.sh - Keep
scripts/run_with_pypy.sh - Update
scripts/quick_check.py - Keep, simplify
scripts/quick_test.py - Keep, simplify
```

### Essential Documentation
```
docs/OPENING_BOOK_SETUP.md - Keep
docs/START_HERE.md - Keep and update
docs/TESTING_GUIDE.md - Keep and simplify
```

### All Source Code (Keep)
```
src/*.py - All essential
tests/conftest.py
tests/perft_test.py
main.py
requirements.txt
pyproject.toml
```

## Cleanup Script

Run: `bash cleanup_repo.sh`
