#!/usr/bin/env python3
"""
Final API test for opening book integration.
Run after starting the server: uvicorn main:app --reload
"""

import requests
import json

def test_api():
    """Test API with opening book"""
    base_url = "http://localhost:8000"
    
    test_cases = [
        {
            "name": "Starting position",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "expected_source": "book"
        },
        {
            "name": "After 1.e4",
            "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            "expected_source": "book"
        },
        {
            "name": "Random midgame",
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6",
            "expected_source": "search"  # Unlikely to be in book
        }
    ]
    
    print("=" * 80)
    print("API OPENING BOOK TEST")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}] {test['name']}")
        print(f"    FEN: {test['fen']}")
        
        try:
            response = requests.post(
                f"{base_url}/get_move",
                json={"fen": test['fen'], "depth": 8},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                move = data.get('move')
                source = data.get('source', 'unknown')
                
                print(f"    Move: {move}")
                print(f"    Source: {source}")
                
                if source == test['expected_source']:
                    print(f"    ✅ PASS")
                else:
                    print(f"    ⚠️  Expected {test['expected_source']}, got {source}")
            else:
                print(f"    ❌ FAIL - Status {response.status_code}")
                print(f"    {response.text[:200]}")
                
        except Exception as e:
            print(f"    ❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_api()
