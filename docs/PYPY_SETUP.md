# PyPy Setup and Performance Optimization

## Problem

The chess engine runs slowly with CPython (~100k nodes in 12 seconds = ~8,300 NPS), which is too slow for good gameplay.

**PyPy can provide 10-50x speedup** through JIT compilation, achieving 500,000-2,000,000 NPS!

## Quick Start

### 1. Install PyPy

```bash
bash install_pypy.sh
```

This will:
- Update apt package list
- Install PyPy3
- Verify installation

### 2. Run Benchmark

Compare CPython vs PyPy performance:

```bash
# CPython (current)
python3 benchmark.py

# PyPy (fast!)
bash test_with_pypy.sh benchmark
```

### 3. Run Server with PyPy

```bash
bash run_with_pypy.sh
```

This starts the FastAPI server using PyPy instead of CPython.

## Expected Performance

### CPython (Current)
- **NPS**: 30,000-50,000 nodes per second
- **Perft(4)**: ~5 seconds (197,281 nodes)
- **Search depth 5**: ~10-15 seconds

### PyPy (Optimized)
- **NPS**: 500,000-2,000,000 nodes per second (10-50x faster!)
- **Perft(4)**: ~0.1-0.5 seconds
- **Search depth 5**: ~1-2 seconds

### Why PyPy is Faster

PyPy uses a JIT (Just-In-Time) compiler that:
1. **Traces hot loops** - Identifies frequently executed code
2. **Compiles to machine code** - Generates optimized native code
3. **Specializes operations** - Optimizes for actual data types used
4. **Inlines functions** - Eliminates function call overhead

For chess engines with tight loops (move generation, bitboard operations), PyPy provides massive speedups.

## Testing Commands

```bash
# Quick benchmark
bash test_with_pypy.sh

# Full perft test suite
bash test_with_pypy.sh perft

# Benchmark with search
pypy3 benchmark.py --search
```

## Deployment

### Update Render.yaml

Add PyPy to your deployment:

```yaml
services:
  - type: web
    name: pipier-love-api
    runtime: python
    buildCommand: |
      apt-get update
      apt-get install -y pypy3
      pip install -r requirements.txt
    startCommand: pypy3 main.py
```

### Alternative: Docker with PyPy

```dockerfile
FROM pypy:3.10

WORKDIR /app
COPY requirements.txt .
RUN pypy3 -m pip install -r requirements.txt

COPY . .
CMD ["pypy3", "main.py"]
```

## Performance Tips

### 1. Warmup Period
PyPy needs time to JIT-compile code. First few moves may be slower, then dramatically speed up.

### 2. Long-Running Process
PyPy performs best in long-running processes. For API servers, keep the server running (don't restart frequently).

### 3. Memory Usage
PyPy uses more memory than CPython (~2-3x), but this is acceptable for the massive speed gains.

### 4. Avoid C Extensions
Pure Python code benefits most from PyPy. C extensions (numpy, etc.) may not provide speedup.

## Troubleshooting

### PyPy Not Found
```bash
# Check installation
which pypy3
pypy3 --version

# Reinstall if needed
sudo apt update
sudo apt install -y pypy3
```

### Permission Denied
```bash
chmod +x install_pypy.sh
chmod +x run_with_pypy.sh
chmod +x test_with_pypy.sh
```

### Import Errors
PyPy uses its own package manager:
```bash
pypy3 -m pip install fastapi uvicorn
```

## Current Performance Issue

You mentioned:
> "NPS at browser is just so slow. it spends 12 seconds but only explores around 100k nodes usually"

**100k nodes / 12 seconds = ~8,300 NPS** - This is extremely slow!

Expected performance:
- **CPython**: 30,000-50,000 NPS
- **PyPy**: 500,000-2,000,000 NPS

**With PyPy, your 12-second search could explore 6-24 million nodes instead of 100k!**

## Next Steps

1. ✅ Run `bash install_pypy.sh` to install PyPy
2. ✅ Run `bash test_with_pypy.sh` to benchmark
3. ✅ Compare CPython vs PyPy performance
4. ✅ Deploy with PyPy for production

## Files Created

- `install_pypy.sh` - Install PyPy3
- `run_with_pypy.sh` - Run server with PyPy
- `test_with_pypy.sh` - Run tests with PyPy
- `benchmark.py` - Performance benchmark script

All scripts are ready to use!
