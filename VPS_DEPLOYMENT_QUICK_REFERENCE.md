# VPS Deployment - Quick Reference

**Feature:** Image Caption  
**Target:** Production VPS

---

## ⚡ Quick Commands

### 1️⃣ Backup Database (REQUIRED)
```bash
mysqldump -u DB_USER -p DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2️⃣ Upload Files
```bash
# Via Git (recommended)
git pull origin feature/base-template-migration

# Or via SCP
scp migrate_caption.py user@vps:/path/to/app/
```

### 3️⃣ Run Migration
```bash
# Option A: Python script (safe)
python3 migrate_caption.py

# Option B: SQL direct
mysql -u DB_USER -p DB_NAME < add_image_caption_column.sql

# Option C: Interactive
mysql -u DB_USER -p
> USE DB_NAME;
> ALTER TABLE svg_image ADD COLUMN caption TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL AFTER keywords;
> DESCRIBE svg_image;
> EXIT;
```

### 4️⃣ Restart App
```bash
# Systemd
sudo systemctl restart tikz2svg

# PM2
pm2 restart tikz2svg

# Gunicorn
sudo systemctl restart gunicorn
```

### 5️⃣ Verify
```bash
# Check DB
mysql -u DB_USER -p DB_NAME -e "DESCRIBE svg_image"

# Check app
curl https://your-domain.com/health

# Check logs
tail -f /var/log/your-app.log
```

---

## 🎯 One-Liner (Full Deployment)

```bash
mysqldump -u DB_USER -p DB_NAME > backup_$(date +%Y%m%d).sql && \
git pull && \
python3 migrate_caption.py && \
sudo systemctl restart tikz2svg && \
echo "✅ Deployment complete!"
```

---

## ❌ Rollback (If Needed)

```bash
# Restore database
mysql -u DB_USER -p DB_NAME < backup_YYYYMMDD.sql

# Revert code
git checkout main && git pull

# Restart
sudo systemctl restart tikz2svg
```

---

## 🐛 Quick Debug

```bash
# Check if column exists
mysql -u DB_USER -p -e "USE DB_NAME; DESCRIBE svg_image;" | grep caption

# Test caption API
curl -X GET https://your-domain.com/view_svg/test.svg

# Check logs
journalctl -u tikz2svg -n 50 --no-pager
```

---

## 📋 Checklist

- [ ] Database backup created
- [ ] Migration script uploaded
- [ ] Migration executed successfully  
- [ ] Application restarted
- [ ] Feature tested on production
- [ ] No errors in logs

---

**Files to Deploy:**
1. `migrate_caption.py` (migration)
2. `app.py` (backend)
3. `templates/base.html` (MathJax)
4. `templates/view_svg.html` (UI)
5. `static/css/view_svg.css` (styling)
6. `static/js/view_svg.js` (logic)

**Database Change:**
```sql
ALTER TABLE svg_image 
ADD COLUMN caption TEXT 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci 
DEFAULT NULL 
AFTER keywords;
```

**Verify Success:**
- Visit: `https://your-domain.com/view_svg/any_image.svg`
- See: "📝 Mô tả ảnh" section
- Test: Add/edit caption works
- Check: MathJax renders formulas

---

*Quick ref version: 1.0*

