# Comments Feature - Hướng Dẫn Sử Dụng

**Phiên bản:** 1.2.1 Final  
**Ngày:** 2025-10-22  
**Trạng thái:** ✅ Sẵn sàng sử dụng

---

## 📖 Mục lục

1. [Giới thiệu](#giới-thiệu)
2. [Tính năng chính](#tính-năng-chính)
3. [Cách sử dụng](#cách-sử-dụng)
4. [Hỗ trợ LaTeX](#hỗ-trợ-latex)
5. [Quy tắc bình luận](#quy-tắc-bình-luận)
6. [FAQ](#faq)

---

## Giới thiệu

Hệ thống bình luận cho phép người dùng trao đổi, thảo luận về các hình ảnh TikZ SVG. 

### ✨ Điểm nổi bật

- 💬 Bình luận và trả lời (nested comments)
- 👍 Thích bình luận
- ✏️ Chỉnh sửa/Xóa bình luận của bạn
- 🔢 Hỗ trợ công thức toán (LaTeX/MathJax)
- 📱 Responsive (mobile-friendly)
- 🔒 Bảo mật cao (chống spam, XSS)

---

## Tính năng chính

### 1. Tạo bình luận mới

**Yêu cầu:** Đã đăng nhập

1. Truy cập trang xem SVG
2. Cuộn xuống phần "💬 Bình luận"
3. Nhập nội dung vào ô textarea
4. Nhấn "📨 Gửi bình luận"

**Giới hạn:**
- Tối đa 5000 ký tự/bình luận
- Rate limit: 50 bình luận/giờ

### 2. Trả lời bình luận

1. Nhấn nút "💬 Trả lời" dưới bình luận
2. Nhập nội dung trả lời
3. Nhấn "Gửi"

**Lưu ý:** Trả lời sẽ hiển thị lồng vào bình luận gốc.

### 3. Thích bình luận

1. Nhấn nút "👍" dưới bình luận
2. Nhấn lại để bỏ thích

**Đặc điểm:**
- Cập nhật ngay lập tức (optimistic UI)
- Hiển thị số lượt thích
- Chỉ 1 like/người dùng

### 4. Chỉnh sửa bình luận

**Điều kiện:** Chỉ chỉnh sửa bình luận của mình

1. Nhấn nút "⋮" (menu) ở góc trên phải bình luận
2. Chọn "✏️ Chỉnh sửa"
3. Sửa nội dung trong ô textarea
4. Nhấn "Lưu" hoặc "Hủy"

**Lưu ý:** Bình luận đã chỉnh sửa sẽ có nhãn "(đã chỉnh sửa)".

### 5. Xóa bình luận

**Điều kiện:** Chỉ xóa bình luận của mình

1. Nhấn nút "⋮" (menu)
2. Chọn "🗑️ Xóa"
3. Xác nhận trong hộp thoại

**Cảnh báo:** Xóa bình luận gốc sẽ xóa tất cả câu trả lời.

---

## Hỗ trợ LaTeX

Bạn có thể sử dụng công thức toán trong bình luận!

### Cú pháp

**Inline math** (trong dòng):
```
Công thức Euler: $e^{i\pi} + 1 = 0$
```
Hiển thị: Công thức Euler: $e^{i\pi} + 1 = 0$

**Display math** (riêng dòng):
```
$$\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$
```
Hiển thị: 
$$\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$

### Ví dụ

```
Định lý Pythagore: $a^2 + b^2 = c^2$

Chuỗi Taylor:
$$f(x) = \sum_{n=0}^{\infty} \frac{f^{(n)}(a)}{n!}(x-a)^n$$

Ma trận: $\begin{pmatrix} a & b \\ c & d \end{pmatrix}$
```

---

## Quy tắc bình luận

### ✅ Được phép

- Thảo luận về hình ảnh TikZ
- Đặt câu hỏi kỹ thuật
- Chia sẻ kiến thức
- Góp ý xây dựng
- Sử dụng LaTeX cho công thức toán

### ❌ Không được phép

- Spam (lặp lại nội dung)
- Quảng cáo không liên quan
- Ngôn từ thô tục, xúc phạm
- Chia sẻ thông tin cá nhân
- Link đến trang web nguy hiểm

### 🚨 Hệ thống chống spam

Bình luận sẽ bị từ chối nếu:
- Chứa từ khóa spam ("BUY NOW", "CLICK HERE", v.v.)
- Có quá nhiều link (>2 URLs)
- Toàn bộ chữ IN HOA (>20 ký tự)
- Ký tự lặp lại quá nhiều

---

## FAQ

### 1. Tôi chưa đăng nhập, có thể bình luận không?

**Không.** Bạn cần đăng nhập bằng Google để bình luận.

**Cách đăng nhập:**
1. Nhấn nút "Đăng nhập" trong phần bình luận
2. Chọn "Đăng nhập Google"
3. Hoàn tất xác thực

---

### 2. Tại sao bình luận của tôi bị từ chối?

**Nguyên nhân phổ biến:**
- Nội dung trống
- Quá dài (>5000 ký tự)
- Bị phát hiện là spam
- Bình luận trùng lặp (trong vòng 1 phút)

**Giải pháp:** Kiểm tra và sửa nội dung, thử lại sau 1 phút.

---

### 3. Làm sao để xuống dòng trong bình luận?

Nhấn **Enter** để xuống dòng. Khoảng trắng sẽ được giữ nguyên.

**Ví dụ:**
```
Dòng 1
Dòng 2
Dòng 3
```

---

### 4. Tôi có thể chỉnh sửa bình luận sau khi gửi không?

**Có**, nếu đó là bình luận của bạn:
1. Nhấn nút "⋮" (menu)
2. Chọn "✏️ Chỉnh sửa"

---

### 5. Bình luận có bị xóa tự động không?

**Không.** Bình luận chỉ bị xóa khi:
- Bạn tự xóa
- Admin xóa (vi phạm quy tắc)
- Hình ảnh SVG bị xóa (xóa cascade)

---

### 6. Làm sao để nhận thông báo khi có người trả lời?

Tính năng thông báo real-time đang được phát triển. Hiện tại:
- Reload trang để xem bình luận mới
- Hoặc nhấn F5

---

### 7. Tôi có thể báo cáo bình luận spam không?

Hiện chưa có nút "Báo cáo" trực tiếp. Vui lòng liên hệ admin qua email nếu thấy nội dung vi phạm.

---

### 8. Có giới hạn số lượng bình luận không?

**Có**, để tránh spam:
- **50 bình luận/giờ** mỗi người dùng
- **100 requests/giờ** mỗi IP

Nếu vượt quá, bạn sẽ nhận thông báo và cần chờ 1 giờ.

---

### 9. LaTeX không render, làm sao?

**Nguyên nhân:**
- Cú pháp LaTeX sai
- MathJax chưa load xong

**Giải pháp:**
1. Kiểm tra cú pháp (dùng `$...$` hoặc `$$...$$`)
2. Đợi 2-3 giây để MathJax render
3. Reload trang nếu vẫn không hiển thị

---

### 10. Bình luận có hỗ trợ hình ảnh/video không?

**Chưa.** Hiện chỉ hỗ trợ:
- Text thuần
- LaTeX math
- Link (tự động clickable)

---

## 💡 Tips & Tricks

### Viết bình luận hay

1. **Rõ ràng:** Diễn đạt ngắn gọn, dễ hiểu
2. **Tôn trọng:** Lịch sự với người khác
3. **Có ích:** Chia sẻ kiến thức, không spam
4. **Format:** Sử dụng LaTeX cho công thức
5. **Kiểm tra:** Đọc lại trước khi gửi

### Keyboard Shortcuts

- **Tab:** Di chuyển giữa các nút
- **Enter:** Gửi bình luận (khi focus vào nút)
- **Esc:** Đóng menu/form

### Tối ưu trải nghiệm

- Sử dụng trình duyệt hiện đại (Chrome, Firefox, Safari)
- Bật JavaScript
- Đăng nhập trước khi vào trang để tránh lag

---

## 🔗 Liên hệ & Hỗ trợ

- **Email:** support@tikz2svg.com
- **GitHub Issues:** [Link repository]
- **Documentation:** Xem `COMMENTS_IMPLEMENTATION_ROADMAP.md`

---

## 📜 Changelog

### Version 1.2.1 Final (2025-10-22)
- ✅ Full CRUD operations
- ✅ Nested replies support
- ✅ Like/Unlike functionality
- ✅ MathJax integration
- ✅ Spam detection
- ✅ Optimistic UI updates
- ✅ Mobile responsive
- ✅ WCAG AAA accessibility

---

**Cập nhật lần cuối:** 2025-10-22  
**Người viết:** TikZ2SVG Development Team


