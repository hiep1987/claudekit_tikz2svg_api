# Hướng dẫn Setup Identity Verification System

## Tổng quan
Hệ thống xác thực danh tính tài khoản đã được implement với các tính năng:
- Xác thực email cho tài khoản mới
- Hiển thị trạng thái xác thực trên profile
- Badge xác thực cho tài khoản đã verify
- Quy trình xác thực với terms & conditions

## Các file đã tạo/cập nhật

### 1. Database Setup
- `identity_verification_setup.sql` - SQL để thêm trường identity_verified

### 2. Templates
- `templates/profile_verification.html` - Trang xác thực danh tính
- `templates/emails/identity_verification.html` - Template email xác thực
- `templates/profile_settings.html` - Cập nhật hiển thị trạng thái xác thực

### 3. Backend
- `app.py` - Thêm route `/profile/verification` và logic xử lý
- `email_service.py` - Thêm method `send_identity_verification_email`
- `email_config.py` - Thêm template `identity_verification`

### 4. Assets
- `static/identity-verification-icon.svg` - Icon badge xác thực

## Cách setup

### Bước 1: Chạy SQL Setup
```bash
# Kết nối vào database
mysql -u hiep1987 -p tikz2svg

# Chạy file SQL
source identity_verification_setup.sql;
```

Hoặc chạy trực tiếp:
```bash
mysql -u hiep1987 -p tikz2svg < identity_verification_setup.sql
```

### Bước 2: Kiểm tra cấu trúc database
```sql
DESCRIBE user;
```

Đảm bảo có các trường mới:
- `identity_verified` (BOOLEAN)
- `identity_verification_code` (VARCHAR(6))
- `identity_verification_expires_at` (DATETIME)
- `identity_verification_attempts` (INT)

### Bước 3: Test hệ thống

1. **Truy cập trang profile settings**
   - Vào `/profile/{user_id}/settings`
   - Kiểm tra hiển thị trạng thái "Chưa xác thực"

2. **Test xác thực danh tính**
   - Nhấn nút "Xác thực tài khoản"
   - Đọc và đồng ý với terms & conditions
   - Nhận email xác thực
   - Nhập mã xác thực

3. **Kiểm tra kết quả**
   - Trạng thái chuyển thành "Đã xác thực"
   - Hiển thị icon badge xác thực

## Quy trình hoạt động

### 1. Tài khoản mới
- Hiển thị "⚠ Chưa xác thực"
- Có nút "Xác thực tài khoản"

### 2. Quá trình xác thực
1. Nhấn nút xác thực → Redirect đến `/profile/verification`
2. Đọc terms & conditions
3. Nhấn "Tôi đồng ý" → Gửi email xác thực
4. Nhập mã 6 số → Xác thực thành công

### 3. Tài khoản đã xác thực
- Hiển thị "✔ Đã xác thực" + icon badge
- Thông báo "Tài khoản đã được xác thực!"

## Tính năng bảo mật

### 1. Rate Limiting
- Tối đa 5 lần thử mã xác thực
- Mã có hiệu lực 24 giờ
- Tự động reset sau khi hết hạn

### 2. Email Security
- Mã xác thực 6 số ngẫu nhiên
- Template email chuyên nghiệp
- Hướng dẫn chi tiết

### 3. Database Security
- Mã hóa thông tin xác thực
- Index tối ưu cho truy vấn
- Cleanup tự động

## Troubleshooting

### Lỗi thường gặp

1. **Email không gửi được**
   - Kiểm tra cấu hình SMTP trong `.env`
   - Kiểm tra log email service

2. **Database error**
   - Chạy lại SQL setup
   - Kiểm tra quyền database user

3. **Template không hiển thị**
   - Kiểm tra đường dẫn template
   - Clear cache browser

### Debug Commands

```bash
# Kiểm tra trạng thái user
mysql -u hiep1987 -p tikz2svg -e "SELECT id, email, identity_verified FROM user WHERE id = 1;"

# Kiểm tra email log
mysql -u hiep1987 -p tikz2svg -e "SELECT * FROM email_log WHERE template = 'identity_verification' ORDER BY created_at DESC LIMIT 5;"
```

## Cập nhật Production

1. **Backup database**
```bash
mysqldump -u hiep1987 -p tikz2svg > backup_before_identity_verification.sql
```

2. **Deploy code**
```bash
# Upload các file mới
# Restart application
```

3. **Chạy SQL setup**
```bash
mysql -u hiep1987 -p tikz2svg < identity_verification_setup.sql
```

4. **Test production**
- Kiểm tra email gửi
- Test quy trình xác thực
- Verify UI hiển thị

## Kết luận

Hệ thống identity verification đã được implement hoàn chỉnh với:
- ✅ Database schema
- ✅ Backend logic
- ✅ Frontend UI
- ✅ Email templates
- ✅ Security features
- ✅ Documentation

Sẵn sàng để deploy và sử dụng trong production!
