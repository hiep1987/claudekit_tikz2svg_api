# 📁 Cấu hình Static Files và Thư mục Làm việc - TikZ to SVG API

## 🚨 Vấn đề Quan trọng

### Thư mục làm việc hiện tại
- **Ứng dụng chạy từ:** `/var/www/tikz2svg_api/current/` (do WorkingDirectory trong service)
- **Thư mục current:** `/var/www/tikz2svg_api/current/` (symbolic link)
- **Thư mục shared:** `/var/www/tikz2svg_api/shared/`

### Cấu hình STATIC_ROOT
```python
# Trong app.py
STATIC_ROOT = os.environ.get('TIKZ_SVG_DIR', os.path.join(os.getcwd(), 'static'))
```

**Vấn đề:** Biến môi trường `TIKZ_SVG_DIR` không được set, nên ứng dụng sử dụng:
- `os.getcwd()` = `/var/www/tikz2svg_api/current/` (do WorkingDirectory)
- `STATIC_ROOT` = `/var/www/tikz2svg_api/current/static/`

**Nhưng thư mục `/var/www/tikz2svg_api/current/static/` là thư mục thực, không phải symbolic link!**

## 📂 Cấu trúc thư mục thực tế

```
/var/www/tikz2svg_api/
├── shared/
│   └── static/
│       ├── avatars/                    ← Ảnh avatar thực tế (4 files)
│       │   ├── avatar_2de74228358b4add9401f11be264069c.png
│       │   ├── avatar_4438c389b4c546be89ecc7b2423c5bd7.png
│       │   ├── avatar_6e44d63b109a448799d0bf4efc514a2d.png
│       │   └── avatar_981ea111072146589fa26c214c492b77.png
│       ├── css -> /var/www/tikz2svg_api/current/static/css
│       ├── js -> /var/www/tikz2svg_api/current/static/js
│       └── images/
├── current/ (symbolic link)
│   └── static/                         ← ĐÃ THÀNH SYMBOLIC LINK
│       └── (trỏ đến shared/static)
└── static/                             ← SYMBOLIC LINK
    └── (trỏ đến shared/static)
```

## 🔗 Symbolic Link - Giải thích chi tiết

### Symbolic Link là gì?
Symbolic link (symlink) giống như một "shortcut" hoặc "đường dẫn tắt" trong hệ thống file. Nó trỏ đến một thư mục hoặc file khác.

### Ví dụ minh họa:

#### **Trước khi tạo symbolic link:**
```
/var/www/tikz2svg_api/
├── shared/
│   └── static/                    ← Thư mục thực chứa file cũ
│       ├── avatars/
│       ├── file1.svg
│       └── file2.png
└── current/ (symbolic link)
    └── static/                    ← Thư mục thực riêng biệt
        ├── avatars/
        ├── file3.svg              ← File mới được tạo ở đây
        └── file4.png
```

**Vấn đề:** 
- Ứng dụng chạy từ `current/` nên tạo file trong `current/static/`
- Khi deploy mới, `current/` sẽ trỏ đến release mới → file bị mất
- File trong `shared/static/` vẫn tồn tại

#### **Sau khi tạo symbolic link:**
```
/var/www/tikz2svg_api/
├── shared/
│   └── static/                    ← Thư mục thực chứa tất cả file
│       ├── avatars/
│       ├── file1.svg
│       ├── file2.png
│       ├── file3.svg              ← File mới được tạo ở đây
│       └── file4.png
└── current/ (symbolic link)
    └── static/                    ← Symbolic link trỏ đến shared/static
        └── (tất cả file từ shared/static)
```

**Lợi ích:**
- Ứng dụng vẫn chạy từ `current/` (không thay đổi)
- File được tạo trong `shared/static/` (bền vững)
- Khi deploy mới, file không bị mất

### Cách hoạt động của symbolic link:

#### **Trước khi tạo symbolic link:**
```bash
# Ứng dụng chạy từ current/
cd /var/www/tikz2svg_api/current/

# STATIC_ROOT = /var/www/tikz2svg_api/current/static
# File được tạo trong current/static/file.svg (thư mục thực)
```

