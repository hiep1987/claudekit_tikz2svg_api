# 🌏 Hướng Dẫn: Sử Dụng Chữ Trung, Nhật, Hàn trong TikZ

**Dành cho:** Người dùng tikz2svg_api  
**Ngày cập nhật:** 30/10/2025

---

## 🎯 TÓM TẮT NHANH

**Để hiển thị chữ Trung Quốc, Nhật Bản, Hàn Quốc trong TikZ:**

### ❌ SAI (Chữ hiện thành hộp `��`):

```latex
\begin{tikzpicture}
  \node {中文: 富贵};
\end{tikzpicture}
```

### ✅ ĐÚNG (Thêm 1 dòng chọn font):

```latex
\setmainfont{STSong}

\begin{tikzpicture}
  \node {中文: 富贵};
\end{tikzpicture}
```

---

## 📋 FONTS TIẾNG TRUNG CÓ SẴN

Hệ thống hỗ trợ các fonts sau (macOS):

| Font Name | Kiểu chữ | Dùng cho |
|-----------|----------|----------|
| **STSong** | Song thể (宋体) | ✅ **Khuyến nghị** - Chữ in thông thường |
| Heiti TC/SC | Hắc thể (黑体) | Chữ đậm, tiêu đề |
| Kaiti TC/SC | Khải thư (楷书) | Chữ viết tay đẹp |
| Baoli TC/SC | Báo lệ (报隶) | Chữ lệ thư |

**Lưu ý:**
- **TC** = Traditional Chinese (繁體中文 - Phồn thể)
- **SC** = Simplified Chinese (简体中文 - Giản thể)

---

## 💡 CÁC CÁCH SỬ DỤNG

### Cách 1: Đổi font toàn bộ document (Đơn giản nhất)

```latex
\setmainfont{STSong}  % Áp dụng cho TẤT CẢ text

\begin{tikzpicture}
  \node {中文: 富贵};
  \node at (0,-1) {日本語: こんにちは};
  \node at (0,-2) {한국어: 안녕하세요};
\end{tikzpicture}
```

---

### Cách 2: Chỉ áp dụng cho node cụ thể

```latex
\begin{tikzpicture}
  \node {English text};  % Font mặc định
  \node[font=\fontspec{STSong}] at (0,-1) {中文: 富贵};  % Chỉ node này
  \node at (0,-2) {Back to default};
\end{tikzpicture}
```

---

### Cách 3: Định nghĩa font riêng cho CJK (Chuyên nghiệp)

```latex
\newfontfamily\zhfont{STSong}[Script=CJK]
\newfontfamily\jafont{Hiragino Sans}[Script=CJK]

\begin{tikzpicture}
  \node {Latin text};
  \node[font=\zhfont] at (0,-1) {中文: 富贵};
  \node[font=\jafont] at (0,-2) {日本語: こんにちは};
\end{tikzpicture}
```

---

## 🔧 VÍ DỤ THỰC TẾ

### Ví dụ 1: Biểu đồ toán học với chú thích tiếng Trung

```latex
\setmainfont{STSong}

\begin{tikzpicture}[scale=1.5]
  % Trục tọa độ
  \draw[->] (-2,0) -- (3,0) node[right] {$x$};
  \draw[->] (0,-2) -- (0,3) node[above] {$y$};
  
  % Đồ thị hàm số
  \draw[thick,blue] plot[domain=-1.5:2.5] (\x,{\x*\x-1});
  
  % Chú thích tiếng Trung
  \node at (2,3) {抛物线};  % Parabola
  \node at (2,2.5) {$y = x^2 - 1$};
\end{tikzpicture}
```

---

### Ví dụ 2: Chữ thư pháp (calligraphy)

```latex
\setmainfont{Kaiti SC}  % Font chữ viết tay

\begin{tikzpicture}
  \node[scale=3] {富贵};  % Phú quý
  \node at (0,-2) {吉祥};  % Cát tường
\end{tikzpicture}
```

---

### Ví dụ 3: Kết hợp nhiều ngôn ngữ

```latex
\setmainfont{STSong}

\begin{tikzpicture}
  % Tiếng Việt (OK với font mặc định)
  \node at (0,2) {Tiếng Việt: Xin chào};
  
  % Tiếng Trung (cần font CJK)
  \node at (0,1) {中文: 你好};
  
  % Tiếng Nhật (cần font CJK)
  \node at (0,0) {日本語: こんにちは};
  
  % Tiếng Hàn (cần font CJK)
  \node at (0,-1) {한국어: 안녕하세요};
\end{tikzpicture}
```

---

## ❌ CÁC LỖI THƯỜNG GẶP

