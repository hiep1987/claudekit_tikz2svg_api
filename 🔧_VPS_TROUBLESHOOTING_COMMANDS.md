# 🔧 VPS TROUBLESHOOTING - Service Not Starting

**Issue:** Deploy thành công nhưng service không start, nginx trả về `410 Gone`

---

## 🚨 Kiểm Tra Ngay:

### 1. Check Service Status

```bash
# Kiểm tra status của service
sudo systemctl status tikz2svg

# Hoặc tên service khác:
sudo systemctl status tikz2svg_api
sudo systemctl status gunicorn
```

**Tìm:**
- ❌ `Active: failed` hoặc `Active: inactive (dead)`
- 🔍 Lỗi gì trong status output

---

### 2. Check Service Logs (QUAN TRỌNG NHẤT!)

```bash
# Xem logs của service (real-time)
sudo journalctl -u tikz2svg -f

# Hoặc xem 100 dòng cuối:
sudo journalctl -u tikz2svg -n 100

# Nếu tên service khác:
sudo journalctl -u tikz2svg_api -n 100
sudo journalctl -u gunicorn -n 100
```

**Tìm các lỗi:**
- ❌ Python import errors
- ❌ Missing dependencies
- ❌ Port already in use
- ❌ Permission denied
- ❌ Environment variables missing

---

### 3. Check Application Logs

```bash
# Nếu app có file log riêng:
tail -100 /var/www/tikz2svg_api/logs/app.log
tail -100 /var/www/tikz2svg_api/current/logs/app.log

# Hoặc:
tail -100 /var/log/tikz2svg/error.log
```

---

### 4. Test Manual Start (Debugging)

```bash
# Vào thư mục hiện tại
cd /var/www/tikz2svg_api/current

# Activate venv
source /var/www/tikz2svg_api/venv/bin/activate

# Test import
python3 -c "from app import app; print('✅ Import OK')"

# Nếu có lỗi → Check error message
```

**Các lỗi thường gặp:**

#### A. ModuleNotFoundError
```
ModuleNotFoundError: No module named 'flask_limiter'
```
**Fix:**
```bash
source /var/www/tikz2svg_api/venv/bin/activate
pip install Flask-Limiter==4.0.0
```

#### B. ImportError
```
ImportError: cannot import name 'XXX' from 'YYY'
```
**Fix:** Code mới có thay đổi import, cần check app.py

#### C. Environment Variables Missing
```
KeyError: 'DB_PASSWORD'
```
**Fix:** Check file `.env` có đầy đủ không

---

### 5. Check .env File

```bash
# Kiểm tra .env có tồn tại không
ls -la /var/www/tikz2svg_api/current/.env

# Xem nội dung (cẩn thận, có password!)
cat /var/www/tikz2svg_api/current/.env

# Check các biến quan trọng:
grep -E "DB_|FLASK_ENV|SECRET_KEY" /var/www/tikz2svg_api/current/.env
```

**Cần có:**
```env
FLASK_ENV=production
SECRET_KEY=...
DB_HOST=localhost
DB_USER=hiep1987
DB_PASSWORD=...
DB_NAME=tikz2svg
```

---

### 6. Check Port Conflicts

```bash
# Kiểm tra port 5000 hoặc 8000 có bị chiếm không
sudo netstat -tlnp | grep ':5000'
sudo netstat -tlnp | grep ':8000'

# Hoặc dùng ss:
sudo ss -tlnp | grep ':5000'
```

**Nếu port đã bị chiếm:**
```bash
# Kill process cũ
sudo kill -9 <PID>

# Hoặc restart service
sudo systemctl restart tikz2svg
```

---

### 7. Check Symlink

```bash
# Kiểm tra symlink 'current' có đúng không
ls -la /var/www/tikz2svg_api/current

# Expected: current -> releases/20251101_002052
```

**Nếu sai:**
```bash
cd /var/www/tikz2svg_api
sudo rm -f current
sudo ln -sf releases/20251101_002052 current
```

---

### 8. Check Permissions

