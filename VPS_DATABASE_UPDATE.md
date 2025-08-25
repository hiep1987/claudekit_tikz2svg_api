# Hướng dẫn cập nhật Database trên VPS

## Phương án 1: SSH trực tiếp vào VPS

### Bước 1: Kết nối SSH vào VPS
```bash
ssh your-username@your-vps-ip
```

### Bước 2: Kết nối MySQL
```bash
mysql -u hiep1987 -p tikz2svg
```
Nhập password khi được yêu cầu.

### Bước 3: Chạy SQL cập nhật
```sql
-- Thêm các trường cho xác thực profile settings
ALTER TABLE `user` 
ADD COLUMN `profile_verification_code` VARCHAR(10) NULL,
ADD COLUMN `profile_verification_expires_at` DATETIME NULL,
ADD COLUMN `pending_profile_changes` JSON NULL COMMENT 'Lưu thay đổi profile đang chờ xác thực',
ADD COLUMN `profile_verification_attempts` INT DEFAULT 0 COMMENT 'Số lần thử xác thực sai';

-- Tạo index cho việc tìm kiếm mã xác thực
CREATE INDEX `idx_profile_verification_code` ON `user` (`profile_verification_code`);
CREATE INDEX `idx_profile_verification_expires` ON `user` (`profile_verification_expires_at`);

-- Thêm comment cho các trường mới
ALTER TABLE `user` 
MODIFY COLUMN `profile_verification_code` VARCHAR(10) NULL COMMENT 'Mã xác thực thay đổi profile (6-10 ký tự)',
MODIFY COLUMN `profile_verification_expires_at` DATETIME NULL COMMENT 'Thời gian hết hạn mã xác thực',
MODIFY COLUMN `pending_profile_changes` JSON NULL COMMENT 'Lưu thay đổi profile đang chờ xác thực (username, bio, avatar)';

-- Kiểm tra kết quả
DESCRIBE user;
```

### Bước 4: Thoát MySQL
```sql
EXIT;
```

## Phương án 2: Upload file SQL và chạy

### Bước 1: Upload file SQL lên VPS
```bash
# Từ Mac, upload file SQL
scp profile_settings_verification.sql your-username@your-vps-ip:/tmp/
```

### Bước 2: SSH vào VPS và chạy SQL
```bash
ssh your-username@your-vps-ip

# Chạy SQL file
mysql -u hiep1987 -p tikz2svg < /tmp/profile_settings_verification.sql

# Xóa file tạm
rm /tmp/profile_settings_verification.sql
```

## Phương án 3: Sử dụng script tự động

### Bước 1: Cài đặt sshpass (nếu chưa có)
```bash
# Trên Mac
brew install sshpass
```

### Bước 2: Cập nhật thông tin VPS trong script
```bash
# Chỉnh sửa file update_database_vps.sh
nano update_database_vps.sh

# Thay đổi các thông tin:
VPS_HOST="your-vps-ip-or-domain"
VPS_USER="your-username"
VPS_PASSWORD="your-password"
DB_PASSWORD="your-db-password"
```

### Bước 3: Chạy script
```bash
chmod +x update_database_vps.sh
./update_database_vps.sh
```

## Kiểm tra kết quả

Sau khi chạy SQL, kiểm tra xem các trường đã được thêm chưa:

```sql
mysql -u hiep1987 -p tikz2svg

-- Kiểm tra cấu trúc bảng user
DESCRIBE user;

-- Kiểm tra các trường mới
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'tikz2svg' 
AND TABLE_NAME = 'user' 
AND COLUMN_NAME IN ('profile_verification_code', 'profile_verification_expires_at', 'pending_profile_changes', 'profile_verification_attempts');
```

## Lưu ý quan trọng

1. **Backup database** trước khi chạy SQL:
   ```bash
   mysqldump -u hiep1987 -p tikz2svg > backup_before_update.sql
   ```

2. **Kiểm tra quyền** của user MySQL:
   ```sql
   SHOW GRANTS FOR 'hiep1987'@'localhost';
   ```

3. **Nếu có lỗi**, kiểm tra:
   - Quyền ALTER TABLE
   - Phiên bản MySQL (cần hỗ trợ JSON)
   - Kết nối database

4. **Sau khi cập nhật**, restart ứng dụng:
   ```bash
   # Nếu dùng systemd
   sudo systemctl restart your-app-service
   
   # Hoặc kill và start lại process
   ```

## Troubleshooting

### Lỗi "Access denied":
```bash
# Kiểm tra quyền user
mysql -u root -p
GRANT ALL PRIVILEGES ON tikz2svg.* TO 'hiep1987'@'localhost';
FLUSH PRIVILEGES;
```

### Lỗi "JSON not supported":
```sql
-- Kiểm tra phiên bản MySQL
SELECT VERSION();
-- Cần MySQL 5.7+ để hỗ trợ JSON
```

### Lỗi "Column already exists":
```sql
-- Kiểm tra xem trường đã tồn tại chưa
SHOW COLUMNS FROM user LIKE 'profile_verification_code';
```
