#!/usr/bin/env python3
"""
Script tự động chuyển đổi rate limiting mode giữa development và production
"""

import os
import sys
import shutil
from datetime import datetime

def backup_config():
    """Backup file cấu hình hiện tại"""
    backup_file = f"email_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2('email_config.py', backup_file)
    print(f"✅ Backup created: {backup_file}")
    return backup_file

def switch_to_development():
    """Chuyển sang development mode"""
    print("🛠️ Switching to DEVELOPMENT mode...")
    
    # Backup config hiện tại
    backup_file = backup_config()
    
    # Đọc file config hiện tại
    with open('email_config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Thay thế cấu hình rate limiting
    dev_config = """# Cấu hình rate limiting cho email
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 1000,   # Tăng giới hạn cho development
    'max_emails_per_day': 10000,   # Tăng giới hạn cho development
    'cooldown_minutes': 0.1        # Giảm thời gian chờ cho development (6 giây)
}"""
    
    # Tìm và thay thế
    import re
    pattern = r'# Cấu hình rate limiting cho email\nEMAIL_RATE_LIMIT = \{[\s\S]*?\}'
    new_content = re.sub(pattern, dev_config, content)
    
    # Ghi file mới
    with open('email_config.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Rate limiting switched to DEVELOPMENT mode")
    print("   - max_emails_per_hour: 1000")
    print("   - max_emails_per_day: 10000")
    print("   - cooldown_minutes: 0.1 (6 giây)")
    print(f"   - Backup: {backup_file}")

def switch_to_production():
    """Chuyển sang production mode"""
    print("🚀 Switching to PRODUCTION mode...")
    
    # Backup config hiện tại
    backup_file = backup_config()
    
    # Đọc file config hiện tại
    with open('email_config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Thay thế cấu hình rate limiting
    prod_config = """# Cấu hình rate limiting cho email
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 50,     # Giới hạn thấp cho production
    'max_emails_per_day': 500,     # Giới hạn thấp cho production
    'cooldown_minutes': 5          # Thời gian chờ dài cho production (5 phút)
}"""
    
    # Tìm và thay thế
    import re
    pattern = r'# Cấu hình rate limiting cho email\nEMAIL_RATE_LIMIT = \{[\s\S]*?\}'
    new_content = re.sub(pattern, prod_config, content)
    
    # Ghi file mới
    with open('email_config.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Rate limiting switched to PRODUCTION mode")
    print("   - max_emails_per_hour: 50")
    print("   - max_emails_per_day: 500")
    print("   - cooldown_minutes: 5 (5 phút)")
    print(f"   - Backup: {backup_file}")

def show_current_config():
    """Hiển thị cấu hình hiện tại"""
    print("📋 Current Rate Limiting Configuration:")
    print("=" * 50)
    
    try:
        with open('email_config.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Tìm cấu hình rate limiting
        import re
        pattern = r'EMAIL_RATE_LIMIT = \{[\s\S]*?\}'
        match = re.search(pattern, content)
        
        if match:
            config = match.group(0)
            print(config)
            
            # Phân tích mode
            if 'max_emails_per_hour.*1000' in config:
                print("\n🎯 Mode: DEVELOPMENT")
            elif 'max_emails_per_hour.*50' in config:
                print("\n🎯 Mode: PRODUCTION")
            else:
                print("\n🎯 Mode: CUSTOM")
        else:
            print("❌ Rate limiting config not found")
            
    except Exception as e:
        print(f"❌ Error reading config: {e}")

def reset_rate_limiting():
    """Reset rate limiting data"""
    print("🔄 Resetting rate limiting data...")
    
    try:
        # Import và chạy reset script
        import subprocess
        result = subprocess.run(['python', 'reset_rate_limit.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Rate limiting data reset successfully")
        else:
            print(f"❌ Reset failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error resetting rate limiting: {e}")

def main():
    """Main function"""
    print("🚦 Rate Limiting Mode Switcher")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python switch_rate_limit_mode.py dev     # Switch to development")
        print("  python switch_rate_limit_mode.py prod    # Switch to production")
        print("  python switch_rate_limit_mode.py show    # Show current config")
        print("  python switch_rate_limit_mode.py reset   # Reset rate limiting data")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'dev':
        switch_to_development()
        print("\n💡 Next steps:")
        print("   1. Restart Flask app")
        print("   2. Test with: python test_email_bypass_rate_limit.py")
        
    elif command == 'prod':
        switch_to_production()
        print("\n💡 Next steps:")
        print("   1. Deploy to VPS")
        print("   2. Restart service")
        print("   3. Monitor logs")
        
    elif command == 'show':
        show_current_config()
        
    elif command == 'reset':
        reset_rate_limiting()
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: dev, prod, show, reset")

if __name__ == "__main__":
    main()
