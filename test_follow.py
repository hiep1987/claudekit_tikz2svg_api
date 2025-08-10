#!/usr/bin/env python3

import json

# Test data
test_response_success = {
    "success": True,
    "message": "Successfully followed"
}

test_response_error = {
    "success": False,
    "message": "Database error"
}

# Test JavaScript logic
def test_js_logic():
    print("Testing JavaScript logic...")
    
    # Test success case
    data = test_response_success
    if data.get('success'):
        print("✅ Success case: data.success is True")
        print(f"   Message: {data.get('message', 'No message')}")
    else:
        print("❌ Success case: data.success is False")
        print(f"   Error: {data.get('error', data.get('message', 'No error message'))}")
    
    # Test error case
    data = test_response_error
    if data.get('success'):
        print("✅ Error case: data.success is True")
        print(f"   Message: {data.get('message', 'No message')}")
    else:
        print("❌ Error case: data.success is False")
        print(f"   Error: {data.get('error', data.get('message', 'No error message'))}")

if __name__ == "__main__":
    test_js_logic() 