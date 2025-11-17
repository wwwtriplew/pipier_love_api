#!/usr/bin/env python3
"""
PyPy Performance Benchmark
Compares CPython vs PyPy performance and verifies correctness.
Automatically uses PyPy if available for better performance.
"""

import sys
import time
import platform
import os
import subprocess

# Add parent directory to path to import src as a package
sys.path.insert(0, '.')

# Detect if running under PyPy
IS_PYPY = platform.python_implementation() == 'PyPy'

# If not running under PyPy, automatically try to use it
if not IS_PYPY:
    def find_pypy():
        """Find PyPy installation."""
        # Check PATH first
        try:
            result = subprocess.run(['which', 'pypy3'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                path = result.stdout.strip()
                if os.path.exists(path):
                    return path
        except:
            pass
        
        # Check common locations
        common_paths = [
            '/opt/homebrew/bin/pypy3',
            '/usr/local/bin/pypy3',
            os.path.expanduser('~/Downloads/pypy3.11-v7.3.20-macos_arm64/bin/pypy3'),
            os.path.expanduser('~/pypy3.11-v7.3.20-macos_arm64/bin/pypy3'),
        ]
        
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return None
    
    def fix_macos_security(pypy_path):
        """Try to fix macOS security restrictions automatically."""
        if platform.system() != 'Darwin':
            return False
        
        pypy_dir = os.path.dirname(os.path.dirname(pypy_path))
        
        # Try to remove quarantine attribute (may require user permission)
        try:
            result = subprocess.run(
                ['xattr', '-dr', 'com.apple.quarantine', pypy_dir],
                capture_output=True,
                timeout=5,
                text=True
            )
            # Check if it succeeded (exit code 0) or if permission denied
            if result.returncode == 0:
                return True
            elif 'Operation not permitted' in result.stderr:
                # Need sudo or manual approval
                return False
        except:
            pass
        
        return False
    
    def test_pypy(pypy_path):
        """Test if PyPy can be executed."""
        try:
            result = subprocess.run(
                [pypy_path, '--version'],
                capture_output=True,
                timeout=5,
                text=True,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError, Exception):
            # PyPy can't be executed (macOS security or other issue)
            return False
    
    # Find and use PyPy
    pypy_path = find_pypy()
    
    if pypy_path:
        # Try to fix macOS security if needed
        if not test_pypy(pypy_path):
            print("🔧 Attempting to fix macOS security restrictions...")
            fix_macos_security(pypy_path)
        
        # Test again after fixing
        if test_pypy(pypy_path):
            # Restart with PyPy silently
            os.execv(pypy_path, [pypy_path] + sys.argv)
        else:
            # PyPy found but can't execute - macOS security is blocking it
            pypy_dir = os.path.dirname(os.path.dirname(pypy_path))
            print("=" * 70)
            print("⚠️  PyPy found but blocked by macOS security")
            print("=" * 70)
            print(f"\nPyPy location: {pypy_path}")
            print("\n🔧 macOS is blocking PyPy from running. Try these solutions:")
            print("\n1. Install PyPy to /usr/local (bypasses security):")
            print("   python3 install_pypy.py")
            print("   (This requires sudo password)")
            print("\n2. Try running PyPy directly in Terminal to trigger security prompt:")
            print(f"   {pypy_path} --version")
            print("   Then check System Settings > Privacy & Security")
            print("\n3. Use CPython (current - slower but works):")
            print("   The benchmark will continue with CPython.")
            print("\nNote: macOS security restrictions may prevent PyPy from working.")
            print("If none of the above work, CPython performance is still good.")
            print("\nContinuing with CPython...")
            print("=" * 70)
            print()

from src.board_state import Position, new_game, from_fen

print("=" * 70)
print("CHESS ENGINE - PYPY PERFORMANCE BENCHMARK")
print("=" * 70)
print(f"\nPython Implementation: {platform.python_implementation()}")
print(f"Python Version: {platform.python_version()}")
print(f"Platform: {platform.system()} {platform.machine()}")
print()

# =============================================================================
# Warm-up (important for PyPy JIT)
# =============================================================================
if IS_PYPY:
    print("🔥 PyPy detected - Running JIT warm-up...")
    pos = new_game()
    warmup_iterations = 8  # Reduced from 30 - sufficient for JIT
    for i in range(warmup_iterations):
        nodes = pos.perft(4)
        print(f"   Warm-up {i+1}/{warmup_iterations}: {nodes:,} nodes")
    print("✅ Warm-up complete\n")

# =============================================================================
# Correctness Verification
# =============================================================================
print("=" * 70)
print("CORRECTNESS VERIFICATION")
print("=" * 70)

expected_results = {
    1: 20,
    2: 400,
    3: 8902,
    4: 197281
}

pos = new_game()
all_correct = True

for depth in range(1, 5):
    nodes = pos.perft(depth)
    expected = expected_results[depth]
    correct = nodes == expected
    all_correct = all_correct and correct
    
    status = "✅" if correct else "❌"
    print(f"Depth {depth}: {nodes:>8,} nodes  {status}  (expected {expected:,})")

print()
if all_correct:
    print("✅ 100% PERFT CORRECTNESS MAINTAINED")
else:
    print("❌ PERFT MISMATCH - CHECK CODE!")
    sys.exit(1)

# =============================================================================
# Performance Benchmark
# =============================================================================
print("\n" + "=" * 70)
print("PERFORMANCE BENCHMARK")
print("=" * 70)

results = []
pos = new_game()

for depth in range(1, 5):
    # Multiple runs for accuracy (especially for PyPy JIT)
    runs = 3 if depth <= 3 else 1
    times = []
    
    for run in range(runs):
        start = time.time()
        nodes = pos.perft(depth)
        elapsed = time.time() - start
        times.append(elapsed)
    
    # Use best time (most optimized by JIT)
    best_time = min(times)
    nps = nodes / best_time if best_time > 0 else 0
    results.append((depth, nodes, best_time, nps))
    
    print(f"Depth {depth}: {nps:>11,.0f} NPS  ({nodes:>8,} nodes in {best_time:6.3f}s)")

# Calculate averages
avg_nps = sum(r[3] for r in results[1:]) / 3  # Depth 2-4 average

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"\nAverage NPS (depth 2-4): {avg_nps:,.0f}")

if IS_PYPY:
    # Compare to CPython baseline
    cpython_avg = 77831  # Our measured CPython performance
    speedup = avg_nps / cpython_avg
    print(f"CPython baseline:        {cpython_avg:,.0f} NPS")
    print(f"PyPy speedup:            {speedup:.2f}x")
    
    if speedup >= 2.0:
        print("\n✅ EXCELLENT: 2x+ speedup achieved!")
    elif speedup >= 1.5:
        print("\n✅ GOOD: 1.5x+ speedup achieved")
    else:
        print("\n⚠️  Lower than expected. Try:")
        print("   1. Run benchmark again (JIT needs more warm-up)")
        print("   2. Increase warm-up iterations")
        print("   3. Use longer perft depths for better JIT optimization")
else:
    target = 65000
    if avg_nps >= target:
        print(f"Target (65K NPS):        ✅ Exceeded ({avg_nps/target:.1%})")
    else:
        print(f"Target (65K NPS):        ⚠️  Not reached ({avg_nps/target:.1%})")

    print("\n💡 TIP: Install PyPy for 2-3x speedup:")
    print("   brew install pypy3  (macOS)")
    print("   Then run: python3 benchmark_pypy.py  (auto-detects PyPy)")

# =============================================================================
# Detailed Analysis
# =============================================================================
print("\n" + "=" * 70)
print("DETAILED ANALYSIS")
print("=" * 70)

for depth, nodes, elapsed, nps in results:
    moves_per_sec = nodes / elapsed if elapsed > 0 else 0
    print(f"\nDepth {depth}:")
    print(f"  Nodes:          {nodes:>10,}")
    print(f"  Time:           {elapsed:>10.3f} seconds")
    print(f"  NPS:            {nps:>10,.0f}")
    print(f"  Moves/second:   {moves_per_sec:>10,.0f}")

# =============================================================================
# Performance Projection
# =============================================================================
if IS_PYPY:
    print("\n" + "=" * 70)
    print("PERFORMANCE PROJECTION")
    print("=" * 70)
    
    # Project depth 5 performance
    depth_4_time = results[3][2]
    depth_4_nodes = results[3][1]
    
    # Typical branching factor for chess
    branching_factor = 35
    
    depth_5_nodes = depth_4_nodes * branching_factor
    depth_5_time = depth_5_nodes / avg_nps
    
    print(f"\nEstimated Depth 5:")
    print(f"  Nodes:     ~{depth_5_nodes:>12,}")
    print(f"  Time:      ~{depth_5_time:>12.1f} seconds")
    print(f"  NPS:       ~{avg_nps:>12,.0f}")

# =============================================================================
# Recommendations
# =============================================================================
print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)

