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

### ❌ Không nên làm
- Chỉnh sửa trực tiếp trong `/var/www/tikz2svg_api/current/`
- Deploy mà không test
- Commit với message không rõ ràng
- Xóa releases mà không backup

### Static files
- Thư mục `static/` đã bỏ khỏi Git, các file SVG/PNG/avatars sẽ lưu trong `shared/static` để không mất khi deploy.

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
- **Current release**: `20250810_053746`
- **Service name**: `tikz2svg`
- **Socket file**: `/var/www/tikz2svg_api/shared/tikz2svg.sock`
- **User/Group**: `hiep1987/www-data`
