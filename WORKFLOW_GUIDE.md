# TikZ2SVG Development Workflow Guide

## Cấu trúc môi trường

### DEV Environment (`~/dev/tikz2svg_api/`)
- **Mục đích**: Phát triển và test code
- **Git repository**: `git@github.com:hiep1987/tikz2svg_api.git`
- **Virtual environment**: `.venv/`
- **Branch**: `main`

### PRODUCTION Environment (`/var/www/tikz2svg_api/`)
- **Mục đích**: Chạy ứng dụng thực tế
- **Cấu trúc**: Releases với symlink `current/`
- **Virtual environment**: `venv/`
- **Service**: `tikz2svg` (systemd)

## Quy trình làm việc


### 1. Phát triển trong DEV
```bash
cd ~/dev/tikz2svg_api

# Kích hoạt virtual environment
source .venv/bin/activate

# Chỉnh sửa code
# Test ứng dụng
python app.py
```

#### Chạy DEV server trên VPS và truy cập từ Mac

1. **Trên VPS**:
    ```bash
    tikz2svg-dev
    ```
    (script đã cấu hình sẵn để chạy Flask DEV trên cổng 5173 với môi trường .env từ PROD)

2. **Trên máy Mac**:
    ```bash
    ssh -L 5173:127.0.0.1:5173 h2cloud-hiep1987
    ssh -L 5173:127.0.0.1:5173 hiep1987@36.50.134.234
    ```
    - Sau đó mở trình duyệt và truy cập `http://localhost:5173/` để xem giao diện DEV chạy trên VPS.

### 2. Commit và Push
```bash
# Kiểm tra trạng thái
git status

# Thêm file mới
git add .

# Commit thay đổi
git commit -m "Mô tả thay đổi"

# Push lên GitHub
git push origin main
```

### 3. Deploy lên Production
```bash
# Chuẩn bị thư mục static shared (nếu chưa có)
mkdir -p /var/www/tikz2svg_api/shared/static

# Deploy từ GitHub
sudo bash /var/www/tikz2svg_api/deploy.sh git@github.com:hiep1987/tikz2svg_api.git main
```
Static đã được chuyển sang `shared/static` và cần chắc chắn thư mục này tồn tại, sẽ được deploy.sh tự tạo.

### 4. Kiểm tra Production
```bash
# Kiểm tra service
systemctl status tikz2svg

# Kiểm tra socket
curl --unix-socket /var/www/tikz2svg_api/shared/tikz2svg.sock -I http://localhost/

# Kiểm tra website
curl -I -H 'Host: tikz2svg.mathlib.io.vn' http://127.0.0.1/
```

### 5. Rollback nếu cần
```bash
sudo bash /var/www/tikz2svg_api/rollback.sh
# Chọn release muốn rollback tới
```

## Lệnh hữu ích

### Kiểm tra logs
```bash
# Logs của service
journalctl -u tikz2svg -n 50

# Logs của gunicorn
tail -f /var/www/tikz2svg_api/shared/logs/gunicorn_error.log
tail -f /var/www/tikz2svg_api/shared/logs/gunicorn_output.log
```

### Quản lý releases
```bash
# Xem danh sách releases
ls -la /var/www/tikz2svg_api/releases/

# Xem release hiện tại
ls -la /var/www/tikz2svg_api/current

# Xóa releases cũ (giữ 5 bản mới nhất)
cd /var/www/tikz2svg_api/releases
ls -1t | tail -n +6 | xargs -r sudo rm -rf
```

## Lưu ý quan trọng

### ✅ Nên làm
- Phát triển trong `~/dev/tikz2svg_api/`
- Test kỹ trước khi deploy
- Commit thường xuyên với message rõ ràng
- Backup trước khi deploy lớn
- Kiểm tra logs sau khi deploy
- Test static files trên cả DEV và PROD sau khi thay đổi cấu hình
- Kiểm tra cấu hình nginx khi thay đổi đường dẫn static files

### ❌ Không nên làm
- Chỉnh sửa trực tiếp trong `/var/www/tikz2svg_api/current/`
- Deploy mà không test
- Commit với message không rõ ràng
- Xóa releases mà không backup

### Static files
- Thư mục `static/` đã bỏ khỏi Git, các file SVG/PNG/avatars sẽ lưu trong `shared/static` để không mất khi deploy.
- **Cấu hình**: Flask app sử dụng `STATIC_ROOT = '/var/www/tikz2svg_api/shared/static'` cho cả DEV và PROD
- **Đồng bộ**: DEV và PROD sử dụng cùng thư mục shared để đảm bảo dữ liệu nhất quán

