#!/usr/bin/env python3
"""
Script để reset rate limiting cho development
"""

import os
import sys
from datetime import datetime, timedelta
from email_service import EmailService
from flask import Flask

def reset_rate_limit():
    """Reset rate limiting cho development"""
    print("🔄 Resetting email rate limiting...")
    
    # Tạo Flask app tạm thời
    app = Flask(__name__)
    
    # Khởi tạo email service
    email_service = EmailService(app)
    
    # Reset rate limit data
    email_service.rate_limit_data = {
        'hourly_count': 0,
        'daily_count': 0,
        'last_hour_reset': datetime.now(),
        'last_day_reset': datetime.now(),
        'last_email_time': None
    }
    
    print("✅ Rate limiting đã được reset!")
    print(f"   - Hourly count: {email_service.rate_limit_data['hourly_count']}")
    print(f"   - Daily count: {email_service.rate_limit_data['daily_count']}")
    print(f"   - Last email time: {email_service.rate_limit_data['last_email_time']}")
    
    return True

if __name__ == "__main__":
    print("🚀 Email Rate Limit Reset Tool")
    print("=" * 40)
    
    success = reset_rate_limit()
    
    if success:
        print("\n🎉 Rate limiting reset completed!")
    else:
        print("\n❌ Rate limiting reset failed!")
        sys.exit(1)
