#!/bin/bash

# ================================================================
# TikZ2SVG API - VPS Timezone Configuration Script
# ================================================================
# Purpose: Automatically configure timezone settings for VPS deployment
# Author: AI Assistant  
# Date: 2025-10-27
# Usage: bash setup_timezone_vps.sh
# ================================================================

set -e  # Exit on any error

echo "🚀 TikZ2SVG API - VPS Timezone Configuration Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check current status
print_status "Checking current timezone configuration..."

echo "📅 Current server timezone:"
timedatectl status | grep "Time zone" || echo "Could not detect timezone"

echo ""
echo "🗄️ Current MySQL timezone (if available):"
if command_exists mysql; then
    mysql -u root -p -e "SELECT @@system_time_zone as system_tz, @@session.time_zone as session_tz, NOW() as current_time;" 2>/dev/null || echo "Could not connect to MySQL (normal if not configured)"
else
    print_warning "MySQL client not found"
fi

echo ""
print_status "Starting timezone configuration..."

# 2. Configure server timezone
print_status "Setting server timezone to Asia/Ho_Chi_Minh..."

if command_exists timedatectl; then
    sudo timedatectl set-timezone Asia/Ho_Chi_Minh
    sudo timedatectl set-ntp true
    print_success "Server timezone configured successfully"
    
    echo "New timezone status:"
    timedatectl status | grep "Time zone"
else
    print_error "timedatectl not found. Please set timezone manually."
    exit 1
fi

# 3. Configure MySQL timezone
print_status "Configuring MySQL timezone..."

if command_exists mysql; then
    print_status "Please enter MySQL root password when prompted..."
    
    # Try to configure MySQL timezone
    mysql -u root -p -e "
        SET GLOBAL time_zone = '+07:00';
        SELECT 'MySQL timezone configured successfully' as status, 
               @@system_time_zone as system_tz, 
               @@session.time_zone as session_tz,
               NOW() as current_time;
    " 2>/dev/null || {
        print_warning "Could not configure MySQL timezone. Please do it manually:"
        echo "mysql -u root -p"
        echo "SET GLOBAL time_zone = '+07:00';"
    }
    
    # Add timezone to MySQL config
    MYSQL_CONFIG="/etc/mysql/mysql.conf.d/mysqld.cnf"
    MYSQL_CONFIG_ALT="/etc/mysql/my.cnf"
    
    if [ -f "$MYSQL_CONFIG" ]; then
        CONFIG_FILE="$MYSQL_CONFIG"
    elif [ -f "$MYSQL_CONFIG_ALT" ]; then
        CONFIG_FILE="$MYSQL_CONFIG_ALT"
    else
        print_warning "MySQL config file not found. Please add manually:"
        echo "Add this line to [mysqld] section: default-time-zone = \"+07:00\""
        CONFIG_FILE=""
    fi
    
    if [ -n "$CONFIG_FILE" ]; then
        if ! grep -q "default-time-zone" "$CONFIG_FILE"; then
            print_status "Adding timezone to MySQL config..."
            sudo bash -c "echo 'default-time-zone = \"+07:00\"' >> $CONFIG_FILE"
            print_success "MySQL config updated"
        else
            print_success "MySQL config already has timezone setting"
        fi
        
        # Restart MySQL
        print_status "Restarting MySQL service..."
        sudo systemctl restart mysql || print_warning "Could not restart MySQL. Please restart manually."
    fi
    
else
    print_warning "MySQL client not found. Please install and configure manually."
fi

# 4. Test Python timezone
print_status "Testing Python timezone configuration..."

python3 -c "
import sys
from datetime import datetime

try:
    try:
        from zoneinfo import ZoneInfo
        tz_vn = ZoneInfo('Asia/Ho_Chi_Minh')
        print('✅ Using zoneinfo (Python 3.9+)')
    except ImportError:
        from pytz import timezone
        tz_vn = timezone('Asia/Ho_Chi_Minh')
        print('✅ Using pytz (fallback)')
    
    vn_time = datetime.now(tz_vn)
    utc_time = datetime.utcnow()
    
    print(f'🇻🇳 Vietnam Time: {vn_time}')
    print(f'🌍 UTC Time: {utc_time}')
    
    # Calculate difference
    diff_hours = (vn_time.replace(tzinfo=None) - utc_time).total_seconds() / 3600
    print(f'⏰ Time difference: {diff_hours:.1f} hours from UTC')
    
    if abs(diff_hours - 7.0) < 0.1:
        print('✅ Python timezone configured correctly!')
    else:
        print('❌ Python timezone may have issues')
        
except Exception as e:
    print(f'❌ Python timezone test failed: {e}')
    sys.exit(1)
" || print_error "Python timezone test failed"

# 5. Provide next steps
echo ""
print_success "Timezone configuration completed!"
echo ""
print_status "Next steps:"
echo "1. Restart your TikZ2SVG application:"
echo "   sudo systemctl restart your-app-service"
echo "   # or if using PM2:"
echo "   pm2 restart tikz2svg-api"
echo ""
echo "2. Test the application:"
echo "   - Create a new SVG file"
echo "   - Add a comment"
echo "   - Check if timestamps are correct"
echo ""
echo "3. If issues persist, check the troubleshooting guide in:"
echo "   VPS_TIMEZONE_CONFIGURATION_GUIDE.md"

# 6. Final verification
echo ""
print_status "Final verification:"
echo "📅 Server timezone: $(timedatectl status | grep 'Time zone' | awk '{print $3}')"

if command_exists mysql; then
    echo "🗄️ MySQL timezone:"
    mysql -u root -p -e "SELECT @@session.time_zone;" 2>/dev/null || echo "   (Could not verify - please check manually)"
fi

echo "🐍 Python timezone: Asia/Ho_Chi_Minh configured"

print_success "Setup completed! The 7-hour timezone issue should now be resolved."

echo ""
print_warning "IMPORTANT: Please restart your application and test thoroughly!"
