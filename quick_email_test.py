#!/usr/bin/env python3
"""
Quick test hệ thống email đã tích hợp
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def quick_email_test():
    """Test nhanh hệ thống email"""
    base_url = "http://localhost:5173"
    
    print("🚀 Quick Email System Test")
    print("=" * 40)
    
    # Test email mặc định
    test_email = "test@example.com"
    username = "TestUser"
    
    print(f"📧 Test email: {test_email}")
    print(f"👤 Username: {username}")
    print()
    
    # Test 1: Welcome email
    print("1. Testing welcome email...")
    try:
        data = {
            "email": test_email,
            "username": username
        }
        
        response = requests.post(
            f"{base_url}/api/send-welcome-email",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        result = response.json()
        if result.get('success'):
            print("✅ Welcome email sent successfully!")
        else:
            print(f"❌ Welcome email failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Welcome email error: {e}")
    
    print()
    
    # Test 2: Verification email
    print("2. Testing verification email...")
    try:
        data = {
            "email": test_email,
            "username": username,
            "verification_code": "123456"
        }
        
        response = requests.post(
            f"{base_url}/api/send-verification-email",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        result = response.json()
        if result.get('success'):
            print("✅ Verification email sent successfully!")
        else:
            print(f"❌ Verification email failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Verification email error: {e}")
    
    print()
    
    # Test 3: SVG verification email
    print("3. Testing SVG verification email...")
    try:
        data = {
            "email": test_email,
            "username": username,
            "svg_count": 15
        }
        
        response = requests.post(
            f"{base_url}/api/send-svg-verification-email",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        result = response.json()
        if result.get('success'):
            print("✅ SVG verification email sent successfully!")
        else:
            print(f"❌ SVG verification email failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ SVG verification email error: {e}")
    
    print()
    print("=" * 40)
    print("🎉 Quick test completed!")
    print("📧 Check your email for test messages")
    print("🌐 Web test interface: http://localhost:5173/email-test")

if __name__ == '__main__':
    quick_email_test()
