# 🔐 Hướng dẫn Setup Google OAuth cho TikZ2SVG

## 📋 Tổng quan

Tài liệu này hướng dẫn chi tiết cách cấu hình Google OAuth cho ứng dụng TikZ2SVG để đáp ứng yêu cầu của Google Auth Platform về Privacy Policy và các thông tin pháp lý cần thiết.

## 🎯 Yêu cầu đã hoàn thành

### ✅ 1. Privacy Policy Page
- **URL**: `/privacy-policy`
- **File**: `templates/privacy_policy.html`
- **Route**: `app.py` - function `privacy_policy()`
- **Nội dung**: Chính sách bảo mật chi tiết theo chuẩn Google OAuth

### ✅ 2. Terms of Service Page
- **URL**: `/terms-of-service` 
- **File**: `templates/terms_of_service.html`
- **Route**: `app.py` - function `terms_of_service()`
- **Nội dung**: Điều khoản sử dụng đầy đủ

### ✅ 3. Navigation Integration
- **Footer Links**: Thêm links đến Privacy Policy và Terms of Service
- **Mobile Menu**: Thêm section pháp lý trong mobile navigation
- **Responsive Design**: Tối ưu cho mobile và desktop

## 🚀 Cách sử dụng với Google OAuth Platform

### Bước 1: Truy cập Google Cloud Console
1. Mở [Google Cloud Console](https://console.cloud.google.com/)
2. Chọn project của bạn hoặc tạo project mới
3. Vào **APIs & Services > Credentials**

### Bước 2: Cấu hình OAuth 2.0 Client ID
1. Click **Create Credentials > OAuth 2.0 Client ID**
2. Chọn **Web Application**
3. Thiết lập các thông tin:

#### Authorized JavaScript Origins:
```
https://yourdomain.com
https://www.yourdomain.com
http://localhost:5000  (cho development)
```

#### Authorized Redirect URIs:
```
https://yourdomain.com/login/google/authorized
https://www.yourdomain.com/login/google/authorized
http://localhost:5000/login/google/authorized  (cho development)
```

### Bước 3: Cấu hình OAuth Consent Screen
1. Vào **APIs & Services > OAuth consent screen**
2. Chọn **External** user type
3. Điền các thông tin bắt buộc:

#### App Information:
- **App name**: TikZ2SVG
- **User support email**: support@yourdomain.com
- **Developer contact information**: support@yourdomain.com

#### App Domain:
- **Application home page**: `https://yourdomain.com`
- **Application privacy policy link**: `https://yourdomain.com/privacy-policy` ⭐
- **Application terms of service link**: `https://yourdomain.com/terms-of-service` ⭐

#### Authorized Domains:
```
yourdomain.com
```

### Bước 4: Scopes Configuration
Thêm các scopes cần thiết:
- `../auth/userinfo.email` 
- `../auth/userinfo.profile`
- `openid`

### Bước 5: Test Users (nếu app chưa verified)
Trong quá trình development, thêm test users:
- Thêm email addresses của các tester
- Tối đa 100 test users

## 🔧 Environment Variables

Đảm bảo file `.env` có các biến sau:

```bash
# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=your_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_here

# Flask Configuration
SECRET_KEY=your_secret_key_here
OAUTHLIB_INSECURE_TRANSPORT=1  # Chỉ cho development
```

## 📝 Checklist Verification

### ✅ Legal Pages
- [x] Privacy Policy accessible at `/privacy-policy`
- [x] Terms of Service accessible at `/terms-of-service`
- [x] Both pages có responsive design
- [x] Links được thêm vào footer và mobile menu
- [x] Nội dung tuân thủ yêu cầu của Google

### ✅ Technical Implementation  
- [x] Routes hoạt động chính xác
- [x] Templates extend base.html properly
- [x] CSS styling nhất quán với design system
- [x] SEO meta tags được thiết lập
- [x] Mobile-friendly design

### 🔲 Google OAuth Setup (cần làm)
- [ ] Tạo OAuth 2.0 Client ID
- [ ] Cấu hình OAuth Consent Screen
- [ ] Thêm Privacy Policy URL vào Google Console
- [ ] Thêm Terms of Service URL vào Google Console
- [ ] Test OAuth flow hoàn chỉnh

## 🌐 URLs cần cung cấp cho Google

Khi setup OAuth Consent Screen, sử dụng các URLs sau:

### Production URLs:
```
Application home page: https://yourdomain.com
Privacy Policy: https://yourdomain.com/privacy-policy
Terms of Service: https://yourdomain.com/terms-of-service
```

### Development URLs (for testing):
```
Application home page: http://localhost:5000
Privacy Policy: http://localhost:5000/privacy-policy  
Terms of Service: http://localhost:5000/terms-of-service
```

## 🔍 Validation và Testing

### Test Privacy Policy:
```bash
curl -I http://localhost:5000/privacy-policy
# Expected: HTTP/1.1 200 OK
```

### Test Terms of Service:
```bash
curl -I http://localhost:5000/terms-of-service
# Expected: HTTP/1.1 200 OK
```

### Manual Testing:
1. Truy cập `/privacy-policy` - kiểm tra hiển thị đúng
2. Truy cập `/terms-of-service` - kiểm tra hiển thị đúng  
3. Test responsive design trên mobile
4. Kiểm tra links trong footer và mobile menu

## 🚨 Lưu ý quan trọng

### Legal Compliance:
- **Privacy Policy** phải chính xác mô tả cách ứng dụng thu thập và sử dụng dữ liệu
- **Terms of Service** phải rõ ràng về quyền và nghĩa vụ của người dùng
- Cập nhật ngày sửa đổi khi có thay đổi

### Google Review Process:
- Google có thể mất 1-2 tuần để review ứng dụng
- Đảm bảo tất cả links hoạt động trước khi submit
- Có thể yêu cầu thông tin bổ sung trong quá trình review

### Security:
- Luôn sử dụng HTTPS cho production
- Bảo mật CLIENT_SECRET
- Định kỳ rotate OAuth credentials

## 📧 Liên hệ và Hỗ trợ

Nếu gặp vấn đề trong quá trình setup:

1. **Kiểm tra logs**: Check Flask application logs
2. **Google Console**: Xem error messages trong Google Cloud Console
3. **Documentation**: Tham khảo [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)

## 🎉 Kết luận

Với việc hoàn thành Privacy Policy và Terms of Service, ứng dụng TikZ2SVG đã sẵn sàng cho việc cấu hình Google OAuth. Các trang pháp lý được thiết kế responsive, tuân thủ yêu cầu của Google và tích hợp tốt với design system hiện tại.

**Next Steps:**
1. Deploy ứng dụng lên production server
2. Cấu hình Google OAuth Console với URLs thật
3. Submit cho Google review process
4. Monitor và maintain compliance

---

**Tài liệu được tạo**: 25/09/2025  
**Phiên bản**: 1.0  
**Tác giả**: TikZ2SVG Development Team