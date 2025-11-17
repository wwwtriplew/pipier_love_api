"""
Sophisticated Chess Engine Profiler
Identifies performance bottlenecks with detailed analysis
"""

import cProfile
import pstats
import io
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from board_state import Position


class EngineProfiler:
    """Comprehensive profiler for chess engine performance analysis."""
    
    def __init__(self):
        self.results = {}
        self.positions = {
            'starting': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'kiwipete': 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -',
            'complex': 'r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1',
        }
    
    def profile_perft(self, position_name: str, depth: int, iterations: int = 5):
        """Profile perft execution with detailed statistics."""
        print(f"\n{'='*70}")
        print(f"Profiling: {position_name} at depth {depth}")
        print(f"Iterations: {iterations}")
        print('='*70)
        
        pos = Position(self.positions[position_name])
        
        # Warm-up
        print("Warming up JIT...")
        for _ in range(3):
            pos.perft(depth)
        
        # Profile
        profiler = cProfile.Profile()
        
        print(f"Running {iterations} iterations with profiling...")
        start = time.time()
        
        profiler.enable()
        for _ in range(iterations):
            result = pos.perft(depth)
        profiler.disable()
        
        elapsed = time.time() - start
        
        # Analyze results
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        
        print(f"\n{'='*70}")
        print(f"RESULTS: {position_name} depth {depth}")
        print(f"{'='*70}")
        print(f"Total nodes:        {result:,}")
        print(f"Total time:         {elapsed:.3f}s")
        print(f"Average NPS:        {result * iterations / elapsed:,.0f}")
        print(f"Time per iteration: {elapsed / iterations:.3f}s")
        
        # Store results
        key = f"{position_name}_d{depth}"
        self.results[key] = {
            'nodes': result,
            'total_time': elapsed,
            'iterations': iterations,
            'nps': result * iterations / elapsed,
            'stats': stats
        }
        
        return stats
    
    def print_hotspots(self, stats, top_n=30):
        """Print top N hotspots with detailed information."""
        print(f"\n{'='*70}")
        print(f"TOP {top_n} HOTSPOTS (by cumulative time)")
        print(f"{'='*70}")
        print(f"{'Function':<50} {'Calls':>12} {'Time':>8} {'%':>6}")
        print('-'*70)
        
        stats.sort_stats('cumulative')
        
        # Get stats
        s = io.StringIO()
        stats.stream = s
        stats.print_stats(top_n)
        output = s.getvalue()
        
        print(output)
        
        # Also by total time
        print(f"\n{'='*70}")
        print(f"TOP {top_n} HOTSPOTS (by total time)")
        print(f"{'='*70}")
        
        s = io.StringIO()
        stats.stream = s
        stats.sort_stats('tottime')
        stats.print_stats(top_n)
        output = s.getvalue()
        
        print(output)
    
    def analyze_function_calls(self, stats):
        """Analyze function call patterns."""
        print(f"\n{'='*70}")
        print("FUNCTION CALL ANALYSIS")
        print(f"{'='*70}")
        
        # Get callers for key functions
        key_functions = [
            'make_move',
            'unmake_move',
            'generate_moves',
            'is_square_attacked',
            'pop_lsb',
            'get_rook_attacks',
            'get_bishop_attacks',
            'get_queen_attacks',
        ]
        
        for func_name in key_functions:
            print(f"\n{func_name}:")
            s = io.StringIO()
            stats.stream = s
            stats.print_callers(func_name)
            output = s.getvalue()
            if output.strip():
                print(output)
            else:
                print("  (not found in profile)")
    
    def generate_report(self, output_file='profile_report.txt'):
        """Generate comprehensive profiling report."""
        print(f"\n{'='*70}")
        print("GENERATING COMPREHENSIVE REPORT")
        print(f"{'='*70}")
        
        with open(output_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("CHESS ENGINE PERFORMANCE PROFILE REPORT\n")
            f.write("="*70 + "\n\n")
            
            # Summary
            f.write("SUMMARY\n")
            f.write("-"*70 + "\n")
            for key, data in self.results.items():
                f.write(f"\n{key}:\n")
                f.write(f"  Nodes:      {data['nodes']:,}\n")
                f.write(f"  Time:       {data['total_time']:.3f}s\n")
                f.write(f"  Iterations: {data['iterations']}\n")
                f.write(f"  Avg NPS:    {data['nps']:,.0f}\n")
            
            # Detailed stats for each test
            for key, data in self.results.items():
                f.write(f"\n\n{'='*70}\n")
                f.write(f"DETAILED PROFILE: {key}\n")
                f.write(f"{'='*70}\n\n")
                
                stats = data['stats']
                
                # Cumulative time
                s = io.StringIO()
                stats.stream = s
                stats.sort_stats('cumulative')
                stats.print_stats(50)
                f.write("TOP 50 FUNCTIONS (cumulative time):\n")
                f.write("-"*70 + "\n")
                f.write(s.getvalue())
                
                # Total time
                s = io.StringIO()
                stats.stream = s
                stats.sort_stats('tottime')
                stats.print_stats(50)
                f.write("\n\nTOP 50 FUNCTIONS (total time):\n")
                f.write("-"*70 + "\n")
                f.write(s.getvalue())
        
        print(f"✅ Report saved to {output_file}")
    
    def identify_optimizations(self):
        """Identify safe optimization opportunities based on profile data."""
        print(f"\n{'='*70}")
        print("OPTIMIZATION OPPORTUNITIES")
        print(f"{'='*70}")
        
        recommendations = []
        
        print("\nAnalyzing profile data...")
        
        # Check if we have data
        if not self.results:
            print("No profile data available. Run profiling first.")
            return []
        
        # Get the most recent stats
        latest_key = list(self.results.keys())[-1]
        stats = self.results[latest_key]['stats']
        
        # Extract function timing data
        function_times = {}
        for func_info in stats.stats:
            func_name = func_info[2] if len(func_info) > 2 else str(func_info)
            tottime = stats.stats[func_info][2]
            cumtime = stats.stats[func_info][3]
            ncalls = stats.stats[func_info][0]
            
            function_times[func_name] = {
                'tottime': tottime,
                'cumtime': cumtime,
                'ncalls': ncalls
            }
        
        # Analyze bottlenecks
        print("\nKey findings:")
        
        # Check for frequently called functions
        for func_name, data in sorted(function_times.items(), 
                                      key=lambda x: x[1]['ncalls'], 
                                      reverse=True)[:10]:
            if data['ncalls'] > 100000:
                print(f"  • {func_name}: called {data['ncalls']:,} times")
                if data['tottime'] > 0.1:
                    recommendations.append({
                        'function': func_name,
                        'issue': 'High call frequency',
                        'calls': data['ncalls'],
                        'time': data['tottime'],
                        'suggestion': 'Consider caching or inlining'
                    })
        
        # Check for time-consuming functions
        for func_name, data in sorted(function_times.items(), 
                                      key=lambda x: x[1]['tottime'], 
                                      reverse=True)[:10]:
            if data['tottime'] > 0.5:
                print(f"  • {func_name}: {data['tottime']:.2f}s total time")
                recommendations.append({
                    'function': func_name,
                    'issue': 'High total time',
                    'time': data['tottime'],
                    'suggestion': 'Profile internally for optimization'
                })
        
        return recommendations


def main():
    """Run comprehensive profiling suite."""
    print("\n" + "="*70)
    print("CHESS ENGINE SOPHISTICATED PROFILER")
    print("="*70)
    
    profiler = EngineProfiler()
    
    # Profile different positions at different depths
    tests = [
        ('starting', 3, 10),
        ('starting', 4, 3),
        ('kiwipete', 3, 5),
        ('complex', 3, 5),
    ]
    
    for position, depth, iterations in tests:
        stats = profiler.profile_perft(position, depth, iterations)
        profiler.print_hotspots(stats, top_n=20)
    
    # Analyze patterns
    if profiler.results:
        latest_key = list(profiler.results.keys())[-1]
        profiler.analyze_function_calls(profiler.results[latest_key]['stats'])
    
    # Generate report
    profiler.generate_report()
    
    # Identify optimizations
    recommendations = profiler.identify_optimizations()
    
    if recommendations:
        print(f"\n{'='*70}")
        print("RECOMMENDED OPTIMIZATIONS")
        print(f"{'='*70}")
        for i, rec in enumerate(recommendations[:10], 1):
            print(f"\n{i}. {rec['function']}")
            print(f"   Issue: {rec['issue']}")
            if 'calls' in rec:
                print(f"   Calls: {rec['calls']:,}")
            if 'time' in rec:
                print(f"   Time:  {rec['time']:.3f}s")
            print(f"   → {rec['suggestion']}")
    
    print(f"\n{'='*70}")
    print("PROFILING COMPLETE")
    print(f"{'='*70}")
    print("\n✅ Detailed report saved to profile_report.txt")
    print("✅ Review the report for optimization opportunities")


if __name__ == '__main__':
    main()
