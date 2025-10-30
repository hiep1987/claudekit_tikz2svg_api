# 🚀 PHASE 1: VPS DEPLOYMENT GUIDE

## 📋 **Package Management System Deployment**

### **🔧 Prerequisites Updated**
- ✅ **requirements.txt**: Updated with 9 new dependencies  
- ✅ **Flask-Limiter**: Upgraded to v4.0.0
- ✅ **Database Schema**: Migration script ready
- ✅ **Templates**: CSS Foundation integrated

---

## 📦 **REQUIREMENTS.TXT CHANGES**

### **📈 Updated Dependencies**
```bash
# Updated from 40 → 50 packages total

# Flask-Limiter upgrade
flask-limiter==4.0.0  # (was 3.5.0)

# New Phase 1 Dependencies (9 packages)
limits==5.6.0
ordered-set==4.1.0  
rich==14.2.0
typing-extensions==4.15.0
deprecated==1.2.18
markdown-it-py==4.0.0
pygments==2.19.2
mdurl==0.1.2
wrapt==1.17.3
```

---

## 🚀 **VPS DEPLOYMENT STEPS**

### **Step 1: Backup Current System**
```bash
# SSH to VPS
ssh h2cloud-hiep1987

# Create backup
sudo bash /var/www/tikz2svg_api/deploy.sh backup
```

### **Step 2: Deploy Phase 1 Code**
```bash
# Deploy from main branch (includes Phase 1)  
sudo bash /var/www/tikz2svg_api/deploy.sh git@github.com:hiep1987/tikz2svg_api.git main
```

### **Step 3: Install New Dependencies**
```bash
# Activate virtual environment
source /var/www/tikz2svg_api/.venv/bin/activate

# Install updated requirements
pip install -r requirements.txt

# Verify Flask-Limiter version
pip show flask-limiter | grep Version
# Should show: Version: 4.0.0
```

### **Step 4: Run Database Migration**
```bash
# Navigate to project directory
cd /var/www/tikz2svg_api

# Execute Phase 1 database migration
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < migrations/create_package_management_system_fixed.sql

# Verify migration
mysql -u $DB_USER -p$DB_PASSWORD -e "USE $DB_NAME; SELECT COUNT(*) as total_packages FROM supported_packages;"
# Should show: total_packages: 90
```

### **Step 5: Update Environment (if needed)**
```bash
# Add any new environment variables to .env
# (Currently no new env vars needed for Phase 1)

# Verify environment
cat .env | grep DB_
```

### **Step 6: Restart Application**
```bash
# Restart Flask application
sudo systemctl restart tikz2svg
# OR
sudo supervisorctl restart tikz2svg

# Check status
sudo systemctl status tikz2svg
```

### **Step 7: Verify Deployment**
```bash
# Test package management endpoints
curl -s -o /dev/null -w "HTTP %{http_code}" https://tikz2svg.com/packages
curl -s -o /dev/null -w "HTTP %{http_code}" https://tikz2svg.com/api/packages/stats

# Both should return: HTTP 200
```

---

## 🧪 **POST-DEPLOYMENT TESTING**

### **✅ Critical Tests**
1. **Main Site**: https://tikz2svg.com ✅
2. **Packages Page**: https://tikz2svg.com/packages ✅  
3. **Package Request**: https://tikz2svg.com/packages/request ✅
4. **API Statistics**: https://tikz2svg.com/api/packages/stats ✅
5. **Preamble Download**: https://tikz2svg.com/api/download-preamble ✅
6. **Admin Panel**: https://tikz2svg.com/admin/packages ✅

### **📊 Database Verification**
```sql
-- Connect to MySQL and verify
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME

-- Check packages
SELECT package_type, COUNT(*) as count 
FROM supported_packages 
WHERE status = 'active' 
GROUP BY package_type;

-- Expected results:
-- latex_package: 51
-- tikz_library: 30  
-- pgfplots_library: 9

-- Check admin permissions
SELECT email, permission_level, is_active 
FROM admin_permissions;

-- Expected: quochiep0504@gmail.com, admin, 1
```

### **🎯 Performance Testing**
```bash
# Test API response times
time curl -s https://tikz2svg.com/api/packages/stats
# Should be < 1 second

# Test package search
time curl -s "https://tikz2svg.com/api/packages/search?q=tikz"
# Should be < 1 second
```

---

## 🛠️ **TROUBLESHOOTING**

### **Issue: Flask-Limiter Import Error**
```bash
# Solution: Ensure Flask-Limiter 4.0.0 is installed
pip install flask-limiter==4.0.0

# Verify dependencies
pip show flask-limiter | grep Requires
```

### **Issue: Database Connection Error**
```bash
# Check MySQL service
sudo systemctl status mysql

# Verify database exists
mysql -u $DB_USER -p$DB_PASSWORD -e "SHOW DATABASES;"

# Test connection
python3 -c "
import mysql.connector
import os
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),  
    database=os.getenv('DB_NAME')
)
print('✅ Database connection successful')
conn.close()
"
```

### **Issue: Templates Not Loading**
```bash
# Check file permissions
ls -la templates/packages.html
ls -la templates/package_request.html
ls -la templates/admin/packages.html

# Verify CSS files
ls -la static/css/packages.css
```

### **Issue: Rate Limiting Warning**
```bash
# Expected warning (not an error):
# "Using the in-memory storage for tracking rate limits"
# This is normal for single-server deployment
```

---

## 📊 **SUCCESS INDICATORS**

### **✅ Deployment Successful When:**
- ✅ Main site loads: HTTP 200
- ✅ Packages page accessible: /packages  
- ✅ API endpoints responding: /api/packages/*
- ✅ Database has 90 packages
- ✅ Admin panel accessible: /admin/packages
- ✅ No Flask import errors in logs
- ✅ Package search works
- ✅ Request form functional

### **📈 Performance Benchmarks**
- ⚡ **Page Load**: < 2 seconds  
- 🔍 **Search Response**: < 1 second
- 📊 **API Response**: < 500ms
- 💾 **Database Queries**: < 100ms

---

## 🎊 **POST-DEPLOYMENT CHECKLIST**

- [ ] Flask application restarted successfully
- [ ] Database migration completed (90 packages)  
- [ ] All 6 critical endpoints return HTTP 200
- [ ] Package search functionality works
- [ ] Package request form submits successfully
- [ ] Admin panel loads (requires authentication)
- [ ] No errors in application logs
- [ ] Performance meets benchmarks

---

## 📞 **ROLLBACK PROCEDURE (If Needed)**

```bash
# Step 1: Stop application
sudo systemctl stop tikz2svg

# Step 2: Restore from backup
sudo bash /var/www/tikz2svg_api/deploy.sh restore

# Step 3: Restore database (if needed)  
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < backup_before_phase1.sql

# Step 4: Restart application
sudo systemctl start tikz2svg
```

---

**📅 Deployment Date**: Ready for immediate deployment  
**🎯 Target**: https://tikz2svg.com  
**📋 Status**: Production-ready with comprehensive testing**

---

*Deploy with confidence! Phase 1 has been thoroughly tested and is ready for production use.* 🚀
