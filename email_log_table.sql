-- Tạo bảng email_log để theo dõi việc gửi email
CREATE TABLE IF NOT EXISTS email_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipient VARCHAR(255) NOT NULL,
    template VARCHAR(100) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_recipient (recipient),
    INDEX idx_template (template),
    INDEX idx_sent_at (sent_at),
    INDEX idx_success (success)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tạo bảng verification_tokens để quản lý tất cả các loại token xác thực
CREATE TABLE IF NOT EXISTS verification_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    verification_type VARCHAR(50) NOT NULL, -- 'account_verification', 'svg_verification', 'password_reset'
    verification_code VARCHAR(10) NULL, -- Mã xác thực 6 số
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_user_id (user_id),
    INDEX idx_verification_type (verification_type),
    INDEX idx_verification_code (verification_code),
    INDEX idx_expires_at (expires_at),
    INDEX idx_used (used)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tạo bảng password_reset_tokens để quản lý token đặt lại mật khẩu (backward compatibility)
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tạo bảng email_notifications để quản lý thông báo email
CREATE TABLE IF NOT EXISTS email_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    action_url VARCHAR(500),
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_notification_type (notification_type),
    INDEX idx_sent (sent),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Thêm cột email_preferences vào bảng user (nếu chưa có)
ALTER TABLE user 
ADD COLUMN IF NOT EXISTS email_preferences JSON DEFAULT '{"welcome": true, "password_reset": true, "svg_shared": true, "notifications": true}',
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP NULL;

-- Tạo index cho các cột mới
ALTER TABLE user 
ADD INDEX IF NOT EXISTS idx_email_verified (email_verified),
ADD INDEX IF NOT EXISTS idx_email_verification_token (email_verification_token);
