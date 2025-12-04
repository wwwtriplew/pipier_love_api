"""
Quick API integration test for opening book.

This tests the actual /calculate_move endpoint with opening positions.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_api_opening_position():
    """Test API with starting position."""
    print_section("API Test: Starting Position")
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    try:
        print(f"  FEN: {fen}")
        print(f"  Sending request...")
        
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/calculate_move",
            json={"fen": fen},
            timeout=15
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n  ✅ Success! Response in {elapsed*1000:.1f} ms")
            print(f"  Move: {data['move']}")
            print(f"  Time: {data.get('time_ms', 'N/A')} ms")
            print(f"  Depth: {data.get('depth', 'N/A')}")
            print(f"  Nodes: {data.get('nodes', 'N/A'):,}" if data.get('nodes') else "  Nodes: N/A")
            
            # Check if it's from opening book
            if data.get('time_ms', 999) < 10 and data.get('depth', 0) == 0:
                print("\n  🎯 OPENING BOOK HIT!")
                print("  Response was instant - came from book")
            else:
                print("\n  🔍 SEARCH RESULT")
                print("  Position searched (not in book or book disabled)")
            
            return True
        else:
            print(f"  ❌ Error: {response.status_code}")
            print(f"  {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("  ⚠️  API not running")
        print("  Start with: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

def test_api_after_e4():
    """Test API after 1.e4."""
    print_section("API Test: After 1.e4")
    
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    
    try:
        print(f"  FEN: {fen}")
        print(f"  Sending request...")
        
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/calculate_move",
            json={"fen": fen},
            timeout=15
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n  ✅ Success! Response in {elapsed*1000:.1f} ms")
            print(f"  Move: {data['move']}")
            print(f"  Time: {data.get('time_ms', 'N/A')} ms")
            
            if data.get('time_ms', 999) < 10 and data.get('depth', 0) == 0:
                print("\n  🎯 OPENING BOOK HIT!")
            else:
                print("\n  🔍 SEARCH RESULT")
            
            return True
        else:
            print(f"  ❌ Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("  ⚠️  API not running")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

def test_api_midgame():
    """Test API with midgame (should NOT be in book)."""
    print_section("API Test: Midgame (Fallback Test)")
    
    # Random midgame position
    fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1"
    
    try:
        print(f"  FEN: {fen}")
        print(f"  Sending request...")
        
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/calculate_move",
            json={"fen": fen},
            timeout=15
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n  ✅ Success! Response in {elapsed*1000:.1f} ms")
            print(f"  Move: {data['move']}")
            print(f"  Time: {data.get('time_ms', 'N/A')} ms")
            print(f"  Depth: {data.get('depth', 'N/A')}")
            
            if data.get('time_ms', 0) > 100:
                print("\n  ✅ GRACEFUL FALLBACK WORKING")
                print("  Position not in book - engine searched normally")
            else:
                print("\n  🎯 Possibly in book (or very fast search)")
            
            return True
        else:
            print(f"  ❌ Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("  ⚠️  API not running")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  OPENING BOOK API INTEGRATION TEST")
    print("="*60)
    print("\n  Prerequisites:")
    print("  - API running: uvicorn main:app --reload")
    print("  - Opening book file present")
    
    results = []
    results.append(("Starting Position", test_api_opening_position()))
    results.append(("After 1.e4", test_api_after_e4()))
    results.append(("Midgame (Fallback)", test_api_midgame()))
    
    print_section("SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")
    
    print(f"\n  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  ✅ ALL TESTS PASSED - API integration working!")
    elif passed > 0:
        print("\n  ⚠️  PARTIAL SUCCESS - Check failed tests")
    else:
        print("\n  ❌ TESTS FAILED - Is the API running?")

if __name__ == "__main__":
    main()
