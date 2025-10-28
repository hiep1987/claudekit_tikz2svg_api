# Phase 3: Production Deployment & Hardening Guide
# Enhanced Whitelist + Resource Limits v2.0

## 🎯 **OVERVIEW**

Complete production deployment package for VPS deployment with enterprise-grade security, performance optimization, and monitoring capabilities.

## 📋 **DEPLOYMENT CHECKLIST**

### ✅ **Pre-Deployment Requirements**
- [ ] Ubuntu 20.04+ or Debian 11+ VPS
- [ ] Minimum 2GB RAM (4GB recommended)  
- [ ] At least 20GB free disk space
- [ ] Domain name pointing to VPS IP
- [ ] Root or sudo access
- [ ] Email account for notifications
- [ ] Google OAuth credentials

### ✅ **Environment Variables Required**
Update `/opt/tikz2svg_api/.env` after deployment:

```bash
# Google OAuth (Required)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://yourdomain.com/login/google/authorized

# Email Configuration (Required)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
SENDER_EMAIL=your_email@gmail.com
REPLY_TO_EMAIL=your_email@gmail.com

# Domain Configuration
DOMAIN_NAME=yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
```

## 🚀 **QUICK DEPLOYMENT**

### **Step 1: Upload Files to VPS**
```bash
# Upload deployment package to VPS
scp -r . root@your-vps-ip:/tmp/tikz2svg_deployment/

# SSH to VPS  
ssh root@your-vps-ip
cd /tmp/tikz2svg_deployment/
```

### **Step 2: Run Deployment Script**
```bash
# Make script executable
chmod +x deploy_vps_production.sh

# Set environment variables (optional)
export DOMAIN_NAME="yourdomain.com"
export ADMIN_EMAIL="admin@yourdomain.com"

# Run deployment
sudo ./deploy_vps_production.sh
```

### **Step 3: Configure Application**
```bash
# Update environment variables
nano /opt/tikz2svg_api/.env

# Restart application
systemctl restart tikz2svg

# Check status
systemctl status tikz2svg
```

### **Step 4: Verify Deployment**
```bash
# Health check
curl https://yourdomain.com/health

# System status
/usr/local/bin/tikz2svg-monitor

# Service logs
journalctl -u tikz2svg -f
```

## 📁 **DEPLOYMENT FILES OVERVIEW**

### **🔧 Configuration Files**
- `config_production.py` - Production Flask configuration
- `requirements_production.txt` - Production Python dependencies  
- `wsgi_production.py` - WSGI application entry point
- `gunicorn.conf.py` - Gunicorn server configuration

### **📜 Deployment Scripts**
- `deploy_vps_production.sh` - Complete VPS deployment automation
- `backup_production.sh` - Automated backup system

### **⚙️ Service Files** (Auto-generated)
- `/etc/systemd/system/tikz2svg.service` - Systemd service
- `/etc/nginx/sites-available/tikz2svg` - Nginx configuration
- `/etc/fail2ban/jail.local` - Fail2ban configuration

## 🛡️ **SECURITY FEATURES**

### **✅ Implemented Security Measures**
- **SSL/TLS**: Automatic Let's Encrypt certificates
- **Firewall**: UFW with restrictive rules
- **Rate Limiting**: Nginx + Flask-Limiter integration
- **Fail2ban**: Brute force protection
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **Process Isolation**: Systemd security directives
- **File Permissions**: Restrictive permissions on sensitive files
- **Input Validation**: 26+ dangerous pattern detection

### **🔒 Security Configuration**
```bash
# Firewall Status
ufw status

# Fail2ban Status  
fail2ban-client status

# SSL Certificate Status
certbot certificates

# Security Headers Test
curl -I https://yourdomain.com
```

## ⚡ **PERFORMANCE OPTIMIZATION**

### **✅ Performance Features**
- **Gunicorn**: Multi-worker WSGI server
- **Nginx**: Reverse proxy with caching
- **Redis**: Session storage and rate limiting
- **MySQL**: Optimized database configuration
- **Gzip Compression**: Static and dynamic content
- **Static Files**: CDN-ready with proper headers

### **📊 Performance Monitoring**
```bash
# System Resources
htop
iotop
nethogs

# Application Metrics
curl http://localhost/metrics

# Database Performance
mysql -u root -e "SHOW PROCESSLIST;"
```

## 📊 **MONITORING & LOGGING**

### **✅ Monitoring Components**
- **System Monitor**: `/usr/local/bin/tikz2svg-monitor`
- **Health Endpoint**: `https://yourdomain.com/health`
- **Metrics Endpoint**: `http://localhost/metrics` (localhost only)
- **Log Rotation**: Automatic log cleanup
- **Backup System**: Automated daily backups

