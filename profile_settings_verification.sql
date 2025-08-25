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
