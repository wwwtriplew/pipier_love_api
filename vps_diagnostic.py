#!/usr/bin/env python3
"""
VPS Performance Diagnostic Script

Quick diagnostic to identify why PyPy performance is poor on VPS.

Run this script on your VPS:
    pypy3 vps_diagnostic.py

Expected output will tell you exactly what's wrong.
"""

import sys
import time
import platform


def print_header(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def check_python_version():
    """Check Python implementation and version."""
    print_header("1. PYTHON VERSION CHECK")
    
    impl = platform.python_implementation()
    version = platform.python_version()
    executable = sys.executable
    
    print(f"Implementation: {impl}")
    print(f"Version: {version}")
    print(f"Executable: {executable}")
    
    if impl != "PyPy":
        print("\n❌ PROBLEM: Not running PyPy!")
        print("   You're using CPython, which is 10x slower")
        print("   Solution: Install PyPy and run with 'pypy3' instead of 'python'")
        return False
    
    print("\n✅ Running PyPy")
    
    try:
        import __pypy__
        print(f"   JIT Backend: {__pypy__.jit_backend_name}")
    except:
        print("   ⚠️  Cannot detect JIT backend")
    
    return True


def check_c_extensions():
    """Check for C extension imports that kill PyPy JIT."""
    print_header("2. C EXTENSION CHECK")
    
    problem_found = False
    
    # Check for python-chess
    try:
        import chess
        print("❌ PROBLEM: python-chess is imported!")
        print("   This is a C extension that disables PyPy JIT")
        print(f"   Version: {getattr(chess, '__version__', 'unknown')}")
        print("\n   Impact: Reduces performance from 300k NPS to 30k NPS")
        print("   Solution: Remove 'import chess' from your code")
        problem_found = True
    except ImportError:
        print("✅ python-chess not imported (GOOD)")
    
    # Check for other common C extensions
    c_extensions = ['numpy', 'scipy', 'pandas', 'lxml']
    for ext in c_extensions:
        try:
            __import__(ext)
            print(f"⚠️  WARNING: {ext} imported (C extension)")
            problem_found = True
        except ImportError:
            pass
    
    if not problem_found:
        print("✅ No C extensions found")
    
    return not problem_found


def benchmark_engine():
    """Benchmark the chess engine."""
    print_header("3. ENGINE PERFORMANCE TEST")
    
    try:
        from src.chess_engine import ChessBoard
        from src.magic_bitboards import get_lsb
    except ImportError as e:
        print(f"❌ Cannot import engine: {e}")
        return 0
    
    def perft(board, depth):
        if depth == 0:
            return 1
        nodes = 0
        for from_sq, to_sq, promo in board.generate_moves():
            board.make_move(from_sq, to_sq, promo)
            king_sq = get_lsb(board.pieces[1 - board.side_to_move][5])
            if not board.is_square_attacked(king_sq, board.side_to_move):
                nodes += perft(board, depth - 1)
            board.unmake_move()
        return nodes
    
    board = ChessBoard()
    
    # Warmup
    print("Warming up (5 iterations)...")
    for _ in range(5):
        perft(board, 2)
    
    # Benchmark
    print("Running perft(4) benchmark...")
    print("Expected: 197,281 nodes")
    
    start = time.time()
    nodes = perft(board, 4)
    elapsed = time.time() - start
    nps = int(nodes / elapsed) if elapsed > 0 else 0
    
    print(f"\nResults:")
    print(f"  Nodes: {nodes:,}")
    print(f"  Time:  {elapsed:.3f}s")
    print(f"  NPS:   {nps:,}")
    
    # Evaluate
    print(f"\nPerformance Rating:")
    if nps < 30_000:
        print("  ❌ CRITICAL: < 30k NPS (something is broken)")
    elif nps < 100_000:
        print("  ❌ SLOW: 30-100k NPS (CPython level, PyPy JIT not working)")
        print("     → Check for C extension imports")
    elif nps < 200_000:
        print("  ⚠️  OK: 100-200k NPS (PyPy with partial JIT)")
        print("     → Some optimizations missing")
    elif nps < 400_000:
        print("  ✅ GOOD: 200-400k NPS (PyPy with full JIT)")
    else:
        print("  🚀 EXCELLENT: > 400k NPS (PyPy fully optimized)")
    
    return nps


def check_jit_warmup():
    """Check if JIT warmup is effective."""
    print_header("4. JIT WARMUP TEST")
    
    if platform.python_implementation() != "PyPy":
        print("⏭️  Skipped (not running PyPy)")
        return
    
    try:
        from src.jit_warmup import warmup_jit
        
        print("Running JIT warmup...")
        nps = warmup_jit()
        print(f"Warmup NPS: {nps:,}")
        
        if nps < 50_000:
            print("\n❌ PROBLEM: Warmup didn't help")
            print("   JIT is not compiling code")
            print("   → Check for C extension imports")
        else:
            print("\n✅ Warmup effective")
        
    except Exception as e:
        print(f"⚠️  Warmup test failed: {e}")


def check_service_config():
    """Check systemd service configuration."""
    print_header("5. SERVICE CONFIGURATION")
    
    import os
    import subprocess
    
    # Check if running in systemd service
    if os.getenv('INVOCATION_ID'):
        print("✅ Running as systemd service")
        
        # Try to get service status
        try:
            result = subprocess.run(
                ['systemctl', 'show', 'pipier_love_api', '--property=ExecStart'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"Service exec: {result.stdout.strip()}")
                
                if 'pypy' not in result.stdout.lower():
                    print("\n❌ PROBLEM: Service not using PyPy!")
                    print("   Update systemd service to use pypy3")
        except:
            pass
    else:
        print("ℹ️  Not running as systemd service")


def generate_report():
    """Generate diagnostic report with recommendations."""
    print_header("DIAGNOSTIC SUMMARY")
    
    is_pypy = check_python_version()
    no_c_ext = check_c_extensions()
    nps = benchmark_engine()
    check_jit_warmup()
    check_service_config()
    
    # Final recommendations
    print_header("RECOMMENDATIONS")
    
    if not is_pypy:
        print("🔧 CRITICAL: Install and use PyPy")
        print("   1. Install: apt install pypy3 pypy3-dev")
        print("   2. Install deps: pypy3 -m pip install -r requirements.txt")
        print("   3. Update service: ExecStart=/usr/bin/pypy3 -m uvicorn main:app")
        print("   4. Restart: systemctl restart pipier_love_api")
        print()
    
    if not no_c_ext:
        print("🔧 CRITICAL: Remove python-chess dependency")
        print("   1. Edit main.py: Remove 'import chess' lines")
        print("   2. Remove tablebase code (lines 56-124)")
        print("   3. Update requirements.txt: Remove 'chess>=1.10.0'")
        print("   4. Reinstall: pypy3 -m pip install -r requirements.txt")
        print("   5. Restart service")
        print()
    
    if is_pypy and no_c_ext and nps < 200_000:
        print("🔧 INVESTIGATE: PyPy should be faster")
        print("   1. Run: pypy3 critical_tests.py")
        print("   2. Check for other bottlenecks")
        print("   3. Profile: pypy3 -m cProfile -o profile.stats main.py")
        print()
    
    if nps >= 200_000:
        print("✅ Performance is GOOD!")
        print("   Engine is running at expected speed")
        print("   No action needed")
        print()
    
    # Expected improvement
    if not is_pypy or not no_c_ext:
        print("EXPECTED IMPROVEMENT:")
        print(f"  Current NPS:  {nps:,}")
        print(f"  Expected NPS: 300,000+ (10x faster)")
        print(f"  Speedup:      {300_000 // max(nps, 1)}x")


if __name__ == "__main__":
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + "VPS PERFORMANCE DIAGNOSTIC".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    generate_report()
    
    print("\n" + "=" * 80)
    print("Diagnostic complete. See recommendations above.")
    print("=" * 80 + "\n")