#### **Sau khi tạo symbolic link:**
```bash
# Ứng dụng vẫn chạy từ current/
cd /var/www/tikz2svg_api/current/

# STATIC_ROOT = /var/www/tikz2svg_api/current/static
# Nhưng current/static là symbolic link trỏ đến shared/static
# File được tạo trong shared/static/file.svg (thực tế)
```

### Quá trình tạo symbolic link:
```bash
# 1. Backup thư mục hiện tại
cp -r /var/www/tikz2svg_api/current/static /var/www/tikz2svg_api/current/static_backup

# 2. Copy file mới về shared/static
cp /var/www/tikz2svg_api/current/static/file.svg /var/www/tikz2svg_api/shared/static/

# 3. Xóa thư mục current/static
rm -rf /var/www/tikz2svg_api/current/static

# 4. Tạo symbolic link
ln -s /var/www/tikz2svg_api/shared/static /var/www/tikz2svg_api/current/static
```

### Kiểm tra symbolic link:
```bash
# Xem symbolic link
ls -la /var/www/tikz2svg_api/current/static
# Kết quả: lrwxrwxrwx 1 hiep1987 hiep1987 35 Aug 25 23:09 static -> /var/www/tikz2svg_api/shared/static

# Truy cập file qua symbolic link
ls /var/www/tikz2svg_api/current/static/
# Hiển thị tất cả file từ shared/static/
```

## 🔧 Giải pháp đề xuất

### 1. Tạo symbolic link (Khuyến nghị)
```bash
# Tạo symbolic link từ thư mục gốc đến shared/static
cd /var/www/tikz2svg_api/
ln -s shared/static static

# Tạo symbolic link từ current/static đến shared/static
rm -rf /var/www/tikz2svg_api/current/static
ln -s /var/www/tikz2svg_api/shared/static /var/www/tikz2svg_api/current/static
```

### 2. Set biến môi trường ✅ ĐÃ THỰC HIỆN
Thêm vào file `/var/www/tikz2svg_api/shared/.env`:
```env
TIKZ_SVG_DIR=/var/www/tikz2svg_api/shared/static
```

### 3. Sửa code app.py
```python
# Thay đổi cấu hình STATIC_ROOT
STATIC_ROOT = os.environ.get('TIKZ_SVG_DIR', '/var/www/tikz2svg_api/shared/static')
```

## ⚠️ Lưu ý quan trọng

### Vấn đề hiện tại:
1. **Avatar files bị phân tán:** 
   - 4 files cũ trong `shared/static/avatars/`
   - 1 file mới trong `current/static/avatars/`

2. **Cấu hình không nhất quán:**
   - CSS/JS sử dụng symbolic links đến current
   - Avatars sử dụng thư mục thực trong shared

3. **Ứng dụng có thể không tìm thấy static files:**
   - STATIC_ROOT trỏ đến thư mục không tồn tại
   - Flask có thể fallback về thư mục khác

### Hành động cần thiết:
1. **Kiểm tra logs** để xem Flask có báo lỗi về static files không
2. **Thống nhất cấu trúc** thư mục static
3. **Test upload avatar** để đảm bảo hoạt động đúng
4. **Backup dữ liệu** trước khi thay đổi

## 🚨 Vấn đề 502 Bad Gateway - ĐÃ KHẮC PHỤC

### Nguyên nhân:
```
FileExistsError: [Errno 17] File exists: '/var/www/tikz2svg_api/shared/static/avatars'
```

### Vấn đề cụ thể:
- Thư mục `avatars` trong `shared/static/` đã trở thành symbolic link
- Symbolic link trỏ đến thư mục không tồn tại: `/var/www/tikz2svg_api/current/static/avatars`
- Ứng dụng cố gắng tạo thư mục `avatars` nhưng gặp lỗi vì nó đã tồn tại (dưới dạng symbolic link)

### Giải pháp đã áp dụng:
```bash
# 1. Xóa symbolic link
cd /var/www/tikz2svg_api/shared/static
rm avatars

# 2. Tạo lại thư mục thực
mkdir avatars

# 3. Khôi phục các file avatar từ backup
cp /var/www/tikz2svg_api/releases/20250825_164713/static/avatars/* /var/www/tikz2svg_api/shared/static/avatars/

# 4. Khởi động lại service
sudo systemctl restart tikz2svg.service
```

