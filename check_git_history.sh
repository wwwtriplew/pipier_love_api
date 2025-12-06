#!/bin/bash
# Show git history to see what changed

echo "Git log (last 5 commits):"
git log --oneline -5

echo ""
echo "=========================================="
echo "Changes in last commit:"
git show --stat HEAD

echo ""
echo "=========================================="
echo "Show actual code changes:"
git diff HEAD~1 HEAD src/chess_engine.py | head -50
