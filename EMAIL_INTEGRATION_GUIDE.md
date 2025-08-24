# 📧 Email System Integration Guide

## 🎯 Tổng quan

Hệ thống email đã được tích hợp thành công vào `app.py` với **hosted logo** để đảm bảo tương thích tốt với tất cả email clients.

## ✅ Tính năng đã tích hợp

### 1. **Hosted Logo System**
- Logo PNG được host trên server thay vì base64
- Tự động chuyển đổi từ SVG sang PNG (120x120px)
- URL: `http://localhost:5173/static/images/email_logo.png`

### 2. **Email Templates**
- **Welcome Email**: Chào mừng user mới
- **Verification Email**: Xác thực tài khoản với mã code
- **SVG Verification Email**: Thông báo khi lưu nhiều SVG

### 3. **API Endpoints**
- `/api/send-welcome-email` - Gửi email chào mừng
- `/api/send-verification-email` - Gửi email xác thực
- `/api/send-svg-verification-email` - Gửi email thông báo SVG
- `/api/send-test-email` - Gửi email test (cho admin)

### 4. **Web Interface**
- `/email-test` - Trang test email cho admin (yêu cầu đăng nhập)

## 🔧 Cấu hình

### Environment Variables
```bash
# Zoho Mail SMTP
ZOHO_SMTP_SERVER=smtp.zoho.com
ZOHO_SMTP_PORT=587
ZOHO_EMAIL=support@tikz2svg.com
ZOHO_APP_PASSWORD=your_app_password_here
```

### Logo Setup
Logo sẽ được tự động tạo khi cần thiết:
```python
# Tự động chuyển đổi SVG -> PNG
create_hosted_logo()
```

## 🚀 Cách sử dụng

### 1. **Test qua Web Interface**
```bash
# Truy cập: http://localhost:5173/email-test
# Yêu cầu đăng nhập Google
```

### 2. **Test qua API**
```bash
# Test welcome email
curl -X POST http://localhost:5173/api/send-welcome-email \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"TestUser"}'

# Test verification email
curl -X POST http://localhost:5173/api/send-verification-email \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"TestUser","verification_code":"123456"}'

# Test SVG verification email
curl -X POST http://localhost:5173/api/send-svg-verification-email \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"TestUser","svg_count":15}'
```

### 3. **Test bằng Python Script**
```bash
source venv/bin/activate && python test_integrated_email.py
```

## 📧 Email Templates

### Welcome Email
- **Subject**: "Chào mừng bạn đến với TikZ2SVG, {username}!"
- **Content**: Giới thiệu dịch vụ và hướng dẫn sử dụng

### Verification Email
- **Subject**: "Xác thực tài khoản - TikZ2SVG"
- **Content**: Mã xác thực 6 số với hướng dẫn bảo mật

### SVG Verification Email
- **Subject**: "Xác thực lưu SVG - TikZ2SVG"
- **Content**: Thông báo khi user lưu nhiều SVG trong ngày

## 🎨 Logo System

### Logo URL
```
http://localhost:5173/static/images/email_logo.png
```

### Logo Specifications
- **Format**: PNG
- **Size**: 120x120px
- **Source**: `static/logo.svg`
- **Quality**: High (6KB)
- **Compatibility**: Excellent

### Logo Creation Process
1. Đọc `static/logo.svg`
2. Chuyển đổi sang PNG với `cairosvg`
3. Lưu vào `static/images/email_logo.png`
4. Serve qua `/static/images/` endpoint

## 🔒 Bảo mật

### Authentication
- Email test endpoints yêu cầu đăng nhập (`@login_required`)
- Production endpoints không yêu cầu auth (cho automation)

### Rate Limiting
- Cần implement rate limiting cho production
- Log email activities

### Error Handling
- Graceful error handling cho SMTP failures
- Fallback mechanisms

## 📊 Monitoring

### Email Logging
```python
# Log email activities
print(f"📧 Email sent: {email} - {subject}")
```

### Health Checks
```bash
# Check logo endpoint
curl -I http://localhost:5173/static/images/email_logo.png

# Check email APIs
curl -X POST http://localhost:5173/api/send-welcome-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"Test"}'
```

## 🚀 Production Deployment

### 1. **Environment Setup**
```bash
# Set production environment variables
export ZOHO_APP_PASSWORD="your_production_password"
export ZOHO_EMAIL="support@tikz2svg.com"
```

### 2. **Logo Deployment**
```bash
# Ensure logo is created
python -c "from app import create_hosted_logo; create_hosted_logo()"
```

### 3. **Testing**
```bash
# Test all email endpoints
python test_integrated_email.py
```

## 📝 Notes

### Advantages of Hosted Logo
- ✅ Works on all email clients
- ✅ No base64 encoding issues
- ✅ High quality (120x120px)
- ✅ Fast loading
- ✅ Easy to update

### Integration Points
- User registration → Welcome email
- Account verification → Verification email
- SVG save limit → SVG verification email

### Future Enhancements
- Email templates customization
- A/B testing for email content
- Email analytics and tracking
- Advanced rate limiting
- Email queue system

## 🎉 Kết luận

Hệ thống email đã được tích hợp thành công với:
- **Hosted logo** cho tương thích tối đa
- **3 loại email templates** cho các use cases khác nhau
- **RESTful APIs** cho automation
- **Web interface** cho testing
- **Error handling** và logging

Sẵn sàng cho production deployment! 🚀
