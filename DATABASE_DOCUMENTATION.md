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
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `google_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rank` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `score` int DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `google_id` (`google_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `id`: Khóa chính, tự động tăng
- `username`: Tên người dùng (duy nhất)
- `email`: Email người dùng
- `google_id`: ID từ Google OAuth (duy nhất)
- `avatar`: URL avatar người dùng
- `rank`: Cấp bậc người dùng
- `score`: Điểm số người dùng
- `created_at`: Thời gian tạo tài khoản

### 2. Bảng `svg_image` - Lưu trữ hình ảnh SVG

**Mô tả:** Lưu trữ thông tin các file SVG được tạo từ mã TikZ.

**Cấu trúc:**
```sql
CREATE TABLE `svg_image` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tikz_code` text COLLATE utf8mb4_unicode_ci,
  `keywords` text COLLATE utf8mb4_unicode_ci,
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
- `created_at`: Thời gian tạo
- `user_id`: ID người dùng tạo (khóa ngoại đến bảng `user`)

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
  `svg_image_id` int NOT NULL,
  `keyword_id` int NOT NULL,
  PRIMARY KEY (`svg_image_id`,`keyword_id`),
  KEY `keyword_id` (`keyword_id`),
  CONSTRAINT `svg_image_keyword_ibfk_1` FOREIGN KEY (`svg_image_id`) REFERENCES `svg_image` (`id`),
  CONSTRAINT `svg_image_keyword_ibfk_2` FOREIGN KEY (`keyword_id`) REFERENCES `keyword` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Các trường:**
- `svg_image_id`: ID hình ảnh SVG (khóa ngoại)
- `keyword_id`: ID từ khóa (khóa ngoại)

### 5. Bảng `svg_like` - Quản lý like hình ảnh

**Mô tả:** Lưu trữ thông tin người dùng like các hình ảnh SVG.

**Cấu trúc (được suy luận từ code):**
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

**Cấu trúc (được suy luận từ code):**
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

### 7. Bảng `svg_action_log` - Log hoạt động

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

## Mối quan hệ giữa các bảng

### Sơ đồ quan hệ:

```
user (1) ←→ (N) svg_image
user (1) ←→ (N) svg_like
user (1) ←→ (N) user_follow (follower)
user (1) ←→ (N) user_follow (followee)
user (1) ←→ (N) svg_action_log
svg_image (1) ←→ (N) svg_like
svg_image (1) ←→ (N) svg_action_log
svg_image (N) ←→ (N) keyword (thông qua svg_image_keyword)
```

### Chi tiết quan hệ:

1. **user → svg_image**: Một người dùng có thể tạo nhiều hình ảnh SVG
2. **user → svg_like**: Một người dùng có thể like nhiều hình ảnh
3. **user → user_follow**: Quan hệ follow giữa các người dùng
4. **svg_image → keyword**: Quan hệ nhiều-nhiều thông qua bảng trung gian
5. **svg_image → svg_action_log**: Ghi log các hoạt động với hình ảnh

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

### 1. Lấy danh sách hình ảnh với thông tin like:
```sql
SELECT 
    s.id, 
    s.filename, 
    s.tikz_code, 
    s.keywords, 
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
GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, u.id, u.username, u.email, user_like.id
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
    s.id, s.filename, s.tikz_code, s.keywords, s.created_at,
    u.id as creator_id, u.username as creator_username,
    COUNT(sl.id) as like_count,
    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
FROM svg_image s
JOIN user u ON s.user_id = u.id
JOIN user_follow uf ON u.id = uf.followee_id
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = ?
WHERE uf.follower_id = ?
GROUP BY s.id, s.filename, s.tikz_code, s.created_at, u.id, u.username, user_like.id
ORDER BY s.created_at DESC
LIMIT 50
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

## Monitoring và Maintenance

### Các chỉ số cần theo dõi:
- Số lượng người dùng đăng ký
- Số lượng hình ảnh được tạo
- Tỷ lệ like/follow
- Hiệu suất truy vấn database

### Bảo trì định kỳ:
- Tối ưu hóa index
- Dọn dẹp dữ liệu cũ
- Kiểm tra tính toàn vẹn dữ liệu
- Cập nhật backup

---

*Tài liệu này được cập nhật lần cuối: Tháng 7 năm 2025*
