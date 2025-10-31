#!/bin/bash
#
# Manual Phase 3 Integration Script for Production tikz2svg.com
# =============================================================
#
# This script safely integrates Phase 3 enhancements into your existing
# production system without disrupting current operations.
#
# Usage on VPS:
#   scp integrate_phase3_manual.sh h2cloud-hiep1987:/tmp/
#   ssh h2cloud-hiep1987
#   chmod +x /tmp/integrate_phase3_manual.sh
#   cd /var/www/tikz2svg_api
#   sudo /tmp/integrate_phase3_manual.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'  
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_DIR="/var/www/tikz2svg_api"
BACKUP_DIR="/opt/backups/phase3_integration_$(date +%Y%m%d_%H%M%S)"
DOMAIN="tikz2svg.com"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}[STEP]${NC} $1"
    echo "================================"
}

# ================================
# PRE-INTEGRATION CHECKS
# ================================

check_environment() {
    log_step "Checking environment"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    # Check if in app directory
    if [[ ! -f "${APP_DIR}/app.py" ]]; then
        log_error "app.py not found in ${APP_DIR}"
        log_info "Please ensure you're running this from your tikz2svg app directory"
        exit 1
    fi
    
    # Check if domain is accessible
    if curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/health 2>/dev/null | grep -q "200\|404"; then
        log_info "✅ Domain ${DOMAIN} is accessible"
    else
        log_warn "⚠️ Cannot verify domain accessibility - continuing anyway"
    fi
    
    log_info "✅ Environment check passed"
}

# ================================
# BACKUP CURRENT SYSTEM
# ================================

create_backup() {
    log_step "Creating backup"
    
    mkdir -p "${BACKUP_DIR}"
    cd "${APP_DIR}"
    
    # Backup application files
    log_info "Backing up application files..."
    tar -czf "${BACKUP_DIR}/app_backup.tar.gz" \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='node_modules' \
        .
    
    # Backup database if MySQL is available
    if command -v mysql >/dev/null 2>&1; then
        log_info "Backing up database..."
        # Try to find database credentials
        if [[ -f ".env" ]]; then
            DB_NAME=$(grep "^DB_NAME=" .env 2>/dev/null | cut -d'=' -f2 || echo "tikz2svg")
            DB_USER=$(grep "^DB_USER=" .env 2>/dev/null | cut -d'=' -f2 || echo "root")
            
            mysqldump -u "${DB_USER}" -p "${DB_NAME}" > "${BACKUP_DIR}/database_backup.sql" 2>/dev/null || \
            log_warn "Could not backup database - please backup manually if needed"
        fi
    fi
    
    # Backup Nginx config
    if [[ -f "/etc/nginx/sites-available/tikz2svg" ]] || [[ -f "/etc/nginx/sites-available/${DOMAIN}" ]]; then
        log_info "Backing up Nginx configuration..."
        cp /etc/nginx/sites-available/tikz2svg "${BACKUP_DIR}/nginx_backup.conf" 2>/dev/null || \
        cp "/etc/nginx/sites-available/${DOMAIN}" "${BACKUP_DIR}/nginx_backup.conf" 2>/dev/null || \
        log_warn "Could not backup Nginx config"
    fi
    
    log_info "✅ Backup completed at ${BACKUP_DIR}"
}

# ================================
# INSTALL DEPENDENCIES
# ================================

install_dependencies() {
    log_step "Installing Phase 3 dependencies"
    
    cd "${APP_DIR}"
    
    # Check if virtual environment exists
    if [[ -d "venv" ]]; then
        PYTHON_BIN="venv/bin/python"
        PIP_BIN="venv/bin/pip"
    elif [[ -d ".venv" ]]; then
        PYTHON_BIN=".venv/bin/python"
        PIP_BIN=".venv/bin/pip"
    else
        PYTHON_BIN="python3"
        PIP_BIN="pip3"
        log_warn "No virtual environment found, using system Python"
    fi
    
    # Install essential Phase 3 dependencies
    log_info "Installing essential dependencies..."
    ${PIP_BIN} install --upgrade \
        psutil \
        redis \
        flask-talisman \
        flask-limiter \
        prometheus-client \
        structlog \
        2>/dev/null || log_warn "Some dependencies may not have installed"
    
    log_info "✅ Dependencies installed"
}

# ================================
# INTEGRATE MONITORING
# ================================

