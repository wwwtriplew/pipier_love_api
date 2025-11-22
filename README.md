# Piper Love Chess Engine API

High-performance chess engine with FastAPI backend for web integration.


## 📡 API Endpoints

### GET /
Health check endpoint - returns welcome message

### GET /health  
Returns `{"status": "healthy"}`

### POST /move
Calculate best chess move for a position

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "ai_thinking_ms": 1000
}
```

**Response:**
```json
{
  "move": "e2e4",
  "score": 25,
  "depth": 5,
  "nodes": 12847,
  "nps": 12847,
  "time_ms": 1000,
  "pv": "e2e4 e7e5 g1f3"
}
```

### JavaScript Integration

```javascript
async function getAIMove(fen, thinkingTime = 2000) {
  const response = await fetch('https://your-api.onrender.com/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fen: fen,
      ai_thinking_ms: thinkingTime
    })
  });
  
  const data = await response.json();
  return data.move; // "e2e4"
}
```

## 🔧 Configuration

Update CORS origins in `main.py` (line 38) to match your frontend domain:
```python
allow_origins=[
    "https://wwwtriplew.me",
    "https://www.wwwtriplew.me",
]
```

## 📦 Project Structure

```
pipier_love_api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── render.yaml         # Render deployment config
├── src/                # Chess engine core
│   ├── board_state.py
│   ├── chess_engine.py
│   ├── evaluation.py
│   ├── move_generation.py
│   ├── move_execution.py
│   ├── search.py
│   ├── zobrist_full.py
│   └── ...
└── testing/           # Essential tests
    ├── perft_test.py
    └── test_evaluation.py
```

## 🏆 Features

- **Bitboard representation** for fast move generation
- **Magic bitboards** for sliding piece attacks
- **Alpha-beta pruning** with iterative deepening
- **Transposition table** for position caching
- **Quiescence search** for tactical stability
- **Move ordering** (MVV-LVA, killer moves, history heuristic)
- **Zobrist hashing** with incremental updates
- **Advanced evaluation** (material, piece-square tables, mobility, king safety, pawn structure)

## ⚡ Performance

- **77,000+ NPS** (nodes per second)
- **Depth 6-10** plies at 2000ms thinking time
- **256MB** transposition table
- **~1800-2000 Elo** estimated strength

## 🔒 Security

- CORS configured for specific origins
- Input validation with Pydantic
- Request timeout limits (100-30000ms)
- No shared state between requests

## 📄 License

© 2025 Piper Love Chess Engine
