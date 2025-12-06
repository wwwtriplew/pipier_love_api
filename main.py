from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import sys
import os
import time

from src.chess_engine import ChessBoard
from src.evaluation import Evaluator
from src.search import (
    MoveOrderer, SearchStats, iterative_deepening,
    move_to_uci
)
from src.opening_book import probe_book
from src.jit_warmup import warmup_jit

# ========================================
# PYPY JIT WARMUP (Critical for Performance)
# ========================================
# PyPy JIT needs ~25 iterations to compile hot loops.
# Without warmup, first request is SLOW (5-8k NPS).
# With warmup, all requests are FAST (50k-200k+ NPS).
try:
    import __pypy__  # type: ignore[import-not-found]
    # Running under PyPy - warm up the JIT
    print("🔥 Detected PyPy - running JIT warmup...")
    warmup_nps = warmup_jit()
    print(f"✓ PyPy JIT warmed up - ready for {warmup_nps:,} NPS")
except ImportError:
    # Running under CPython - no warmup needed
    print("ℹ️  Running under CPython (no JIT warmup needed)")

# Maximum search depth
MAX_DEPTH = 50  # Iterative deepening will stop at time limit anyway

# Initialize engine components (reuse across requests for performance)
# NOTE: Evaluator is stateless and can be shared across requests
# MoveOrderer is created per request (maintains killers/history per search)
evaluator = Evaluator()
# NOTE: TT was removed after testing showed +26.7% performance improvement
# at production depth (4-5). Zobrist hashing is retained for repetition detection.

app = FastAPI(
    title="Piper Love Chess Engine API",
    version="1.0.0",
    description="High-performance chess engine API for move calculation"
)

# CORS middleware configuration
# For production: Only allow your domain
# For development: Add localhost ports explicitly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://wwwtriplew.me",
        "https://www.wwwtriplew.me",
        "https://pipier-love-api.vercel.app",  # Vercel API domain
        "http://localhost:3000",  # Common React dev port
        "http://localhost:5173",  # Common Vite dev port
        "http://localhost:8080",  # Common Vue dev port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],  # Only allow needed methods
    allow_headers=["*"],
)


class MoveRequest(BaseModel):
    fen: str = Field(..., description="FEN position string")
    ai_thinking_ms: int = Field(default=1000, ge=100, le=30000, description="Thinking time in milliseconds (100-30000)")


class MoveResponse(BaseModel):
    move: str = Field(..., description="Best move in UCI format (e.g., 'e2e4', 'e7e8q')")
    score: int = Field(..., description="Evaluation score in centipawns")
    depth: int = Field(..., description="Search depth completed")
    nodes: int = Field(..., description="Total nodes searched")
    nps: int = Field(..., description="Nodes per second")
    time_ms: int = Field(..., description="Actual time taken in milliseconds")
    pv: Optional[str] = Field(None, description="Principal variation (best line)")


@app.get("/")
async def root():
    """API root - returns basic info"""
    return {
        "name": "Piper Love Chess Engine",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/move": "Calculate best move (POST)"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "engine": "ready"}


@app.post("/move", response_model=MoveResponse)
async def calculate_move(request: MoveRequest):
    """
    Calculate the best chess move for a given position.
    
    - **fen**: FEN position string (e.g., "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    - **ai_thinking_ms**: Time to think in milliseconds (100-30000, default 1000)
    
    Returns the best move with evaluation details.
    """
    try:
        # Setup board from FEN
        board = ChessBoard()
        board.setup_from_fen(request.fen)
        
        # Check if game is already over
        moves = list(board.generate_moves())
        if len(moves) == 0:
            raise HTTPException(
                status_code=400,
                detail="No legal moves available (checkmate or stalemate)"
            )
        
        # ========================================
        # OPENING BOOK PROBE (fast path)
        # ========================================
        # Check custom book up to move 20 (deeper preparation lines)
        # Then fallback to baron30.bin or search
        book_move = None
        if board.fullmove_number <= 20:
            # Try opening book first - instant response if position is in book
            # This avoids expensive search for known opening positions
            book_move = probe_book(board, randomize=True)
        
        if book_move is not None:
            # Found move in opening book - return immediately
            from_sq, to_sq, promo = book_move
            move_uci = move_to_uci(book_move)
            
            # Return book move with minimal stats (instant response)
            return MoveResponse(
                move=move_uci,
                score=0,  # Book moves don't have evaluation
                depth=0,  # Book move, not searched
                nodes=0,  # No nodes searched
                nps=0,    # Instant response
                time_ms=0,  # < 1ms typically
                pv=move_uci  # Single move from book
            )
        
        # ========================================
        # FULL SEARCH (if not in opening book or tablebase)
        # ========================================
        # Initialize search components
        stats = SearchStats()
        # NO TT: Tests show +26.7% performance improvement at depth 4-5 (12s searches)
        # Zobrist hashing is kept for repetition detection
        orderer = MoveOrderer()  # Fresh move orderer per request
        
        # Run iterative deepening search
        # Note: repetition_stack is created internally by iterative_deepening
        best_move, best_score, pv_line = iterative_deepening(
            board=board,
            max_time_ms=request.ai_thinking_ms,
            max_depth=MAX_DEPTH,
            evaluator=evaluator,
            tt=None,  # TT removed: +26.7% faster at production depth
            orderer=orderer,
            stats=stats
        )
        
        if best_move is None:
            # Fallback to first legal move if search fails
            best_move = moves[0]
            best_score = 0
            pv_line = [best_move]
        
        # Convert move to UCI format
        from_sq, to_sq, promo = best_move
        move_uci = move_to_uci(best_move)
        
        # Build PV string
        pv_str = " ".join([move_to_uci(m) for m in pv_line]) if pv_line else move_uci
        
        # Calculate elapsed time
        elapsed_ms = int((time.time() - stats.start_time) * 1000) if stats.start_time > 0 else 0
        
        return MoveResponse(
            move=move_uci,
            score=best_score,
            depth=MAX_DEPTH,  # Placeholder - real depth tracked by iterative deepening
            nodes=stats.nodes,
            nps=stats.nps(),
            time_ms=elapsed_ms,
            pv=pv_str
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine error: {str(e)}")
