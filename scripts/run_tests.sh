#!/bin/bash
# Opening Book Test Runner
# Run this script to execute all tests in order

echo "=================================================================="
echo "  OPENING BOOK TEST SUITE"
echo "=================================================================="
echo ""
echo "Book file: openingbook/baron343/baron30.bin"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Test 1: Quick Test
echo "=================================================================="
echo "  STEP 1: Quick Verification (30 seconds)"
echo "=================================================================="
python3 quick_test.py
QUICK_RESULT=$?

if [ $QUICK_RESULT -ne 0 ]; then
    echo ""
    echo "❌ Quick test failed. Please review errors above."
    echo "   Check TESTING_GUIDE.md for troubleshooting."
    exit 1
fi

echo ""
read -p "Quick test passed! Press Enter to continue with comprehensive tests..."

# Test 2: Comprehensive Test
echo ""
echo "=================================================================="
echo "  STEP 2: Comprehensive Testing (2 minutes)"
echo "=================================================================="
python3 test_book_manual.py
COMPREHENSIVE_RESULT=$?

if [ $COMPREHENSIVE_RESULT -ne 0 ]; then
    echo ""
    echo "❌ Comprehensive test had issues. Review errors above."
    echo "   If hash test passed, engine may still be safe to deploy."
    exit 1
fi

echo ""
echo "=================================================================="
echo "  ✅ ALL OFFLINE TESTS PASSED!"
echo "=================================================================="
echo ""
echo "Next steps:"
echo "1. Start API: uvicorn main:app --reload"
echo "2. Run API tests: python test_api_book.py"
echo "3. Deploy if all pass!"
echo ""
echo "=================================================================="
