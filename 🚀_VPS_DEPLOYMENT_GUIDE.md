# 🚀 VPS DEPLOYMENT GUIDE - Phase 1-3 Optimizations

**Date:** October 31, 2025  
**Issue:** Pagination không hiển thị trên VPS dù đã có trên local

---

## 🔍 Problem Diagnosis

### Symptoms:
- ✅ Local có pagination UI
- ❌ VPS không có pagination UI
- ✅ Code đã được commit (commit `65742a8`)
- ✅ Code đã được push lên GitHub

### Root Cause:
VPS chưa pull code mới từ GitHub HOẶC chưa restart server sau khi pull.

---

## ✅ Solution: Deploy to VPS

### Step 1: SSH vào VPS

```bash
ssh user@your-vps-ip
# Hoặc
ssh user@your-domain.com
```

---

### Step 2: Navigate to Project Directory

```bash
cd /path/to/tikz2svg_api
# Ví dụ:
cd /var/www/tikz2svg_api
# Hoặc:
cd ~/tikz2svg_api
```

---

### Step 3: Check Current Git Status

```bash
# Kiểm tra branch hiện tại
git branch

# Kiểm tra commit hiện tại
git log --oneline -1

# Nếu không phải commit 65742a8, bạn cần pull code mới
```

**Expected Current State:**
- Commit cũ (không phải `65742a8`)
- Có thể có uncommitted changes

---

### Step 4: Backup Current State (Optional but Recommended)

```bash
# Tạo backup nếu có thay đổi local trên VPS
git stash save "Backup before pulling Phase 1-3 optimizations"

# Hoặc tạo branch backup
git checkout -b backup-before-phase123
git checkout main
```

---

### Step 5: Pull Latest Code from GitHub

```bash
# Đảm bảo đang ở branch main
git checkout main

# Pull code mới
git pull origin main

# Verify commit sau khi pull
git log --oneline -1
```

**Expected Output:**
```
65742a8 feat: Complete 3-phase optimization - Pagination + Rate Limiting + Lazy Loading
```

---

### Step 6: Verify Files Were Updated

```bash
# Kiểm tra app.py có pagination code
grep -n "ITEMS_PER_PAGE\|get_pagination_params" app.py

# Kiểm tra index.html có pagination UI
grep -n "pagination-container" templates/index.html

# Kiểm tra index.css có pagination styles
grep -n "pagination-btn" static/css/index.css
```

**Expected Output:**
- `app.py`: Tìm thấy `ITEMS_PER_PAGE = 50` và `def get_pagination_params`
- `index.html`: Tìm thấy `pagination-container`
- `index.css`: Tìm thấy `.pagination-btn`

---

### Step 7: Check Python Dependencies

```bash
# Activate virtual environment nếu có
source venv/bin/activate

# Kiểm tra Flask-Limiter đã được cài chưa (Phase 2 requirement)
pip list | grep -i flask-limiter

# Nếu chưa có, install
pip install Flask-Limiter==3.5.0
```

**Expected:**
```
Flask-Limiter    3.5.0
```

---

### Step 8: Restart Application

#### Option A: Nếu dùng systemd service

```bash
# Restart service
sudo systemctl restart tikz2svg

# Hoặc tên service khác
sudo systemctl restart tikz2svg_api
sudo systemctl restart gunicorn

# Kiểm tra status
sudo systemctl status tikz2svg

# Kiểm tra logs
sudo journalctl -u tikz2svg -f
```

---

#### Option B: Nếu dùng Gunicorn/uWSGI trực tiếp

```bash
# Tìm process ID
ps aux | grep gunicorn
ps aux | grep uwsgi

# Kill process cũ
sudo pkill gunicorn
# Hoặc
sudo kill -HUP <PID>

# Start lại
gunicorn --bind 0.0.0.0:5173 app:app --daemon
```

---

#### Option C: Nếu dùng screen/tmux

```bash
# List screens
screen -ls

# Attach to screen
screen -r tikz2svg

# Ctrl+C để stop app
# Chạy lại:
python app.py

# Detach: Ctrl+A, D
```

---

#### Option D: Nếu dùng Docker

```bash
# Rebuild image
docker build -t tikz2svg_api .

# Restart container
docker-compose restart
# Hoặc
docker restart tikz2svg_container

# Xem logs
docker logs -f tikz2svg_container
```

---

### Step 9: Verify Deployment Success

#### A. Check Server Logs

```bash
# Nếu dùng systemd
sudo journalctl -u tikz2svg -f

# Nếu có file log
tail -f /var/log/tikz2svg/app.log
tail -f logs/app.log
```

**Expected Log Output:**
```
✅ Pagination configured: 50 items per page
🔧 Rate Limiting: PRODUCTION mode
⚡ Limits: {'api_likes_preview': '30 per minute', ...}
```

---

#### B. Test via Browser

1. Mở browser và truy cập VPS URL:
   ```
   http://your-vps-ip:5173/
   # Hoặc
   https://your-domain.com/
   ```

2. Scroll xuống cuối trang

3. **Kiểm tra:**
   - ✅ Có thấy pagination UI không? (← Trước | 1 2 3 ... | Sau →)
   - ✅ Có thấy "Trang 1 / X" không?
   - ✅ Click vào page 2 có load được không?

---

#### C. Test via curl

```bash
# Test homepage
curl -s http://your-vps-ip:5173/ | grep -i "pagination-container"

# Nếu thấy output, pagination UI đã có
# Expected output: <div class="pagination-container" ...>
```

---

#### D. Test Pagination API

