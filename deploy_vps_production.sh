#!/bin/bash
#
# VPS Production Deployment Script for Enhanced Whitelist + Resource Limits v2.0
# ===============================================================================
#
# Enterprise-grade deployment automation for Ubuntu/Debian VPS with
# security hardening, performance optimization, and monitoring setup.
#
# Usage:
#   chmod +x deploy_vps_production.sh
#   sudo ./deploy_vps_production.sh
#
# Prerequisites:
#   - Ubuntu 20.04+ or Debian 11+ VPS
#   - Root or sudo access
#   - Domain name pointing to VPS IP
#   - At least 2GB RAM recommended

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ================================
# 🎨 CONFIGURATION VARIABLES
# ================================

APP_NAME="tikz2svg_api"
APP_USER="tikz2svg"
APP_GROUP="tikz2svg"
APP_DIR="/opt/${APP_NAME}"
VENV_DIR="${APP_DIR}/venv"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
SYSTEMD_DIR="/etc/systemd/system"

# Domain configuration (update these)
DOMAIN_NAME="${DOMAIN_NAME:-yourdomain.com}"
EMAIL="${ADMIN_EMAIL:-admin@yourdomain.com}"

# Database configuration
DB_NAME="${DB_NAME:-tikz2svg_production}"
DB_USER="${DB_USER:-tikz2svg_user}"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 32)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================
# 📝 LOGGING FUNCTIONS
# ================================

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
# ✅ PRE-DEPLOYMENT CHECKS
# ================================

check_requirements() {
    log_step "Checking system requirements"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    # Check OS version
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        log_info "OS: $PRETTY_NAME"
        
        if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
            log_warn "This script is optimized for Ubuntu/Debian. Proceed with caution."
        fi
    fi
    
    # Check memory
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [[ $TOTAL_MEM -lt 1024 ]]; then
        log_warn "Low memory detected (${TOTAL_MEM}MB). At least 2GB recommended."
    else
        log_info "Memory: ${TOTAL_MEM}MB"
    fi
    
    # Check disk space
    DISK_SPACE=$(df -h / | awk 'NR==2 {print $4}')
    log_info "Available disk space: $DISK_SPACE"
    
    log_info "✅ System requirements check passed"
}

# ================================
# 📦 SYSTEM PACKAGES INSTALLATION
# ================================

install_system_packages() {
    log_step "Installing system packages"
    
    # Update package list
    log_info "Updating package list..."
    apt-get update -y
    
    # Install essential packages
    log_info "Installing essential packages..."
    apt-get install -y \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        ufw \
        fail2ban \
        logrotate \
        htop \
        tree \
        nano \
        vim
    
    # Install Python 3.11+
    log_info "Installing Python 3.11..."
    add-apt-repository ppa:deadsnakes/ppa -y
    apt-get update -y
    apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        python3-setuptools
    
    # Install LaTeX and dependencies
    log_info "Installing LaTeX system (this may take a while)..."
    apt-get install -y \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-luatex \
        pdf2svg \
        imagemagick \
        ghostscript
    
    # Install Nginx
    log_info "Installing Nginx..."
    apt-get install -y nginx
    
    # Install MySQL/MariaDB
    log_info "Installing MariaDB..."
    apt-get install -y mariadb-server mariadb-client
    
    # Install Redis
    log_info "Installing Redis..."
    apt-get install -y redis-server
    
    # Install monitoring tools
    log_info "Installing monitoring tools..."
    apt-get install -y \
        htop \
        iotop \
        nethogs \
        ncdu \
        dstat
    
    log_info "✅ System packages installed successfully"
}

# ================================
# 🔒 SECURITY HARDENING
# ================================

setup_security() {
    log_step "Setting up security hardening"
    
    # Configure UFW firewall
    log_info "Configuring UFW firewall..."
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
    
    # Configure fail2ban
    log_info "Configuring fail2ban..."
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 1800
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
EOF
    
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    # Secure shared memory
    log_info "Securing shared memory..."
    echo 'tmpfs /run/shm tmpfs defaults,noexec,nosuid 0 0' >> /etc/fstab
    
    # Set file permissions
    log_info "Setting secure file permissions..."
    chmod 600 /etc/ssh/sshd_config
    chmod 600 /boot/grub/grub.cfg 2>/dev/null || true
    
    log_info "✅ Security hardening completed"
}

# ================================
# 👤 USER & GROUP SETUP
# ================================

