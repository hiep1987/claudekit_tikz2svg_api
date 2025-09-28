# 🚀 GTM + GA4 Configuration Guide

**Ngày cập nhật:** 28/09/2025  
**Vấn đề đã sửa:** Xung đột giữa GTM và GA4 duplicate setup

## ✅ Vấn đề đã được sửa

### Trước khi sửa:
- GTM load GA4 tự động
- Code riêng biệt cũng cố gắng load GA4 → **Xung đột**
- Cảnh báo: `⚠️ GA4 already loaded - skipping duplicate setup`
- Cookie conflict: `_ga_DH7Q258GXF has been overwritten`

### Sau khi sửa:
- ✅ Chỉ GTM quản lý GA4 (chỉ trong production)
- ✅ Loại bỏ code GA4 riêng biệt
- ✅ GTM bị disable hoàn toàn trong development
- ✅ Giữ lại environment detection cho các helper functions
- ✅ Không còn duplicate warnings và cookie conflicts

## 🔧 Cấu hình GTM Container: GTM-N6J4LQJ4

### Bước 1: Thiết lập GA4 Configuration Tag
1. Vào [Google Tag Manager](https://tagmanager.google.com/)
2. Chọn container `GTM-N6J4LQJ4`
3. Tạo **Tag** mới:
   - **Tag Type**: Google Analytics: GA4 Configuration
   - **Measurement ID**: `G-DH7Q258GXF`
   - **Trigger**: All Pages

### Bước 2: Cấu hình Environment-specific Settings
```javascript
// Custom JavaScript Variable: isProduction
function() {
  return window.location.hostname === 'tikz2svg.com' || 
         window.location.hostname === 'www.tikz2svg.com';
}

// Custom JavaScript Variable: isDevelopment  
function() {
  return window.location.hostname === 'localhost' || 
         window.location.hostname === '127.0.0.1' || 
         window.location.port === '5173' ||
         window.location.port === '5000' ||
         window.location.hostname.includes('localhost');
}
```

### Bước 3: Development vs Production Config

#### Production Settings (tikz2svg.com):
- **Cookie Domain**: `.tikz2svg.com`
- **Cookie Expires**: `63072000` (2 years)
- **Analytics Storage**: `granted`
- **Ad Storage**: `denied`
- **Cookie Flags**: `SameSite=Lax;Secure`

#### Development Settings (localhost):
- **Storage**: `none`
- **Client Storage**: `none`
- **Analytics Storage**: `denied`
- **Debug Mode**: `true`

### Bước 4: Event Tracking Setup
Thiết lập các custom events qua GTM thay vì code:

1. **TikZ Render Event**
   - Event Name: `tikz_render`
   - Parameters: `tikz_length`, `render_time`

2. **Copy Event**
   - Event Name: `tikz_copy`
   - Parameters: `copy_type` (svg/tikz)

3. **Download Event**
   - Event Name: `tikz_download`
   - Parameters: `file_format`

## 🧪 Kiểm tra hoạt động

### 1. Development Mode
```javascript
// Console sẽ hiển thị:
console.log('🔧 Analytics Development Mode - GTM Active');
```

### 2. Production Mode
- Kiểm tra Network tab → filter `collect`
- Xem GA4 Realtime reports
- Debug bằng GA4 DebugView

### 3. Không còn warnings
- ✅ Không còn "GA4 already loaded"
- ✅ Không còn cookie overwrite warnings  
- ✅ Clean console logs
- ✅ GTM chỉ load trong production (tikz2svg.com)
- ✅ Development mode: "🔧 Development Mode - GTM disabled, no cookies"

## 📋 Checklist

- [x] Loại bỏ duplicate GA4 setup code
- [x] Giữ lại GTM container
- [x] Environment detection vẫn hoạt động
- [ ] Cấu hình GA4 tag trong GTM
- [ ] Test tracking events
- [ ] Verify production analytics

## 🔗 Liên quan

- `templates/base.html` - Template chính đã được cập nhật
- `GTM-N6J4LQJ4` - Container ID
- `G-DH7Q258GXF` - GA4 Measurement ID
- `GOOGLE_TAG_MANAGER_SETUP_NOTE.md` - Hướng dẫn GTM ban đầu