### Kết quả:
- ✅ Service `tikz2svg.service` đã chạy thành công
- ✅ Website https://tikz2svg.com/ hoạt động bình thường
- ✅ Trả về HTTP 200 thay vì 502 Bad Gateway

## 🚨 Vấn đề File SVG được lưu sai thư mục - ĐÃ KHẮC PHỤC HOÀN TOÀN

### Nguyên nhân gốc rễ:
- **WorkingDirectory trong service:** `/var/www/tikz2svg_api/current/`
- **STATIC_ROOT thực tế:** `/var/www/tikz2svg_api/current/static/` (thư mục thực)
- **File được lưu trực tiếp vào:** `current/static/` thay vì `shared/static/`

### Vấn đề cụ thể:
- Service file có `WorkingDirectory=/var/www/tikz2svg_api/current/`
- `os.getcwd()` trả về `/var/www/tikz2svg_api/current/`
- `STATIC_ROOT` = `/var/www/tikz2svg_api/current/static/`
- File mới được tạo trong `current/static/` (sẽ bị mất khi deploy)

### Giải pháp cuối cùng đã áp dụng:
```bash
# 1. Backup thư mục current/static
cd /var/www/tikz2svg_api
cp -r current/static current/static_backup

# 2. Copy file mới về shared/static
cp /var/www/tikz2svg_api/current/static/115852900894156127858_060516260825.* /var/www/tikz2svg_api/shared/static/

# 3. Xóa thư mục current/static và tạo symbolic link
rm -rf /var/www/tikz2svg_api/current/static
ln -s /var/www/tikz2svg_api/shared/static /var/www/tikz2svg_api/current/static

# 4. Thêm biến môi trường vào .env
echo "TIKZ_SVG_DIR=/var/www/tikz2svg_api/shared/static" >> /var/www/tikz2svg_api/shared/.env

# 5. Khởi động lại service
sudo systemctl restart tikz2svg.service
```

### Kết quả:
- ✅ **File SVG mới được lưu trong `shared/static/`** (bền vững qua các lần deploy)
- ✅ **Symbolic link `/var/www/tikz2svg_api/current/static/`** trỏ đến `shared/static/`
- ✅ **Cấu hình `STATIC_ROOT` và `UPLOAD_FOLDER`** hoạt động đúng
- ✅ **File không bị mất khi deploy mới**
- ✅ **Ứng dụng vẫn chạy từ `current/` nhưng file được lưu trong `shared/`**
- ✅ **Biến môi trường `TIKZ_SVG_DIR` đã được set trong `.env`**

## 📝 Ghi chú kỹ thuật

### Flask static folder behavior:
- Nếu `static_folder` không tồn tại, Flask sẽ tìm trong thư mục hiện tại
- Có thể fallback về thư mục khác tùy thuộc vào cấu hình

### Symbolic links:
- `css` và `js` đã được link đúng đến `current/static/`
- `avatars` cần được xử lý tương tự hoặc thống nhất

### Environment variables:
- File `.env` trong `shared/` được load bởi `load_dotenv()`
- Biến `TIKZ_SVG_DIR` đã được set: `/var/www/tikz2svg_api/shared/static`

### Service configuration:
- **WorkingDirectory:** `/var/www/tikz2svg_api/current/` (trong override.conf)
- **STATIC_ROOT thực tế:** `/var/www/tikz2svg_api/current/static/`
- **Giải pháp:** Tạo symbolic link từ `current/static` đến `shared/static`

### Troubleshooting 502 Bad Gateway:
1. **Kiểm tra service status:** `sudo systemctl status tikz2svg.service`
2. **Xem logs:** `sudo journalctl -u tikz2svg.service --no-pager -n 50`
3. **Kiểm tra symbolic links:** `ls -la /var/www/tikz2svg_api/shared/static/`
4. **Kiểm tra thư mục đích:** Đảm bảo thư mục đích của symbolic link tồn tại

