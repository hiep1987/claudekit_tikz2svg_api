# 🔍 PHÂN TÍCH: Biên Dịch Chữ Trung Quốc với LuaLaTeX + fontspec

**Ngày tạo:** 30/10/2025  
**Hệ thống:** tikz2svg_api (LuaLaTeX + fontspec)

---

## 📊 HIỆN TRẠNG: Người dùng test code

### Code TikZ của người dùng:

```latex
\begin{tikzpicture}
  \node {中文: 富贵};
\end{tikzpicture}
```

---

## 🧪 KẾT QUẢ TEST THỰC TẾ

### Test 1: Không chỉ định font (mặc định)

```latex
\documentclass[12pt,border=10pt]{standalone}
\usepackage{fontspec}
\usepackage{tikz}

\begin{document}
\begin{tikzpicture}
  \node {中文: 富贵};
\end{tikzpicture}
\end{document}
```

**Kết quả:**
- ✅ **Compile:** THÀNH CÔNG (PDF created)
- ❌ **Hiển thị:** `��: ��` (tofu boxes) thay vì `中文: 富贵`

**Nguyên nhân:**
- `fontspec` mặc định dùng **Latin Modern font**
- Latin Modern **KHÔNG CÓ** ký tự CJK (Chinese/Japanese/Korean)
- LuaLaTeX sử dụng glyphs thay thế (boxes/tofu)

---

### Test 2: Chỉ định font CJK (STSong)

```latex
\documentclass[12pt,border=10pt]{standalone}
\usepackage{fontspec}
\usepackage{tikz}

\setmainfont{STSong}  % ✅ Chọn font có CJK

\begin{document}
\begin{tikzpicture}
  \node {中文: 富贵};
\end{tikzpicture}
\end{document}
```

**Kết quả:**
- ✅ **Compile:** THÀNH CÔNG
- ✅ **Hiển thị:** `中文: 富贵` (CHÍNH XÁC!)

**PDF Content (verified):**
```
中文: 富贵
```

---

## 📋 FONTS CJK CÓ SẴN TRÊN HỆ THỐNG MACOS

```bash
$ fc-list :lang=zh family
```

**Top 10 fonts hỗ trợ tiếng Trung:**
1. **STSong** ✅ (recommended)
2. Heiti TC/SC
3. Kaiti TC/SC
4. Baoli TC/SC
5. LingWai TC/SC
6. Apple LiSung
7. Apple LiGothic

---

## 💡 GIẢI PHÁP CHO NGƯỜI DÙNG

### Cách 1: Thêm font vào code TikZ (RECOMMENDED)

**Code người dùng nên viết:**

```latex
% Khai báo font ở đầu code (trước tikzpicture)
%!<fontspec>
\setmainfont{STSong}

\begin{tikzpicture}
  \node {中文: 富贵};
\end{tikzpicture}
```

**Lưu ý:**
- `fontspec` đã có sẵn trong `TEX_TEMPLATE` → KHÔNG cần `%!<fontspec>`
- Chỉ cần thêm `\setmainfont{STSong}` vào code TikZ

**Code đơn giản hơn:**

```latex
\setmainfont{STSong}  % Thêm dòng này

\begin{tikzpicture}
  \node {中文: 富贵};
\end{tikzpicture}
```

---

### Cách 2: Dùng `\fontfamily` cho chữ cụ thể (inline)

```latex
\begin{tikzpicture}
  \node[font=\fontspec{STSong}] {中文: 富贵};
\end{tikzpicture}
```

---

### Cách 3: Dùng `newfontfamily` (chuyên nghiệp)

```latex
\newfontfamily\zhfont{STSong}[Script=CJK]

\begin{tikzpicture}
  \node[font=\zhfont] {中文: 富贵};
\end{tikzpicture}
```

---

## ⚠️  TẠI SAO KHÔNG DÙNG CJKutf8?

### So sánh 2 cách tiếp cận:

| Đặc điểm | `CJKutf8` (pdfLaTeX) | `fontspec` (LuaLaTeX) |
|----------|---------------------|---------------------|
| Compiler | ❌ pdfLaTeX only | ✅ LuaLaTeX/XeLaTeX |
| Syntax | Phức tạp: `\begin{CJK*}{UTF8}{gbsn}...\end{CJK*}` | Đơn giản: `\setmainfont{STSong}` |
| Unicode native | ❌ Cần wrapper | ✅ Native support |
| Conflict với hệ thống | ⚠️  Xung đột với fontspec | ✅ Tích hợp mượt mà |
| Font selection | Hạn chế | Tự do chọn bất kỳ system font |

