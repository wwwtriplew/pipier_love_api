# PiperLove API

A FastAPI-based REST API for PiperLove chess AI integration.

## Features

- FastAPI framework for high performance and modern API development
- CORS support for secure cross-origin requests from https://wwwtriplew.me
- Health check endpoint for monitoring
- Chess move endpoint with FEN position support
- Type-safe request/response models using Pydantic

## Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`:
  - fastapi
  - uvicorn[standard]
  - pydantic

## Installation

1. Clone the repository:
```bash
git clone https://github.com/wwwtriplew/pipier_love_api.git
cd pipier_love_api
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode

Run the server with auto-reload enabled:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

Run the server in production:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): http://localhost:8000/docs
- Alternative API documentation (ReDoc): http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

## API Endpoints

### GET /health

Health check endpoint to verify the API is running.

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

### POST /move

Chess move endpoint that accepts a FEN position and AI thinking time.

**Request Body:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "ai_thinking_ms": 1000
}
```

**Response:**
```json
{
  "move": "e2e4"
}
```

**Parameters:**
- `fen` (string): Chess position in FEN (Forsyth-Edwards Notation) format
- `ai_thinking_ms` (integer): Time in milliseconds for AI to think

**Example:**
```bash
curl -X POST http://localhost:8000/move \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "ai_thinking_ms": 1000}'
```

## CORS Configuration

The API is configured to accept requests from:
- https://wwwtriplew.me

Cross-origin requests from other domains will be blocked for security.

## Project Structure

```
pipier_love_api/
├── main.py              # FastAPI application and endpoints
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

## Development

### Code Style

The codebase follows Python best practices:
- Type hints for better code clarity
- Pydantic models for request/response validation
- Async/await for optimal performance
- Clear docstrings for documentation

### Testing

To test the endpoints manually:

1. Start the server:
```bash
uvicorn main:app --reload
```

2. Test the health endpoint:
```bash
curl http://localhost:8000/health
```

3. Test the move endpoint:
```bash
curl -X POST http://localhost:8000/move \
  -H "Content-Type: application/json" \
  -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "ai_thinking_ms": 1000}'
```

## Future Enhancements

- Integration with chess engine (Stockfish, etc.)
- Move validation
- Multiple difficulty levels
- Game state persistence
- Authentication and rate limiting
- WebSocket support for real-time games

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
