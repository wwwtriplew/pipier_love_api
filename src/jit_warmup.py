"""
PyPy JIT Warmup Module

Problem: PyPy JIT needs ~20-30 function calls to compile hot loops.
When browser makes a chess move, the first search is SLOW (5-8k NPS)
because JIT hasn't warmed up yet.

Solution: Warm up the JIT at startup by running perft operations.
This pre-compiles all hot loops so real requests are FAST.
"""

import time
from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb

def warmup_jit():
    """
    Warm up PyPy JIT by exercising all hot code paths.
    Run this at application startup.
    """
    print("🔥 Warming up PyPy JIT...")
    start = time.time()
    
    board = ChessBoard()
    
    # Simple perft to warm up move generation
    def perft(board, depth):
        if depth == 0:
            return 1
        
        nodes = 0
        for from_sq, to_sq, promo in board.generate_moves():
            board.make_move(from_sq, to_sq, promo)
            king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])  # KING=5
            if not board.is_square_attacked(king_sq, board.side_to_move):
                nodes += perft(board, depth - 1)
            board.unmake_move()
        return nodes
    
    # Warmup iterations - force JIT compilation
    print("  Running warmup iterations...")
    for i in range(25):
        perft(board, 2)  # Depth 2 = 400 nodes, fast but exercises all code paths
        if i % 5 == 0:
            print(f"    Iteration {i+1}/25...")
    
    # Test final performance
    print("  Testing post-warmup performance...")
    test_start = time.time()
    nodes = perft(board, 3)
    test_time = time.time() - test_start
    nps = int(nodes / test_time)
    
    elapsed = time.time() - start
    print(f"✓ JIT warmup complete in {elapsed:.1f}s")
    print(f"  Post-warmup NPS: {nps:,}")
    
    if nps < 15000:
        print("  ⚠️ WARNING: NPS still low! JIT might not be working properly.")
    elif nps < 50000:
        print("  ⚠️ JIT partially working but suboptimal.")
    else:
        print("  ✓ JIT is working well!")
    
    return nps

if __name__ == "__main__":
    # Test warmup
    warmup_jit()
