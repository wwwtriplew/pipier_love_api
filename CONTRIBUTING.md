# Contributing to Piper Love API

## Project Structure

The project is organized as follows:

- **`src/`**: Core engine source code.
- **`tests/`**: Unit tests (run with `pytest`).
- **`scripts/`**: Utility scripts for benchmarking, diagnostics, and deployment.
- **`docs/`**: Documentation and analysis logs.
- **`main.py`**: FastAPI application entry point.

## Development Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest ruff mypy
   ```

2. **Run Tests**:
   ```bash
   pytest
   ```

3. **Run Benchmark**:
   ```bash
   python scripts/benchmark.py
   ```

4. **Linting**:
   ```bash
   ruff check .
   ```

## Deployment

The application is deployed on Render/VPS. See `docs/DEPLOY.md` for details.
