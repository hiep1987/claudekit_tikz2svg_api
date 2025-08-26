-- Thêm trường identity_verified vào bảng user
-- Trường này sẽ lưu trạng thái xác thực danh tính của người dùng

ALTER TABLE `user` 
ADD COLUMN `identity_verified` BOOLEAN DEFAULT FALSE COMMENT 'Trạng thái xác thực danh tính người dùng',
ADD COLUMN `identity_verification_code` VARCHAR(6) NULL COMMENT 'Mã xác thực danh tính',
ADD COLUMN `identity_verification_expires_at` DATETIME NULL COMMENT 'Thời gian hết hạn mã xác thực danh tính',
ADD COLUMN `identity_verification_attempts` INT DEFAULT 0 COMMENT 'Số lần thử xác thực danh tính';

-- Thêm index để tối ưu truy vấn
CREATE INDEX `idx_identity_verified` ON `user` (`identity_verified`);
CREATE INDEX `idx_identity_verification_code` ON `user` (`identity_verification_code`);

-- Cập nhật comment cho bảng
ALTER TABLE `user` COMMENT = 'Bảng người dùng với hỗ trợ xác thực email và danh tính';
