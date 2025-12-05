#!/bin/bash

echo "==========================================="
echo "Running Chess Engine with PyPy"
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

# Run the main application with PyPy
echo "Starting server with PyPy..."
echo ""

cd /workspaces/pipier_love_api
pypy3 main.py
