# Hướng dẫn Thiết lập Zoho Mail cho support@tikz2svg.com

## 🚀 Bước 1: Thiết lập Zoho Mail

### 1.1 Đăng nhập vào Zoho Mail

1. **Truy cập Zoho Mail:**
   - Mở trình duyệt và vào: https://mail.zoho.com
   - Hoặc: https://www.zoho.com/mail/

2. **Đăng nhập:**
   - Email: `support@tikz2svg.com`
   - Mật khẩu: [Mật khẩu tài khoản của bạn]

### 1.2 Tạo App Password

1. **Vào Settings:**
   - Sau khi đăng nhập, click vào **Settings** (⚙️) ở góc trên bên phải
   - Hoặc click vào avatar/profile picture → **Settings**

2. **Chọn Mail Accounts:**
   - Trong menu bên trái, tìm và click **Mail Accounts**
   - Chọn tài khoản `support@tikz2svg.com`

3. **Vào Security:**
   - Trong tab **Security** hoặc **Advanced**
   - Tìm mục **App Passwords** hoặc **Application Specific Passwords**

4. **Tạo App Password mới:**
   - Click **Generate** hoặc **Create New App Password**
   - Đặt tên cho app password: `TikZ2SVG API`
   - Chọn quyền: **SMTP** (nếu có tùy chọn)
   - Click **Generate** hoặc **Create**

5. **Lưu App Password:**
   - **⚠️ QUAN TRỌNG:** Copy và lưu app password này ngay lập tức
   - App password sẽ chỉ hiển thị một lần
   - Ví dụ: `abcd1234efgh5678ijkl9012mnop3456`

### 1.3 Thông tin SMTP Zoho

Sau khi có app password, đây là thông tin SMTP:

```
SMTP Server: smtp.zoho.com
Port: 587 (TLS) hoặc 465 (SSL)
Username: support@tikz2svg.com
Password: [App Password đã tạo]
Encryption: TLS (cho port 587) hoặc SSL (cho port 465)
```

### 1.4 Cấu hình file .env

Tạo hoặc cập nhật file `.env` trong thư mục dự án:

```bash
# Zoho Mail SMTP Settings
ZOHO_EMAIL=support@tikz2svg.com
ZOHO_APP_PASSWORD=your-app-password-here

# App Configuration
APP_URL=https://yourdomain.com

# Admin Email
ADMIN_EMAIL=admin@yourdomain.com

# Email Rate Limiting
EMAIL_MAX_PER_HOUR=50
EMAIL_MAX_PER_DAY=500
EMAIL_COOLDOWN_MINUTES=5

# SVG Verification Settings
DAILY_SVG_LIMIT=10  # Số file SVG tối đa/ngày trước khi cần xác thực
```

### 1.5 Test kết nối SMTP

Chạy script test để kiểm tra kết nối:

```bash
python test_smtp_connection.py
```

## 🔧 Troubleshooting

### Lỗi thường gặp:

#### 1. SMTP Authentication Failed
```
Error: SMTP authentication failed
```
**Giải pháp:**
- Kiểm tra lại ZOHO_APP_PASSWORD trong file .env
- Đảm bảo đã tạo App Password (không phải mật khẩu thường)
- Kiểm tra email support@tikz2svg.com có tồn tại không

#### 2. SMTP Connection Failed
```
Error: SMTP connection failed
```
**Giải pháp:**
- Kiểm tra kết nối internet
- Kiểm tra firewall có chặn port 587 không
- Thử port 465 (SSL) nếu port 587 không hoạt động

#### 3. App Password không hiển thị
**Giải pháp:**
- App password chỉ hiển thị một lần khi tạo
- Nếu quên, hãy xóa app password cũ và tạo mới
- Lưu app password vào file an toàn ngay khi tạo

#### 4. Không tìm thấy App Passwords
**Giải pháp:**
- Đảm bảo đã đăng nhập đúng tài khoản support@tikz2svg.com
- Kiểm tra quyền admin của tài khoản
- Liên hệ Zoho support nếu cần thiết

## 📋 Checklist

- [ ] Đăng nhập thành công vào Zoho Mail
- [ ] Tạo App Password cho TikZ2SVG API
- [ ] Lưu App Password an toàn
- [ ] Cấu hình file .env với thông tin SMTP
- [ ] Test kết nối SMTP thành công
- [ ] Nhận được email test

## 🔒 Bảo mật

### Lưu ý quan trọng:
1. **Không commit app password vào git**
2. **Sử dụng environment variables**
3. **Rotate app password định kỳ**
4. **Không chia sẻ app password với ai**

### File .env example:
```bash
# Copy file env_email_example.txt thành .env và điền thông tin thực
cp env_email_example.txt .env
# Sau đó chỉnh sửa file .env với thông tin thực
```

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs trong console
2. Xem hướng dẫn troubleshooting ở trên
3. Liên hệ Zoho support nếu cần
4. Kiểm tra network connectivity

---

**Lưu ý:** Đảm bảo tuân thủ các quy định về email marketing và spam laws của quốc gia bạn.
