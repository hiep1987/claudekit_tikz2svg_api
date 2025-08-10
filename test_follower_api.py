#!/usr/bin/env python3

import requests
import json

def test_follower_count_api():
    """Test the follower count API"""
    
    # Test with user ID 5
    user_id = 5
    url = f"http://localhost:5000/api/follower_count/{user_id}"
    
    try:
        print(f"Testing API: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data}")
            print(f"   Follower count: {data.get('follower_count', 'N/A')}")
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_follower_count_api() 