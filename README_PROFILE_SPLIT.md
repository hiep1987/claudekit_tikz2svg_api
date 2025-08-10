# Hướng dẫn tách trang profile.html thành 3 trang riêng biệt

## Tổng quan
File `profile.html` hiện tại rất lớn (3757 dòng) và chứa 3 phần chính. Việc tách thành 3 trang riêng biệt sẽ giúp:
- Dễ bảo trì và phát triển
- Tải trang nhanh hơn
- Code sạch và có tổ chức hơn

## 3 trang cần tạo:

### 1. Trang Cài đặt Profile (`profile_settings.html`)
**Phần tương ứng:** `id="profile-content"` trong file gốc

**Nội dung chính:**
- Form cài đặt thông tin cá nhân
- Upload và crop avatar
- Editor bio (Quill)
- Các thông tin: email, username, bio

**Các file cần include:**
- Bootstrap CSS/JS
- Quill Editor
- Cropper.js
- Font Awesome

### 2. Trang File SVG (`profile_svg_files.html`)
**Phần tương ứng:** `class="svg-files-section"` trong file gốc

**Nội dung chính:**
- Grid hiển thị các file SVG đã tạo
- Nút like/unlike
- Menu hành động (tải ảnh, share Facebook, copy link, xem code, xóa)
- Thông tin file (thời gian tạo, kích thước, người tạo)

**Các file cần include:**
- Bootstrap CSS/JS
- Font Awesome
- CodeMirror (cho xem code TikZ)

### 3. Trang Bài đăng theo dõi (`profile_followed_posts.html`)
**Phần tương ứng:** `class="followed-posts-section"` trong file gốc

**Nội dung chính:**
- Danh sách bài đăng từ người đã follow
- Loading spinner
- Thông báo khi chưa có bài đăng
- Các chức năng tương tự trang file SVG

## Cấu trúc thư mục đề xuất:
```
tikz2svg_api/templates/
├── profile.html (giữ lại làm trang chính)
├── profile_settings.html (trang cài đặt)
├── profile_svg_files.html (trang file SVG)
├── profile_followed_posts.html (trang bài đăng theo dõi)
└── components/
    ├── navbar.html (tách phần navbar)
    ├── modals.html (tách các modal)
    └── scripts.html (tách JavaScript chung)
```

## Các bước thực hiện:

### Bước 1: Tách phần chung
1. **Navbar:** Tách phần `navbar-header-user` thành component riêng
2. **Modals:** Tách các modal (logout, delete, cropper) thành component
3. **Scripts:** Tách JavaScript chung thành file riêng

### Bước 2: Tạo từng trang
1. **profile_settings.html:**
   - Copy phần `id="profile-content"`
   - Include các thư viện cần thiết
   - Giữ nguyên logic JavaScript

2. **profile_svg_files.html:**
   - Copy phần `class="svg-files-section"`
   - Include các thư viện cần thiết
   - Giữ nguyên logic like và action buttons

3. **profile_followed_posts.html:**
   - Copy phần `class="followed-posts-section"`
   - Include các thư viện cần thiết
   - Giữ nguyên logic polling và load data

### Bước 3: Cập nhật routing
Cần thêm routes mới trong Flask:
```python
@app.route('/profile/settings')
def profile_settings():
    # Logic hiện tại của profile route
    pass

@app.route('/profile/svg-files')
def profile_svg_files():
    # Logic load SVG files
    pass

@app.route('/profile/followed-posts')
def profile_followed_posts():
    # Logic load followed posts
    pass
```

### Bước 4: Cập nhật navigation
Thêm links trong navbar để chuyển đổi giữa các trang:
```html
<a href="/profile/settings">Cài đặt</a>
<a href="/profile/svg-files">File SVG</a>
<a href="/profile/followed-posts">Bài đăng theo dõi</a>
```

## Lưu ý quan trọng:

### 1. JavaScript Variables
Cần đảm bảo các biến global được truyền đúng:
```javascript
window.isLoggedIn = {{ 'true' if current_user.is_authenticated else 'false' }};
window.activeFeedbackCount = 0;
window.isOwner = {{ 'true' if is_owner else 'false' }};
```

### 2. Context Variables
Cần truyền đầy đủ context từ Flask:
- `current_user`
- `current_avatar`
- `current_username`
- `current_user_email`
- `user_email`
- `avatar`
- `username`
- `bio`
- `email_verified`
- `svg_files`
- `is_owner`

### 3. API Endpoints
Đảm bảo các API endpoints vẫn hoạt động:
- `/like_svg`
- `/delete_svg`
- `/api/followed_posts`
- `/api/like_counts`
- `/api/follower_count/<user_id>`

### 4. CSS Conflicts
Kiểm tra và tránh xung đột CSS giữa các trang:
- Sử dụng CSS modules hoặc prefix
- Tách CSS thành file riêng cho từng trang

### 5. Performance
- Lazy load các thư viện không cần thiết
- Minify CSS/JS
- Sử dụng CDN cho các thư viện bên ngoài

## Lợi ích sau khi tách:

1. **Maintainability:** Dễ bảo trì và debug
2. **Performance:** Tải trang nhanh hơn
3. **Scalability:** Dễ mở rộng tính năng
4. **Code Organization:** Code sạch và có tổ chức
5. **Team Development:** Nhiều developer có thể làm việc song song

## Kết luận
Việc tách trang `profile.html` thành 3 trang riêng biệt là cần thiết để cải thiện maintainability và performance. Cần thực hiện từng bước một cách cẩn thận để đảm bảo không ảnh hưởng đến functionality hiện tại. 