### Troubleshooting File lưu sai thư mục:
1. **Kiểm tra WorkingDirectory:** `sudo cat /etc/systemd/system/tikz2svg.service.d/override.conf`
2. **Kiểm tra STATIC_ROOT:** `python3 -c "import os; print(os.environ.get('TIKZ_SVG_DIR', os.path.join(os.getcwd(), 'static')))"`
3. **Kiểm tra symbolic link:** `ls -la /var/www/tikz2svg_api/current/static`
4. **Kiểm tra file mới:** `find /var/www/tikz2svg_api -name "*.svg" -newer /var/www/tikz2svg_api/current/static/`
5. **Copy file về đúng thư mục:** `cp /var/www/tikz2svg_api/current/static/* /var/www/tikz2svg_api/shared/static/`

### Kiểm tra biến môi trường:
```bash
# Kiểm tra biến TIKZ_SVG_DIR
python3 -c "import os; from dotenv import load_dotenv; load_dotenv('/var/www/tikz2svg_api/shared/.env'); print('TIKZ_SVG_DIR:', os.environ.get('TIKZ_SVG_DIR'))"

# Kiểm tra STATIC_ROOT thực tế
python3 -c "import os; from dotenv import load_dotenv; load_dotenv('/var/www/tikz2svg_api/shared/.env'); STATIC_ROOT = os.environ.get('TIKZ_SVG_DIR', os.path.join(os.getcwd(), 'static')); print('STATIC_ROOT:', STATIC_ROOT)"
```

---

## 🔴 YÊU CẦU BẮT BUỘC CHO VPS DEPLOYMENT

### ⚠️ Redis Server - BẮT BUỘC

**Tại sao cần Redis?**
- Flask-Limiter sử dụng Redis để lưu trữ rate limit counters
- Đảm bảo rate limiting hoạt động đúng với multiple Gunicorn workers
- Tracking chính xác số requests per IP address
- Tránh tình trạng tất cả users share chung rate limit counter

**Vấn đề nếu không có Redis:**
- ❌ Flask-Limiter fallback về `memory://` storage
- ❌ Mỗi worker có counter riêng → không đồng bộ
- ❌ Rate limiting không chính xác
- ❌ Users bị 429 (TOO MANY REQUESTS) sai

### 📋 Cài đặt Redis trên VPS

#### **Ubuntu/Debian:**
```bash
# 1. Cài đặt Redis
sudo apt update
sudo apt install redis-server -y

# 2. Cấu hình Redis để chạy như service
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 3. Kiểm tra Redis hoạt động
redis-cli ping
# Expected output: PONG

# 4. Kiểm tra Redis đang listen
sudo systemctl status redis-server
```

#### **CentOS/RHEL:**
```bash
# 1. Cài đặt Redis
sudo yum install redis -y

# 2. Start và enable Redis
sudo systemctl enable redis
sudo systemctl start redis

# 3. Kiểm tra
redis-cli ping
```

### 🔧 Cấu hình Redis cho TikZ2SVG

#### **1. Thêm REDIS_URL vào .env:**
```bash
# File: /var/www/tikz2svg_api/shared/.env
echo "REDIS_URL=redis://localhost:6379/0" >> /var/www/tikz2svg_api/shared/.env
```

#### **2. Cấu hình Systemd Service:**
```bash
# Edit service override
sudo systemctl edit tikz2svg.service

# Thêm vào file override:
[Service]
EnvironmentFile=/var/www/tikz2svg_api/shared/.env
Environment="REDIS_URL=redis://localhost:6379/0"
```

#### **3. Reload và restart:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart tikz2svg.service
```

### ✅ Kiểm tra Redis hoạt động

#### **Test Redis connection:**
```bash
# 1. Check Redis keys
redis-cli KEYS "LIMITER*"

# 2. Monitor Redis in real-time
redis-cli MONITOR