```bash
# Test page 1
curl -s "http://your-vps-ip:5173/?page=1" | grep -i "trang 1"

# Test page 2
curl -s "http://your-vps-ip:5173/?page=2" | grep -i "trang 2"
```

---

### Step 10: Test Rate Limiting (Phase 2)

```bash
# Test likes preview endpoint (should be rate limited)
for i in {1..35}; do
  echo "Request $i:"
  curl -s -o /dev/null -w "%{http_code}\n" \
    "http://your-vps-ip:5173/api/svg/1/likes/preview"
  sleep 0.5
done

# Expected:
# - First 30 requests: 200
# - Request 31+: 429 (Too Many Requests)
```

---

### Step 11: Monitor Performance

```bash
# Monitor CPU and memory
htop

# Monitor network
sudo iftop

# Monitor application logs
tail -f /var/log/tikz2svg/app.log
```

---

## 🐛 Troubleshooting

### Issue 1: Git Pull Fails

**Error:**
```
error: Your local changes to the following files would be overwritten by merge
```

**Solution:**
```bash
# Option A: Stash changes
git stash
git pull origin main
git stash pop

# Option B: Discard local changes
git reset --hard HEAD
git pull origin main
```

---

### Issue 2: Pagination UI Not Showing

**Check 1: Verify HTML Template**
```bash
grep -A 5 "pagination-container" templates/index.html
```

**Check 2: Verify CSS Loaded**
```bash
# Check if CSS file exists
ls -la static/css/index.css

# Check for pagination styles
grep "pagination-btn" static/css/index.css
```

**Check 3: Clear Browser Cache**
- Hard refresh: Ctrl+Shift+R (Chrome/Firefox)
- Or clear browser cache completely

**Check 4: Verify Backend Variables**
```python
# Check app.py logs for these variables
print(f"page={page}, total_pages={total_pages}")
```

---

### Issue 3: 500 Internal Server Error

**Check 1: Python Dependencies**
```bash
source venv/bin/activate
pip list | grep Flask-Limiter
```

**Check 2: Import Errors**
```bash
python -c "from app import app; print('✅ OK')"
```

**Check 3: Database Connection**
```bash
# Check if MySQL is running
sudo systemctl status mysql

# Check database credentials in .env
cat .env | grep DB_
```

---

### Issue 4: Rate Limiting Not Working

**Check 1: Flask-Limiter Installed**
```bash
pip show Flask-Limiter
```

**Check 2: Environment Variables**
```bash
cat .env | grep FLASK_ENV
# Should be 'production' on VPS
```

**Check 3: Test Rate Limit**
```bash
# Should return 429 after 30 requests
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code} " \
    "http://localhost:5173/api/svg/1/likes/preview"
done
echo ""
```

---

### Issue 5: Static Files Not Loading (404)

**Check 1: Static Files Exist**
```bash
ls -la static/css/index.css
ls -la static/js/file_card.js
```

**Check 2: Nginx Configuration (if using)**
```nginx
location /static {
    alias /path/to/tikz2svg_api/static;
}
```

**Check 3: File Permissions**
```bash
chmod -R 755 static/
```

---

## 📋 Verification Checklist

After deployment, verify all features:

### Phase 1: Pagination ✅
- [ ] Pagination UI visible on homepage (if > 50 files)
- [ ] Previous/Next buttons work
- [ ] Page numbers clickable
- [ ] URL updates with `?page=N`
- [ ] Pagination info displays (Trang X / Y)

### Phase 2: Rate Limiting ✅
- [ ] Rate limit config visible in logs
- [ ] 429 error after exceeding limit
- [ ] Custom 429 error page displays
- [ ] Rate limits are PRODUCTION values (30/min)

### Phase 3: Lazy Loading ✅
- [ ] Only ~10-15 images load initially
- [ ] Images load as you scroll
- [ ] Skeleton shimmer animation appears
- [ ] Likes preview loads progressively
- [ ] No 429 errors on initial page load

---

## 🎯 Quick Reference Commands

```bash
# 1. SSH to VPS
ssh user@vps-ip

# 2. Navigate to project
cd /path/to/tikz2svg_api

# 3. Pull latest code
git pull origin main

# 4. Verify commit
git log --oneline -1  # Should show: 65742a8

# 5. Install dependencies (if needed)
source venv/bin/activate
pip install Flask-Limiter==3.5.0

# 6. Restart service
sudo systemctl restart tikz2svg

# 7. Check logs
sudo journalctl -u tikz2svg -f

# 8. Test in browser
curl -s http://localhost:5173/ | grep pagination-container
```

---

## 📊 Expected Results

### Before Deployment:
```
❌ No pagination UI on VPS
❌ Old commit (not 65742a8)
❌ All 50+ files load at once
```

### After Deployment:
```
✅ Pagination UI visible (← Trước | 1 2 3 ... | Sau →)
✅ Commit 65742a8 active
✅ Lazy loading works (~10-15 initial loads)
✅ Rate limiting active (30 requests/min)
✅ Page loads faster (<2s)
```

---

## 🎉 Success!

If you see this after deployment:

1. ✅ Pagination UI at bottom of page
2. ✅ "Trang 1 / X • Hiển thị 50 / Y files"
3. ✅ Click page 2 works
4. ✅ No 429 errors on initial load

**Congratulations! Deployment successful!** 🚀

---

## 📞 Need Help?

If issues persist:

1. Check server logs: `sudo journalctl -u tikz2svg -f`
2. Check Python errors: `python -c "from app import app"`
3. Check git status: `git status && git log --oneline -1`
4. Verify files exist: `ls -la templates/index.html`

---

**End of Deployment Guide** 🎯

