from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="PiperLove API", version="1.0.0")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://wwwtriplew.me"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MoveRequest(BaseModel):
    fen: str
    ai_thinking_ms: int


class MoveResponse(BaseModel):
    move: str


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/move", response_model=MoveResponse)
async def move(request: MoveRequest):
    """
    Move endpoint that accepts FEN position and AI thinking time.
    Currently returns a placeholder move.
    """
    # For now, return a placeholder move
    return {"move": "e2e4"}