### Code người dùng cũ (với CJKutf8):

```latex
%!<CJKutf8>
\begin{tikzpicture}
  \node[font=\fontfamily{qag}\selectfont] at (3,-4.5) {Code by Lương Như Quỳnh};
  
  \begin{CJK*}{UTF8}{gbsn}
    \node at (-3,4.5) {富};
    \node at (-3,3.5) {贵};
  \end{CJK*}
\end{tikzpicture}
```

**Vấn đề:**
- ❌ `CJKutf8` KHÔNG tương thích với LuaLaTeX + `fontspec`
- ❌ Gây lỗi compile trên hệ thống
- ❌ Cú pháp phức tạp

### Code nên viết (với fontspec):

```latex
\setmainfont{STSong}

\begin{tikzpicture}
  \node[font=\fontfamily{qag}\selectfont] at (3,-4.5) {Code by Lương Như Quỳnh};
  \node at (-3,4.5) {富};
  \node at (-3,3.5) {贵};
\end{tikzpicture}
```

**Ưu điểm:**
- ✅ Hoạt động HOÀN HẢO với LuaLaTeX
- ✅ Không cần `\begin{CJK*}...\end{CJK*}`
- ✅ Đơn giản, dễ đọc

---

## 🎯 TÓM TẮT & KẾT LUẬN

### ✅ Hiện trạng hệ thống tikz2svg_api:

1. **Compiler:** LuaLaTeX ✅
2. **TEX_TEMPLATE:** Có `\usepackage{fontspec}` ✅
3. **Unicode support:** Native với LuaLaTeX ✅
4. **Chinese fonts:** STSong có sẵn trên macOS ✅

### ❌ Vấn đề của code `\node {中文: 富贵}`:

- Không chỉ định font → Dùng Latin Modern mặc định
- Latin Modern thiếu CJK glyphs → Hiển thị `��`

### ✅ Giải pháp:

**Người dùng chỉ cần thêm MỘT DÒNG vào đầu code TikZ:**

```latex
\setmainfont{STSong}

\begin{tikzpicture}
  \node {中文: 富贵};
\end{tikzpicture}
```

### 📝 KHÔNG CẦN:

- ❌ Thêm `%!<CJKutf8>` (xung đột với fontspec)
- ❌ Thêm `\usepackage{fontspec}` (đã có sẵn)
- ❌ Thêm `\usepackage[utf8]{vietnam}` (không liên quan đến Trung Quốc)
- ❌ Sửa `app.py` hoặc `TEX_TEMPLATE`

---

## 🔧 HỆ THỐNG ĐÃ SẴN SÀNG

**Kết luận cuối cùng:**

```
✅ LuaLaTeX + fontspec = Hỗ trợ HOÀN HẢO Unicode (Việt, Trung, Nhật, Hàn, v.v.)
✅ Người dùng chỉ cần CHỌN FONT phù hợp
✅ KHÔNG CẦN thêm package hay sửa hệ thống
```

**Best practice cho người dùng tikz2svg_api:**

```latex
% Đối với tiếng Việt: fontspec + Unicode trực tiếp (mặc định OK)
% Đối với tiếng Trung/Nhật/Hàn: Thêm \setmainfont{STSong} hoặc font CJK khác

\setmainfont{STSong}  % Chỉ cần khi dùng CJK

\begin{tikzpicture}
  \node {Tiếng Việt: OK mặc định};
  \node {中文: Cần chọn font};
  \node {日本語: Cần chọn font};
\end{tikzpicture}
```

---

## 📚 TÀI LIỆU LIÊN QUAN

- `FONTSPEC_IMPACT_ANALYSIS.md` - Phân tích tầm quan trọng của fontspec
- `CJKUTF8_SOLUTION_FOR_LUALATEX.md` - Tại sao không dùng CJKutf8
- `EXPLANATION_DATABASE_VS_TEMPLATE.md` - Cách hệ thống quản lý packages

---

**📌 Lưu ý cho admin:**

Nếu có nhiều người dùng cần chữ Trung, có thể:
1. Thêm `\setmainfont{STSong}` vào `TEX_TEMPLATE` (nhưng ảnh hưởng tất cả)
2. Hoặc giữ nguyên và hướng dẫn người dùng tự thêm khi cần

**Khuyến nghị:** Giữ nguyên để linh hoạt, hướng dẫn người dùng tự chọn font.

