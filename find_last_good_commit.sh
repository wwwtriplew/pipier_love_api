#!/bin/bash
# Find the last good commit by testing git history

cd /root/pipier_love_api

echo "=========================================="
echo "GIT HISTORY SEARCH - Finding Last Good Commit"
echo "=========================================="
echo ""

echo "Recent commits:"
git log --oneline -10
echo ""

# Get list of recent commits
commits=$(git log --oneline -10 | awk '{print $1}')

echo "Testing each commit to find when performance broke..."
echo ""

# Test function
test_commit() {
    local commit=$1
    
    git checkout -q $commit 2>/dev/null
    
    # Clear cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Test performance
    nps=$(/root/venv/bin/python3 -c "
from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb
import time

board = ChessBoard()

def perft(b, d):
    if d == 0: return 1
    n = 0
    for f, t, p in b.generate_moves():
        b.make_move(f, t, p)
        k = get_lsb(b.pieces[1-b.side_to_move][5])
        if not b.is_square_attacked(k, b.side_to_move):
            n += perft(b, d-1)
        b.unmake_move()
    return n

for _ in range(500):
    perft(board, 2)

start = time.time()
nodes = perft(board, 3)
elapsed = time.time() - start
print(int(nodes/elapsed))
" 2>/dev/null)
    
    echo "$nps"
}

echo "Commit    NPS      Status"
echo "----------------------------------------"

for commit in $commits; do
    nps=$(test_commit $commit)
    
    if [ -z "$nps" ]; then
        status="ERROR"
    elif [ "$nps" -gt 40000 ]; then
        status="✓ GOOD"
    elif [ "$nps" -gt 20000 ]; then
        status="⚠ SLOW"
    else
        status="✗ BROKEN"
    fi
    
    printf "%-9s %-8s %s\n" "$commit" "${nps:-N/A}" "$status"
    
    # If we found a good commit, note it
    if [ "$nps" -gt 40000 ]; then
        echo ""
        echo "Found good commit: $commit with ${nps} NPS"
        echo "To revert to this commit, run:"
        echo "  git reset --hard $commit"
        echo ""
        break
    fi
done

# Return to main branch
git checkout -q main
echo ""
echo "Returned to main branch"
