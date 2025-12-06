#!/bin/bash
# Search git history for performance-related changes

cd /root/pipier_love_api

echo "=========================================="
echo "SEARCHING GIT HISTORY"
echo "=========================================="
echo ""

echo "Showing all commits (last 30):"
git log --oneline -30

echo ""
echo "=========================================="
echo "Looking for commits that mention performance/optimization:"
git log --all --grep="fast\|perf\|optim\|speed\|pypy" --oneline -20

echo ""
echo "=========================================="
echo "Major file changes in src/ (last 20 commits):"
git log --oneline --stat -20 -- src/ | grep -E "(commit|src/)" | head -40

echo ""
echo "=========================================="
echo "To test a specific old commit:"
echo "  git checkout <commit-hash>"
echo "  python3 diagnostic.py"
echo "  git checkout main"
echo ""
