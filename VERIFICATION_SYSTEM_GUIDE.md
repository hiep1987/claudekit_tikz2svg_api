# Hướng dẫn Hệ thống Xác thực Email với Zoho Mail

## 📋 Tổng quan

Hệ thống email xác thực mới sử dụng **support@tikz2svg.com** để gửi các loại email sau:

- ✅ **Email chào mừng** cho user mới
- ✅ **Email xác thực tài khoản** với mã 6 số
- ✅ **Email xác thực lưu SVG** khi vượt quá giới hạn hàng ngày
- ✅ **Email đặt lại mật khẩu** (tính năng cũ)
- ✅ **Rate limiting** và **bảo mật** nâng cao

## 🚀 Bước 1: Thiết lập Zoho Mail

### 1.1 Tạo App Password cho support@tikz2svg.com
1. Đăng nhập vào Zoho Mail với tài khoản `support@tikz2svg.com`
2. Vào **Settings** → **Mail Accounts**
3. Chọn tài khoản `support@tikz2svg.com`
4. Vào **Security** → **App Passwords**
5. Tạo app password mới cho ứng dụng
6. **Lưu lại password này** (sẽ không hiển thị lại)

### 1.2 Cấu hình SMTP
```
SMTP Server: smtp.zoho.com
Port: 587 (TLS)
Username: support@tikz2svg.com
Password: [App Password đã tạo]
```

## 🔧 Bước 2: Cấu hình Environment Variables

### 2.1 Thêm vào file `.env`
```bash
# Zoho Mail SMTP Settings
ZOHO_EMAIL=support@tikz2svg.com
ZOHO_APP_PASSWORD=your-app-password

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

## 🗄️ Bước 3: Thiết lập Database

### 3.1 Chạy SQL script cập nhật
```bash
mysql -u your_username -p your_database < email_log_table.sql
```

### 3.2 Kiểm tra bảng mới
```sql
SHOW TABLES LIKE '%verification%';
DESCRIBE verification_tokens;
```

## 🔌 Bước 4: Tích hợp vào app.py

### 4.1 Import services
```python
from email_service import init_email_service, get_email_service
from verification_service import init_verification_service, get_verification_service

# Khởi tạo services
email_service = init_email_service(app)
verification_service = init_verification_service()
```

### 4.2 Thêm routes cho xác thực
```python
@app.route('/send-account-verification/<int:user_id>')
@login_required
def send_account_verification(user_id):
    verification_service = get_verification_service()
    user = get_user_by_id(user_id)
    if user:
        success = verification_service.send_account_verification(
            user_id=user_id,
            email=user.email,
            username=user.username
        )
        return jsonify({'success': success})
    return jsonify({'success': False, 'error': 'User not found'})

@app.route('/verify-account')
def verify_account():
    code = request.args.get('code')
    verification_service = get_verification_service()
    
    if verification_service.verify_account(code):
        flash('Tài khoản đã được xác thực thành công!', 'success')
    else:
        flash('Mã xác thực không hợp lệ hoặc đã hết hạn!', 'error')
    
    return redirect(url_for('index'))

@app.route('/verify-svg')
@login_required
def verify_svg():
    code = request.args.get('code')
    verification_service = get_verification_service()
    
    if verification_service.verify_svg_save(code):
        flash('Xác thực lưu SVG thành công!', 'success')
    else:
        flash('Mã xác thực không hợp lệ hoặc đã hết hạn!', 'error')
    
    return redirect(url_for('index'))
```

### 4.3 Cập nhật hàm save_svg để kiểm tra giới hạn
```python
@app.route('/save_svg', methods=['POST'])
@login_required
def save_svg():
    # ... existing code ...
    
    # Kiểm tra giới hạn SVG trước khi lưu
    verification_service = get_verification_service()
    requires_verification, stats = verification_service.check_svg_verification_required(current_user.id)
    
    if requires_verification:
        # Gửi email xác thực
        success = verification_service.send_svg_verification(
            user_id=current_user.id,
            email=current_user.email,
            username=current_user.username,
            new_svg_filename=svg_filename
        )
        
        if success:
            return jsonify({
                "success": False, 
                "requires_verification": True,
                "message": f"Bạn đã lưu {stats['today']} file SVG hôm nay. Vui lòng kiểm tra email để xác thực."
            })
        else:
            return jsonify({"error": "Không thể gửi email xác thực"}), 500
    
    # Tiếp tục lưu SVG nếu không cần xác thực
    # ... existing save logic ...
```

## 📧 Bước 5: Sử dụng Hệ thống

### 5.1 Gửi email chào mừng
```python
email_service = get_email_service()
success = email_service.send_welcome_email(
    email="user@example.com",
    username="John Doe"
)
```

### 5.2 Gửi email xác thực tài khoản
```python
verification_service = get_verification_service()
success = verification_service.send_account_verification(
    user_id=user.id,
    email=user.email,
    username=user.username
)
```

### 5.3 Gửi email xác thực SVG
```python
verification_service = get_verification_service()
success = verification_service.send_svg_verification(
    user_id=user.id,
    email=user.email,
    username=user.username,
    new_svg_filename="my_svg_file.svg"
)
```

### 5.4 Xác thực bằng mã
```python
# Xác thực tài khoản
success = verification_service.verify_account("123456")

