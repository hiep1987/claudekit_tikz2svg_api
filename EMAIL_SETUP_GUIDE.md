# Hướng dẫn thiết lập Email System với Zoho Mail

## 📋 Tổng quan

Hệ thống email này sử dụng **Zoho Mail SMTP** để gửi email từ ứng dụng TikZ2SVG API. Hệ thống bao gồm:

- ✅ Gửi email chào mừng cho user mới
- ✅ Gửi email đặt lại mật khẩu
- ✅ Gửi email thông báo chia sẻ SVG
- ✅ Gửi email thông báo tùy chỉnh
- ✅ Rate limiting để tránh spam
- ✅ Logging và thống kê email
- ✅ Template HTML đẹp mắt

## 🚀 Bước 1: Thiết lập Zoho Mail

### 1.1 Tạo tài khoản Zoho Mail
1. Truy cập [Zoho Mail](https://www.zoho.com/mail/)
2. Đăng ký tài khoản miễn phí hoặc trả phí
3. Xác minh email và thiết lập domain

### 1.2 Tạo App Password
1. Đăng nhập vào Zoho Mail
2. Vào **Settings** → **Mail Accounts**
3. Chọn tài khoản email của bạn
4. Vào **Security** → **App Passwords**
5. Tạo app password mới cho ứng dụng
6. **Lưu lại password này** (sẽ không hiển thị lại)

### 1.3 Thông tin SMTP Zoho
```
SMTP Server: smtp.zoho.com
Port: 587 (TLS) hoặc 465 (SSL)
Username: your-email@zoho.com
Password: [App Password đã tạo]
```

## 🔧 Bước 2: Cấu hình Environment Variables

### 2.1 Thêm vào file `.env`
```bash
# Zoho Mail SMTP Settings
ZOHO_EMAIL=your-email@zoho.com
ZOHO_APP_PASSWORD=your-app-password

# App Configuration
APP_URL=https://yourdomain.com

# Admin Email
ADMIN_EMAIL=admin@yourdomain.com

# Email Rate Limiting (optional)
EMAIL_MAX_PER_HOUR=50
EMAIL_MAX_PER_DAY=500
EMAIL_COOLDOWN_MINUTES=5
```

### 2.2 Kiểm tra cấu hình
```bash
python test_email.py
```

## 🗄️ Bước 3: Thiết lập Database

### 3.1 Chạy SQL script
```bash
mysql -u your_username -p your_database < email_log_table.sql
```

### 3.2 Kiểm tra bảng đã tạo
```sql
SHOW TABLES LIKE '%email%';
DESCRIBE email_log;
DESCRIBE password_reset_tokens;
DESCRIBE email_notifications;
```

## 🔌 Bước 4: Tích hợp vào app.py

### 4.1 Import và khởi tạo
```python
from email_service import init_email_service, get_email_service

# Trong hàm create_app() hoặc sau khi tạo app
email_service = init_email_service(app)
```

### 4.2 Thêm routes cho email
```python
@app.route('/send-welcome-email/<int:user_id>')
@login_required
def send_welcome_email(user_id):
    email_service = get_email_service()
    # Lấy thông tin user từ database
    user = get_user_by_id(user_id)
    if user:
        success = email_service.send_welcome_email(user.email, user.username)
        return jsonify({'success': success})
    return jsonify({'success': False, 'error': 'User not found'})

@app.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    email = request.form.get('email')
    email_service = get_email_service()
    
    # Tạo reset token
    reset_token = generate_reset_token(email)
    
    # Gửi email
    success = email_service.send_password_reset_email(email, username, reset_token)
    return jsonify({'success': success})
```

## 📧 Bước 5: Sử dụng Email Service

### 5.1 Gửi email chào mừng
```python
from email_service import get_email_service

email_service = get_email_service()
success = email_service.send_welcome_email(
    email="user@example.com",
    username="John Doe"
)
```

### 5.2 Gửi email đặt lại mật khẩu
```python
success = email_service.send_password_reset_email(
    email="user@example.com",
    username="John Doe",
    reset_token="abc123..."
)
```

### 5.3 Gửi email thông báo
```python
success = email_service.send_notification_email(
    recipient_email="user@example.com",
    title="SVG mới được tạo",
    message="Bạn đã tạo thành công một SVG mới!",
    action_url="https://yourdomain.com/view/123"
)
```

### 5.4 Gửi email hàng loạt
```python
recipients = ["user1@example.com", "user2@example.com"]
results = email_service.send_bulk_email(
    recipients=recipients,
    template_name="notification",
    context={'message': 'Thông báo quan trọng'},
    delay_seconds=2
)
```

## 📊 Bước 6: Monitoring và Thống kê

### 6.1 Xem thống kê email
```python
stats = email_service.get_email_stats()
print(f"Total emails: {stats['overall']['total_emails']}")
print(f"Success rate: {stats['overall']['successful_emails'] / stats['overall']['total_emails'] * 100}%")
```

### 6.2 Query database trực tiếp
```sql
-- Thống kê email theo ngày
SELECT DATE(sent_at) as date, COUNT(*) as total, 
       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
FROM email_log 
WHERE sent_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(sent_at)
ORDER BY date DESC;

-- Email lỗi gần đây
SELECT recipient, template, error_message, sent_at
FROM email_log 
WHERE success = 0 
ORDER BY sent_at DESC 
LIMIT 10;
```

## 🛠️ Bước 7: Troubleshooting

### 7.1 Lỗi thường gặp

#### SMTP Authentication Failed
```
Error: SMTP authentication failed
Solution: Kiểm tra lại ZOHO_EMAIL và ZOHO_APP_PASSWORD
```

#### Connection Timeout
```
Error: Connection timeout
Solution: Kiểm tra firewall, proxy, hoặc thử port 465 (SSL)
```

#### Rate Limit Exceeded
```
Error: Rate limit exceeded
Solution: Tăng EMAIL_COOLDOWN_MINUTES hoặc giảm số email gửi
```

### 7.2 Debug Mode
```python
# Bật debug mode trong email_config.py
ZOHO_MAIL_CONFIG = {
    # ... other config
    'MAIL_DEBUG': True,  # Bật debug
    'MAIL_SUPPRESS_SEND': True,  # Không gửi thật (test mode)
}
```

### 7.3 Test Connection
```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.zoho.com', 587)
server.starttls()
server.login('your-email@zoho.com', 'your-app-password')
print('Connection successful!')
server.quit()
"
```

## 🔒 Bước 8: Bảo mật

### 8.1 Bảo vệ App Password
- Không commit app password vào git
- Sử dụng environment variables
- Rotate app password định kỳ

### 8.2 Rate Limiting
- Giới hạn số email gửi mỗi giờ/ngày
- Implement cooldown giữa các lần gửi
- Monitor và block spam

### 8.3 Email Validation
```python
import re

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

## 📈 Bước 9: Tối ưu hóa

### 9.1 Async Email Sending
```python
import threading

def send_email_async(email_service, recipient, template, context):
    thread = threading.Thread(
        target=email_service.send_email,
        args=(recipient, template),
        kwargs={'context': context}
    )
    thread.start()
    return thread
```

### 9.2 Email Queue
```python
# Sử dụng Redis hoặc database để queue email
def queue_email(recipient, template, context):
    # Thêm vào queue
    add_to_email_queue(recipient, template, context)
    # Worker sẽ xử lý queue
```

### 9.3 Template Caching
```python
# Cache rendered templates
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_template(template_name, **context):
    return render_template(template_name, **context)
```

## 🎯 Bước 10: Production Checklist

- [ ] Zoho Mail account đã được thiết lập
- [ ] App password đã được tạo và lưu an toàn
- [ ] Environment variables đã được cấu hình
- [ ] Database tables đã được tạo
- [ ] Email service đã được tích hợp vào app
- [ ] Test email đã được gửi thành công
- [ ] Rate limiting đã được cấu hình
- [ ] Error handling đã được implement
- [ ] Monitoring và logging đã được thiết lập
- [ ] Backup và recovery plan đã được chuẩn bị

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Logs trong console
2. Database email_log table
3. Zoho Mail dashboard
4. Network connectivity
5. Firewall settings

---

**Lưu ý:** Đảm bảo tuân thủ các quy định về email marketing và spam laws của quốc gia bạn.
