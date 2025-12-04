from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import sys
import os
import time
import chess
import chess.syzygy

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chess_engine import ChessBoard
from evaluation import Evaluator
from search import (
    TranspositionTable, MoveOrderer, SearchStats, iterative_deepening,
    move_to_uci
)
from opening_book import probe_book

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

# ========================================
# SYZYGY ENDGAME TABLEBASE (optional)
# ========================================
# Load Syzygy tablebases if available (perfect endgame play)
# Graceful fallback: engine works normally if tablebases not found
tablebase = None
tablebase_path = os.environ.get('TABLEBASE_PATH', '/root/syzygy')

try:
    if os.path.exists(tablebase_path) and os.path.isdir(tablebase_path):
        tablebase = chess.syzygy.open_tablebase(tablebase_path)
        print(f"✅ Syzygy tablebases loaded from: {tablebase_path}")
    else:
        print(f"⚪ Syzygy tablebases not found at: {tablebase_path}")
        print(f"   Engine will work normally without tablebases")
except Exception as e:
    print(f"⚠️  Failed to load tablebases: {e}")
    print(f"   Engine will work normally without tablebases")
    tablebase = None

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
        # Only check opening book in early game (moves 1-13)
        # After move 13, positions are rarely in book and checking wastes time
        book_move = None
        if board.fullmove_number <= 13:
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
        # SYZYGY TABLEBASE PROBE (endgame fast path)
        # ========================================
        # If position has ≤5 pieces and tablebases loaded, probe for perfect play
        # Safety: Multiple fallback layers ensure engine never crashes
        if tablebase is not None:
            try:
                # Convert our board to python-chess board for tablebase probe
                chess_board = chess.Board(request.fen)
                piece_count = len(chess_board.piece_map())
                
                # Only probe if position has ≤5 pieces (3-4-5 piece tables)
                if piece_count <= 5 and not chess_board.is_checkmate() and not chess_board.is_stalemate():
                    # Probe tablebase for WDL (Win/Draw/Loss)
                    wdl = tablebase.probe_wdl(chess_board)
                    
                    # If tablebase has result, find best move
                    if wdl is not None:
                        best_tb_move = None
                        best_tb_wdl = -3  # Worst possible
                        
                        # Try all legal moves to find one that maintains/improves WDL
                        for move in chess_board.legal_moves:
                            chess_board.push(move)
                            try:
                                # Get WDL after this move (negated for opponent)
                                next_wdl = -tablebase.probe_wdl(chess_board)
                                if next_wdl > best_tb_wdl:
                                    best_tb_wdl = next_wdl
                                    best_tb_move = move
                            except:
                                pass  # Move leads to position not in tablebase
                            finally:
                                chess_board.pop()
                        
                        # If we found a tablebase move, return it
                        if best_tb_move is not None:
                            move_uci = best_tb_move.uci()
                            # Convert WDL to centipawns
                            # Use best_tb_wdl (the WDL after our move) not wdl (before move)
                            # WDL values: 2=Win, 1=CursedWin, 0=Draw, -1=BlessedLoss, -2=Loss
                            tb_score = best_tb_wdl * 10000  # ±20000 for win/loss, 0 for draw
                            
                            return MoveResponse(
                                move=move_uci,
                                score=tb_score,
                                depth=0,  # Tablebase = perfect depth
                                nodes=0,  # No search needed
                                nps=0,    # Instant
                                time_ms=0,
                                pv=move_uci + " (Tablebase)"
                            )
            except KeyboardInterrupt:
                raise  # Always allow Ctrl+C
            except Exception as e:
                # Tablebase probe failed - gracefully fall through to normal search
                # This ensures engine never crashes due to tablebase issues
                print(f"⚠️  Tablebase probe failed: {e}")
                pass
        
        # ========================================
        # FULL SEARCH (if not in opening book or tablebase)
        # ========================================
        # Initialize search components
        stats = SearchStats()
        # Create fresh TT for this request (avoid cache pollution)
        tt = TranspositionTable(size_mb=1024)  # 1GB per request (VPS has 2.5GB RAM)
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
