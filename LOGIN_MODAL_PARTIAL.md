## Login Modal Partial (`templates/partials/_login_modal.html`)

### Mục đích
- Cung cấp modal đăng nhập dùng lại trên nhiều trang.
- Tách HTML modal khỏi template chính để dễ bảo trì, tránh trùng lặp.

### Cấu trúc HTML (rút gọn)
```html
<div id="login-modal">
  <div class="login-modal-box">
    <h3>Đăng nhập để sử dụng tính năng này</h3>
    <p>Vui lòng đăng nhập để có thể:</p>
    <ul>
      <li>👁️ Xem TikZ code</li>
      <li>👍 Like và unlike ảnh</li>
      <li>💾 Lưu ảnh vào server</li>
      <li>👥 Theo dõi người dùng khác</li>
    </ul>
    <p class="login-note">💡 Bạn vẫn có thể dùng Facebook Share và Copy Link không cần đăng nhập!</p>
    <div class="login-modal-actions">
      <button id="modal-login-btn" class="google-login-btn">
        <span class="google-login-content">[Google SVG Icon] Đăng nhập Google</span>
      </button>
      <button class="btn-cancel">Huỷ</button>
    </div>
  </div>
</div>
```

### Cách include trong template
```jinja2
{% include 'partials/_login_modal.html' %}
```

Nên đặt ngay trước các thẻ script cuối trang để CSS đã load trước khi modal hiển thị.

### CSS yêu cầu
- Đã gom tại: `static/css/login_modal.css`
- Đảm bảo thêm link CSS ở `<head>`:
```jinja2
<link rel="stylesheet" href="{{ url_for('static', filename='css/login_modal.css', v='1.0') }}">
```

Các class chính:
- `#login-modal`: overlay và container modal
- `.login-modal-box`: hộp nội dung
- `.login-modal-actions`: vùng nút
- `.google-login-btn`, `.btn-cancel`, `.login-note`

### JS tương tác gợi ý
- Nút mở modal: thêm class `show` hoặc thay `display` qua JS.
- Nút đóng modal: chọn `.btn-cancel` để ẩn modal.
- Nút `#modal-login-btn`: điều hướng `/login/google` hoặc gọi hàm đăng nhập.

Ví dụ khởi tạo tối thiểu:
```javascript
(function () {
  const modal = document.getElementById('login-modal');
  const openers = document.querySelectorAll('[data-open-login-modal="true"]');
  const cancelBtn = modal?.querySelector('.btn-cancel');
  const loginBtn = modal?.querySelector('#modal-login-btn');

  openers.forEach(btn => btn.addEventListener('click', () => modal.style.display = 'flex'));
  cancelBtn?.addEventListener('click', () => modal.style.display = 'none');
  loginBtn?.addEventListener('click', () => { window.location.href = '/login/google'; });
})();
```

Lưu ý: Ở các trang đã có logic mở modal riêng (vd. `static/js/index.js`, `static/js/view_svg.js`), chỉ cần đảm bảo phần tử `#login-modal` tồn tại.

### Best practices
- Không nhúng inline CSS/JS trong partial.
- Điều khiển hiển thị bằng `classList` hoặc CSS, hạn chế `style.display` trực tiếp nếu đã có lớp tiện ích.
- Tối ưu FOUC: chỉ gắn event sau khi DOM sẵn sàng (`DOMContentLoaded` hoặc cuối `<body>`).


