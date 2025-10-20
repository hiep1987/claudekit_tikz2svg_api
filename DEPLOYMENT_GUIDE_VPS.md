# Deployment Guide - Caption Feature to VPS

**Date:** October 20, 2025  
**Feature:** Image Caption with MathJax support

---

## 📋 Pre-Deployment Checklist

- [ ] Backup database trước khi migrate
- [ ] Test migration script trên local
- [ ] Review tất cả code changes
- [ ] Có quyền truy cập VPS (SSH)
- [ ] Có database credentials (user, password)

---

## 🗄️ Step 1: Backup Database (QUAN TRỌNG!)

### Trên VPS:

```bash
# SSH vào VPS
ssh user@your-vps-ip

# Backup database
mysqldump -u your_db_user -p your_db_name > backup_before_caption_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file exists
ls -lh backup_before_caption_*.sql

# Optional: Download backup to local
scp user@vps-ip:/path/to/backup_before_caption_*.sql ~/backups/
```

---

## 🔧 Step 2: Upload Files to VPS

### Method 1: Using Git (Recommended)

```bash
# Trên local: Commit và push
git add .
git commit -m "feat: Add image caption feature with MathJax support"
git push origin feature/base-template-migration

# Trên VPS: Pull changes
ssh user@your-vps-ip
cd /path/to/tikz2svg_api
git pull origin feature/base-template-migration
```

### Method 2: Using SCP (Direct Upload)

```bash
# Upload migration script
scp migrate_caption.py user@vps-ip:/path/to/tikz2svg_api/

# Upload modified files
scp app.py user@vps-ip:/path/to/tikz2svg_api/
scp templates/view_svg.html user@vps-ip:/path/to/tikz2svg_api/templates/
scp templates/base.html user@vps-ip:/path/to/tikz2svg_api/templates/
scp static/css/view_svg.css user@vps-ip:/path/to/tikz2svg_api/static/css/
scp static/js/view_svg.js user@vps-ip:/path/to/tikz2svg_api/static/js/
```

---

## 💾 Step 3: Run Database Migration

### Option A: Using Python Script (RECOMMENDED)

```bash
# SSH to VPS
ssh user@your-vps-ip

# Navigate to project
cd /path/to/tikz2svg_api

# Activate virtual environment if using one
source venv/bin/activate  # hoặc source .venv/bin/activate

# Run migration script
python3 migrate_caption.py

# Sẽ hỏi confirm:
# Continue with migration? (yes/no): yes
```

**Expected Output:**
```
============================================================
Caption Column Migration Script
============================================================

Connecting to database:
  Host: localhost
  Database: tikz2svg
  User: your_db_user

✅ Connected successfully!

Checking if 'caption' column exists...

📝 Adding 'caption' column...
✅ Migration successful!

📋 Verifying new schema:
  - id                   int                  NO    PRI  
  - filename             varchar(255)         YES        
  - tikz_code            text                 YES        
  - keywords             text                 YES        
  - caption              text                 YES         🆕
  - created_at           datetime             YES        
  - user_id              int                  YES   MUL  

📊 Total images in database: 120
   All images now have 'caption' column (default: NULL)

============================================================
✅ Migration completed successfully!
============================================================
```

### Option B: Using MySQL Command Line

```bash
# SSH to VPS
ssh user@your-vps-ip

# Method 1: Run SQL file
mysql -u your_db_user -p your_db_name < add_image_caption_column.sql

# Method 2: Interactive mode
mysql -u your_db_user -p
```

```sql
USE your_db_name;

-- Add caption column
ALTER TABLE svg_image 
ADD COLUMN caption TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
COMMENT 'Image caption/description with LaTeX/MathJax support'
AFTER keywords;

-- Verify
DESCRIBE svg_image;

-- Should see:
-- caption | text | YES |  | NULL |

EXIT;
```

### Option C: Using phpMyAdmin (if available)

1. Login to phpMyAdmin
2. Select your database
3. Click on `svg_image` table
4. Go to "Structure" tab
5. Click "Add column" after `keywords`
6. Set:
   - Name: `caption`
   - Type: `TEXT`
   - Collation: `utf8mb4_unicode_ci`
   - Null: `Yes`
   - Default: `NULL`
7. Click "Save"

---

## 🔄 Step 4: Restart Application

### For Systemd Service:

```bash
# Restart Flask app
sudo systemctl restart tikz2svg

# Check status
sudo systemctl status tikz2svg

# View logs
sudo journalctl -u tikz2svg -f
```

### For PM2:

```bash
# Restart app
pm2 restart tikz2svg

# Check status
pm2 status

# View logs
pm2 logs tikz2svg
```

### For Gunicorn/uWSGI:

```bash
# Restart gunicorn
sudo systemctl restart gunicorn

# Or reload gracefully
sudo systemctl reload gunicorn

# Check status
sudo systemctl status gunicorn
```

### Manual Restart:

```bash
# Kill old process
pkill -f "flask run"
# or
pkill -f "gunicorn"

# Start new process (adjust based on your setup)
cd /path/to/tikz2svg_api
source venv/bin/activate
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app &
```

---

## ✅ Step 5: Verify Deployment

### 5.1 Check Database

```bash
mysql -u your_db_user -p your_db_name -e "DESCRIBE svg_image"
```

Expected: Column `caption` exists

### 5.2 Test Web Interface

