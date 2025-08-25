# 🚦 Rate Limiting Quick Reference

## ⚡ Quick Commands

### Development (Bật bypass)
```bash
# Reset rate limiting
python reset_rate_limit.py

# Test với bypass
python test_email_bypass_rate_limit.py

# Test API trực tiếp
python test_email_api_direct.py
```

### Production (Tắt bypass)
```bash
# Kiểm tra logs
tail -f /var/log/tikz2svg/app.log | grep "Rate limit"

# Kiểm tra database
mysql -u hiep1987 -p tikz2svg -e "SELECT * FROM email_log WHERE error_message LIKE '%rate limit%' ORDER BY sent_at DESC;"
```

## 🔧 Quick Config Changes

### Development Config
```python
# email_config.py
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 1000,   # Cao
    'max_emails_per_day': 10000,   # Cao
    'cooldown_minutes': 0.1        # Thấp (6 giây)
}
```

### Production Config
```python
# email_config.py
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 50,     # Thấp
    'max_emails_per_day': 500,     # Thấp
    'cooldown_minutes': 5          # Cao (5 phút)
}
```

## 🎯 Quick Code Changes

### Development (Thêm bypass)
```python
# Thêm bypass_rate_limit=True
success = email_service.send_email(
    email, template, context, 
    bypass_rate_limit=True  # ← Thêm dòng này
)
```

### Production (Xóa bypass)
```python
# Xóa bypass_rate_limit=True
success = email_service.send_email(
    email, template, context
    # Không có bypass_rate_limit=True
)
```

## 📊 Status Messages

| Status | Message | Action |
|--------|---------|--------|
| ✅ Success | `Email sent successfully` | Không cần làm gì |
| ⚠️ Rate Limited | `Rate limit exceeded` | Đợi cooldown hoặc reset |
| ❌ Error | `Email service error` | Kiểm tra logs |

## 🚨 Emergency Commands

### Tắt rate limiting tạm thời
```python
# Thêm vào code tạm thời
bypass_rate_limit = True
```

### Reset rate limiting
```bash
python reset_rate_limit.py
```

### Kiểm tra email service
```bash
python test_email.py
```

## 📱 Environment Variables

```bash
# Development
export FLASK_ENV=development
export EMAIL_RATE_LIMIT_BYPASS=true

# Production  
export FLASK_ENV=production
# Không set EMAIL_RATE_LIMIT_BYPASS
```

## 🔄 Deployment Checklist

### Dev → Prod
- [ ] Giảm `max_emails_per_hour` từ 1000 → 50
- [ ] Giảm `max_emails_per_day` từ 10000 → 500  
- [ ] Tăng `cooldown_minutes` từ 0.1 → 5
- [ ] Xóa tất cả `bypass_rate_limit=True`
- [ ] Deploy và restart service

### Prod → Dev
- [ ] Tăng `max_emails_per_hour` từ 50 → 1000
- [ ] Tăng `max_emails_per_day` từ 500 → 10000
- [ ] Giảm `cooldown_minutes` từ 5 → 0.1
- [ ] Thêm `bypass_rate_limit=True` cho test
- [ ] Reset rate limiting

## 📞 Quick Support

| Problem | Solution |
|---------|----------|
| Rate limit quá nhiều | Tăng giới hạn hoặc dùng bypass |
| Rate limit không hoạt động | Reset rate limiting |
| Email không gửi được | Kiểm tra email service |
| Logs không hiển thị | Kiểm tra log level |

## 🎯 Remember

- **Development**: Bypass rate limit, giới hạn cao, cooldown thấp
- **Production**: Không bypass, giới hạn thấp, cooldown cao
- **Emergency**: Có thể bypass tạm thời cho admin
- **Monitoring**: Luôn kiểm tra logs và database
