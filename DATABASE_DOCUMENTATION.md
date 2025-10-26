# Tài liệu Cơ sở dữ liệu - TikZ to SVG API

## Tổng quan

Cơ sở dữ liệu của website TikZ to SVG API được xây dựng trên MySQL 8.0.42, sử dụng để lưu trữ thông tin người dùng, hình ảnh SVG được tạo từ mã TikZ, và các tương tác xã hội như like, follow.

## Cấu trúc Database

### 1. Bảng `user` - Quản lý người dùng

**Mô tả:** Lưu trữ thông tin người dùng đăng ký và đăng nhập qua Google OAuth.

**Cấu trúc:**
```sql
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bio` text COLLATE utf8mb4_unicode_ci,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `google_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rank` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `score` int DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `profile_verification_code` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `profile_verification_expires_at` datetime DEFAULT NULL,
  `pending_profile_changes` json DEFAULT NULL,
  `profile_verification_attempts` int DEFAULT '0',
  `identity_verified` tinyint(1) DEFAULT '0',
  `identity_verification_code` varchar(6) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `identity_verification_expires_at` datetime DEFAULT NULL,
  `identity_verification_attempts` int DEFAULT '0',
  `profile_verification_usage_count` int DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `google_id` (`google_id`),
  KEY `idx_profile_verification_code` (`profile_verification_code`),
  KEY `idx_profile_verification_expires` (`profile_verification_expires_at`),
  KEY `idx_identity_verified` (`identity_verified`),
  KEY `idx_identity_verification_code` (`identity_verification_code`),
  KEY `idx_profile_verification_usage` (`profile_verification_usage_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `username`: Tên người dùng (duy nhất)
- `bio`: Mô tả/giới thiệu người dùng (HTML format)
- `email`: Email người dùng
- `google_id`: ID từ Google OAuth (duy nhất)
- `avatar`: URL avatar người dùng
- `rank`: Cấp bậc người dùng
- `score`: Điểm số người dùng
- `created_at`: Thời gian tạo tài khoản
- `email_preferences`: Cài đặt email (JSON format)
- `email_verified`: Email đã xác thực hay chưa
- `email_verification_token`: Token xác thực email
- `email_verification_expires_at`: Thời gian hết hạn token xác thực email

#### (Mới) Trường xác thực danh tính
- `identity_verified` (BOOLEAN): Trạng thái xác thực danh tính người dùng (badge xanh)
- `identity_verification_code` (VARCHAR(6)): Mã xác thực 6 số đang hiệu lực
- `identity_verification_expires_at` (DATETIME): Thời gian hết hạn mã xác thực
- `identity_verification_attempts` (INT): Số lần nhập sai mã (tối đa 5)

Chúng được thêm bằng script `identity_verification_setup.sql` và có index:
- `idx_identity_verified` trên `identity_verified`
- `idx_identity_verification_code` trên `identity_verification_code`

#### (Mới) Trường xác thực profile settings
- `profile_verification_code` (VARCHAR(10)): Mã xác thực thay đổi profile (6-10 ký tự)
- `profile_verification_expires_at` (DATETIME): Thời gian hết hạn mã xác thực profile
- `pending_profile_changes` (JSON): Lưu thay đổi profile đang chờ xác thực
- `profile_verification_attempts` (INT): Số lần thử xác thực sai (tối đa 5)
- `profile_verification_usage_count` (INT): Số lần mã xác thực đã được sử dụng thành công (tối đa 5 lần)

Chúng được thêm bằng script `profile_settings_verification.sql` và `add_usage_count_field.sql` với các index:
- `idx_profile_verification_code` trên `profile_verification_code`
- `idx_profile_verification_expires` trên `profile_verification_expires_at`
- `idx_profile_verification_usage` trên `profile_verification_usage_count`

**Code Usage Limit Logic:**
- Một mã xác thực có thể được sử dụng tối đa **5 lần** trong vòng **10 phút**
- Field `profile_verification_usage_count` track số lần đã sử dụng thành công
- Khi `usage_count >= 5` hoặc hết hạn 10 phút, hệ thống tạo mã mới
- Logic này được implement trong `app.py` với fallback compatibility cho database cũ

### 2. Bảng `svg_image` - Lưu trữ hình ảnh SVG

**Mô tả:** Lưu trữ thông tin các file SVG được tạo từ mã TikZ.

**Cấu trúc:**
```sql
CREATE TABLE `svg_image` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tikz_code` text COLLATE utf8mb4_unicode_ci,
  `keywords` text COLLATE utf8mb4_unicode_ci,
  `caption` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `svg_image_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `filename`: Tên file SVG
- `tikz_code`: Mã TikZ gốc được sử dụng để tạo SVG
- `keywords`: Từ khóa mô tả hình ảnh (phân cách bằng dấu phẩy)
- `caption`: Mô tả chi tiết cho ảnh SVG, hỗ trợ LaTeX/MathJax (ví dụ: `$x^2$`, `$\alpha$`)
- `created_at`: Thời gian tạo
- `user_id`: ID người dùng tạo (khóa ngoại đến bảng `user`)

#### (Mới) Trường Image Caption với MathJax Support
- `caption` (TEXT): Mô tả/chú thích cho ảnh SVG
- Hỗ trợ plain text và công thức toán học LaTeX
- Sử dụng MathJax để render công thức inline `$...$` và display `$$...$$`
- Cho phép NULL (ảnh cũ không bắt buộc có caption)
- Charset `utf8mb4_unicode_ci` để hỗ trợ đầy đủ Unicode
- Chủ sở hữu ảnh có thể thêm/chỉnh sửa caption qua giao diện trang view_svg
- Chuẩn bị cho tính năng comments trong tương lai

### 3. Bảng `keyword` - Quản lý từ khóa

**Mô tả:** Lưu trữ các từ khóa được sử dụng để gắn thẻ cho hình ảnh SVG.

**Cấu trúc:**
```sql
CREATE TABLE `keyword` (
  `id` int NOT NULL AUTO_INCREMENT,
  `word` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `word` (`word`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `word`: Từ khóa (duy nhất)

### 4. Bảng `svg_image_keyword` - Quan hệ nhiều-nhiều giữa SVG và từ khóa

**Mô tả:** Bảng trung gian để liên kết nhiều từ khóa với một hình ảnh SVG.

**Cấu trúc:**
```sql
CREATE TABLE `svg_image_keyword` (
  `id` int NOT NULL AUTO_INCREMENT,
  `svg_image_id` int NOT NULL,
  `keyword_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `svg_image_id` (`svg_image_id`),
  KEY `keyword_id` (`keyword_id`),
  CONSTRAINT `svg_image_keyword_ibfk_1` FOREIGN KEY (`svg_image_id`) REFERENCES `svg_image` (`id`),
  CONSTRAINT `svg_image_keyword_ibfk_2` FOREIGN KEY (`keyword_id`) REFERENCES `keyword` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `svg_image_id`: ID hình ảnh SVG (khóa ngoại)
- `keyword_id`: ID từ khóa (khóa ngoại)

### 5. Bảng `svg_like` - Quản lý like hình ảnh

**Mô tả:** Lưu trữ thông tin người dùng like các hình ảnh SVG.

**Cấu trúc:**
```sql
CREATE TABLE `svg_like` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `svg_image_id` int NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_svg_unique` (`user_id`, `svg_image_id`),
  FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  FOREIGN KEY (`svg_image_id`) REFERENCES `svg_image` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `user_id`: ID người dùng like (khóa ngoại)
- `svg_image_id`: ID hình ảnh được like (khóa ngoại)
- `created_at`: Thời gian like

### 6. Bảng `user_follow` - Quản lý follow người dùng

**Mô tả:** Lưu trữ thông tin người dùng follow nhau.

**Cấu trúc:**
```sql
CREATE TABLE `user_follow` (
  `id` int NOT NULL AUTO_INCREMENT,
  `follower_id` int NOT NULL,
  `followee_id` int NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `follower_followee_unique` (`follower_id`, `followee_id`),
  FOREIGN KEY (`follower_id`) REFERENCES `user` (`id`),
  FOREIGN KEY (`followee_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `follower_id`: ID người dùng follow (khóa ngoại)
- `followee_id`: ID người dùng được follow (khóa ngoại)
- `created_at`: Thời gian follow

### 7. Bảng `svg_action_log` - Log hoạt động SVG

**Mô tả:** Ghi lại các hoạt động liên quan đến hình ảnh SVG.

**Cấu trúc:**
```sql
CREATE TABLE `svg_action_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `svg_image_id` int DEFAULT NULL,
  `action` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `svg_image_id` (`svg_image_id`),
  CONSTRAINT `svg_action_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `svg_action_log_ibfk_2` FOREIGN KEY (`svg_image_id`) REFERENCES `svg_image` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `user_id`: ID người dùng thực hiện hành động
- `svg_image_id`: ID hình ảnh liên quan
- `action`: Loại hành động
- `created_at`: Thời gian thực hiện

### 8. Bảng `user_action_log` - Log hoạt động người dùng

**Mô tả:** Ghi lại các hoạt động liên quan đến người dùng và tương tác xã hội.

**Cấu trúc:**
```sql
CREATE TABLE `user_action_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `target_user_id` int DEFAULT NULL,
  `target_svg_id` int DEFAULT NULL,
  `action_type` enum('follow','unfollow','like','unlike','view','share') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `target_user_id` (`target_user_id`),
  KEY `target_svg_id` (`target_svg_id`),
  KEY `action_type` (`action_type`),
  CONSTRAINT `user_action_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `user_action_log_ibfk_2` FOREIGN KEY (`target_user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `user_action_log_ibfk_3` FOREIGN KEY (`target_svg_id`) REFERENCES `svg_image` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `user_id`: ID người dùng thực hiện hành động
- `target_user_id`: ID người dùng mục tiêu (cho follow/unfollow)
- `target_svg_id`: ID hình ảnh mục tiêu (cho like/unlike/view/share)
- `action_type`: Loại hành động (follow, unfollow, like, unlike, view, share)
- `created_at`: Thời gian thực hiện

### 9. Bảng `email_log` - Log gửi email

**Mô tả:** Ghi lại tất cả các email đã gửi để theo dõi và debug.

**Cấu trúc:**
```sql
CREATE TABLE `email_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `recipient` varchar(255) NOT NULL,
  `template` varchar(100) NOT NULL,
  `success` boolean NOT NULL DEFAULT FALSE,
  `error_message` text,
  `sent_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_recipient` (`recipient`),
  KEY `idx_template` (`template`),
  KEY `idx_sent_at` (`sent_at`),
  KEY `idx_success` (`success`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `recipient`: Email người nhận
- `template`: Loại template email (welcome, verification, svg_verification)
- `success`: Trạng thái gửi thành công hay thất bại
- `error_message`: Thông báo lỗi nếu gửi thất bại
- `sent_at`: Thời gian gửi email

### 10. Bảng `verification_tokens` - Quản lý token xác thực

**Mô tả:** Lưu trữ tất cả các loại token xác thực (tài khoản, SVG, đặt lại mật khẩu).

**Cấu trúc:**
```sql
CREATE TABLE `verification_tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token` varchar(255) NOT NULL UNIQUE,
  `verification_type` varchar(50) NOT NULL,
  `verification_code` varchar(10) NULL,
  `expires_at` timestamp NOT NULL,
  `used` boolean DEFAULT FALSE,
  `used_at` timestamp NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  KEY `idx_token` (`token`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_verification_type` (`verification_type`),
  KEY `idx_verification_code` (`verification_code`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_used` (`used`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `user_id`: ID người dùng (khóa ngoại)
- `token`: Token xác thực (duy nhất)
- `verification_type`: Loại xác thực (account_verification, svg_verification, password_reset)
- `verification_code`: Mã xác thực 6 số (nếu có)
- `expires_at`: Thời gian hết hạn token
- `used`: Đã sử dụng hay chưa
- `used_at`: Thời gian sử dụng
- `created_at`: Thời gian tạo token

### 11. Bảng `password_reset_tokens` - Token đặt lại mật khẩu (DEPRECATED)

**Mô tả:** Bảng này KHÔNG CẦN THIẾT vì hệ thống chỉ sử dụng Google OAuth. Google tự quản lý việc đặt lại mật khẩu.

**Lý do không cần:**
- Hệ thống chỉ cho phép đăng nhập qua Google OAuth
- Không có mật khẩu local để reset
- Google tự quản lý password reset và security
- Bảng này được tạo để backward compatibility nhưng không sử dụng

**Ghi chú:** Có thể xóa bảng này nếu muốn dọn dẹp database.

### 12. Bảng `email_notifications` - Quản lý thông báo email

**Mô tả:** Lưu trữ các thông báo email cần gửi cho người dùng.

**Cấu trúc:**
```sql
CREATE TABLE `email_notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `notification_type` varchar(100) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `action_url` varchar(500),
  `sent` boolean DEFAULT FALSE,
  `sent_at` timestamp NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  KEY `idx_user_id` (`user_id`),
  KEY `idx_notification_type` (`notification_type`),
  KEY `idx_sent` (`sent`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `user_id`: ID người dùng (khóa ngoại)
- `notification_type`: Loại thông báo
- `title`: Tiêu đề thông báo
- `message`: Nội dung thông báo
- `action_url`: URL hành động (nếu có)
- `sent`: Đã gửi hay chưa
- `sent_at`: Thời gian gửi
- `created_at`: Thời gian tạo thông báo

### 13. Bảng `notifications` - Thông báo trong ứng dụng

**Mô tả:** Lưu trữ thông báo in-app cho người dùng về các tương tác (like, comment, reply, follow).

**Cấu trúc:**
```sql
CREATE TABLE `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT 'User receiving the notification',
  `actor_id` INT NOT NULL COMMENT 'User who performed the action',
  `notification_type` ENUM('comment', 'like', 'reply', 'follow') NOT NULL,
  `target_type` ENUM('svg_image', 'comment', 'user') NOT NULL,
  `target_id` VARCHAR(255) NOT NULL,
  `content` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action_url` VARCHAR(500) DEFAULT NULL,
  `is_read` BOOLEAN DEFAULT FALSE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `read_at` TIMESTAMP NULL DEFAULT NULL,
  
  FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`actor_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_is_read` (`is_read`),
  INDEX `idx_created_at` (`created_at`),
  INDEX `idx_user_unread` (`user_id`, `is_read`, `created_at`),
  INDEX `idx_actor_type` (`actor_id`, `notification_type`, `created_at`),
  
  CONSTRAINT `chk_target_type_id` CHECK (
    (target_type = 'svg_image' AND target_id REGEXP '^[a-zA-Z0-9_\\-]+\\.svg$') OR
    (target_type = 'comment' AND target_id REGEXP '^[0-9]+$') OR
    (target_type = 'user' AND target_id REGEXP '^[0-9]+$')
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `user_id`: ID người nhận thông báo (owner của SVG/comment)
- `actor_id`: ID người thực hiện hành động (người like, comment, follow)
- `notification_type`: Loại thông báo
  - `comment`: Bình luận vào SVG
  - `like`: Thích SVG
  - `reply`: Trả lời bình luận
  - `follow`: Theo dõi user
- `target_type`: Loại đối tượng
  - `svg_image`: Target là SVG file
  - `comment`: Target là comment
  - `user`: Target là user profile
- `target_id`: ID của đối tượng (svg_filename, comment_id, hoặc user_id)
- `content`: Nội dung preview (tối đa 200 ký tự, sanitized HTML)
- `action_url`: URL để navigate khi click notification
- `is_read`: Trạng thái đã đọc (TRUE/FALSE)
- `created_at`: Thời gian tạo thông báo
- `read_at`: Thời gian đánh dấu đã đọc

**Indexes & Performance:**
- `idx_user_id`: Tìm notifications của một user
- `idx_is_read`: Filter theo trạng thái đã đọc
- `idx_created_at`: Sort theo thời gian tạo
- `idx_user_unread`: Composite index cho query "unread notifications" (tối ưu nhất)
- `idx_actor_type`: Analytics queries (ai tạo notification gì)

**Security Features:**
- `chk_target_type_id`: Database-level validation cho target ID format
- Foreign key CASCADE: Tự động xóa notifications khi user bị xóa
- UTF8MB4 charset: Hỗ trợ emoji và Vietnamese characters

**Business Logic:**
- Không tạo notification nếu `user_id == actor_id` (self-notification)
- Content được sanitize để loại bỏ HTML tags
- Action URL phải là internal path (bắt đầu bằng `/`)
- Notifications cũ (>90 ngày và đã đọc) có thể được cleanup tự động

**Migration File:** `migrations/create_notifications_table.sql`

### 14. Bảng `svg_comments` - Hệ thống bình luận

**Mô tả:** Lưu trữ bình luận của người dùng trên các hình ảnh SVG.

**Cấu trúc:**
```sql
CREATE TABLE `svg_comments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `svg_filename` VARCHAR(255) NOT NULL,
  `user_id` INT NOT NULL,
  `comment_text` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `parent_comment_id` INT DEFAULT NULL,
  `likes_count` INT DEFAULT 0,
  `replies_count` INT DEFAULT 0,
  `user_ip` VARCHAR(45) DEFAULT NULL COMMENT 'IP address for spam tracking',
  `content_hash` VARCHAR(64) DEFAULT NULL COMMENT 'SHA256 hash for duplicate detection',
  `is_edited` TINYINT(1) DEFAULT 0,
  `edited_at` DATETIME DEFAULT NULL,
  `deleted_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX idx_svg_filename (svg_filename),
  INDEX idx_user_id (user_id),
  INDEX idx_parent_comment_id (parent_comment_id),
  INDEX idx_created_at_desc (created_at DESC),
  INDEX idx_filename_created_desc (svg_filename, created_at DESC),
  INDEX idx_user_ip (user_ip),
  INDEX idx_content_hash (content_hash),
  
  CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  CONSTRAINT fk_comments_svg_image FOREIGN KEY (svg_filename) REFERENCES svg_image(filename) ON DELETE CASCADE,
  CONSTRAINT fk_comments_parent FOREIGN KEY (parent_comment_id) REFERENCES svg_comments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính
- `svg_filename`: Tên file SVG (foreign key)
- `user_id`: ID người dùng (foreign key)
- `comment_text`: Nội dung bình luận (hỗ trợ LaTeX)
- `parent_comment_id`: ID bình luận cha (cho nested comments, 1 level)
- `likes_count`: Số lượt thích (denormalized counter)
- `replies_count`: Số câu trả lời (denormalized counter)
- `user_ip`: IP address (theo dõi spam)
- `content_hash`: Hash SHA256 (phát hiện duplicate)
- `is_edited`: Đã chỉnh sửa hay chưa
- `edited_at`: Thời gian chỉnh sửa cuối
- `deleted_at`: Thời gian xóa (soft delete)
- `created_at`: Thời gian tạo
- `updated_at`: Thời gian cập nhật cuối

**Indexes:**
- `idx_svg_filename`: Tìm comments theo SVG file
- `idx_user_id`: Tìm comments theo user
- `idx_parent_comment_id`: Tìm replies của comment
- `idx_created_at_desc`: Sắp xếp theo thời gian (DESC)
- `idx_filename_created_desc`: Composite index cho pagination
- `idx_user_ip`: Theo dõi spam theo IP
- `idx_content_hash`: Phát hiện duplicate

### 14. Bảng `svg_comment_likes` - Lượt thích bình luận

**Mô tả:** Lưu trữ lượt thích bình luận.

**Cấu trúc:**
```sql
CREATE TABLE `svg_comment_likes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `comment_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE KEY unique_comment_like (comment_id, user_id),
  INDEX idx_comment_id (comment_id),
  INDEX idx_user_id (user_id),
  
  CONSTRAINT fk_comment_likes_comment FOREIGN KEY (comment_id) REFERENCES svg_comments(id) ON DELETE CASCADE,
  CONSTRAINT fk_comment_likes_user FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính
- `comment_id`: ID bình luận (foreign key)
- `user_id`: ID người dùng (foreign key)
- `created_at`: Thời gian thích

**Constraints:**
- `unique_comment_like`: Đảm bảo mỗi user chỉ like 1 lần mỗi comment

## Mối quan hệ giữa các bảng

### Sơ đồ quan hệ:

```
user (1) ←→ (N) svg_image
user (1) ←→ (N) svg_like
user (1) ←→ (N) user_follow (follower)
user (1) ←→ (N) user_follow (followee)
user (1) ←→ (N) svg_action_log
user (1) ←→ (N) user_action_log (actor)
user (1) ←→ (N) user_action_log (target)
user (1) ←→ (N) verification_tokens
user (1) ←→ (N) password_reset_tokens (DEPRECATED)
user (1) ←→ (N) email_notifications
user (1) ←→ (N) notifications (recipient)
user (1) ←→ (N) notifications (actor)
user (1) ←→ (N) svg_comments
user (1) ←→ (N) svg_comment_likes
svg_image (1) ←→ (N) svg_like
svg_image (1) ←→ (N) svg_action_log
svg_image (1) ←→ (N) user_action_log
svg_image (1) ←→ (N) svg_comments
svg_image (N) ←→ (N) keyword (thông qua svg_image_keyword)
svg_comments (1) ←→ (N) svg_comments (parent-child, self-referencing)
svg_comments (1) ←→ (N) svg_comment_likes
```

### Chi tiết quan hệ:

1. **user → svg_image**: Một người dùng có thể tạo nhiều hình ảnh SVG
2. **user → svg_like**: Một người dùng có thể like nhiều hình ảnh
3. **user → user_follow**: Quan hệ follow giữa các người dùng
4. **user → svg_action_log**: Người dùng thực hiện các hành động với SVG
5. **user → user_action_log**: Người dùng thực hiện các hành động xã hội
6. **user → verification_tokens**: Một người dùng có thể có nhiều token xác thực
7. **user → password_reset_tokens**: (DEPRECATED) Không cần thiết với Google OAuth
8. **user → email_notifications**: Một người dùng có thể có nhiều thông báo email
9. **user → notifications (recipient)**: Một người dùng có thể nhận nhiều thông báo in-app
10. **user → notifications (actor)**: Một người dùng có thể là actor của nhiều thông báo (người thực hiện hành động)
11. **user → svg_comments**: Một người dùng có thể viết nhiều bình luận
12. **user → svg_comment_likes**: Một người dùng có thể like nhiều bình luận
13. **svg_image → svg_comments**: Một SVG có thể có nhiều bình luận
14. **svg_image → keyword**: Quan hệ nhiều-nhiều thông qua bảng trung gian
15. **svg_comments → svg_comments**: Quan hệ parent-child (self-referencing) cho nested comments (1 level)
16. **svg_comments → svg_comment_likes**: Một bình luận có thể có nhiều lượt thích

## Cấu hình kết nối

### Biến môi trường:
- `DB_HOST`: Host database (mặc định: localhost)
- `DB_USER`: Tên người dùng database (mặc định: hiep1987)
- `DB_PASSWORD`: Mật khẩu database
- `DB_NAME`: Tên database (mặc định: tikz2svg)

### Kết nối trong code:
```python
conn = mysql.connector.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'hiep1987'),
    password=os.environ.get('DB_PASSWORD', ''),
    database=os.environ.get('DB_NAME', 'tikz2svg')
)
```

## Các truy vấn chính

### 1. Lấy danh sách hình ảnh với thông tin like và caption:
```sql
SELECT 
    s.id, 
    s.filename, 
    s.tikz_code, 
    s.keywords,
    s.caption,
    s.created_at, 
    u.id as owner_id, 
    u.username, 
    u.email as owner_email,
    COUNT(sl.id) as like_count,
    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = ?
GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.caption, s.created_at, u.id, u.username, u.email, user_like.id
ORDER BY s.created_at DESC
LIMIT 100
```

### 2. Tìm kiếm từ khóa:
```sql
SELECT word FROM keyword 
WHERE word LIKE ? COLLATE utf8mb4_general_ci 
LIMIT 10
```

### 3. Lấy hình ảnh của người dùng được follow:
```sql
SELECT 
    s.id, s.filename, s.tikz_code, s.keywords, s.caption, s.created_at,
    u.id as creator_id, u.username as creator_username,
    COUNT(sl.id) as like_count,
    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
FROM svg_image s
JOIN user u ON s.user_id = u.id
JOIN user_follow uf ON u.id = uf.followee_id
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = ?
WHERE uf.follower_id = ?
GROUP BY s.id, s.filename, s.tikz_code, s.caption, s.created_at, u.id, u.username, user_like.id
ORDER BY s.created_at DESC
LIMIT 50
```

### 4. Phân tích hoạt động người dùng:
```sql
-- Lấy thống kê hoạt động của người dùng
SELECT 
    u.username,
    COUNT(DISTINCT s.id) as total_svg_created,
    COUNT(DISTINCT sl.svg_image_id) as total_likes_given,
    COUNT(DISTINCT uf.followee_id) as total_following,
    COUNT(DISTINCT uf2.follower_id) as total_followers
FROM user u
LEFT JOIN svg_image s ON u.id = s.user_id
LEFT JOIN svg_like sl ON u.id = sl.user_id
LEFT JOIN user_follow uf ON u.id = uf.follower_id
LEFT JOIN user_follow uf2 ON u.id = uf2.followee_id
WHERE u.id = ?
GROUP BY u.id, u.username

-- Lấy lịch sử hoạt động gần đây
SELECT 
    ual.action_type,
    ual.created_at,
    CASE 
        WHEN ual.target_user_id IS NOT NULL THEN tu.username
        WHEN ual.target_svg_id IS NOT NULL THEN si.filename
        ELSE NULL
    END as target_name
FROM user_action_log ual
LEFT JOIN user tu ON ual.target_user_id = tu.id
LEFT JOIN svg_image si ON ual.target_svg_id = si.id
WHERE ual.user_id = ?
ORDER BY ual.created_at DESC
LIMIT 20
```

### 5. Quản lý Email System:
```sql
-- Lấy thống kê email đã gửi
SELECT 
    template,
    COUNT(*) as total_sent,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
    DATE(sent_at) as send_date
FROM email_log
WHERE sent_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY template, DATE(sent_at)
ORDER BY send_date DESC, template

-- Lấy danh sách email lỗi gần đây
SELECT 
    recipient,
    template,
    error_message,
    sent_at
FROM email_log
WHERE success = 0
ORDER BY sent_at DESC
LIMIT 50

-- Lấy token xác thực chưa hết hạn
SELECT 
    vt.token,
    vt.verification_type,
    vt.verification_code,
    vt.expires_at,
    u.email,
    u.username
FROM verification_tokens vt
JOIN user u ON vt.user_id = u.id
WHERE vt.used = 0 AND vt.expires_at > NOW()
ORDER BY vt.created_at DESC

-- Lấy thông báo email chưa gửi
SELECT 
    en.id,
    en.notification_type,
    en.title,
    en.message,
    en.created_at,
    u.email,
    u.username
FROM email_notifications en
JOIN user u ON en.user_id = u.id
WHERE en.sent = 0
ORDER BY en.created_at ASC
LIMIT 100

-- Cập nhật cài đặt email của người dùng
UPDATE user 
SET email_preferences = JSON_SET(
    email_preferences,
    '$.welcome', ?,
    '$.password_reset', ?,
    '$.svg_shared', ?,
    '$.notifications', ?
)
WHERE id = ?

-- Lấy người dùng chưa xác thực email
SELECT 
    id,
    username,
    email,
    created_at
FROM user
WHERE email_verified = 0
ORDER BY created_at DESC

-- Profile Verification System Queries
-- Lấy thống kê usage count của verification codes
SELECT 
    profile_verification_usage_count,
    COUNT(*) as user_count,
    AVG(TIMESTAMPDIFF(MINUTE, 
        DATE_SUB(profile_verification_expires_at, INTERVAL 10 MINUTE), 
        NOW()
    )) as avg_minutes_since_issued
FROM user 
WHERE profile_verification_code IS NOT NULL 
    AND profile_verification_expires_at IS NOT NULL
GROUP BY profile_verification_usage_count
ORDER BY profile_verification_usage_count

-- Lấy verification codes sắp hết hạn (< 2 phút)
SELECT 
    id,
    username,
    email,
    profile_verification_code,
    profile_verification_usage_count,
    TIMESTAMPDIFF(SECOND, NOW(), profile_verification_expires_at) as seconds_until_expiry
FROM user 
WHERE profile_verification_code IS NOT NULL 
    AND profile_verification_expires_at > NOW()
    AND profile_verification_expires_at < DATE_ADD(NOW(), INTERVAL 2 MINUTE)
ORDER BY profile_verification_expires_at ASC

-- Lấy verification codes đã hết lượt sử dụng
SELECT 
    id,
    username,
    email,
    profile_verification_code,
    profile_verification_usage_count,
    profile_verification_expires_at
FROM user 
WHERE profile_verification_usage_count >= 5
    AND profile_verification_code IS NOT NULL
ORDER BY profile_verification_expires_at DESC

-- Debug: Kiểm tra code reuse logic
SELECT 
    id,
    username,
    profile_verification_code,
    profile_verification_usage_count,
    TIMESTAMPDIFF(MINUTE, 
        DATE_SUB(profile_verification_expires_at, INTERVAL 10 MINUTE), 
        NOW()
    ) as minutes_since_issued,
    TIMESTAMPDIFF(MINUTE, NOW(), profile_verification_expires_at) as minutes_until_expiry,
    CASE 
        WHEN profile_verification_usage_count >= 5 THEN 'EXCEEDED_USAGE_LIMIT'
        WHEN profile_verification_expires_at < NOW() THEN 'EXPIRED'
        WHEN profile_verification_code IS NULL THEN 'NO_CODE'
        ELSE 'REUSABLE'
    END as code_status
FROM user 
WHERE id = ? -- Replace with specific user ID
```

### 6. Quản lý Comments System:
```sql
-- Lấy tất cả bình luận cho một SVG (có phân trang)
SELECT 
    c.id,
    c.comment_text,
    c.created_at,
    c.updated_at,
    c.likes_count,
    c.replies_count,
    c.is_edited,
    c.parent_comment_id,
    u.id as user_id,
    u.username,
    u.avatar,
    u.identity_verified
FROM svg_comments c
JOIN user u ON c.user_id = u.id
WHERE c.svg_filename = ?
  AND c.parent_comment_id IS NULL
  AND c.deleted_at IS NULL
ORDER BY c.created_at DESC
LIMIT 20 OFFSET 0;

-- Lấy câu trả lời của một bình luận
SELECT 
    c.id,
    c.comment_text,
    c.created_at,
    c.updated_at,
    c.likes_count,
    c.is_edited,
    u.id as user_id,
    u.username,
    u.avatar,
    u.identity_verified
FROM svg_comments c
JOIN user u ON c.user_id = u.id
WHERE c.parent_comment_id = ?
  AND c.deleted_at IS NULL
ORDER BY c.created_at ASC;

-- Tạo bình luận mới
INSERT INTO svg_comments 
(svg_filename, user_id, comment_text, parent_comment_id, user_ip, content_hash)
VALUES (?, ?, ?, ?, ?, ?);

-- Cập nhật denormalized counters
UPDATE svg_image SET comments_count = comments_count + 1 WHERE filename = ?;
UPDATE svg_comments SET replies_count = replies_count + 1 WHERE id = ?; -- nếu là reply

-- Cập nhật bình luận
UPDATE svg_comments 
SET comment_text = ?, is_edited = 1, edited_at = NOW(), updated_at = NOW()
WHERE id = ? AND user_id = ?;

-- Xóa bình luận (soft delete)
UPDATE svg_comments 
SET deleted_at = NOW()
WHERE id = ? AND user_id = ?;

-- Cập nhật counters khi xóa
UPDATE svg_image SET comments_count = GREATEST(comments_count - 1, 0) WHERE filename = ?;
UPDATE svg_comments SET replies_count = GREATEST(replies_count - 1, 0) WHERE id = ?; -- nếu là reply

-- Thích bình luận
INSERT INTO svg_comment_likes (comment_id, user_id) VALUES (?, ?);
UPDATE svg_comments SET likes_count = likes_count + 1 WHERE id = ?;

-- Bỏ thích bình luận
DELETE FROM svg_comment_likes WHERE comment_id = ? AND user_id = ?;
UPDATE svg_comments SET likes_count = GREATEST(likes_count - 1, 0) WHERE id = ?;

-- Kiểm tra user đã like comment chưa
SELECT id FROM svg_comment_likes 
WHERE comment_id = ? AND user_id = ?;

-- Kiểm tra duplicate comment (trong 1 phút)
SELECT id FROM svg_comments
WHERE content_hash = ? 
  AND user_id = ? 
  AND created_at > DATE_SUB(NOW(), INTERVAL 1 MINUTE)
  AND deleted_at IS NULL;

-- Thống kê comments
SELECT 
    COUNT(*) as total_comments,
    COUNT(DISTINCT svg_filename) as svgs_with_comments,
    COUNT(DISTINCT user_id) as unique_commenters,
    AVG(likes_count) as avg_likes_per_comment
FROM svg_comments
WHERE deleted_at IS NULL;

-- Top SVG có nhiều comments nhất
SELECT 
    svg_filename,
    COUNT(*) as comment_count
FROM svg_comments
WHERE parent_comment_id IS NULL
  AND deleted_at IS NULL
GROUP BY svg_filename
ORDER BY comment_count DESC
LIMIT 10;

-- Top người dùng comment nhiều nhất
SELECT 
    u.username,
    COUNT(c.id) as comment_count
FROM svg_comments c
JOIN user u ON c.user_id = u.id
WHERE c.deleted_at IS NULL
GROUP BY u.username
ORDER BY comment_count DESC
LIMIT 10;

-- Comments được like nhiều nhất
SELECT 
    c.id,
    c.comment_text,
    c.likes_count,
    u.username,
    s.filename as svg_filename
FROM svg_comments c
JOIN user u ON c.user_id = u.id
JOIN svg_image s ON c.svg_filename = s.filename
WHERE c.deleted_at IS NULL
ORDER BY c.likes_count DESC
LIMIT 10;
```

### 7. Quản lý Image Captions:
```sql
-- Lấy thông tin ảnh SVG kèm caption cho view_svg page
SELECT 
    s.id,
    s.filename,
    s.tikz_code,
    s.keywords,
    s.caption,
    s.created_at,
    s.user_id,
    u.username,
    u.email
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
WHERE s.filename = ?
LIMIT 1

-- Cập nhật caption cho ảnh SVG (chỉ owner)
UPDATE svg_image 
SET caption = ?
WHERE filename = ? AND user_id = ?

-- Lấy danh sách ảnh có caption (để hiển thị trong gallery)
SELECT 
    s.id,
    s.filename,
    s.caption,
    u.username,
    COUNT(sl.id) as like_count
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
WHERE s.caption IS NOT NULL AND s.caption != ''
GROUP BY s.id, s.filename, s.caption, u.username
ORDER BY s.created_at DESC
LIMIT 50

-- Tìm kiếm ảnh theo caption (full-text search)
SELECT 
    s.id,
    s.filename,
    s.caption,
    u.username,
    s.created_at
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
WHERE s.caption LIKE ? OR s.keywords LIKE ?
ORDER BY s.created_at DESC
LIMIT 20

-- Thống kê ảnh có/không có caption
SELECT 
    CASE 
        WHEN caption IS NULL OR caption = '' THEN 'No Caption'
        ELSE 'Has Caption'
    END as caption_status,
    COUNT(*) as image_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM svg_image), 2) as percentage
FROM svg_image
GROUP BY caption_status
```

## Backup và Restore

### Backup database:
```bash
mysqldump -u hiep1987 -p tikz2svg > tikz2svg_database_backup.sql
```

### Restore database:
```bash
mysql -u hiep1987 -p tikz2svg < tikz2svg_database_backup.sql
```

## Lưu ý bảo mật

1. **Mã hóa mật khẩu**: Sử dụng biến môi trường để lưu thông tin nhạy cảm
2. **SQL Injection**: Sử dụng parameterized queries để tránh SQL injection
3. **Quyền truy cập**: Giới hạn quyền truy cập database cho ứng dụng
4. **Backup định kỳ**: Thực hiện backup database thường xuyên
5. **Log Security**: Bảo vệ thông tin nhạy cảm trong action logs

## Monitoring và Maintenance

### Các chỉ số cần theo dõi:
- Số lượng người dùng đăng ký
- Số lượng hình ảnh được tạo
- Tỷ lệ like/follow
- Hiệu suất truy vấn database
- Phân tích hành vi người dùng qua action logs

### Bảo trì định kỳ:
- Tối ưu hóa index
- Dọn dẹp dữ liệu cũ (log cũ)
- Kiểm tra tính toàn vẹn dữ liệu
- Cập nhật backup
- Phân tích và tối ưu hóa action logs

---

## 📊 Báo cáo Dữ liệu Thực tế (Database Report)

**Ngày cập nhật:** 2025-10-24 12:10:08  
**Database:** tikz2svg_local  
**Trạng thái:** ✓ HEALTHY

### Tổng quan Hệ thống

| Metric | Count |
|--------|-------|
| Tổng số người dùng | 10 |
| Tổng số SVG images | 48 |
| Tổng số comments | 10 |
| Tổng số comment likes | 4 |
| Tổng số SVG likes | 73 |
| Tổng số user follows | 12 |

### Comments System Statistics

**Phân loại Comments:**
- Top-level comments: 5
- Reply comments: 5
- Trung bình comments per SVG: 1.67

**Top 3 SVGs có nhiều comments nhất:**
1. `114753059215672971959_173220070925.svg` - 2 comments
2. `106711555120517947693_140859260925.svg` - 2 comments
3. `115852900894156127858_051555051025.svg` - 1 comment

**Top 2 người dùng comment nhiều nhất:**
1. quochiep0504 - 8 comments
2. Hiệp-54 - 2 comments

**Top 5 comments được like nhiều nhất:**
1. quochiep0504: 1 like - "Hàm số $y=x^2-3x+2$. Xin chào"
2. Hiệp-54: 1 like - "OK rẫy hay!"
3. quochiep0504: 1 like - "ABX"
4. Hiệp-54: 1 like - "Hình rất đẹp! Cám ơn bạn..."
5. quochiep0504: 0 likes - "Xin $y=x^3$ và"

### User Statistics

**Identity Verification:**
- Verified users: 5 (50%)
- Not verified users: 5 (50%)

**Top 5 Active Users:**
1. Hiệp-54: 26 SVGs, 35 likes given, 2 following, 4 followers
2. Hiepnig04: 7 SVGs, 10 likes given, 2 following, 2 followers
3. Hiệp1987: 6 SVGs, 16 likes given, 2 following, 3 followers
4. Quávui🐱: 5 SVGs, 3 likes given, 2 following, 2 followers
5. lucdo🍙: 2 SVGs, 3 likes given, 2 following, 0 followers

### SVG Image Statistics

**Caption Status:**
- Images with caption: 3 (6.25%)
- Images without caption: 45 (93.75%)

**Top 5 Most Liked SVGs:**
1. `106711555120517947693_140859260925.svg` by lucdo🍙 - 5 likes
2. `110078638093684817345_181311240925.svg` by hiepnig2 - 4 likes
3. `116896879463870011935_230700250725.svg` by Hiepnig04 - 3 likes
4. `115852900894156127858_104500230725.svg` by Hiệp-54 - 3 likes
5. `anonymous_124132030825.svg` by Hiệp1987 - 3 likes

### Database Schema Validation

**Tables Status:**
- ✓ `svg_comments` - 10 records
- ✓ `svg_comment_likes` - 4 records

**Indexes (svg_comments):** 6/5 ✓
- idx_svg_filename
- idx_user_id
- idx_parent_comment_id
- idx_created_at_desc
- idx_filename_created_desc (duplicate entry noted)

**Foreign Keys:** 5/5 ✓
- fk_comment_likes_comment: svg_comment_likes → svg_comments
- fk_comment_likes_user: svg_comment_likes → user
- fk_comments_parent: svg_comments → svg_comments
- fk_comments_svg_image: svg_comments → svg_image
- fk_comments_user: svg_comments → user

### Recent Activity (Last 7 Days)

**Comments per day:**
- 2025-10-23: 9 comments
- 2025-10-22: 1 comment

**SVGs created:** No new SVGs in last 7 days

### Comments System Implementation Progress

| Phase | Status |
|-------|--------|
| Step 1-2 (Database) | ✓ COMPLETE |
| Step 3-4 (Backend API) | ⏳ IN PROGRESS |
| Step 5-7 (Frontend) | ⏳ PENDING |
| Step 8 (Testing) | ⏳ PENDING |
| Step 9 (Documentation) | ⏳ PENDING |
| Step 10 (Deployment) | ⏳ PENDING |

**Ghi chú:** Để chạy lại báo cáo này, sử dụng:
```bash
cd /Users/hieplequoc/web/work/tikz2svg_api
source venv/bin/activate
python3 run_database_report.py
```

---

*Tài liệu này được cập nhật lần cuối: 2025-10-24 (với dữ liệu thực tế)*

---

## Changelog

### Tháng 10 2025
- ✅ **Comments System**: Thêm 2 bảng mới (`svg_comments`, `svg_comment_likes`) cho hệ thống bình luận
- ✅ **Nested Comments**: Hỗ trợ trả lời bình luận (parent_comment_id)
- ✅ **Like Comments**: Hệ thống thích bình luận với denormalized counter
- ✅ **Spam Prevention**: IP tracking, content hashing, duplicate detection
- ✅ **Performance Indexes**: 8 indexes mới cho query optimization
- ✅ **Foreign Keys**: 5 foreign keys đảm bảo data integrity
- ✅ **Cascade Delete**: Xóa SVG/user tự động xóa comments liên quan
- ✅ **Image Caption Feature**: Cột `caption` vào bảng `svg_image` để lưu mô tả ảnh
- ✅ **MathJax Support**: Hỗ trợ hiển thị công thức toán học LaTeX trong caption và comments
- ✅ **UTF8MB4 Support**: Đảm bảo hỗ trợ đầy đủ Unicode và ký tự đặc biệt

### Tháng 1 2025
- ✅ **Thêm Code Usage Limit System**: Field `profile_verification_usage_count` để track số lần sử dụng mã xác thực
- ✅ **Cập nhật schema bảng `user`**: Bao gồm tất cả fields verification hiện tại
- ✅ **Thêm debug queries**: Queries để monitor và troubleshoot verification system
- ✅ **Backward compatibility**: Hỗ trợ database cũ không có field `profile_verification_usage_count`
