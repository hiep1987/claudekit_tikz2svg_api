# 🚦 Rate Limiting Management Guide

## 📋 Tổng quan

Hệ thống email của TikZ2SVG API có cơ chế rate limiting để tránh spam và bảo vệ SMTP server. Hướng dẫn này giúp bạn quản lý rate limiting trong các môi trường khác nhau.

## 🔧 Cấu hình Rate Limiting

### File cấu hình: `email_config.py`

```python
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 100,    # Giới hạn email/giờ
    'max_emails_per_day': 1000,    # Giới hạn email/ngày  
    'cooldown_minutes': 1          # Thời gian chờ giữa các lần gửi (phút)
}
```

## 🛠️ Development Environment

### Bật/Tắt Rate Limiting

#### 1. **Tắt Rate Limiting (Khuyến nghị cho dev)**
```python
# Trong email_service.py, thêm bypass_rate_limit=True
success = email_service.send_email(
    recipient=email,
    template_name=template,
    context=context,
    bypass_rate_limit=True  # ← Tắt rate limiting
)
```

#### 2. **Giảm Rate Limiting cho Development**
```python
# Trong email_config.py
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 1000,   # Tăng giới hạn
    'max_emails_per_day': 10000,   # Tăng giới hạn
    'cooldown_minutes': 0.1        # Giảm cooldown (6 giây)
}
```

#### 3. **Reset Rate Limiting**
```bash
# Chạy script reset
python reset_rate_limit.py
```

### Scripts Test cho Development

```bash
# Test email với bypass rate limit
python test_email_bypass_rate_limit.py

# Test API trực tiếp (có bypass)
python test_email_api_direct.py

# Test rate limiting thực tế
python test_rate_limit_real.py
```

## 🚀 Production Environment

### Bật Rate Limiting (Mặc định)

#### 1. **Cấu hình Production**
```python
# Trong email_config.py
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 50,     # Giới hạn thấp hơn
    'max_emails_per_day': 500,     # Giới hạn thấp hơn
    'cooldown_minutes': 5          # Cooldown dài hơn
}
```

#### 2. **Không sử dụng bypass**
```python
# Trong production code
success = email_service.send_email(
    recipient=email,
    template_name=template,
    context=context
    # Không có bypass_rate_limit=True
)
```

### Monitoring Rate Limiting

#### 1. **Kiểm tra logs**
```bash
# Xem logs của Flask app
tail -f /var/log/tikz2svg/app.log

# Tìm rate limit messages
grep "Rate limit" /var/log/tikz2svg/app.log
```

#### 2. **Kiểm tra database**
```sql
-- Xem email logs
SELECT * FROM email_log 
WHERE error_message LIKE '%rate limit%' 
ORDER BY sent_at DESC;
```

## 📊 Các trạng thái Rate Limiting

### 1. **Hoạt động bình thường**
```
✅ Email sent successfully to user@example.com using template welcome
```

### 2. **Bị rate limit**
```
⚠️ Rate limit exceeded for email to user@example.com
Rate limit: Cooldown active, 2.5 minutes remaining
```

### 3. **Đạt giới hạn**
```
⚠️ Rate limit: Hourly limit reached (50/50)
⚠️ Rate limit: Daily limit reached (500/500)
```

## 🔄 Chuyển đổi giữa Development và Production

### Development → Production

1. **Cập nhật cấu hình**
```python
# email_config.py
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 50,     # Giảm xuống
    'max_emails_per_day': 500,     # Giảm xuống
    'cooldown_minutes': 5          # Tăng lên
}
```

2. **Loại bỏ bypass**
```python
# Tìm và xóa bypass_rate_limit=True trong code
success = email_service.send_email(email, template, context)
```

3. **Deploy và restart**
```bash
# Deploy lên VPS
./tikz2svg-dev-proxy-fixed.sh

# Restart service trên VPS
sudo systemctl restart tikz2svg
```

### Production → Development

1. **Cập nhật cấu hình**
```python
# email_config.py
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 1000,   # Tăng lên
    'max_emails_per_day': 10000,   # Tăng lên
    'cooldown_minutes': 0.1        # Giảm xuống
}
```

2. **Thêm bypass cho test**
```python
# Thêm bypass_rate_limit=True cho test routes
success = email_service.send_email(
    email, template, context, 
    bypass_rate_limit=True
)
```

3. **Reset rate limiting**
```bash
python reset_rate_limit.py
```

## 🚨 Troubleshooting

### Rate Limiting không hoạt động

1. **Kiểm tra Flask app restart**
```bash
# Rate limiting data bị mất khi restart
# Cần persistent storage cho production
```

2. **Kiểm tra email service initialization**
```python
# Đảm bảo email service được khởi tạo đúng
email_service = get_email_service()
if not email_service:
    print("Email service not available")
```

3. **Kiểm tra debug logs**
```python
# Thêm debug logging
print(f"Rate limit check: {self._check_rate_limit()}")
```

### Email bị rate limit quá nhiều

1. **Tăng giới hạn tạm thời**
```python
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 200,    # Tăng gấp đôi
    'max_emails_per_day': 2000,    # Tăng gấp đôi
    'cooldown_minutes': 2          # Giảm cooldown
}
```

2. **Sử dụng bypass cho admin**
```python
# Chỉ admin mới bypass
if is_admin_user(user_id):
    bypass_rate_limit = True
```

## 📝 Checklist

### Development Setup
- [ ] Rate limiting cooldown: 0.1-1 phút
- [ ] Giới hạn hourly: 1000+ emails
- [ ] Giới hạn daily: 10000+ emails
- [ ] Bypass rate limit cho test routes
- [ ] Scripts test đã sẵn sàng

### Production Setup
- [ ] Rate limiting cooldown: 5+ phút
- [ ] Giới hạn hourly: 50-100 emails
- [ ] Giới hạn daily: 500-1000 emails
- [ ] Không có bypass rate limit
- [ ] Monitoring và logging đã bật

### Deployment
- [ ] Cấu hình rate limiting đã cập nhật
- [ ] Code không có bypass (production)
- [ ] Service đã restart
- [ ] Logs được monitor
- [ ] Database email_log được kiểm tra

## 🔗 Related Files

- `email_config.py` - Cấu hình rate limiting
- `email_service.py` - Logic rate limiting
- `reset_rate_limit.py` - Script reset rate limiting
- `test_email_bypass_rate_limit.py` - Test với bypass
- `test_rate_limit_real.py` - Test rate limiting thực tế
- `app.py` - Routes sử dụng email service

## 📞 Support

Nếu gặp vấn đề với rate limiting:
1. Kiểm tra logs: `tail -f /var/log/tikz2svg/app.log`
2. Reset rate limiting: `python reset_rate_limit.py`
3. Test email system: `python test_email.py`
4. Liên hệ admin nếu cần tăng giới hạn
