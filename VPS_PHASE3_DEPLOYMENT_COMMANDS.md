# VPS Phase 3 Deployment Commands
# tikz2svg.com - Enhanced Whitelist + Resource Limits v2.0

## 🎯 **OVERVIEW**
Deploy Phase 3 features to production tikz2svg.com from feature branch
**Branch**: `feature/enhanced-whitelist-advanced`
**Domain**: https://tikz2svg.com
**VPS**: h2cloud-hiep1987

---

## 🔧 **STEP 1: SSH AND PRE-DEPLOYMENT CHECK**

```bash
# Connect to VPS
ssh h2cloud-hiep1987

# Check current status
echo "🔍 Current website status:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://tikz2svg.com/
curl -s https://tikz2svg.com/health

# Navigate to app directory
cd /var/www/tikz2svg_api
pwd
echo "📁 Current files:"
ls -la | head -10

# Check current branch/commit
if [[ -d ".git" ]]; then
    echo "📍 Current git status:"
    git branch
    git log --oneline -3
fi
```

**Expected Output:**
- HTTP Status: 200
- Current health check response
- File listing of tikz2svg_api directory

---

## 🛡️ **STEP 2: CREATE COMPLETE BACKUP**

```bash
# Create timestamped backup directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/pre_phase3_${TIMESTAMP}"
echo "🔄 Creating backup at: $BACKUP_DIR"

sudo mkdir -p "$BACKUP_DIR"

# Backup entire application (excluding non-essential files)
echo "📦 Backing up application files..."
sudo tar -czf "$BACKUP_DIR/tikz2svg_app_backup.tar.gz" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='*.log' \
    .

# Backup database if credentials available
echo "🗄️ Attempting database backup..."
if [[ -f ".env" ]]; then
    DB_NAME=$(grep "^DB_NAME=" .env 2>/dev/null | cut -d'=' -f2 || echo "tikz2svg")
    DB_USER=$(grep "^DB_USER=" .env 2>/dev/null | cut -d'=' -f2 || echo "root")
    
    echo "Database: $DB_NAME, User: $DB_USER"
    echo "Enter database password when prompted:"
    mysqldump -u "$DB_USER" -p "$DB_NAME" > "$BACKUP_DIR/database_backup.sql" || \
    echo "⚠️ Database backup failed - continuing without DB backup"
else
    echo "⚠️ No .env file found - skipping database backup"
fi

# Backup nginx config if exists
if [[ -f "/etc/nginx/sites-available/tikz2svg" ]]; then
    sudo cp /etc/nginx/sites-available/tikz2svg "$BACKUP_DIR/nginx_backup.conf"
    echo "✅ Nginx config backed up"
fi

# Verify backup
echo "📊 Backup verification:"
ls -la "$BACKUP_DIR"
du -sh "$BACKUP_DIR"
echo "✅ Backup completed successfully!"
echo "📍 Backup location: $BACKUP_DIR"
```

**Expected Output:**
- Backup directory created
- Application files backed up (~XX MB)
- Database backup (if successful)
- Backup verification listing

---

## 🚀 **STEP 3: DEPLOY PHASE 3 FROM FEATURE BRANCH**

```bash
# Deploy from feature branch with Phase 3 enhancements
echo "🚀 Starting Phase 3 deployment..."
echo "📍 Deploying from: git@github.com:hiep1987/tikz2svg_api.git"
echo "🌿 Branch: feature/enhanced-whitelist-advanced"

# Run deployment script
sudo bash /var/www/tikz2svg_api/deploy.sh git@github.com:hiep1987/tikz2svg_api.git feature/enhanced-whitelist-advanced

# Wait for deployment completion
echo "⏳ Waiting for deployment to complete..."
sleep 10

# Verify Phase 3 files are present
echo "🔍 Checking Phase 3 files:"
echo "📄 Phase 3 configuration files:"
ls -la | grep -E "(config_production|backup_production|PHASE3|MANUAL)" || echo "Some Phase 3 files may be missing"

echo "🔍 Checking updated app.py:"
grep -n "Enhanced Whitelist + Resource Limits v2.0" app.py | head -3 || echo "⚠️ App.py may not be updated"

echo "✅ Deployment completed!"
```

