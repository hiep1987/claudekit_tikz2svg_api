# 🚀 VPS Deployment Guide - Package Management System

**Target:** VPS Production (tikz2svg.com)  
**Date:** October 30, 2025  
**Method:** Manual SQL execution (GitHub auto-deploys code)

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### ✅ **Local Development Status**
- [x] Package management system working on localhost:5173
- [x] Database schema simplified (active/manual status)
- [x] Admin panel functional (quochiep0504@gmail.com)
- [x] Frontend templates tested
- [x] All code committed to GitHub

### ✅ **VPS Database Analysis**
- [x] VPS database: `tikz2svg`
- [x] User table: `user` (not `users`)
- [x] No existing package tables
- [x] Charset: utf8mb4_unicode_ci

---

## 🗄️ DATABASE SCHEMA DIFFERENCES

### **Local vs VPS:**

| Aspect | Local (tikz2svg_local) | VPS (tikz2svg) |
|--------|------------------------|----------------|
| User table | `user` | `user` ✅ Same |
| Package tables | ✅ Exists | ❌ Need to create |
| Charset | utf8mb4_unicode_ci | utf8mb4_unicode_ci ✅ |
| Collation | utf8mb4_unicode_ci | utf8mb4_unicode_ci ✅ |

---

## 📦 TABLES TO CREATE

### **1. supported_packages**
- **Purpose:** Danh sách packages được hỗ trợ
- **Status:**
  - `active` - Có sẵn trong TEX_TEMPLATE (28 packages)
  - `manual` - Cần thêm `%!<..>` (52 packages)

### **2. package_requests**
- **Purpose:** User requests cho packages mới
- **Fields:** package_name, justification, use_case, requester info, status

### **3. package_changelog**
- **Purpose:** Lịch sử thay đổi packages
- **Fields:** action_type, old/new values, admin email, reason

---

## 🔧 DEPLOYMENT STEPS

### **STEP 1: SSH to VPS**

```bash
ssh root@your-vps-ip
# hoặc
ssh user@tikz2svg.com
```

---

### **STEP 2: Backup Current Database**

```bash
# Backup toàn bộ database
mysqldump -u root -p tikz2svg > ~/backup_tikz2svg_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh ~/backup_tikz2svg_*.sql
```

**Expected output:**
```
-rw-r--r-- 1 root root 12M Oct 30 14:30 backup_tikz2svg_20251030_143000.sql
```

---

### **STEP 3: Connect to MySQL**

```bash
mysql -u root -p tikz2svg
```

**You should see:**
```
MySQL [tikz2svg]>
```

---

### **STEP 4: Verify Current Database**

```sql
-- Check current database
SELECT DATABASE();

-- Check existing tables
SHOW TABLES;

-- Verify NO package tables exist yet
SHOW TABLES LIKE '%package%';
```

**Expected output:**
```
+---------------------------+
| Tables_in_tikz2svg        |
+---------------------------+
| email_log                 |
| email_notifications       |
| keyword                   |
| notifications             |
| svg_action_log            |
| svg_comments              |
| svg_comment_likes         |
| svg_image                 |
| svg_image_keyword         |
| svg_like                  |
| user                      |
| user_action_log           |
| user_follow               |
| verification_tokens       |
+---------------------------+

Empty set (0.00 sec)  ← No package tables yet ✅
```

---

### **STEP 5: Execute Migration Script**

**Option A: Upload and execute file**

```bash
# Exit MySQL first
exit

# Upload migration script to VPS
scp VPS_PACKAGE_MANAGEMENT_MIGRATION.sql root@your-vps:/root/

# Execute script
mysql -u root -p tikz2svg < /root/VPS_PACKAGE_MANAGEMENT_MIGRATION.sql
```

---

**Option B: Copy-paste in MySQL prompt** (RECOMMENDED)

1. Open file: `VPS_PACKAGE_MANAGEMENT_MIGRATION.sql`
2. Copy entire content
3. In MySQL prompt, paste and press Enter
4. Wait for execution (~5-10 seconds)

**You should see output like:**
```
+----------------+---------------+
| current_database | migration_started |
+----------------+---------------+
| tikz2svg       | 2025-10-30 14:35:00 |
+----------------+---------------+

Query OK, 0 rows affected (0.02 sec)
Query OK, 0 rows affected (0.03 sec)
Query OK, 0 rows affected (0.02 sec)
Query OK, 11 rows affected (0.01 sec)
Query OK, 16 rows affected (0.01 sec)
...
```

