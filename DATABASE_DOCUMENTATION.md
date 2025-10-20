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
svg_image (1) ←→ (N) svg_like
svg_image (1) ←→ (N) svg_action_log
svg_image (1) ←→ (N) user_action_log
svg_image (N) ←→ (N) keyword (thông qua svg_image_keyword)
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
9. **svg_image → keyword**: Quan hệ nhiều-nhiều thông qua bảng trung gian

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

### 6. Quản lý Image Captions:
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

*Tài liệu này được cập nhật lần cuối: Tháng 10 năm 2025*

## Changelog

### Tháng 10 2025
- ✅ **Thêm Image Caption Feature**: Cột `caption` vào bảng `svg_image` để lưu mô tả ảnh
- ✅ **MathJax Support**: Hỗ trợ hiển thị công thức toán học LaTeX trong caption (inline `$...$` và display `$$...$$`)
- ✅ **Caption Management Queries**: Thêm các queries để quản lý, tìm kiếm và thống kê caption
- ✅ **Chuẩn bị Comments Feature**: Thiết kế schema phù hợp cho tính năng bình luận trong tương lai
- ✅ **UTF8MB4 Support**: Đảm bảo hỗ trợ đầy đủ Unicode và ký tự đặc biệt trong caption

### Tháng 1 2025
- ✅ **Thêm Code Usage Limit System**: Field `profile_verification_usage_count` để track số lần sử dụng mã xác thực
- ✅ **Cập nhật schema bảng `user`**: Bao gồm tất cả fields verification hiện tại
- ✅ **Thêm debug queries**: Queries để monitor và troubleshoot verification system
- ✅ **Backward compatibility**: Hỗ trợ database cũ không có field `profile_verification_usage_count`