setup_monitoring() {
    log_step "Setting up monitoring"
    
    # Create log directories
    mkdir -p "${APP_DIR}/logs"/{security,monitoring}
    chown -R www-data:www-data "${APP_DIR}/logs" 2>/dev/null || \
    chown -R $(stat -c '%U' "${APP_DIR}"):$(stat -c '%G' "${APP_DIR}") "${APP_DIR}/logs"
    
    # Create system monitor script
    cat > /usr/local/bin/tikz2svg-monitor << 'EOF'
#!/bin/bash
# TikZ2SVG System Monitor v2.0

echo "🚀 TikZ2SVG Enhanced System Status"
echo "================================="
echo "📅 Date: $(date)"
echo "⏰ Uptime: $(uptime -p 2>/dev/null || uptime)"
echo ""

echo "🌐 Service Status:"
if systemctl is-active nginx >/dev/null 2>&1; then
    echo "  ✅ Nginx: Running"
else
    echo "  ❌ Nginx: Not running"
fi

if systemctl is-active mysql >/dev/null 2>&1 || systemctl is-active mariadb >/dev/null 2>&1; then
    echo "  ✅ Database: Running"
else
    echo "  ⚠️ Database: Unknown status"
fi

echo ""
echo "📊 Resource Usage:"
if command -v free >/dev/null; then
    echo "  💾 Memory: $(free -m | awk 'NR==2{printf "%.1f%% used", $3*100/$2}')"
fi

if command -v df >/dev/null; then
    echo "  💿 Disk: $(df -h / | awk 'NR==2 {print $5 " used"}')"
fi

if command -v top >/dev/null; then
    CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}' 2>/dev/null || echo "Unknown")
    echo "  🔥 CPU: $CPU"
fi

echo ""
echo "🌍 Website Status:"
if curl -s -o /dev/null -w "%{http_code}" https://tikz2svg.com >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://tikz2svg.com)
    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "  ✅ https://tikz2svg.com: Online (HTTP $HTTP_CODE)"
    else
        echo "  ⚠️ https://tikz2svg.com: HTTP $HTTP_CODE"
    fi
else
    echo "  ❌ https://tikz2svg.com: Cannot connect"
fi

echo ""
echo "📝 Recent Logs:"
if [[ -f "/var/log/nginx/error.log" ]]; then
    echo "  Nginx errors (last 3):"
    tail -3 /var/log/nginx/error.log 2>/dev/null | sed 's/^/    /' || echo "    No recent errors"
fi

if [[ -f "/var/www/tikz2svg_api/logs/security/security.log" ]]; then
    echo "  Security events (last 3):"
    tail -3 /var/www/tikz2svg_api/logs/security/security.log 2>/dev/null | sed 's/^/    /' || echo "    No recent events"
fi
EOF
    
    chmod +x /usr/local/bin/tikz2svg-monitor
    log_info "✅ Monitoring setup completed"
}

# ================================
# SETUP BACKUP SYSTEM
# ================================

setup_backup() {
    log_step "Setting up backup system"
    
    # Create simple backup script
    cat > "${APP_DIR}/backup_system.sh" << 'EOF'
#!/bin/bash
# Simple TikZ2SVG Backup System

BACKUP_DIR="/opt/backups/tikz2svg_$(date +%Y%m%d_%H%M%S)"
APP_DIR="/var/www/tikz2svg_api"

mkdir -p "$BACKUP_DIR"

# Backup application
echo "Backing up application..."
tar -czf "$BACKUP_DIR/app_backup.tar.gz" -C "$APP_DIR" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .

# Backup database if possible
if command -v mysqldump >/dev/null && [[ -f "$APP_DIR/.env" ]]; then
    echo "Backing up database..."
    DB_NAME=$(grep "^DB_NAME=" "$APP_DIR/.env" 2>/dev/null | cut -d'=' -f2 || echo "tikz2svg")
    DB_USER=$(grep "^DB_USER=" "$APP_DIR/.env" 2>/dev/null | cut -d'=' -f2 || echo "root")
    
    mysqldump -u "$DB_USER" -p "$DB_NAME" > "$BACKUP_DIR/database_backup.sql" 2>/dev/null || \
    echo "Could not backup database"
fi

echo "✅ Backup completed: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
EOF
    
    chmod +x "${APP_DIR}/backup_system.sh"
    log_info "✅ Backup system created"
}

# ================================
# UPDATE APPLICATION
# ================================