---

### **STEP 6: Verify Migration**

```sql
-- 1. Check tables were created
SHOW TABLES LIKE '%package%';
```

**Expected:**
```
+---------------------------+
| Tables_in_tikz2svg        |
+---------------------------+
| package_changelog         |
| package_requests          |
| supported_packages        |
+---------------------------+
3 rows in set (0.00 sec)
```

---

```sql
-- 2. Count packages by status
SELECT 
    status,
    COUNT(*) as count
FROM supported_packages 
GROUP BY status;
```

**Expected:**
```
+--------+-------+
| status | count |
+--------+-------+
| active |    28 |
| manual |    52 |
+--------+-------+
2 rows in set (0.00 sec)
```

---

```sql
-- 3. Show active packages
SELECT package_name 
FROM supported_packages 
WHERE status = 'active' 
ORDER BY package_name;
```

**Expected (28 packages):**
```
+---------------------------+
| package_name              |
+---------------------------+
| amsfonts                  |
| amsmath                   |
| amssymb                   |
| angles                    |
| arrows.meta               |
| backgrounds               |
| calc                      |
| decorations.markings      |
| decorations.pathreplacing |
| decorations.text          |
| fontspec                  |
| graphicx                  |
| hobby                     |
| intersections             |
| math                      |
| patterns                  |
| patterns.meta             |
| pgfplots                  |
| polar                     |
| positioning               |
| quotes                    |
| shadings                  |
| spy                       |
| tikz                      |
| tikz-3dplot               |
| tkz-euclide               |
| tkz-tab                   |
| xcolor                    |
+---------------------------+
28 rows in set (0.00 sec)
```

---

```sql
-- 4. Check table structure
DESCRIBE supported_packages;
```

**Expected:**
```
+--------------+-------------------------+------+-----+-------------------+-------------------+
| Field        | Type                    | Null | Key | Default           | Extra             |
+--------------+-------------------------+------+-----+-------------------+-------------------+
| id           | int                     | NO   | PRI | NULL              | auto_increment    |
| package_name | varchar(255)            | NO   | UNI | NULL              |                   |
| status       | enum('active','manual') | NO   | MUL | manual            |                   |
| created_at   | timestamp               | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at   | timestamp               | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+--------------+-------------------------+------+-----+-------------------+-------------------+
```

---

```sql
-- 5. Check changelog
SELECT * FROM package_changelog ORDER BY created_at DESC LIMIT 1;
```

**Expected:**
```
+----+-----------------------+-------------+-------------+------------------------------+------------------------+
| id | package_name          | action_type | new_values  | changed_by_email            | change_reason          |
+----+-----------------------+-------------+-------------+------------------------------+------------------------+
|  1 | SYSTEM_INITIALIZATION | added       | {"schema...}| quochiep0504@gmail.com      | Initial setup...       |
+----+-----------------------+-------------+-------------+------------------------------+------------------------+
```

---

### **STEP 7: Exit MySQL**

```sql
exit
```

---

### **STEP 8: Pull Latest Code from GitHub**

```bash
cd /var/www/tikz2svg_api  # hoặc thư mục deploy của bạn

# Pull latest code
git pull origin main

# Check which files updated
git log --oneline -5
```

**Expected output:**
```
d4431d5 Fix: Error log not displaying
f1df69d fix: Resolve 3 critical bugs
1b234f7 feat: Add CJK Unicode support & Package Management
...
```

---

### **STEP 9: Restart Application**

```bash
# If using systemd
sudo systemctl restart tikz2svg

# Or if using supervisor
sudo supervisorctl restart tikz2svg

# Or if running directly
pkill -f "python.*app.py"
cd /var/www/tikz2svg_api
source venv/bin/activate
nohup python3 app.py &
```

---

### **STEP 10: Verify Application**

```bash
# Check if app is running
ps aux | grep app.py

# Check logs
tail -f /var/log/tikz2svg/app.log  # hoặc đường dẫn log của bạn
```

---

## 🧪 TESTING

### **Test 1: Access Packages Page**

```bash
curl http://tikz2svg.com/packages
```

**Expected:** HTML page với danh sách packages

---

### **Test 2: Access API**

```bash
curl http://tikz2svg.com/api/available_packages
```

**Expected JSON:**
```json
{
  "active_packages": 28,
  "manual_packages": 52,
  "total_packages": 80,
  "packages": [...]
}
```

---

### **Test 3: Test Request Form**

Visit: `http://tikz2svg.com/packages/request`

**Expected:** Form to request new package

