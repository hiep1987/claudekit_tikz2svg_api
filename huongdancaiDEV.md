


# Hướng dẫn thiết lập & chạy môi trường DEV Tikz2SVG trên Mac  
**Thư mục dự án:** `/Users/hieplequoc/web/work/tikz2svg_api`  

---

## 1. Chuẩn bị trước

### 1.1. Yêu cầu
- MacOS (đã cài Homebrew).
- Python (phiên bản giống trên VPS, ví dụ Python 3.13).
- SSH đã cấu hình host `h2cloud-hiep1987` trong `~/.ssh/config`.
- MySQL client:
  ```bash
  brew install mysql
  ```
- Node.js (nếu frontend cần build).

---

## 2. Kéo code từ VPS về Mac

```bash
cd /Users/hieplequoc/web/work
scp -r h2cloud-hiep1987:/path/to/tikz2svg_api .
```

Hoặc dùng Git:
```bash
cd /Users/hieplequoc/web/work
git clone git@github.com:.../tikz2svg_api.git
```

---

## 3. Cài đặt môi trường Python

```bash
cd /Users/hieplequoc/web/work/tikz2svg_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Kết nối CSDL từ xa qua SSH tunnel

### 4.1. Mở tunnel

```bash
# Đóng tunnel cũ nếu có
kill -9 $(lsof -ti tcp:3306) 2>/dev/null || true

# Mở tunnel mới
ssh -fN -L 3306:127.0.0.1:3306 h2cloud-hiep1987
```

> App DEV sẽ kết nối `127.0.0.1:3306` và thực chất truy cập MySQL trên VPS.

### 4.2. Kiểm tra kết nối

```bash
mysql -h 127.0.0.1 -P 3306 -u hiep1987 -p tikz2svg -e "SELECT 1;"
```

Nếu ra:
```
+---+
| 1 |
+---+
| 1 |
+---+
```
→ Kết nối thành công.

---

## 5. Chạy môi trường DEV

Có 2 cách:

### 5.1. Thủ công
```bash
cd /Users/hieplequoc/web/work/tikz2svg_api
source .venv/bin/activate
tikz2svg-dev
```

### 5.2. Dùng script `tikz2svg-dev-proxy`
Script này vừa mở tunnel vừa chạy server:
```bash
cd /Users/hieplequoc/web/work/tikz2svg_api
tikz2svg-dev-proxy
```

---

## 6. Kiểm tra tunnel đang chạy

```bash
lsof -iTCP:3306 -sTCP:LISTEN
```

---

## 7. Ngắt & mở lại tunnel

```bash
kill -9 $(lsof -ti tcp:3306) 2>/dev/null || true
ssh -fN -L 3306:127.0.0.1:3306 h2cloud-hiep1987
```

---

## 8. Lưu ý

- **Không chỉnh code kết nối DB trong app** để tránh xung đột khi push lên PROD.  
- Đảm bảo SSH key hoạt động tốt:
  ```bash
  ssh-add -K ~/.ssh/id_rsa
  ```
- Nếu tunnel bị rớt, chỉ cần chạy lại lệnh mở tunnel.
- Có thể dùng `autossh` để tự động reconnect:
  ```bash
  brew install autossh
  autossh -fN -M 0 -L 3306:127.0.0.1:3306 h2cloud-hiep1987
  ```

---

## 9. Quy trình làm việc hằng ngày

1. Mở tunnel:
   ```bash
   ssh -fN -L 3306:127.0.0.1:3306 h2cloud-hiep1987
   ```
2. Chạy DEV:
   ```bash
   cd /Users/hieplequoc/web/work/tikz2svg_api
   tikz2svg-dev-proxy
   ```
3. Truy cập: http://127.0.0.1:5173

---

## 10. Khi kết thúc

```bash
CTRL+C  # dừng Flask server
kill -9 $(lsof -ti tcp:3306) 2>/dev/null || true  # đóng tunnel
```