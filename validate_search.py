#!/usr/bin/env python3
"""
Quick validation that search.py works with tt=None
"""

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import MoveOrderer, SearchStats, iterative_deepening, move_to_uci

def test_search():
    """Test that search works with tt=None"""
    print("Testing search with tt=None...")
    
    # Setup position
    board = ChessBoard()
    evaluator = Evaluator()
    stats = SearchStats()
    orderer = MoveOrderer()
    
    # Run quick search
    best_move, score, pv = iterative_deepening(
        board=board,
        max_time_ms=100,  # 100ms for quick test
        max_depth=3,
        evaluator=evaluator,
        tt=None,  # This is the key test - tt=None should work
        orderer=orderer,
        stats=stats
    )
    
    # Verify results
    assert best_move is not None, "Search should return a move"
    assert isinstance(score, int), "Score should be an integer"
    assert isinstance(pv, list), "PV should be a list"
    assert stats.nodes > 0, "Should have searched some nodes"
    
    move_str = move_to_uci(best_move)
    print(f"✓ Search successful!")
    print(f"  Best move: {move_str}")
    print(f"  Score: {score}")
    print(f"  Nodes: {stats.nodes:,}")
    print(f"  NPS: {stats.nps():,}")
    print(f"  PV length: {len(pv)}")
    
    return True

if __name__ == "__main__":
    try:
        test_search()
        print("\n✅ All tests passed! search.py is working correctly with tt=None")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