# 3. Check Redis info
redis-cli INFO stats
```

#### **Test từ Python:**
```bash
cd /var/www/tikz2svg_api/current
source ../venv/bin/activate
python3 -c "
import redis
import os
from dotenv import load_dotenv
load_dotenv('/var/www/tikz2svg_api/shared/.env')
r = redis.from_url(os.environ.get('REDIS_URL'))
print('Redis PING:', r.ping())
"
# Expected output: Redis PING: True
```

#### **Kiểm tra Rate Limiting logs:**
```bash
# Xem logs để verify Redis storage
tail -100 /var/www/tikz2svg_api/current/logs/gunicorn_error.log | grep "Storage:"
# Expected: 📊 Storage: redis://localhost:6379/0

# Xem rate limit logs
tail -100 /var/www/tikz2svg_api/current/logs/gunicorn_error.log | grep "flask-limiter"
# Expected: ratelimit 500 per 1 minute (REAL_IP) exceeded
```

### 🚨 Troubleshooting Redis

#### **Vấn đề: Redis không kết nối được**
```bash
# Check Redis service
sudo systemctl status redis-server

# Check Redis logs
sudo journalctl -u redis-server -n 50

# Check Redis port
sudo netstat -tlnp | grep 6379

# Test connection
redis-cli -h localhost -p 6379 ping
```

#### **Vấn đề: REDIS_URL không được load**
```bash
# Check .env file
cat /var/www/tikz2svg_api/shared/.env | grep REDIS_URL

# Check systemd environment
sudo systemctl show tikz2svg.service | grep Environment

# Verify trong Python
cd /var/www/tikz2svg_api/current
python3 -c "import os; from dotenv import load_dotenv; load_dotenv('../shared/.env'); print(os.environ.get('REDIS_URL'))"
```

#### **Vấn đề: Rate limiting vẫn dùng memory://**
```bash
# Clear Redis và restart
redis-cli FLUSHDB
sudo systemctl restart tikz2svg.service

# Check logs
tail -50 logs/gunicorn_error.log | grep "Storage:"
```

### 📊 Monitoring Redis

#### **Check Redis memory usage:**
```bash
redis-cli INFO memory | grep used_memory_human
```

#### **Check rate limit keys:**
```bash
# List all rate limit keys
redis-cli KEYS "LIMITER*"

# Count rate limit keys
redis-cli KEYS "LIMITER*" | wc -l

# Check specific IP's counter
redis-cli GET "LIMITER/api/svg/*/likes/preview/YOUR_IP"
```

#### **Clear old rate limit data:**
```bash
# Clear all rate limit keys (careful!)
redis-cli --scan --pattern "LIMITER*" | xargs redis-cli DEL

# Or flush entire database (VERY CAREFUL!)
redis-cli FLUSHDB
```

---

## 📝 VPS Deployment Checklist

### ✅ Pre-deployment Requirements:
- [ ] Redis server installed and running
- [ ] `REDIS_URL` set in `/var/www/tikz2svg_api/shared/.env`
- [ ] Systemd service configured with `EnvironmentFile`
- [ ] Redis connection tested successfully

### ✅ Post-deployment Verification:
- [ ] Check logs for `Storage: redis://localhost:6379/0`
- [ ] Verify rate limiting uses real client IP (not 127.0.0.1)
- [ ] Test rate limits with multiple requests
- [ ] Monitor Redis keys: `redis-cli KEYS "LIMITER*"`

---

**Ngày tạo:** 25/08/2025  
**Người tạo:** AI Assistant  
**Mục đích:** Ghi lại vấn đề cấu hình static files để xử lý sau

**Ngày khắc phục:** 25/08/2025  
**Vấn đề đã khắc phục:** 
1. 502 Bad Gateway do symbolic link avatars bị hỏng
2. File SVG được lưu sai thư mục (current/static thay vì shared/static) - **ĐÃ KHẮC PHỤC HOÀN TOÀN**
3. Biến môi trường `TIKZ_SVG_DIR` đã được thêm vào file `.env`

**Ngày cập nhật:** 01/11/2025  
**Cập nhật mới:**
1. ✅ Thêm yêu cầu BẮT BUỘC: Redis Server cho VPS deployment
2. ✅ Hướng dẫn cài đặt và cấu hình Redis chi tiết
3. ✅ Troubleshooting Redis và rate limiting
4. ✅ Monitoring và maintenance Redis