### Khắc phục vấn đề Static Files

#### Vấn đề: DEV không thấy ảnh SVG như PROD
**Nguyên nhân**: Flask app DEV sử dụng `static_folder` mặc định thay vì `STATIC_ROOT`

**Giải pháp**:
```python
# Trong app.py - cấu hình đúng
STATIC_ROOT = os.environ.get('TIKZ_SVG_DIR', '/var/www/tikz2svg_api/shared/static')
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(os.path.join(STATIC_ROOT, 'avatars'), exist_ok=True)

app = Flask(__name__, static_folder=STATIC_ROOT)  # Quan trọng!
app.config['UPLOAD_FOLDER'] = STATIC_ROOT
```

#### Vấn đề: Nginx không serve static files
**Nguyên nhân**: Cấu hình nginx trỏ sai đường dẫn

**Giải pháp**:
```bash
# Sửa cấu hình nginx HTTPS
sudo sed -i 's|alias /var/www/tikz2svg_api/current/static/;|alias /var/www/tikz2svg_api/shared/static/;|' /etc/nginx/sites-available/tikz2svg_api

# Sửa socket path nếu cần
sudo sed -i 's|proxy_pass http://unix:/var/www/tikz2svg_api/tikz2svg.sock;|proxy_pass http://unix:/var/www/tikz2svg_api/shared/tikz2svg.sock;|' /etc/nginx/sites-available/tikz2svg

# Reload nginx
sudo systemctl reload nginx
```

#### Test static files
```bash
# Test PROD
curl -I https://tikz2svg.mathlib.io.vn/static/filename.svg

# Test DEV
curl -I http://localhost:5173/static/filename.svg
```

### Troubleshooting

#### Kiểm tra nhanh khi có vấn đề static files
```bash
# 1. Kiểm tra file có tồn tại không
ls -la /var/www/tikz2svg_api/shared/static/filename.svg

# 2. Kiểm tra cấu hình nginx
sudo cat /etc/nginx/sites-available/tikz2svg_api | grep "location /static/"

# 3. Kiểm tra quyền truy cập
ls -la /var/www/tikz2svg_api/shared/static/

# 4. Test nginx config
sudo nginx -t

# 5. Reload nginx nếu cần
sudo systemctl reload nginx
```

#### Debug DEV server
```bash
# Kiểm tra cấu hình Flask
cd ~/dev/tikz2svg_api
grep -n "static_folder\|STATIC_ROOT" app.py

# Test DEV server
source .venv/bin/activate
python app.py
# Sau đó test: curl -I http://localhost:5000/static/filename.svg
```

## Health endpoint

- **Route**: `GET /health` → `{"status":"ok"}`
- **Health-check trong deploy**:  
  ```bash
  curl --unix-socket /var/www/tikz2svg_api/shared/tikz2svg.sock http://localhost/health
  ```

## Workflow tóm tắt

```
DEV (~/dev/tikz2svg_api/) 
    ↓ (chỉnh sửa code)
    ↓ (git add, commit, push)
GitHub Repository
    ↓ (deploy.sh)
PRODUCTION (/var/www/tikz2svg_api/)
    ↓ (rollback.sh nếu cần)
Previous Release
```

## Thông tin hiện tại

- **DEV workspace**: `~/dev/tikz2svg_api/`
- **PROD workspace**: `/var/www/tikz2svg_api/`
- **Current release**: `20250816_041033`
- **Service name**: `tikz2svg`
- **Socket file**: `/var/www/tikz2svg_api/shared/tikz2svg.sock`
- **Static files**: `/var/www/tikz2svg_api/shared/static/` (shared giữa DEV và PROD)
- **User/Group**: `hiep1987/www-data`
- **Nginx config**: Đã cập nhật để sử dụng shared/static

## Thay đổi gần đây

### Refactor: Navbar dùng chung

- Tạo `templates/_navbar.html` chứa toàn bộ thanh điều hướng (desktop + mobile).
- Các trang sau đã thay navbar inline bằng include:
  - `templates/index.html`
  - `templates/profile_settings.html`
  - `templates/profile_svg_files.html`
  - `templates/profile_followed_posts.html`
  - `templates/view_svg.html`
- Cách dùng ở template khác:

```jinja
{% include '_navbar.html' %}
```

- Lưu ý: Navbar dựa trên các biến context: `current_user`, `current_user_email`, `current_username`, `current_avatar` (được inject bởi `@app.context_processor`).
