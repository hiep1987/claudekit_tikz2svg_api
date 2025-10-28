# Manual Phase 3 Integration Guide
# Enhanced Whitelist + Resource Limits v2.0 for Production tikz2svg.com

## 🎯 **OVERVIEW**

This guide helps you manually integrate Phase 3 improvements into your existing production system at https://tikz2svg.com without disrupting current operations.

## 📊 **CURRENT PRODUCTION ANALYSIS**

Based on https://tikz2svg.com analysis:
- ✅ **Working Features**: TikZ compilation, Google OAuth, file saving, likes, search
- ✅ **User Base**: Active users (quochiep0504, Hiệp-54, lucdo🍙, etc.)
- ✅ **Infrastructure**: VPS with existing deployment system
- ✅ **Domain**: SSL-enabled production domain

## 🔄 **MANUAL INTEGRATION STEPS**

### **STEP 1: PREPARATION & BACKUP**

#### **1.1 Connect to VPS**
```bash
ssh h2cloud-hiep1987
cd /var/www/tikz2svg_api
```

#### **1.2 Create Complete Backup**
```bash
# Create backup directory
sudo mkdir -p /opt/backups/pre_phase3_$(date +%Y%m%d)
cd /opt/backups/pre_phase3_$(date +%Y%m%d)

# Backup application files
sudo tar -czf tikz2svg_app_backup.tar.gz /var/www/tikz2svg_api/

# Backup database (adjust credentials as needed)
sudo mysqldump -u root -p tikz2svg > tikz2svg_database_backup.sql

# Backup system configs
sudo tar -czf system_configs_backup.tar.gz \
  /etc/nginx/sites-available/ \
  /etc/systemd/system/ \
  /etc/ssl/ \
  /etc/fail2ban/ 2>/dev/null || true

# List backups
ls -la
echo "✅ Backup completed at $(pwd)"
```

### **STEP 2: UPLOAD PHASE 3 FILES**

#### **2.1 Prepare Phase 3 Files on Local**
```bash
# On your local machine (where Phase 3 files are)
cd /Users/hieplequoc/web/work/tikz2svg_api

# Create Phase 3 package
tar -czf phase3_package.tar.gz \
  config_production.py \
  requirements_production.txt \
  wsgi_production.py \
  gunicorn.conf.py \
  backup_production.sh \
  PHASE3_PRODUCTION_DEPLOYMENT_GUIDE.md

# Upload to VPS
scp phase3_package.tar.gz h2cloud-hiep1987:/tmp/
```

#### **2.2 Extract Phase 3 Files on VPS**
```bash
# On VPS
ssh h2cloud-hiep1987
cd /var/www/tikz2svg_api

# Extract Phase 3 files
sudo tar -xzf /tmp/phase3_package.tar.gz
sudo chown -R www-data:www-data .
```

### **STEP 3: INTEGRATE PRODUCTION CONFIGURATION**

#### **3.1 Update Python Dependencies**
```bash
# Backup current requirements
cp requirements.txt requirements_backup.txt

# Install new dependencies (non-disruptive)
source venv/bin/activate  # or your virtual environment path
pip install psutil redis flask-talisman flask-limiter prometheus-client

# Optional: Update to production requirements
# pip install -r requirements_production.txt
```

#### **3.2 Update Environment Configuration**
```bash
# Backup current .env
cp .env .env.backup

# Add Phase 3 environment variables to existing .env
cat >> .env << 'EOF'

# Phase 3: Enhanced Configuration
ENHANCED_WHITELIST_ENABLED=true
SECURITY_MONITORING_ENABLED=true
BACKUP_ENABLED=true
MONITORING_ENABLED=true
REDIS_URL=redis://localhost:6379/0
EOF
```

### **STEP 4: INTEGRATE SECURITY ENHANCEMENTS**

#### **4.1 Update Nginx Configuration (Gradual)**
```bash
# Backup current Nginx config
sudo cp /etc/nginx/sites-available/tikz2svg /etc/nginx/sites-available/tikz2svg.backup

# Add security headers to existing Nginx config
sudo nano /etc/nginx/sites-available/tikz2svg
```

**Add these security headers to your existing server block:**
```nginx
# Security Headers (add to existing server block)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options DENY always; 
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Rate limiting (add before existing location blocks)
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=compile:10m rate=5r/m;

# Add to your main location block
location / {
    limit_req zone=compile burst=2 nodelay;
    # ... your existing proxy settings
}
```

#### **4.2 Test and Reload Nginx**
```bash
# Test configuration
sudo nginx -t

# If successful, reload
sudo systemctl reload nginx
```

### **STEP 5: INTEGRATE MONITORING & LOGGING**