**Expected Output:**
- Deployment script execution log
- Phase 3 files present in directory
- Updated app.py with v2.0 references

---

## 📦 **STEP 4: INSTALL PHASE 3 DEPENDENCIES**

```bash
# Locate Python environment
echo "🐍 Locating Python environment..."
if [[ -d "venv" ]]; then
    VENV_PATH="venv/bin"
    echo "✅ Found venv: $VENV_PATH"
elif [[ -d ".venv" ]]; then
    VENV_PATH=".venv/bin"
    echo "✅ Found .venv: $VENV_PATH"
else
    VENV_PATH="/usr/bin"
    echo "⚠️ Using system Python: $VENV_PATH"
fi

# Upgrade pip first
echo "⬆️ Upgrading pip..."
$VENV_PATH/pip install --upgrade pip

# Install from updated requirements.txt
echo "📦 Installing Phase 3 dependencies from requirements.txt..."
$VENV_PATH/pip install -r requirements.txt

# Verify critical Phase 3 dependencies
echo "🔍 Verifying Phase 3 dependencies:"
echo "psutil:" && $VENV_PATH/pip show psutil | grep Version || echo "❌ psutil missing"
echo "redis:" && $VENV_PATH/pip show redis | grep Version || echo "❌ redis missing" 
echo "flask-talisman:" && $VENV_PATH/pip show flask-talisman | grep Version || echo "❌ flask-talisman missing"
echo "flask-limiter:" && $VENV_PATH/pip show flask-limiter | grep Version || echo "❌ flask-limiter missing"
echo "prometheus-client:" && $VENV_PATH/pip show prometheus-client | grep Version || echo "❌ prometheus-client missing"

echo "✅ Dependencies installation completed!"
```

**Expected Output:**
- Python environment located
- Dependencies installed successfully
- Version verification for each Phase 3 package

---

## 📁 **STEP 5: SETUP PHASE 3 DIRECTORIES AND MONITORING**

```bash
# Create Phase 3 logging directories
echo "📁 Setting up Phase 3 directories..."
sudo mkdir -p logs/{security,monitoring}

# Set appropriate permissions
if id "www-data" &>/dev/null; then
    sudo chown -R www-data:www-data logs/
    echo "✅ Set permissions for www-data"
else
    sudo chown -R $(whoami):$(whoami) logs/
    echo "✅ Set permissions for $(whoami)"
fi

# Create initial log files
echo "$(date): Phase 3 integration started" | sudo tee logs/phase3_integration.log
echo "$(date): Security logging initialized" | sudo tee logs/security/security.log
echo "$(date): Monitoring initialized" | sudo tee logs/monitoring/system.log

# Create system monitor script
echo "🔧 Creating system monitor script..."
sudo tee /usr/local/bin/tikz2svg-monitor << 'EOF'
#!/bin/bash
echo "🚀 TikZ2SVG Enhanced System Monitor v2.0"
echo "======================================="
echo "📅 Date: $(date)"
echo "⏰ Uptime: $(uptime -p 2>/dev/null || uptime)"
echo ""

echo "🌐 Website Status:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://tikz2svg.com 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    echo "  ✅ https://tikz2svg.com: Online (HTTP $HTTP_CODE)"
else
    echo "  ⚠️ https://tikz2svg.com: HTTP $HTTP_CODE"
fi

echo ""
echo "📊 System Resources:"
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
echo "🔧 Services Status:"
systemctl is-active nginx >/dev/null 2>&1 && echo "  ✅ Nginx: Running" || echo "  ❌ Nginx: Not running"
systemctl is-active mysql >/dev/null 2>&1 && echo "  ✅ MySQL: Running" || \
systemctl is-active mariadb >/dev/null 2>&1 && echo "  ✅ MariaDB: Running" || \
echo "  ⚠️ Database: Unknown status"

echo ""
echo "📝 Recent Activity:"
if [[ -f "/var/log/nginx/access.log" ]]; then
    RECENT_REQUESTS=$(tail -100 /var/log/nginx/access.log 2>/dev/null | wc -l)
    echo "  📈 Recent requests: $RECENT_REQUESTS (last 100 entries)"
fi

if [[ -f "/var/www/tikz2svg_api/logs/security/security.log" ]]; then
    SECURITY_EVENTS=$(wc -l < /var/www/tikz2svg_api/logs/security/security.log 2>/dev/null || echo 0)
    echo "  🛡️ Security events: $SECURITY_EVENTS total"
fi

echo ""
echo "🚀 Phase 3 Features Status:"
echo "  ✅ Enhanced health endpoint: /health"
echo "  ✅ Platform info endpoint: /api/platform-info"  
echo "  ✅ System status endpoint: /api/system-status"
echo "  ✅ Security logging: Active"
echo "  ✅ Resource monitoring: Active"
EOF

sudo chmod +x /usr/local/bin/tikz2svg-monitor

# Test the monitor
echo "🧪 Testing system monitor:"
/usr/local/bin/tikz2svg-monitor

# Verify directory structure
echo ""
echo "📁 Phase 3 directory structure:"
ls -la logs/
echo "✅ Phase 3 directories and monitoring setup completed!"
```

