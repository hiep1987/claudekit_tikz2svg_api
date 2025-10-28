# Hướng Dẫn Cấu Hình Timezone trên VPS

## Vấn Đề
Khi triển khai ứng dụng TikZ2SVG lên VPS, thời gian hiển thị bị lệch 7 giờ:
- Notification báo "vừa bình luận" nhưng hiển thị "cách đây 7 giờ"
- Thời gian tạo SVG files bị lệch 7 giờ

## Nguyên Nhân
1. **VPS Server** timezone mặc định là UTC (GMT+0)
2. **Python Application** sử dụng timezone Asia/Ho_Chi_Minh (GMT+7)  
3. **MySQL Database** có thể sử dụng timezone khác
4. **JavaScript Client** sử dụng browser timezone

## Giải Pháp Chi Tiết

### 1. Kiểm Tra Timezone Hiện Tại

```bash
# Kiểm tra timezone của VPS server
timedatectl status

# Kiểm tra timezone của MySQL
mysql -u root -p -e "SELECT @@system_time_zone, @@session.time_zone;"

# Kiểm tra thời gian hiện tại
date
```

### 2. Thiết Lập Timezone Cho VPS Server

```bash
# Thiết lập timezone Asia/Ho_Chi_Minh cho toàn bộ server
sudo timedatectl set-timezone Asia/Ho_Chi_Minh

# Xác nhận thay đổi
timedatectl status

# Đồng bộ thời gian với NTP server
sudo timedatectl set-ntp true
```

### 3. Cấu Hình MySQL Timezone

```bash
# Truy cập MySQL
mysql -u root -p

# Kiểm tra timezone hiện tại
SELECT @@system_time_zone, @@session.time_zone;

# Thiết lập timezone cho MySQL session
SET time_zone = '+07:00';

# Thiết lập timezone global cho MySQL
SET GLOBAL time_zone = '+07:00';

# Kiểm tra lại
SELECT @@system_time_zone, @@session.time_zone;
```

### 4. Cấu Hình MySQL Timezone Vĩnh Viễn

Chỉnh sửa file cấu hình MySQL:

```bash
# Mở file cấu hình MySQL
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# hoặc
sudo nano /etc/mysql/my.cnf
```

Thêm vào section `[mysqld]`:

```ini
[mysqld]
default-time-zone = '+07:00'
```

Khởi động lại MySQL:

```bash
sudo systemctl restart mysql
```

### 5. Cập Nhật Python Application

Kiểm tra xem ứng dụng đã có timezone setting chưa trong `app.py`:

```python
# Đã có sẵn trong code
try:
    from zoneinfo import ZoneInfo
    tz_vn = ZoneInfo("Asia/Ho_Chi_Minh")
except ImportError:
    from pytz import timezone
    tz_vn = timezone('Asia/Ho_Chi_Minh')
```

### 6. Khởi Động Lại Ứng Dụng

```bash
# Khởi động lại application
sudo systemctl restart your-app-service
# hoặc nếu chạy với supervisor/pm2
pm2 restart tikz2svg-api
```

### 7. Kiểm Tra Kết Quả

```bash
# Test timezone
python3 -c "
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    tz_vn = ZoneInfo('Asia/Ho_Chi_Minh')
except ImportError:
    from pytz import timezone
    tz_vn = timezone('Asia/Ho_Chi_Minh')

print('Current time with VN timezone:', datetime.now(tz_vn))
print('Current UTC time:', datetime.utcnow())
"
```

### 8. Script Tự Động Cấu Hình

Tạo script tự động:

```bash
#!/bin/bash
# setup_timezone_vps.sh

echo "🔧 Configuring VPS timezone for TikZ2SVG API..."

# 1. Set server timezone
echo "📅 Setting server timezone to Asia/Ho_Chi_Minh..."
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo timedatectl set-ntp true

echo "✅ Server timezone configured:"
timedatectl status

# 2. Configure MySQL timezone
echo "🗄️ Configuring MySQL timezone..."
mysql -u root -p -e "
SET GLOBAL time_zone = '+07:00';
SELECT 'MySQL timezone configured:' as status, @@system_time_zone as system_tz, @@session.time_zone as session_tz;
"

# 3. Add timezone to MySQL config if not exists
if ! grep -q "default-time-zone" /etc/mysql/mysql.conf.d/mysqld.cnf; then
    echo "📝 Adding timezone to MySQL config..."
    sudo bash -c 'echo "default-time-zone = \"+07:00\"" >> /etc/mysql/mysql.conf.d/mysqld.cnf'
fi

# 4. Restart MySQL
echo "🔄 Restarting MySQL..."
sudo systemctl restart mysql

echo "✅ Timezone configuration completed!"
echo "🚀 Please restart your application to apply changes."
```

### 9. Verification Commands

```bash
# Kiểm tra tổng quan
echo "=== SERVER TIMEZONE ===" 
timedatectl status

echo "=== MYSQL TIMEZONE ==="
mysql -u root -p -e "SELECT @@system_time_zone, @@session.time_zone, NOW() as current_time;"

echo "=== PYTHON TIMEZONE ==="
python3 -c "
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    tz_vn = ZoneInfo('Asia/Ho_Chi_Minh')
except ImportError:
    from pytz import timezone
    tz_vn = timezone('Asia/Ho_Chi_Minh')
print('VN Time:', datetime.now(tz_vn))
print('UTC Time:', datetime.utcnow())
"
```

## Troubleshooting

### Nếu vẫn còn lệch thời gian:

1. **Kiểm tra browser timezone** của client
2. **Clear browser cache** và reload page
3. **Kiểm tra JavaScript** xử lý timezone
4. **Restart toàn bộ services** (nginx, mysql, app)

### Lỗi phổ biến:

- **"mysql command not found"**: Cài đặt mysql client
- **"Permission denied"**: Sử dụng sudo cho các lệnh system
- **"Time zone name is invalid"**: Đảm bảo timezone string đúng format

## Ghi Chú Bảo Mật

- Backup database trước khi thay đổi timezone settings
- Test trên development environment trước
- Monitor logs sau khi thay đổi để đảm bảo không có lỗi

---

**Sau khi thực hiện các bước trên, vấn đề lệch 7 giờ sẽ được khắc phục hoàn toàn.**
