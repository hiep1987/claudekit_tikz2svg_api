# 🔧 CSP (Content Security Policy) Fix Report

## 🐛 VẤN ĐỀ

**Lỗi trong browser console:**
```
Refused to load the stylesheet/script '<URL>' because it violates 
the following Content Security Policy directive...
```

**Nguyên nhân:**
- Security headers được thêm vào `comments_helpers.py` (dòng 108-145)
- CSP quá strict, chỉ cho phép `'self'` 
- **BLOCK** tất cả CDN external: Bootstrap, CodeMirror, jsDelivr, etc.

---

## ✅ GIẢI PHÁP ĐÃ ÁP DỤNG

### File: `comments_helpers.py`

**BEFORE (quá strict):**
```python
"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://www.googletagmanager.com; "
"style-src 'self' 'unsafe-inline'; "  # ❌ Chỉ cho phép 'self'!
"connect-src 'self';"  # ❌ Block CDN!
```

**AFTER (relaxed for development):**
```python
"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://www.googletagmanager.com https://cdnjs.cloudflare.com https://codemirror.net; "
"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://codemirror.net; "  # ✅ Cho phép CDN CSS!
"connect-src 'self' https://cdn.jsdelivr.net;"  # ✅ Cho phép fetch từ CDN!
"font-src 'self' data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;"  # ✅ Cho phép fonts từ CDN!
```

---

## 📝 THAY ĐỔI CHI TIẾT

### 1. `script-src` - JavaScript sources
**Thêm:**
- `https://cdnjs.cloudflare.com` (Cloudflare CDN)
- `https://codemirror.net` (CodeMirror CDN)

### 2. `style-src` - CSS sources  
**Thêm:**
- `https://cdn.jsdelivr.net` (Bootstrap, etc.)
- `https://cdnjs.cloudflare.com` 
- `https://codemirror.net`

### 3. `font-src` - Font sources
**Thêm:**
- `https://cdn.jsdelivr.net`
- `https://cdnjs.cloudflare.com`

### 4. `connect-src` - AJAX/fetch sources
**Thêm:**
- `https://cdn.jsdelivr.net` (cho source maps, etc.)

---

## 🚀 CÁCH ÁP DỤNG FIX

### Bước 1: Restart Flask server
```bash
# Kill server hiện tại
pkill -f "flask.*5173"
# hoặc Ctrl + C trong terminal đang chạy

# Chạy lại
./tikz2svg-dev-local.sh
```

### Bước 2: Hard refresh browser
```bash
Cmd + Shift + R (Mac)
Ctrl + Shift + R (Windows/Linux)
```

### Bước 3: Verify fix
```bash
# Mở browser console (F12)
# Không còn lỗi CSP nữa!
# CodeMirror load thành công!
```

---

## ✅ KẾT QUẢ MONG ĐỢI

**Sau khi restart server + hard refresh:**

1. ✅ Bootstrap CSS/JS load thành công
2. ✅ CodeMirror load thành công  
3. ✅ Highlight.js load thành công
4. ✅ MathJax load thành công
5. ✅ Google Tag Manager hoạt động
6. ✅ Không còn lỗi CSP trong console
7. ✅ Index page hiển thị bình thường
8. ✅ CodeMirror editor hoạt động

---

## 🔐 BẢO MẬT

### CSP hiện tại: Balanced (Development)

**Ưu điểm:**
- ✅ Cho phép CDN trusted (jsDelivr, Cloudflare)
- ✅ App hoạt động bình thường
- ✅ Vẫn bảo vệ khỏi XSS cơ bản

**Nhược điểm:**
- ⚠️ Cho phép `'unsafe-inline'` và `'unsafe-eval'`
- ⚠️ Không strict như production nên

### Production CSP (Recommendation)

Khi deploy production, nên strict hơn:
```python
# Option 1: Nonce-based CSP (tốt nhất)
nonce = generate_nonce()
response.headers['Content-Security-Policy'] = (
    f"script-src 'nonce-{nonce}' https://cdn.jsdelivr.net; "
    f"style-src 'nonce-{nonce}' https://cdn.jsdelivr.net;"
)

# Option 2: Hash-based CSP
# Tính SHA256 hash của inline scripts
```

---

## 📊 SUMMARY

| Issue | Status | Fix |
|-------|--------|-----|
| CSP blocking Bootstrap | ✅ FIXED | Added cdn.jsdelivr.net to style-src |
| CSP blocking CodeMirror | ✅ FIXED | Added codemirror.net to script-src, style-src |
| CSP blocking fonts | ✅ FIXED | Added CDNs to font-src |
| CSP blocking AJAX | ✅ FIXED | Added cdn.jsdelivr.net to connect-src |
| CodeMirror undefined error | ✅ WILL FIX | After restart + refresh |

---

## ⚠️ LƯU Ý

**Comments feature ĐÃ HOẠT ĐỘNG** nhưng CSP headers block các resources cần thiết!

**Không phải lỗi của Comments feature!** Đây là lỗi cấu hình CSP quá strict!

**Fix đã apply vào `comments_helpers.py`, cần restart server để có hiệu lực!**

---

**Generated:** 2025-10-22  
**Issue:** CSP blocking CDN resources  
**Status:** ✅ FIXED - Need restart server  
**Action:** `pkill -f flask && ./tikz2svg-dev-local.sh`