# Xác thực lưu SVG
success = verification_service.verify_svg_save("789012")
```

## 📊 Bước 6: Monitoring và Thống kê

### 6.1 Xem thống kê SVG của user
```python
verification_service = get_verification_service()
stats = verification_service.get_user_svg_stats(user_id)
print(f"SVG hôm nay: {stats['today']}")
print(f"SVG tuần này: {stats['weekly']}")
print(f"SVG tháng này: {stats['monthly']}")
print(f"Tổng SVG: {stats['total']}")
```

### 6.2 Kiểm tra giới hạn SVG
```python
requires_verification, stats = verification_service.check_svg_verification_required(user_id)
if requires_verification:
    print(f"User đã lưu {stats['today']} SVG hôm nay, cần xác thực")
```

### 6.3 Query database trực tiếp
```sql
-- Xem token xác thực
SELECT * FROM verification_tokens 
WHERE verification_type = 'svg_verification' 
ORDER BY created_at DESC;

-- Thống kê email theo loại
SELECT template, COUNT(*) as count, 
       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
FROM email_log 
GROUP BY template 
ORDER BY count DESC;
```

## ⚙️ Bước 7: Cấu hình Nâng cao

### 7.1 Điều chỉnh giới hạn SVG
```bash
# Trong file .env
DAILY_SVG_LIMIT=5   # Giảm xuống 5 file/ngày
DAILY_SVG_LIMIT=20  # Tăng lên 20 file/ngày
```

### 7.2 Điều chỉnh thời gian hết hạn mã
```python
# Trong email_config.py
SVG_VERIFICATION_CONFIG = {
    'daily_svg_limit': 10,
    'verification_code_expiry_hours': 12,  # Giảm xuống 12 giờ
    'verification_code_length': 6
}
```

### 7.3 Điều chỉnh rate limiting
```bash
# Trong file .env
EMAIL_MAX_PER_HOUR=100   # Tăng lên 100 email/giờ
EMAIL_MAX_PER_DAY=1000   # Tăng lên 1000 email/ngày
EMAIL_COOLDOWN_MINUTES=2 # Giảm cooldown xuống 2 phút
```

## 🛠️ Bước 8: Troubleshooting

### 8.1 Lỗi thường gặp

#### SMTP Authentication Failed
```
Error: SMTP authentication failed
Solution: Kiểm tra lại ZOHO_APP_PASSWORD
```

#### Verification Code Not Found
```
Error: Verification code not found
Solution: Kiểm tra mã xác thực và thời gian hết hạn
```

#### Database Connection Error
```
Error: Database connection failed
Solution: Kiểm tra cấu hình database và bảng verification_tokens
```

### 8.2 Debug Mode
```python
# Bật debug mode
ZOHO_MAIL_CONFIG = {
    # ... other config
    'MAIL_DEBUG': True,
    'MAIL_SUPPRESS_SEND': True,  # Không gửi thật
}
```

### 8.3 Test Hệ thống
```bash
# Test toàn bộ hệ thống
python test_verification_system.py

# Test riêng email
python test_email.py
```

## 🔒 Bước 9: Bảo mật

### 9.1 Bảo vệ App Password
- Không commit app password vào git
- Sử dụng environment variables
- Rotate app password định kỳ

### 9.2 Rate Limiting
- Giới hạn số email gửi mỗi giờ/ngày
- Implement cooldown giữa các lần gửi
- Monitor và block spam

### 9.3 Token Security
- Token có thời hạn tự động
- Token chỉ sử dụng một lần
- Xóa token cũ tự động

## 📈 Bước 10: Tối ưu hóa

### 10.1 Async Email Sending
```python
import threading

def send_verification_async(user_id, email, username):
    thread = threading.Thread(
        target=verification_service.send_account_verification,
        args=(user_id, email, username)
    )
    thread.start()
    return thread
```

### 10.2 Email Queue
```python
# Sử dụng Redis hoặc database để queue email
def queue_verification_email(user_id, email, username):
    # Thêm vào queue
    add_to_verification_queue(user_id, email, username)
    # Worker sẽ xử lý queue
```

### 10.3 Caching
```python
# Cache thống kê SVG
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_svg_stats(user_id):
    return verification_service.get_user_svg_stats(user_id)
```

## 🎯 Production Checklist

- [ ] Zoho Mail account `support@tikz2svg.com` đã được thiết lập
- [ ] App password đã được tạo và lưu an toàn
- [ ] Environment variables đã được cấu hình
- [ ] Database tables đã được tạo
- [ ] Email service đã được tích hợp vào app
- [ ] Verification service đã được tích hợp
- [ ] Test email đã được gửi thành công
- [ ] Rate limiting đã được cấu hình
- [ ] Error handling đã được implement
- [ ] Monitoring và logging đã được thiết lập
- [ ] Backup và recovery plan đã được chuẩn bị

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Logs trong console
2. Database verification_tokens table
3. Zoho Mail dashboard
4. Network connectivity
5. Firewall settings

---

**Lưu ý:** Đảm bảo tuân thủ các quy định về email marketing và spam laws của quốc gia bạn.
