#!/bin/bash

echo "==========================================="
echo "Running Tests with PyPy"
echo "==========================================="

# Check if PyPy is installed
if ! command -v pypy3 &> /dev/null; then
    echo "❌ PyPy3 not found!"
    echo ""
    echo "Please install PyPy3 first:"
    echo "  bash install_pypy.sh"
    exit 1
fi

echo ""
echo "Using PyPy: $(which pypy3)"
pypy3 --version
echo ""

cd /workspaces/pipier_love_api

# Run benchmark
if [ "$1" == "benchmark" ]; then
    echo "Running benchmark..."
    pypy3 benchmark.py
elif [ "$1" == "perft" ]; then
    echo "Running perft tests..."
    pypy3 testing/perft_test.py
else
    echo "Running quick benchmark..."
    pypy3 benchmark.py
    
    echo ""
    echo "==========================================="
    echo "Available test commands:"
    echo "==========================================="
    echo "  bash test_with_pypy.sh benchmark    # Run performance benchmark"
    echo "  bash test_with_pypy.sh perft        # Run perft tests"
    echo ""
fi