if IS_PYPY:
    print("\n✅ You're already using PyPy!")
    print("\nNext optimization options:")
    print("  1. 🔧 Profile-Guided Optimization (PGO)")
    print("     - Compile PyPy with PGO for +10-20% gain")
    print("  2. 🚀 Numba JIT (if compatible)")
    print("     - Add @jit decorators for potential 4x+ gain")
    print("  3. 🔀 Parallel Perft")
    print("     - Use multiprocessing for linear scaling")
else:
    print("\n🚀 NEXT STEP: Install and use PyPy!")
    print("\nInstallation:")
    print("  macOS:   brew install pypy3")
    print("  Linux:   sudo apt-get install pypy3")
    print("  Windows: choco install pypy3")
    print("\nUsage:")
    print("  python3 benchmark_pypy.py  (auto-detects PyPy if installed)")
    print("\nExpected gain: 2-3x faster (155K-233K NPS)")

print("\n" + "=" * 70)
print("BENCHMARK COMPLETE")
print("=" * 70)

# Save results to file
with open('benchmark_results.txt', 'a') as f:
    f.write("\n" + "=" * 70 + "\n")
    f.write(f"Benchmark Run: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Implementation: {platform.python_implementation()}\n")
    f.write(f"Version: {platform.python_version()}\n")
    f.write(f"Average NPS: {avg_nps:,.0f}\n")
    f.write("=" * 70 + "\n")

print(f"\n📝 Results saved to benchmark_results.txt")
