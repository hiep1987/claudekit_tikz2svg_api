# 📁 Cấu hình Static Files và Thư mục Làm việc - TikZ to SVG API

## 🎯 Tổng quan
Tài liệu này mô tả cấu hình static files và các vấn đề liên quan đến thư mục làm việc trong ứng dụng TikZ to SVG API.

## 🏗️ Cấu trúc thư mục hiện tại

```
/var/www/tikz2svg_api/
├── shared/                          # Thư mục chia sẻ giữa các releases
│   ├── .env                        # File cấu hình môi trường
│   ├── static/                     # Static files chính
│   │   ├── avatars/               # Ảnh avatar người dùng
│   │   │   ├── avatar_2de74228358b4add9401f11be264069c.png
│   │   │   ├── avatar_4438c389b4c546be89ecc7b2423c5bd7.png
│   │   │   ├── avatar_6e44d63b109a448799d0bf4efc514a2d.png
│   │   │   └── avatar_981ea111072146589fa26c214c492b77.png
│   │   ├── css -> /var/www/tikz2svg_api/current/static/css
│   │   ├── js -> /var/www/tikz2svg_api/current/static/js
│   │   └── images/                # Ảnh SVG và PNG
│   └── tikz2svg.sock              # Unix socket cho gunicorn
├── current/                        # Release hiện tại (symbolic link)
│   └── static/
│       ├── avatars/               # Chỉ có 1 file avatar mới
│       │   └── avatar_e859f8cf697c4a6388aad14b846e7ce6.png
│       ├── css/
│       └── js/
└── releases/                       # Các releases khác
```

## ⚙️ Cấu hình trong app.py

### Biến môi trường STATIC_ROOT
```python
# Dòng 31-32 trong app.py
STATIC_ROOT = os.environ.get('TIKZ_SVG_DIR', os.path.join(os.getcwd(), 'static'))
os.makedirs(os.path.join(STATIC_ROOT, 'avatars'), exist_ok=True)
```

### Flask app configuration
```python
# Dòng 35 trong app.py
app = Flask(__name__, static_folder=STATIC_ROOT)
app.config['UPLOAD_FOLDER'] = STATIC_ROOT
```

## 🔍 Vấn đề thư mục làm việc

### 1. Thư mục làm việc hiện tại
- **Ứng dụng chạy từ:** `/var/www/tikz2svg_api/`
- **Biến TIKZ_SVG_DIR:** Không được set trong .env
- **STATIC_ROOT thực tế:** `/var/www/tikz2svg_api/static` (không tồn tại)

### 2. Vấn đề phát hiện
- Ứng dụng được cấu hình để sử dụng `/var/www/tikz2svg_api/static`
- Nhưng thư mục này không tồn tại
- Static files thực tế nằm trong `/var/www/tikz2svg_api/shared/static/`

### 3. Symbolic links
- `avatars` → `/var/www/tikz2svg_api/current/static/avatars` (symbolic link)
- `css` → `/var/www/tikz2svg_api/current/static/css` (symbolic link)  
- `js` → `/var/www/tikz2svg_api/current/static/js` (symbolic link)
- `images` → thư mục thực (không phải symbolic link)

## 🚨 Các vấn đề cần chú ý

### 1. Inconsistency trong cấu hình
- Avatar files được lưu vào `current/static/avatars/` (dòng 3569 trong app.py)
- Nhưng hiển thị từ `shared/static/avatars/`
- Có thể dẫn đến mất dữ liệu khi deploy release mới

### 2. Thư mục làm việc không đúng
- Ứng dụng chạy từ `/var/www/tikz2svg_api/`
- Nhưng STATIC_ROOT được tính toán sai
- Cần set biến môi trường `TIKZ_SVG_DIR` đúng cách

### 3. Symbolic links không đồng nhất
- `avatars`, `css`, `js` được link đến `current/static/`
- `images` không được link, chỉ tồn tại trong `shared/static/`
- Có thể gây confusion khi maintain

## 🔧 Giải pháp đề xuất

### 1. Set biến môi trường đúng
```bash
# Thêm vào /var/www/tikz2svg_api/shared/.env
TIKZ_SVG_DIR=/var/www/tikz2svg_api/shared/static
```

### 2. Tạo symbolic link cho avatars (ĐÃ HOÀN THÀNH)
```bash
# Tạo link từ shared/static/avatars đến current/static/avatars
ln -sf /var/www/tikz2svg_api/current/static/avatars /var/www/tikz2svg_api/shared/static/avatars

# Kiểm tra kết quả:
ls -la /var/www/tikz2svg_api/shared/static/ | grep avatars
# Kết quả: lrwxrwxrwx 1 hiep1987 hiep1987 44 Aug 25 17:08 avatars -> /var/www/tikz2svg_api/current/static/avatars
```

### 3. Tạo symbolic link cho images (KHUYẾN NGHỊ)
```bash
# Tạo link từ shared/static/images đến current/static/images
ln -sf /var/www/tikz2svg_api/current/static/images /var/www/tikz2svg_api/shared/static/images
```

### 3. Cập nhật cấu hình upload
```python
# Trong app.py, dòng 3569
save_path = os.path.join(STATIC_ROOT, 'avatars', filename)
# Đảm bảo STATIC_ROOT trỏ đến shared/static
```

## 📋 Checklist khi deploy

- [ ] Kiểm tra biến môi trường `TIKZ_SVG_DIR`
- [ ] Đảm bảo symbolic links được tạo đúng
- [ ] Kiểm tra quyền truy cập thư mục avatars
- [ ] Backup avatar files trước khi deploy
- [ ] Test upload avatar sau khi deploy

## 🔄 Cách hoạt động của Symbolic Links

### ✅ **2-way sync (avatars, css, js):**
```bash
# Tạo file trong current/static/avatars/ → sẽ có trong shared/static/avatars/
touch /var/www/tikz2svg_api/current/static/avatars/test.png

# Tạo file trong shared/static/avatars/ → sẽ có trong current/static/avatars/
touch /var/www/tikz2svg_api/shared/static/avatars/test2.png

# Cả hai file đều xuất hiện ở cả hai thư mục
ls /var/www/tikz2svg_api/current/static/avatars/
ls /var/www/tikz2svg_api/shared/static/avatars/
```

### ❌ **1-way sync (images):**
```bash
# Tạo file trong shared/static/images/ → CHỈ có trong shared/static/images/
touch /var/www/tikz2svg_api/shared/static/images/test.png

# File KHÔNG xuất hiện trong current/static/images/
ls /var/www/tikz2svg_api/current/static/images/  # Không có test.png
```

### 🎯 **Khuyến nghị:**
- **Luôn tạo file trong `current/static/`** để đảm bảo version control
- **Tạo symbolic link cho `images`** để có 2-way sync
- **Backup files quan trọng** trước khi thay đổi symbolic links

## 🎯 Kết luận

**Ảnh avatar hiện tại hiển thị từ:** `/var/www/tikz2svg_api/shared/static/avatars/`

**Cần sửa cấu hình để đảm bảo consistency và tránh mất dữ liệu khi deploy.**

---
*Tạo ngày: $(date)*
*Cập nhật lần cuối: $(date)*