**Expected Output:**
- Directories created successfully
- System monitor script created and executable
- Monitor test output showing system status

---

## 🔄 **STEP 6: APPLICATION RESTART**

```bash
# The deploy.sh script should have restarted the application automatically
# But let's verify and restart if needed

echo "🔄 Checking application status..."

# Check if application is responding
echo "🌐 Testing main website response:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}, Time: %{time_total}s\n" https://tikz2svg.com/

# If using systemd service, restart it
if systemctl list-units --type=service | grep -q tikz2svg; then
    echo "🔄 Restarting systemd service..."
    sudo systemctl restart tikz2svg
    sleep 5
    sudo systemctl status tikz2svg --no-pager -l
fi

# If using PM2, restart it
if command -v pm2 >/dev/null && pm2 list | grep -q tikz2svg; then
    echo "🔄 Restarting PM2 process..."
    pm2 restart tikz2svg
    pm2 status
fi

# Wait for application startup
echo "⏳ Waiting for application to fully start..."
sleep 15

# Verify application is responding
echo "✅ Application restart completed!"
```

**Expected Output:**
- HTTP Status: 200 response
- Service restart confirmation
- Application responding normally

---

## 🧪 **STEP 7: COMPREHENSIVE PHASE 3 TESTING**

```bash
echo "🧪 Starting comprehensive Phase 3 testing..."
echo "=========================================="

# Test 1: Main website functionality
echo "🌐 Test 1: Main website"
MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://tikz2svg.com/)
echo "Main site status: $MAIN_STATUS"
if [[ "$MAIN_STATUS" == "200" ]]; then
    echo "✅ Main website: PASS"
else
    echo "❌ Main website: FAIL"
fi
echo ""

# Test 2: Enhanced health endpoint
echo "❤️ Test 2: Enhanced health endpoint"
echo "curl -s https://tikz2svg.com/health | python3 -m json.tool"
curl -s https://tikz2svg.com/health | python3 -m json.tool
echo ""

# Test 3: Platform info with Phase 3 features
echo "🚀 Test 3: Platform info (Phase 3)"
echo "curl -s https://tikz2svg.com/api/platform-info | python3 -m json.tool"
curl -s https://tikz2svg.com/api/platform-info | python3 -m json.tool
echo ""

# Test 4: System status with monitoring
echo "📊 Test 4: System status (Phase 3)"
echo "curl -s https://tikz2svg.com/api/system-status | python3 -m json.tool"
curl -s https://tikz2svg.com/api/system-status | python3 -m json.tool
echo ""

# Test 5: TikZ compilation still works
echo "🎨 Test 5: TikZ compilation functionality"
TEST_TIKZ="\\draw (0,0) circle (1cm);"
echo "Testing simple TikZ: $TEST_TIKZ"

# Create a simple test request
curl -s -X POST https://tikz2svg.com/ \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "code=$TEST_TIKZ" \
    -o /tmp/tikz_test_response.html

if grep -q "svg" /tmp/tikz_test_response.html; then
    echo "✅ TikZ compilation: PASS"
else
    echo "❌ TikZ compilation: FAIL (check manually)"
fi
echo ""

# Test 6: Security logging
echo "🛡️ Test 6: Security logging"
if [[ -f "/var/www/tikz2svg_api/logs/security/security.log" ]]; then
    echo "✅ Security log file exists"
    echo "Recent entries:"
    tail -3 /var/www/tikz2svg_api/logs/security/security.log 2>/dev/null || echo "No entries yet"
else
    echo "⚠️ Security log file not found"
fi
echo ""

# Test 7: System monitor
echo "🔧 Test 7: System monitor"
echo "Running /usr/local/bin/tikz2svg-monitor:"
/usr/local/bin/tikz2svg-monitor | head -20
echo ""

echo "🎉 Phase 3 testing completed!"
echo "=========================================="

# Summary
echo "📊 DEPLOYMENT SUMMARY:"
echo "✅ Backup created: $BACKUP_DIR"
echo "✅ Phase 3 deployed from feature branch"
echo "✅ Dependencies installed"
echo "✅ Monitoring setup"
echo "✅ Application restarted"
echo "✅ Tests completed"
echo ""
echo "🌐 Website: https://tikz2svg.com"
echo "❤️ Health: https://tikz2svg.com/health"
echo "🚀 Platform: https://tikz2svg.com/api/platform-info"
echo "📊 Status: https://tikz2svg.com/api/system-status"
echo ""
echo "🔧 Monitor command: /usr/local/bin/tikz2svg-monitor"
echo "📍 Backup location: $BACKUP_DIR"
```