setup_user() {
    log_step "Setting up application user"
    
    # Create application user and group
    if ! getent group ${APP_GROUP} >/dev/null; then
        log_info "Creating group: ${APP_GROUP}"
        groupadd ${APP_GROUP}
    fi
    
    if ! getent passwd ${APP_USER} >/dev/null; then
        log_info "Creating user: ${APP_USER}"
        useradd -r -s /bin/false -g ${APP_GROUP} -d ${APP_DIR} ${APP_USER}
    fi
    
    # Create application directory
    log_info "Creating application directory: ${APP_DIR}"
    mkdir -p ${APP_DIR}
    chown -R ${APP_USER}:${APP_GROUP} ${APP_DIR}
    chmod 755 ${APP_DIR}
    
    log_info "✅ Application user setup completed"
}

# ================================
# 🗄️ DATABASE SETUP
# ================================

setup_database() {
    log_step "Setting up database"
    
    # Secure MariaDB installation
    log_info "Securing MariaDB..."
    mysql_secure_installation --use-default
    
    # Start and enable MariaDB
    systemctl start mariadb
    systemctl enable mariadb
    
    # Create application database and user
    log_info "Creating database and user..."
    mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Configure MySQL for production
    log_info "Configuring MySQL for production..."
    cat > /etc/mysql/mariadb.conf.d/99-tikz2svg.cnf << EOF
[mysqld]
# TikZ2SVG Production Configuration
max_connections = 100
innodb_buffer_pool_size = 256M
innodb_log_file_size = 64M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
query_cache_type = 1
query_cache_size = 32M
query_cache_limit = 2M
tmp_table_size = 32M
max_heap_table_size = 32M
EOF
    
    systemctl restart mariadb
    
    log_info "✅ Database setup completed"
    log_info "Database: ${DB_NAME}"
    log_info "User: ${DB_USER}"
    log_info "Password: ${DB_PASSWORD}"
}

# ================================
# 🐍 PYTHON APPLICATION DEPLOYMENT
# ================================

deploy_application() {
    log_step "Deploying Python application"
    
    # Create virtual environment
    log_info "Creating Python virtual environment..."
    sudo -u ${APP_USER} python3.11 -m venv ${VENV_DIR}
    
    # Create directory structure
    log_info "Creating directory structure..."
    sudo -u ${APP_USER} mkdir -p ${APP_DIR}/{logs,static,templates,temp_svg,error_tikz}
    sudo -u ${APP_USER} mkdir -p ${APP_DIR}/logs/{errors,security}
    
    # Copy application files (assuming current directory has the app)
    log_info "Copying application files..."
    if [[ -f "app.py" ]]; then
        cp -r . ${APP_DIR}/source/
        chown -R ${APP_USER}:${APP_GROUP} ${APP_DIR}/source/
        
        # Install Python dependencies
        log_info "Installing Python dependencies..."
        sudo -u ${APP_USER} ${VENV_DIR}/bin/pip install --upgrade pip
        sudo -u ${APP_USER} ${VENV_DIR}/bin/pip install -r ${APP_DIR}/source/requirements_production.txt
    else
        log_warn "Application files not found in current directory"
        log_info "Please manually copy your application to ${APP_DIR}/source/"
    fi
    
    # Create environment file
    log_info "Creating environment configuration..."
    cat > ${APP_DIR}/.env << EOF
# Production Environment Configuration
FLASK_ENV=production
FLASK_CONFIG=config_production

# Security
SECRET_KEY=$(openssl rand -base64 32)

# Database
DB_HOST=localhost
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
DB_PORT=3306

# Google OAuth (Update these with your values)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret  
GOOGLE_REDIRECT_URI=https://${DOMAIN_NAME}/login/google/authorized

# Email Configuration (Update these with your values)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
REPLY_TO_EMAIL=your_email@gmail.com

# Application Settings
DOMAIN_NAME=${DOMAIN_NAME}
ADMIN_EMAIL=${EMAIL}

# Performance
GUNICORN_WORKERS=2
MAX_WORKER_MEMORY=512
EOF
    
    chown ${APP_USER}:${APP_GROUP} ${APP_DIR}/.env
    chmod 600 ${APP_DIR}/.env
    
    log_info "✅ Application deployment completed"
    log_warn "⚠️ Please update the .env file with your actual OAuth and email credentials"
}

# ================================
# ⚙️ SYSTEMD SERVICE SETUP
# ================================

