#!/bin/bash

# Script để cập nhật database trên VPS
# Thay đổi các thông tin kết nối VPS của bạn

VPS_HOST="your-vps-ip-or-domain"
VPS_USER="your-username"
VPS_PASSWORD="your-password"
DB_NAME="tikz2svg"
DB_USER="hiep1987"
DB_PASSWORD="your-db-password"

echo "🔧 Cập nhật database trên VPS..."
echo "Host: $VPS_HOST"
echo "Database: $DB_NAME"

# Tạo file SQL tạm thời trên VPS
cat > /tmp/profile_verification_update.sql << 'EOF'
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
EOF

# Upload file SQL lên VPS và chạy
sshpass -p "$VPS_PASSWORD" scp /tmp/profile_verification_update.sql $VPS_USER@$VPS_HOST:/tmp/

# Chạy SQL trên VPS
sshpass -p "$VPS_PASSWORD" ssh $VPS_USER@$VPS_HOST << EOF
    echo "📊 Chạy SQL cập nhật database..."
    mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < /tmp/profile_verification_update.sql
    
    if [ \$? -eq 0 ]; then
        echo "✅ Cập nhật database thành công!"
    else
        echo "❌ Có lỗi khi cập nhật database"
        exit 1
    fi
    
    # Xóa file tạm
    rm /tmp/profile_verification_update.sql
EOF

# Xóa file tạm trên Mac
rm /tmp/profile_verification_update.sql

echo "🎉 Hoàn thành cập nhật database!"