```bash
# Open browser and navigate to:
https://your-domain.com/view_svg/any_existing_image.svg

# Should see:
# - "📝 Mô tả ảnh" section
# - "Thêm mô tả" button (if you're the owner)
# - No JavaScript errors in console (F12)
```

### 5.3 Test Caption CRUD

**As Image Owner:**
1. Navigate to your own image
2. Click "Thêm mô tả"
3. Enter text: "Test caption with formula: $x^2$"
4. Click "Lưu"
5. Verify:
   - ✅ Caption displays without refresh
   - ✅ Formula renders as x²
   - ✅ Success message shows

**Test Edit:**
1. Click "Chỉnh sửa mô tả"
2. Change text
3. Click "Lưu"
4. Verify update works

**Test Line Breaks:**
1. Enter caption with Enter key
2. Verify preview shows line breaks
3. Save and verify display shows line breaks

---

## 🐛 Troubleshooting

### Problem 1: Migration fails with "Access denied"

**Error:**
```
MySQL Error: (1142, "ALTER command denied to user 'user'@'localhost' for table 'svg_image'")
```

**Solution:**
```sql
-- Grant ALTER permission
GRANT ALTER ON your_db_name.* TO 'your_db_user'@'localhost';
FLUSH PRIVILEGES;
```

### Problem 2: Column already exists

**Error:**
```
MySQL Error: (1060, "Duplicate column name 'caption'")
```

**Solution:**
Migration already ran. Verify with:
```sql
DESCRIBE svg_image;
```

### Problem 3: MathJax not rendering

**Symptoms:**
- Formulas show as raw text: `$x^2$`
- No rendering

**Check:**
1. Open browser console (F12)
2. Look for MathJax errors
3. Verify MathJax CDN loads:
   ```
   Network tab → Filter: mathjax
   Should see: tex-mml-chtml.js (200 OK)
   ```

**Solution:**
Clear browser cache: Ctrl+Shift+R

### Problem 4: "Edit button not found"

**Check Console:**
```javascript
document.getElementById('edit-caption-btn')
// Should return: <button> element
// If null: User not owner or not logged in
```

**Solution:**
- Verify logged in as image owner
- Check `user_id` matches image `user_id`

### Problem 5: Line breaks not showing

**Solution:**
Hard refresh: Ctrl+Shift+R (clear CSS cache)

---

## 📊 Monitoring

### Check Logs

```bash
# System logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Application logs
tail -f /path/to/app.log

# PM2 logs
pm2 logs tikz2svg --lines 100
```

### Database Queries

```sql
-- Check total images with captions
SELECT COUNT(*) FROM svg_image WHERE caption IS NOT NULL AND caption != '';

-- Check recent captions
SELECT id, filename, LEFT(caption, 50) as caption_preview, created_at 
FROM svg_image 
WHERE caption IS NOT NULL 
ORDER BY created_at DESC 
LIMIT 10;

-- Check caption with formulas
SELECT id, filename, caption 
FROM svg_image 
WHERE caption LIKE '%$%' 
LIMIT 5;
```

---

## 🔄 Rollback Plan (If Needed)

### If migration causes issues:

```bash
# 1. Restore from backup
mysql -u your_db_user -p your_db_name < backup_before_caption_YYYYMMDD_HHMMSS.sql

# 2. Revert code changes
git checkout main  # or previous stable branch
git pull

# 3. Restart application
sudo systemctl restart tikz2svg

# 4. Verify old version works
curl https://your-domain.com/health
```

### If only want to remove caption column:

```sql
ALTER TABLE svg_image DROP COLUMN caption;
```

---

## 📝 Post-Deployment Tasks

- [ ] Verify migration successful
- [ ] Test caption CRUD operations
- [ ] Test MathJax rendering
- [ ] Test on mobile device
- [ ] Monitor error logs for 24h
- [ ] Update production documentation
- [ ] Notify team of new feature
- [ ] Create user guide (optional)

---

## 🔐 Security Checklist

- [ ] XSS protection verified (HTML escaped)
- [ ] Owner validation works (403 for non-owners)
- [ ] Input validation (max 5000 chars)
- [ ] No SQL injection possible (parameterized queries)
- [ ] HTTPS enabled for production

---

## 📞 Support

If issues persist:

1. **Check logs:** Application + Database + Nginx
2. **Test locally:** Reproduce issue on local dev
3. **Database state:** Verify schema and data
4. **Browser console:** Check for JS errors
5. **Network tab:** Verify API calls succeed

**Debug Command:**
```bash
# SSH to VPS
ssh user@vps-ip

# Run Python debug
cd /path/to/tikz2svg_api
source venv/bin/activate

python3 << 'EOF'
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    database=os.environ.get('DB_NAME')
)

cursor = conn.cursor(dictionary=True)

# Test query
cursor.execute("SELECT * FROM svg_image WHERE caption IS NOT NULL LIMIT 1")
result = cursor.fetchone()

if result:
    print("✅ Caption column working!")
    print(f"Sample: {result['filename']} → {result['caption'][:50]}")
else:
    print("⚠️ No captions found yet")

cursor.close()
conn.close()
EOF
```

---

## ✅ Success Criteria

Migration is successful when:

1. ✅ `caption` column exists in `svg_image` table
2. ✅ Application starts without errors
3. ✅ Caption section visible on view_svg page
4. ✅ Owner can add/edit captions
5. ✅ MathJax renders formulas correctly
6. ✅ Line breaks preserved
7. ✅ No console errors
8. ✅ Responsive design works on mobile

---

*Deployment guide created: October 20, 2025*  
*Version: 1.0*