setup_systemd_service() {
    log_step "Setting up systemd service"
    
    # Create Gunicorn service
    cat > ${SYSTEMD_DIR}/tikz2svg.service << EOF
[Unit]
Description=TikZ2SVG Enhanced Whitelist + Resource Limits v2.0
After=network.target mariadb.service redis.service
Wants=mariadb.service redis.service

[Service]
Type=notify
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${APP_DIR}/source
Environment=PATH=${VENV_DIR}/bin
EnvironmentFile=${APP_DIR}/.env
ExecStart=${VENV_DIR}/bin/gunicorn --config gunicorn.conf.py wsgi_production:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${APP_DIR}
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryLimit=1G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF
    
    # Create log rotation for application
    cat > /etc/logrotate.d/tikz2svg << EOF
${APP_DIR}/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ${APP_USER} ${APP_GROUP}
    postrotate
        systemctl reload tikz2svg
    endscript
}
EOF
    
    # Enable and start service
    systemctl daemon-reload
    systemctl enable tikz2svg
    
    log_info "✅ Systemd service setup completed"
}

# ================================
# 🌐 NGINX CONFIGURATION
# ================================

setup_nginx() {
    log_step "Setting up Nginx"
    
    # Remove default site
    rm -f ${NGINX_ENABLED}/default
    
    # Create Nginx configuration
    cat > ${NGINX_AVAILABLE}/tikz2svg << EOF
# TikZ2SVG Enhanced Whitelist + Resource Limits v2.0 - Nginx Configuration
# ========================================================================

# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/m;
limit_req_zone \$binary_remote_addr zone=compile:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=general:10m rate=100r/m;

# Upstream Gunicorn
upstream tikz2svg_app {
    server 127.0.0.1:5000;
    keepalive 2;
}

# HTTP -> HTTPS Redirect
server {
    listen 80;
    server_name ${DOMAIN_NAME} www.${DOMAIN_NAME};
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    
    # Let's Encrypt challenges
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name ${DOMAIN_NAME} www.${DOMAIN_NAME};
    
    # SSL Configuration (will be updated by Certbot)
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self';" always;
    
    # General Settings
    client_max_body_size 16M;
    client_body_timeout 30s;
    client_header_timeout 30s;
    keepalive_timeout 65s;
    send_timeout 30s;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Static Files
    location /static/ {
        alias ${APP_DIR}/source/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        
        # Security for uploaded files
        location ~* \.(php|pl|py|jsp|asp|sh|cgi)$ {
            deny all;
        }
    }
    
    # Temp SVG Files
    location /temp_svg/ {
        alias ${APP_DIR}/source/static/temp_svg/;
        expires 1h;
        add_header Cache-Control "public";
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
    }
    
    # API Endpoints with Rate Limiting
    location ~ ^/api/(compile|save) {
        limit_req zone=compile burst=2 nodelay;
        limit_req_status 429;
        
        proxy_pass http://tikz2svg_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
    }
    
    # General API Endpoints
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        limit_req_status 429;
        
        proxy_pass http://tikz2svg_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }
    
    # Health Check (no rate limiting)
    location /health {
        proxy_pass http://tikz2svg_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }
    
    # Metrics (restrict access)
    location /metrics {
        allow 127.0.0.1;
        deny all;
        
        proxy_pass http://tikz2svg_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Main Application
    location / {
        limit_req zone=general burst=20 nodelay;
        limit_req_status 429;
        
        proxy_pass http://tikz2svg_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
    }
    
    # Security: Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \.(env|ini|conf|bak|old|tmp)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Robots.txt
    location = /robots.txt {
        add_header Content-Type text/plain;
        return 200 "User-agent: *\nDisallow: /api/\nDisallow: /admin/\n";
    }
}
EOF
    
    # Enable site
    ln -sf ${NGINX_AVAILABLE}/tikz2svg ${NGINX_ENABLED}/
    
    # Test Nginx configuration
    nginx -t
    
    # Start and enable Nginx
    systemctl enable nginx
    systemctl restart nginx
    
    log_info "✅ Nginx setup completed"
}

# ================================
# 🔐 SSL CERTIFICATE SETUP
# ================================

setup_ssl() {
    log_step "Setting up SSL certificate"
    
    # Install Certbot
    log_info "Installing Certbot..."
    apt-get install -y certbot python3-certbot-nginx
    
    # Obtain SSL certificate
    log_info "Obtaining SSL certificate for ${DOMAIN_NAME}..."
    certbot --nginx -d ${DOMAIN_NAME} -d www.${DOMAIN_NAME} \
        --email ${EMAIL} \
        --agree-tos \
        --non-interactive \
        --redirect
    
    # Setup automatic renewal
    log_info "Setting up automatic SSL renewal..."
    crontab -l 2>/dev/null | { cat; echo "0 2 * * * certbot renew --quiet && systemctl reload nginx"; } | crontab -
    
    log_info "✅ SSL certificate setup completed"
}

# ================================
# 📊 MONITORING SETUP
# ================================

setup_monitoring() {
    log_step "Setting up monitoring"
    
    # Install monitoring tools
    log_info "Installing monitoring tools..."
    apt-get install -y htop iotop nethogs ncdu dstat
    
    # Create system monitoring script
    cat > /usr/local/bin/tikz2svg-monitor << 'EOF'
#!/bin/bash
# TikZ2SVG System Monitor

echo "=== TikZ2SVG System Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo ""

echo "=== Service Status ==="
systemctl status tikz2svg --no-pager -l | head -10
echo ""

echo "=== Resource Usage ==="
echo "CPU: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "Memory: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
echo "Disk: $(df -h / | awk 'NR==2 {print $5}')"
echo ""

echo "=== Active Connections ==="
ss -tuln | grep :5000
echo ""

echo "=== Recent Errors ==="
tail -5 /opt/tikz2svg_api/logs/error.log 2>/dev/null || echo "No errors"
EOF
    
    chmod +x /usr/local/bin/tikz2svg-monitor
    
    # Create log monitoring
    cat > /etc/cron.daily/tikz2svg-log-cleanup << 'EOF'
#!/bin/bash
# Clean up old log files
find /opt/tikz2svg_api/logs -name "*.log" -mtime +30 -delete
find /opt/tikz2svg_api/static/temp_svg -name "*.svg" -mtime +1 -delete
EOF
    
    chmod +x /etc/cron.daily/tikz2svg-log-cleanup
    
    log_info "✅ Monitoring setup completed"
}

# ================================
# 🚀 MAIN DEPLOYMENT FUNCTION
# ================================

main() {
    log_info "Starting TikZ2SVG Enhanced Whitelist + Resource Limits v2.0 Production Deployment"
    log_info "Target domain: ${DOMAIN_NAME}"
    log_info "Admin email: ${EMAIL}"
    echo ""
    
    # Pre-deployment checks
    check_requirements
    
    # Installation steps
    install_system_packages
    setup_security
    setup_user
    setup_database
    deploy_application
    setup_systemd_service
    setup_nginx
    
    # SSL setup (optional, requires domain)
    if [[ "${DOMAIN_NAME}" != "yourdomain.com" ]]; then
        setup_ssl
    else
        log_warn "Skipping SSL setup - please update DOMAIN_NAME variable"
    fi
    
    setup_monitoring
    
    # Start services
    log_step "Starting services"
    systemctl start redis
    systemctl start mariadb
    systemctl start tikz2svg
    systemctl start nginx
    
    # Final status check
    log_step "Deployment completed!"
    
    echo ""
    log_info "✅ TikZ2SVG Enhanced Whitelist + Resource Limits v2.0 deployed successfully!"
    echo ""
    echo "=== DEPLOYMENT SUMMARY ==="
    echo "Application URL: https://${DOMAIN_NAME}"
    echo "Application Directory: ${APP_DIR}"
    echo "Database: ${DB_NAME}"
    echo "Database User: ${DB_USER}"
    echo "Database Password: ${DB_PASSWORD}"
    echo ""
    echo "=== NEXT STEPS ==="
    echo "1. Update ${APP_DIR}/.env with your OAuth and email credentials"
    echo "2. Test the application: curl https://${DOMAIN_NAME}/health"
    echo "3. Monitor logs: journalctl -u tikz2svg -f"
    echo "4. System status: /usr/local/bin/tikz2svg-monitor"
    echo ""
    echo "=== IMPORTANT SECURITY NOTES ==="
    echo "- Database password has been automatically generated"
    echo "- Update the .env file with real OAuth credentials"
    echo "- Configure your domain's DNS to point to this server"
    echo "- Review firewall settings: ufw status"
    echo ""
    
    log_info "Deployment script completed successfully! 🎉"
}

# ================================
# 🚀 SCRIPT EXECUTION
# ================================

# Run main function
main "$@"