#### **5.1 Setup Enhanced Logging**
```bash
# Create log directories
sudo mkdir -p /var/www/tikz2svg_api/logs/{security,monitoring}
sudo chown -R www-data:www-data /var/www/tikz2svg_api/logs/

# Create monitoring script
sudo cp tikz2svg-monitor /usr/local/bin/ 2>/dev/null || \
sudo tee /usr/local/bin/tikz2svg-monitor << 'EOF'
#!/bin/bash
echo "=== TikZ2SVG System Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
systemctl status nginx --no-pager -l | head -5
systemctl status tikz2svg --no-pager -l | head -5 2>/dev/null || echo "Service: Custom deployment"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $5}')"
EOF

sudo chmod +x /usr/local/bin/tikz2svg-monitor
```

#### **5.2 Test Monitoring**
```bash
# Test system monitor
/usr/local/bin/tikz2svg-monitor
```

### **STEP 6: INTEGRATE BACKUP SYSTEM**

#### **6.1 Setup Backup Script**
```bash
# Make backup script executable
chmod +x backup_production.sh

# Test backup system (dry run)
sudo ./backup_production.sh database

# Setup automated backups
sudo crontab -e
# Add this line:
# 0 2 * * * /var/www/tikz2svg_api/backup_production.sh full
```

### **STEP 7: GRADUAL APP.PY INTEGRATION**

#### **7.1 Backup Current App**
```bash
cp app.py app_original.py
```

#### **7.2 Integrate Phase 3 Features to Existing App**

**Add these imports to your existing app.py:**
```python
# Phase 3 imports (add to existing imports)
import threading
import psutil
import hashlib
from contextlib import contextmanager
from typing import Dict, List, Optional
```

**Add these classes to your existing app.py (after existing imports):**
```python
# Phase 3: Enhanced Security and Monitoring Classes
class CompilationLimits:
    """Resource limits for LaTeX compilation"""
    TIMEOUT_SECONDS = 45
    MAX_MEMORY_MB = 300
    MAX_CONCURRENT = 5
    _active_compilations = 0
    _compilation_lock = threading.Lock()

# Add security logging function
def log_security_event(event_type: str, user_id: str, ip_address: str, details: str):
    """Log security events"""
    try:
        with open('logs/security/security.log', 'a') as f:
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"{timestamp} - {event_type} - User:{user_id} - IP:{ip_address} - {details}\n")
    except Exception as e:
        print(f"Logging error: {e}")
```

#### **7.3 Add New API Endpoints (Non-disruptive)**

**Add these new routes to your existing app.py:**
```python
# Phase 3: New API Endpoints
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
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
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
        "version": "2.0.0"
    }
```

### **STEP 8: TESTING & VERIFICATION**

#### **8.1 Test New Endpoints**
```bash
# Test health endpoint
curl https://tikz2svg.com/health

# Test platform info
curl https://tikz2svg.com/api/platform-info

# Test system status
curl https://tikz2svg.com/api/system-status
```

#### **8.2 Test Core Functionality**
- Visit https://tikz2svg.com
- Test TikZ compilation
- Test user login
- Test file saving
- Test search functionality

#### **8.3 Monitor Logs**
```bash
# Check for errors
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/www/tikz2svg_api/logs/security/security.log

# Monitor system
/usr/local/bin/tikz2svg-monitor
```

### **STEP 9: OPTIMIZE & FINE-TUNE**

#### **9.1 Performance Tuning**
```bash
# Check current resource usage
htop
free -h
df -h

# Optimize based on your VPS specs
# Edit gunicorn.conf.py if using Gunicorn
# Or adjust your current WSGI configuration
```

#### **9.2 Security Verification**
```bash
# Test SSL
curl -I https://tikz2svg.com | grep -i security

# Test rate limiting (from external)
# curl -I https://tikz2svg.com (repeat rapidly)
```

## 🚨 **ROLLBACK PLAN**

If anything goes wrong:

```bash
# Restore application
sudo tar -xzf /opt/backups/pre_phase3_*/tikz2svg_app_backup.tar.gz -C /

# Restore database
mysql -u root -p tikz2svg < /opt/backups/pre_phase3_*/tikz2svg_database_backup.sql

# Restore Nginx config
sudo cp /etc/nginx/sites-available/tikz2svg.backup /etc/nginx/sites-available/tikz2svg
sudo systemctl reload nginx

# Restart your application
sudo systemctl restart your-app-service  # or your restart method
```

## ✅ **SUCCESS VERIFICATION**

- [ ] https://tikz2svg.com loads normally
- [ ] `/health` endpoint returns 200
- [ ] `/api/platform-info` shows v2.0
- [ ] TikZ compilation still works
- [ ] User login still works
- [ ] New security headers present
- [ ] Monitoring script works
- [ ] Backup system functional
- [ ] No errors in logs

## 📞 **SUPPORT**

If you encounter issues:
1. Check `/usr/local/bin/tikz2svg-monitor`
2. Review logs in `/var/www/tikz2svg_api/logs/`
3. Use rollback procedure if needed
4. Test individual components step by step

---

**✨ This manual integration preserves your existing production system while adding Phase 3 enterprise features! ✨**