```bash
# Kiểm tra owner của files
ls -la /var/www/tikz2svg_api/current/

# Expected: hiep1987:hiep1987

# Nếu sai, fix permissions:
sudo chown -R hiep1987:hiep1987 /var/www/tikz2svg_api/current/
```

---

### 9. Manual Start for Testing

```bash
# Stop service trước
sudo systemctl stop tikz2svg

# Activate venv
source /var/www/tikz2svg_api/venv/bin/activate

# Vào thư mục current
cd /var/www/tikz2svg_api/current

# Start manually để xem lỗi
python3 app.py

# HOẶC dùng gunicorn:
gunicorn --bind 127.0.0.1:5000 app:app

# Xem có lỗi gì không
# Ctrl+C để stop sau khi test
```

---

### 10. Restart Everything

```bash
# Restart service
sudo systemctl restart tikz2svg

# Đợi 2-3 giây
sleep 3

# Check status
sudo systemctl status tikz2svg

# Restart nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx
```

---

## 🎯 Các Lệnh Nhanh

```bash
# All-in-one check:
cd /var/www/tikz2svg_api
echo "=== Service Status ===" && \
sudo systemctl status tikz2svg --no-pager && \
echo -e "\n=== Recent Logs ===" && \
sudo journalctl -u tikz2svg -n 50 --no-pager && \
echo -e "\n=== Port Check ===" && \
sudo netstat -tlnp | grep ':5000' && \
echo -e "\n=== Current Symlink ===" && \
ls -la current && \
echo -e "\n=== Python Test ===" && \
source venv/bin/activate && \
cd current && \
python3 -c "from app import app; print('✅ Import OK')"
```

---

## 📋 Debugging Checklist

Chạy từng lệnh và ghi lại kết quả:

1. **Service Status:**
   ```bash
   sudo systemctl status tikz2svg
   ```
   - [ ] Active? (running/failed/inactive)
   - [ ] Error message?

2. **Service Logs:**
   ```bash
   sudo journalctl -u tikz2svg -n 50
   ```
   - [ ] Python errors?
   - [ ] Import errors?
   - [ ] Port conflicts?

3. **Manual Import:**
   ```bash
   cd /var/www/tikz2svg_api/current
   source /var/www/tikz2svg_api/venv/bin/activate
   python3 -c "from app import app; print('OK')"
   ```
   - [ ] Imports successfully?
   - [ ] Error message?

4. **.env File:**
   ```bash
   cat /var/www/tikz2svg_api/current/.env | wc -l
   ```
   - [ ] File exists?
   - [ ] Has content? (>10 lines)

5. **Symlink:**
   ```bash
   ls -la /var/www/tikz2svg_api/current
   ```
   - [ ] Points to latest release?

---

## 🚑 Emergency Quick Fix

Nếu không biết lỗi gì, thử rollback:

```bash
# Rollback về release trước đó
cd /var/www/tikz2svg_api
sudo rm -f current
sudo ln -sf releases/20251031_150039 current
sudo systemctl restart tikz2svg
```

---

## ✅ Sau Khi Fix

```bash
# 1. Restart service
sudo systemctl restart tikz2svg

# 2. Check status
sudo systemctl status tikz2svg

# Expected: Active: active (running)

# 3. Check health endpoint
curl http://localhost:5000/health
# Expected: {"status":"healthy"}

# 4. Check nginx
curl -I http://localhost
# Expected: 200 OK (or 301 redirect to HTTPS)

# 5. Test in browser
# https://your-domain.com/
```

---

## 📤 Báo Lỗi Cho Assistant

Copy output của các lệnh này:

```bash
# 1. Service logs (50 dòng cuối)
sudo journalctl -u tikz2svg -n 50 --no-pager

# 2. Manual import test
cd /var/www/tikz2svg_api/current && \
source /var/www/tikz2svg_api/venv/bin/activate && \
python3 -c "from app import app; print('✅ OK')" 2>&1
```

Paste output và tôi sẽ giúp debug! 😊

