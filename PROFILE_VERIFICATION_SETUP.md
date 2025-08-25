# Hướng dẫn Setup Hệ thống Xác thực Profile Settings

## Quy trình xác thực email cho Profile Settings

### 1. Cập nhật Database

Chạy lệnh SQL sau để thêm các trường cần thiết:

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
```

### 2. Quy trình hoạt động

#### Khi người dùng thay đổi profile:
1. **Nhập thông tin mới** (username, bio, avatar)
2. **Nhấn "Lưu thay đổi"**
3. **Hệ thống kiểm tra thay đổi**:
   - Nếu có thay đổi → Tạo mã xác thực 6 số
   - Lưu thay đổi tạm thời vào database
   - Gửi email xác thực với mã
4. **Hiển thị form xác thực** trên trang

#### Khi người dùng xác thực:
1. **Nhập mã 6 số** từ email
2. **Nhấn "Xác nhận thay đổi"**
3. **Hệ thống kiểm tra**:
   - Mã có đúng không?
   - Mã có hết hạn chưa? (24 giờ)
   - Số lần thử có quá 5 lần không?
4. **Nếu thành công**:
   - Áp dụng thay đổi vào database
   - Xóa thông tin xác thực tạm thời
   - Hiển thị thông báo thành công

### 3. Các tính năng bảo mật

- **Mã xác thực 6 số** ngẫu nhiên
- **Thời gian hết hạn 24 giờ**
- **Giới hạn 5 lần thử sai**
- **Tự động xóa thông tin hết hạn**
- **Log số lần thử sai**

### 4. Email template

Template email được tạo tại: `templates/emails/profile_settings_verification.html`

Bao gồm:
- Mã xác thực nổi bật
- Tóm tắt thay đổi
- Hướng dẫn sử dụng
- Cảnh báo bảo mật
- Link truy cập trang

### 5. Frontend Features

- **Form xác thực tự động hiển thị** khi có thay đổi chờ
- **Auto-focus** vào ô nhập mã
- **Chỉ cho phép nhập số**
- **Auto-submit** khi đủ 6 số
- **Hiển thị số lần thử còn lại**
- **Nút hủy bỏ** thay đổi

### 6. Backend Features

- **So sánh thay đổi** để tránh gửi email không cần thiết
- **Lưu thay đổi tạm thời** trong JSON
- **Xử lý avatar** (file upload và base64)
- **Rate limiting** cho email
- **Error handling** đầy đủ

### 7. Cách test

1. **Cập nhật database** với SQL trên
2. **Khởi động app** với email service
3. **Đăng nhập** và vào trang profile settings
4. **Thay đổi thông tin** và lưu
5. **Kiểm tra email** nhận mã xác thực
6. **Nhập mã** và xác nhận
7. **Kiểm tra** thay đổi đã được áp dụng

### 8. Troubleshooting

#### Email không gửi được:
- Kiểm tra cấu hình SMTP trong `.env`
- Kiểm tra rate limiting
- Xem log email service

#### Mã xác thực không đúng:
- Kiểm tra thời gian hết hạn
- Kiểm tra số lần thử
- Xem log database

#### Avatar không lưu:
- Kiểm tra quyền thư mục `static/avatars`
- Kiểm tra dung lượng file
- Xem log lỗi

### 9. Files đã cập nhật

- `app.py` - Thêm logic xác thực
- `email_service.py` - Thêm method gửi email
- `email_config.py` - Thêm template mới
- `templates/profile_settings.html` - Thêm form xác thực
- `templates/emails/profile_settings_verification.html` - Template email mới
- `profile_settings_verification.sql` - SQL cập nhật database
