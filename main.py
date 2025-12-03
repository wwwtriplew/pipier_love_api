from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chess_engine import ChessBoard
from evaluation import Evaluator
from search import (
    TranspositionTable, MoveOrderer, SearchStats, iterative_deepening,
    move_to_uci
)

# Maximum search depth
MAX_DEPTH = 50  # Iterative deepening will stop at time limit anyway

# Initialize engine components (reuse across requests for performance)
# NOTE: Evaluator and MoveOrderer are stateless and can be shared
evaluator = Evaluator()
# WARNING: Do NOT share TranspositionTable between requests!
# Each request creates its own TT to avoid:
# 1. Race conditions (API is async)
# 2. Cache pollution (different games in TT)
# 3. Incorrect moves from hash collisions

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
        
        # Initialize search components
        stats = SearchStats()
        # Create fresh TT for this request (avoid cache pollution)
        tt = TranspositionTable(size_mb=128)  # 128MB per request
        orderer = MoveOrderer()  # Fresh move orderer per request
        
        # Build repetition stack (empty for now - would need game history)
        # TODO: Accept move history in API request for proper repetition detection
        repetition_stack = []
        
        # Run iterative deepening search
        best_move, best_score, pv_line = iterative_deepening(
            board=board,
            max_time_ms=request.ai_thinking_ms,
            max_depth=MAX_DEPTH,
            evaluator=evaluator,
            tt=tt,
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