---

### **Test 4: Admin Panel Access**

Visit: `http://tikz2svg.com/admin/packages`

**Expected:**
- If logged in as `quochiep0504@gmail.com`: ✅ Admin panel
- If other user: ❌ Access denied message

---

## 📊 MONITORING

### **Check Database Size**

```sql
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS "Size (MB)"
FROM information_schema.TABLES 
WHERE table_schema = 'tikz2svg' 
    AND table_name LIKE '%package%'
ORDER BY (data_length + index_length) DESC;
```

---

### **Monitor Package Requests**

```sql
-- Check pending requests
SELECT 
    COUNT(*) as pending_count
FROM package_requests 
WHERE status = 'pending';

-- Show recent requests
SELECT 
    id, package_name, requester_email, status, created_at
FROM package_requests 
ORDER BY created_at DESC 
LIMIT 10;
```

---

### **Monitor Package Usage**

```sql
-- Top requested packages (if you track usage)
SELECT 
    package_name, 
    status,
    created_at
FROM supported_packages 
ORDER BY created_at DESC 
LIMIT 20;
```

---

## 🔒 SECURITY CHECKLIST

- [x] Only admin email `quochiep0504@gmail.com` can access admin panel
- [x] Package requests require justification
- [x] All user inputs are sanitized
- [x] SQL injection protection (parameterized queries)
- [x] XSS protection (Jinja2 auto-escaping)
- [x] Rate limiting on form submissions
- [x] Changelog tracks all changes

---

## 🐛 TROUBLESHOOTING

### **Issue 1: Migration fails with "Table already exists"**

**Solution:**
```sql
-- Drop existing tables
DROP TABLE IF EXISTS package_changelog;
DROP TABLE IF EXISTS package_requests;
DROP TABLE IF EXISTS supported_packages;

-- Re-run migration script
```

---

### **Issue 2: Foreign key constraint fails**

**Check:**
```sql
-- Verify user table name
SHOW TABLES LIKE '%user%';

-- If it's 'users' instead of 'user', no foreign key will be created
-- This is OK - the system works without FK
```

---

### **Issue 3: Can't access admin panel**

**Debug:**
```python
# In Flask logs, check:
print(f"Current user email: {current_user.email}")
print(f"Admin email: quochiep0504@gmail.com")
print(f"Match: {current_user.email == 'quochiep0504@gmail.com'}")
```

---

### **Issue 4: Packages not showing on frontend**

**Check:**
```sql
-- Verify data exists
SELECT COUNT(*) FROM supported_packages;

-- Check Flask route
curl http://localhost:5000/api/available_packages
```

---

## 📝 ROLLBACK PROCEDURE

If something goes wrong:

```sql
-- Drop new tables
DROP TABLE IF EXISTS package_changelog;
DROP TABLE IF EXISTS package_requests;
DROP TABLE IF EXISTS supported_packages;

-- Restore from backup
exit

mysql -u root -p tikz2svg < ~/backup_tikz2svg_YYYYMMDD_HHMMSS.sql

-- Revert code
cd /var/www/tikz2svg_api
git log --oneline -10  # Find commit before package system
git checkout <commit-hash>

-- Restart app
sudo systemctl restart tikz2svg
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

### **Checklist:**

- [ ] All 3 tables created successfully
- [ ] 80 packages inserted (28 active + 52 manual)
- [ ] Changelog has 1 entry
- [ ] `/packages` page loads
- [ ] `/packages/request` form works
- [ ] `/admin/packages` accessible by admin only
- [ ] API `/api/available_packages` returns JSON
- [ ] No errors in Flask logs
- [ ] GitHub code deployed successfully

---

## 🎉 SUCCESS METRICS

After successful deployment:

```
✅ Tables: 3 (supported_packages, package_requests, package_changelog)
✅ Packages: 80 (28 active, 52 manual)
✅ Endpoints: 
   - /packages
   - /packages/request
   - /admin/packages
   - /api/available_packages
✅ Admin: quochiep0504@gmail.com
✅ Status: Production ready
```

---

## 📞 SUPPORT

If you encounter issues:

1. Check Flask logs: `tail -f /var/log/tikz2svg/app.log`
2. Check MySQL errors: `tail -f /var/log/mysql/error.log`
3. Check database: `mysql -u root -p tikz2svg`
4. Verify code: `git log --oneline -5`

---

**✅ DEPLOYMENT GUIDE COMPLETE!**

**Ready to deploy? Follow STEP 1-10 above!**