### Lỗi 1: Chữ hiện thành hộp `��`

**Nguyên nhân:** Không chọn font CJK  
**Giải pháp:** Thêm `\setmainfont{STSong}`

---

### Lỗi 2: Compile lỗi với `%!<CJKutf8>`

```latex
❌ SAI:
%!<CJKutf8>
\begin{CJK*}{UTF8}{gbsn}
  \node {中文};
\end{CJK*}
```

**Nguyên nhân:** `CJKutf8` không tương thích với LuaLaTeX  
**Giải pháp:** Dùng `fontspec` thay thế

```latex
✅ ĐÚNG:
\setmainfont{STSong}
\node {中文};
```

---

### Lỗi 3: Font not found

```
! Package fontspec Error: The font "XXX" cannot be found.
```

**Nguyên nhân:** Tên font sai hoặc không có trên hệ thống  
**Giải pháp:** Dùng font có sẵn (STSong, Heiti TC, Kaiti SC)

---

## 📊 SO SÁNH CÁCH TIẾP CẬN

| Đặc điểm | Cách CŨ (CJKutf8) | Cách MỚI (fontspec) |
|----------|------------------|-------------------|
| Compiler | pdfLaTeX | LuaLaTeX ✅ |
| Syntax | `\begin{CJK*}{UTF8}{gbsn}...\end{CJK*}` | `\setmainfont{STSong}` |
| Độ phức tạp | 😖 Phức tạp | 😊 Đơn giản |
| Tương thích hệ thống | ❌ Xung đột | ✅ Hoàn hảo |
| Font choices | Hạn chế | Tự do chọn |

---

## 🎯 CHECKLIST KHI DÙNG CHỮ CJK

- [ ] Đã thêm `\setmainfont{STSong}` (hoặc font CJK khác)
- [ ] Đã test với 1 ký tự đơn giản trước (vd: `\node {中};`)
- [ ] Đã kiểm tra preview trước khi submit
- [ ] **KHÔNG** dùng `%!<CJKutf8>` hoặc `\begin{CJK*}`

---

## ❓ CÂU HỎI THƯỜNG GẶP

### Q: Tại sao tiếng Việt OK nhưng tiếng Trung không?

**A:** Font mặc định (Latin Modern) có dấu tiếng Việt nhưng KHÔNG có chữ Hán. Cần chọn font CJK.

---

### Q: Có cần thêm package gì không?

**A:** KHÔNG! `fontspec` đã có sẵn trong hệ thống. Chỉ cần `\setmainfont{...}`.

---

### Q: Font nào tốt nhất cho chữ Trung?

**A:** 
- **Văn bản thông thường:** STSong
- **Tiêu đề, chữ đậm:** Heiti TC/SC
- **Thư pháp, văn nghệ:** Kaiti TC/SC

---

### Q: Có thể dùng font Google (Noto Sans CJK)?

**A:** Có, nếu đã cài font đó trên hệ thống:

```latex
\setmainfont{Noto Sans CJK SC}
```

---

### Q: Làm sao biết font có hỗ trợ CJK không?

**A:** Thử render 1 ký tự đơn giản:

```latex
\setmainfont{YOUR_FONT_NAME}
\begin{tikzpicture}
  \node {中};  % Test với 1 chữ
\end{tikzpicture}
```

Nếu hiện `中` → OK ✅  
Nếu hiện `�` → Font không hỗ trợ ❌

---

## 🔗 TÀI LIỆU THAM KHẢO

### Hệ thống tikz2svg_api:
- Compiler: **LuaLaTeX** (hỗ trợ Unicode native)
- Font engine: **fontspec** (có sẵn trong template)
- Fonts CJK: **STSong, Heiti TC/SC, Kaiti TC/SC** (có sẵn macOS)

### External resources:
- [fontspec manual](https://ctan.org/pkg/fontspec)
- [LuaLaTeX guide](https://www.luatex.org/)
- [CJK in LaTeX](https://en.wikibooks.org/wiki/LaTeX/Internationalization#CJK)

---

## 💬 HỖ TRỢ

Nếu gặp vấn đề:
1. Kiểm tra đã thêm `\setmainfont{STSong}` chưa
2. Test với code đơn giản nhất: `\node {中};`
3. Đảm bảo KHÔNG dùng `%!<CJKutf8>` hoặc `\begin{CJK*}`

**Template đơn giản để test:**

```latex
\setmainfont{STSong}

\begin{tikzpicture}
  \node {富贵};
\end{tikzpicture}
```

---

**✨ Chúc bạn tạo được những hình TikZ đẹp với nhiều ngôn ngữ! ✨**

