#!/bin/bash

echo "==========================================="
echo "Installing PyPy3"
echo "==========================================="

# Update package list
sudo apt update

# Install PyPy3
sudo apt install -y pypy3

# Verify installation
if command -v pypy3 &> /dev/null; then
    echo ""
    echo "✓ PyPy3 installed successfully!"
    echo ""
    pypy3 --version
    echo ""
    echo "PyPy location: $(which pypy3)"
else
    echo ""
    echo "✗ PyPy3 installation failed"
    exit 1
fi

echo ""
echo "==========================================="
echo "Installation complete!"
echo "==========================================="