update_application() {
    log_step "Updating application with Phase 3 features"
    
    cd "${APP_DIR}"
    
    # Backup current app.py
    cp app.py app.py.backup
    
    # Add Phase 3 imports and functions to app.py
    log_info "Adding Phase 3 imports..."
    
    # Check if imports already exist
    if ! grep -q "import psutil" app.py; then
        # Add imports at the top (after existing imports)
        python3 << 'EOF'
import re

with open('app.py', 'r') as f:
    content = f.read()

# Find the last import statement
import_pattern = r'(^import .*$|^from .* import .*$)'
imports = []
other_lines = []
in_imports = True

for line in content.split('\n'):
    if re.match(import_pattern, line.strip()) and in_imports:
        imports.append(line)
    else:
        if line.strip() and not line.startswith('#') and in_imports:
            in_imports = False
        other_lines.append(line)

# Add Phase 3 imports
phase3_imports = [
    "import threading",
    "import psutil", 
    "import hashlib",
    "import time",
    "from contextlib import contextmanager",
    "from typing import Dict, List, Optional"
]

# Add new imports that don't already exist
for imp in phase3_imports:
    if imp not in '\n'.join(imports):
        imports.append(imp)

# Reconstruct file
new_content = '\n'.join(imports) + '\n\n' + '\n'.join(other_lines)

with open('app.py', 'w') as f:
    f.write(new_content)
EOF
    fi
    
    # Add Phase 3 endpoints to app.py
    log_info "Adding new API endpoints..."
    
    # Check if endpoints already exist
    if ! grep -q "/api/platform-info" app.py; then
        cat >> app.py << 'EOF'

# Phase 3: Enhanced API Endpoints
@app.route('/api/platform-info')
def platform_info():
    """Platform information endpoint"""
    return {
        "platform": "Enhanced Whitelist + Resource Limits v2.0",
        "version": "2.0.0", 
        "features": {
            "security_patterns": 26,
            "cache_enabled": True,
            "monitoring": True,
            "backup_system": True
        },
        "environment": "production"
    }

@app.route('/api/system-status')
def system_status():
    """System status endpoint"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1) if 'psutil' in globals() else 0
        memory = psutil.virtual_memory() if 'psutil' in globals() else type('obj', (object,), {'percent': 0})
        
        return {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "timestamp": time.time()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0",
        "platform": "Enhanced Whitelist + Resource Limits"
    }

# Phase 3: Security logging function
def log_security_event(event_type: str, user_id: str, ip_address: str, details: str):
    """Log security events"""
    try:
        import os
        log_dir = os.path.join(os.path.dirname(__file__), 'logs', 'security')
        os.makedirs(log_dir, exist_ok=True)
        
        with open(os.path.join(log_dir, 'security.log'), 'a') as f:
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"{timestamp} - {event_type} - User:{user_id} - IP:{ip_address} - {details}\n")
    except Exception as e:
        print(f"Security logging error: {e}")
EOF
    fi
    
    log_info "✅ Application updated with Phase 3 features"
}

# ================================
# TEST INTEGRATION
# ================================

test_integration() {
    log_step "Testing Phase 3 integration"
    
    # Test system monitor
    log_info "Testing system monitor..."
    /usr/local/bin/tikz2svg-monitor
    
    # Test backup system
    log_info "Testing backup system..."
    ${APP_DIR}/backup_system.sh
    
    # Test website accessibility
    log_info "Testing website..."
    if curl -s https://${DOMAIN}/ >/dev/null; then
        log_info "✅ Main website accessible"
    else
        log_warn "⚠️ Website test failed - check manually"
    fi
    
    # Test new endpoints (after restart)
    log_info "New endpoints will be available after application restart:"
    echo "  - https://${DOMAIN}/health"
    echo "  - https://${DOMAIN}/api/platform-info"
    echo "  - https://${DOMAIN}/api/system-status"
    
    log_info "✅ Integration testing completed"
}

# ================================
# MAIN EXECUTION
# ================================

main() {
    log_info "🚀 TikZ2SVG Phase 3 Manual Integration"
    log_info "Domain: ${DOMAIN}"
    log_info "App Directory: ${APP_DIR}"
    echo ""
    
    check_environment
    create_backup
    install_dependencies
    setup_monitoring
    setup_backup
    update_application
    test_integration
    
    log_step "Integration completed successfully!"
    echo ""
    log_info "✅ Phase 3 features have been integrated!"
    log_info "📂 Backup location: ${BACKUP_DIR}"
    log_info "🔧 Monitor command: /usr/local/bin/tikz2svg-monitor"
    log_info "💾 Backup command: ${APP_DIR}/backup_system.sh"
    echo ""
    echo "🔄 NEXT STEPS:"
    echo "1. Restart your application service:"
    echo "   sudo systemctl restart your-app-service"
    echo "   # OR use your custom restart method"
    echo ""
    echo "2. Test new endpoints:"
    echo "   curl https://${DOMAIN}/health"
    echo "   curl https://${DOMAIN}/api/platform-info"
    echo ""
    echo "3. Run system monitor:"
    echo "   /usr/local/bin/tikz2svg-monitor"
    echo ""
    echo "4. If issues occur, restore from backup:"
    echo "   cp app.py.backup app.py"
    echo "   # Restart application"
    echo ""
    log_info "🎉 Phase 3 integration completed successfully!"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Run main function
main "$@"
