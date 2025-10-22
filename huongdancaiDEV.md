


# Hướng dẫn thiết lập & chạy môi trường DEV Tikz2SVG trên Mac  
**Thư mục dự án:** `/Users/hieplequoc/web/work/tikz2svg_api`  

## 🚀 Quick Start (Cách nhanh nhất)

**Chỉ cần 1 lệnh duy nhất:**
```bash
tikz2svg-dev-local
```

**Kết quả:** Tự động khởi động tất cả services và có thể truy cập:
- 📱 **App:** http://127.0.0.1:5173/
- 🗄️ **phpMyAdmin:** http://localhost:8080/phpmyadmin/

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

### 5.3. Chạy nhanh local dev với alias (tự động khởi động tất cả services)

**Bước 1:** Thêm alias vào cuối file `~/.zshrc`:
```sh
alias tikz2svg-dev-local="/Users/hieplequoc/web/work/tikz2svg_api/tikz2svg-dev-local.sh"
```

Sau đó nạp lại cấu hình:
```sh
source ~/.zshrc
```

**Bước 2:** Chạy development server chỉ với 1 lệnh:
```sh
tikz2svg-dev-local
```

Script sẽ tự động:
- 🚀 **Khởi động MySQL** (nếu chưa chạy)
- 🌐 **Khởi động Apache** (nếu chưa chạy) 
- 📁 Load biến môi trường từ `.env`
- 🐍 Kích hoạt virtualenv
- 🔗 Kiểm tra kết nối database local
- 🚀 Khởi động Flask server ở http://127.0.0.1:5173/

**Kết quả:** Sau khi chạy lệnh, bạn có thể truy cập:
- 📱 **App:** http://127.0.0.1:5173/
- 🗄️ **phpMyAdmin:** http://localhost:8080/phpmyadmin/
- 📊 **Database:** tikz2svg (user: hiep1987, password: trống)

---

## 6. Truy cập Database Local với phpMyAdmin

### 6.1. Tự động với tikz2svg-dev-local
Khi chạy `tikz2svg-dev-local`, phpMyAdmin sẽ tự động khả dụng tại:
```
http://localhost:8080/phpmyadmin/
```

**Thông tin đăng nhập:**
- **Username:** `hiep1987`
- **Password:** (để trống)
- **Database:** `tikz2svg`

### 6.2. Khởi động thủ công (nếu cần)
```bash
# Khởi động MySQL
brew services start mysql

# Khởi động Apache
brew services start httpd

# Kiểm tra trạng thái
brew services list | grep mysql
brew services list | grep httpd
```

### 6.3. So sánh VPS vs Local
| Môi trường | URL | Database |
|------------|-----|----------|
| **VPS** | https://tikz2svg.com/phpmyadmin | Production DB |
| **Local** | http://localhost:8080/phpmyadmin | Local DB |

---

## 7. Kiểm tra tunnel đang chạy

```bash
lsof -iTCP:3306 -sTCP:LISTEN
```

---

## 8. Ngắt & mở lại tunnel

```bash
kill -9 $(lsof -ti tcp:3306) 2>/dev/null || true
ssh -fN -L 3306:127.0.0.1:3306 h2cloud-hiep1987
```

---

## 9. Lưu ý

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
2. Kiểm tra CSDL đang chạy
  ```bash
   lsof -iTCP:3306 -sTCP:LISTEN
   ```
3. Chạy DEV:
   ```bash
   cd /Users/hieplequoc/web/work/tikz2svg_api
   tikz2svg-dev-proxy
   ```
4. Truy cập: http://127.0.0.1:5173

---

## 10. Khi kết thúc

```bash
CTRL+C  # dừng Flask server
kill -9 $(lsof -ti tcp:3306) 2>/dev/null || true  # đóng tunnel
```
## 11. Chạy stagewise
```bash
cd ~/web/demo_site
npx stagewise -b
```

---

## 12. Thay đổi gần đây: Tách Navbar dùng chung

- Đã tách thanh điều hướng (navbar) thành một template dùng chung: `templates/_navbar.html`.
- Các trang sau đã thay phần navbar trùng lặp bằng include:
  - `templates/index.html`
  - `templates/profile_settings.html`
  - `templates/profile_svg_files.html`
  - `templates/profile_followed_posts.html`
  - `templates/view_svg.html`
- Cách sử dụng cho trang mới: chèn dòng sau vào vị trí navbar (ngay sau `<body>` hoặc chỗ phù hợp):

```jinja
{% include '_navbar.html' %}
```

- Template dùng chung dựa trên các biến context đã có sẵn từ Flask/Jinja: `current_user`, `current_user_email`, `current_username`, `current_avatar` (được inject qua `@app.context_processor`).
- Lợi ích: giảm trùng lặp, dễ bảo trì giao diện và logic menu (desktop/mobile, avatar, đăng nhập/đăng xuất).