### **📝 Log Locations**
```bash
# Application Logs
/opt/tikz2svg_api/logs/app.log
/opt/tikz2svg_api/logs/error.log
/opt/tikz2svg_api/logs/security.log

# System Logs
/var/log/nginx/access.log
/var/log/nginx/error.log
journalctl -u tikz2svg

# Backup Logs
/opt/backups/tikz2svg_api/logs/
```

## 💾 **BACKUP SYSTEM**

### **✅ Automated Backups**
```bash
# Manual Backup Commands
/opt/tikz2svg_api/backup_production.sh full      # Complete backup
/opt/tikz2svg_api/backup_production.sh database  # Database only
/opt/tikz2svg_api/backup_production.sh files     # Files only

# Automatic Daily Backups (configured in cron)
0 2 * * * /opt/tikz2svg_api/backup_production.sh full
```

### **📂 Backup Locations**
```bash
/opt/backups/tikz2svg_api/
├── database/
│   ├── daily/     # 7 days retention
│   ├── weekly/    # 4 weeks retention  
│   └── monthly/   # 6 months retention
├── files/         # Application files
├── config/        # System configuration
└── logs/          # Backup logs
```

## 🔧 **MAINTENANCE COMMANDS**

### **📊 System Status**
```bash
# Complete system status
/usr/local/bin/tikz2svg-monitor

# Service status
systemctl status tikz2svg nginx mariadb redis

# Resource usage
free -h
df -h
```

### **🔄 Service Management**
```bash
# Restart application
systemctl restart tikz2svg

# Reload Nginx configuration
systemctl reload nginx

# View application logs
journalctl -u tikz2svg -f

# Clear cache
redis-cli FLUSHDB
```

### **⚙️ Configuration Updates**
```bash
# Update environment variables
nano /opt/tikz2svg_api/.env
systemctl restart tikz2svg

# Update Nginx configuration
nano /etc/nginx/sites-available/tikz2svg
nginx -t && systemctl reload nginx

# Update application code
cd /opt/tikz2svg_api/source
git pull origin main
systemctl restart tikz2svg
```

## 🚨 **TROUBLESHOOTING**

### **Common Issues & Solutions**

#### **❌ Application Won't Start**
```bash
# Check service status
systemctl status tikz2svg

# Check application logs
journalctl -u tikz2svg -n 50

# Check Python environment
/opt/tikz2svg_api/venv/bin/python --version

# Verify dependencies
/opt/tikz2svg_api/venv/bin/pip list
```

#### **❌ SSL Certificate Issues**
```bash
# Check certificate status
certbot certificates

# Renew certificate manually
certbot renew --dry-run

# Check Nginx SSL config
nginx -t
```

#### **❌ Database Connection Issues**
```bash
# Check MySQL status
systemctl status mariadb

# Test database connection
mysql -u tikz2svg_user -p tikz2svg_production

# Check database configuration
cat /etc/mysql/mariadb.conf.d/99-tikz2svg.cnf
```

#### **❌ High Resource Usage**
```bash
# Check system resources
htop
free -h
df -h

# Check application processes
ps aux | grep gunicorn

# Monitor real-time usage
/usr/local/bin/tikz2svg-monitor
```

## 📞 **SUPPORT & UPDATES**

### **📈 Performance Tuning For Your VPS**

**For 2GB RAM VPS:**
- Gunicorn workers: 2
- MySQL buffer pool: 256MB
- Redis maxmemory: 128MB

**For 4GB RAM VPS:**
- Gunicorn workers: 3
- MySQL buffer pool: 512MB  
- Redis maxmemory: 256MB

**For 8GB+ RAM VPS:**
- Gunicorn workers: 4-6
- MySQL buffer pool: 1GB+
- Redis maxmemory: 512MB+

### **🔄 Update Procedure**
```bash
# Backup before update
/opt/tikz2svg_api/backup_production.sh full

# Update system packages
apt update && apt upgrade -y

# Update application code
cd /opt/tikz2svg_api/source
git pull origin main

# Update Python dependencies
/opt/tikz2svg_api/venv/bin/pip install -U -r requirements_production.txt

# Restart services
systemctl restart tikz2svg
systemctl restart nginx
```

## ✅ **DEPLOYMENT SUCCESS INDICATORS**

- [ ] `https://yourdomain.com/health` returns status 200
- [ ] `https://yourdomain.com/api/platform-info` shows v2.0 platform
- [ ] SSL certificate is valid (A+ grade on SSL Labs)
- [ ] Firewall is active with correct rules
- [ ] All services are enabled and running
- [ ] Logs are being written without errors
- [ ] Backups are configured and working
- [ ] TikZ compilation works with security validation
- [ ] Performance metrics are within acceptable ranges

## 🎉 **CONGRATULATIONS!**

Your **Enhanced Whitelist + Resource Limits v2.0** is now deployed in production with enterprise-grade security, performance optimization, and monitoring capabilities!

---

**Need help?** Check the troubleshooting section or review the deployment logs for detailed information.