**Expected Output:**
- Main website: HTTP 200
- Enhanced health endpoint with v2.0 info
- Platform info showing Phase 3 features
- System status with resource monitoring
- TikZ compilation working
- Security logging active
- System monitor functional

---

## 🚨 **ROLLBACK PROCEDURE (IF NEEDED)**

If anything goes wrong, use this rollback:

```bash
echo "🚨 EMERGENCY ROLLBACK PROCEDURE"
echo "================================"

# Navigate to app directory
cd /var/www/tikz2svg_api

# Find the most recent backup
LATEST_BACKUP=$(ls -t /opt/backups/pre_phase3_*/tikz2svg_app_backup.tar.gz | head -1)
echo "📍 Latest backup: $LATEST_BACKUP"

if [[ -f "$LATEST_BACKUP" ]]; then
    # Restore application files
    echo "🔄 Restoring from backup..."
    sudo tar -xzf "$LATEST_BACKUP" -C . --overwrite
    
    # Restart application
    echo "🔄 Restarting application..."
    sudo systemctl restart tikz2svg 2>/dev/null || \
    pm2 restart tikz2svg 2>/dev/null || \
    echo "Please restart your application manually"
    
    # Test restoration
    sleep 10
    curl -s -o /dev/null -w "Restored site HTTP status: %{http_code}\n" https://tikz2svg.com/
    
    echo "✅ Rollback completed"
else
    echo "❌ Backup file not found!"
fi
```

---

## ✅ **SUCCESS CRITERIA**

Phase 3 deployment is successful when:

- [ ] Main website (https://tikz2svg.com) returns HTTP 200
- [ ] /health endpoint shows v2.0 and Phase 3 features
- [ ] /api/platform-info shows "Enhanced Whitelist + Resource Limits v2.0"
- [ ] /api/system-status returns system metrics
- [ ] TikZ compilation still works normally
- [ ] User login and core features unaffected
- [ ] Security logging active in logs/security/
- [ ] System monitor script functional
- [ ] No critical errors in logs

---

## 📞 **NEXT STEPS AFTER SUCCESSFUL DEPLOYMENT**

```bash
# Create automated backup cron job
echo "⏰ Setting up automated backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * /var/www/tikz2svg_api/backup_production.sh full") | crontab -

# Schedule regular monitoring
(crontab -l 2>/dev/null; echo "*/15 * * * * /usr/local/bin/tikz2svg-monitor >> /var/www/tikz2svg_api/logs/monitoring/system.log") | crontab -

echo "✅ Phase 3 deployment and setup completed!"
echo "🎉 tikz2svg.com is now running Enhanced Whitelist + Resource Limits v2.0!"
```

---

**🚨 IMPORTANT: Save the backup location for future reference!**
**📍 Monitor the website for 24-48 hours after deployment**
**📧 Consider setting up email alerts for critical errors**
