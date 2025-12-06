#!/usr/bin/env python
"""
Startup wrapper that configures PyPy JIT before importing heavy modules.
This ensures JIT is properly configured from the start.
"""
import sys

def configure_jit():
    """Configure PyPy JIT with optimal parameters."""
    try:
        import pypyjit
        
        # Try progressively higher trace limits until one works
        # Default PyPy trace_limit is around 6000-10000
        # Higher values allow more complex functions to be JIT-compiled
        trace_limits = [20000, 50000, 100000, 150000]
        
        for limit in trace_limits:
            try:
                pypyjit.set_param(f'trace_limit={limit}')
                print(f"✅ PyPy JIT configured with trace_limit={limit}", file=sys.stderr)
                return True
            except SystemError:
                # TraceLimitTooHigh - try next lower value
                continue
        
        # If all fail, use default
        print("⚠️  Using default PyPy JIT trace_limit", file=sys.stderr)
        return True
        
    except ImportError:
        print("⚠️  Not running on PyPy or pypyjit not available", file=sys.stderr)
        return False

if __name__ == "__main__":
    # Configure JIT before importing anything heavy
    configure_jit()
    
    # Now import and run the main application
    import uvicorn
    from main import app
    
    # Run with explicit configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
