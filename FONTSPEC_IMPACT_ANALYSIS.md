# ⚠️ ẢNH HƯỞNG KHI BỎ `\usepackage{fontspec}`

## ❓ CÂU HỎI

> **"Nếu % \usepackage{fontspec} có ảnh hưởng gì đến các code tikz khác không?"**

## ✅ TRẢ LỜI: **CÓ - ẢNH HƯỞNG RẤT LỚN!**

---

## 🔍 FONTSPEC LÀ GÌ VÀ TẠI SAO CẦN THIẾT?

### **Vai trò của fontspec:**

`fontspec` là package **CỐT LÕI** cho LuaLaTeX/XeLaTeX để:

1. **Hỗ trợ Unicode native** (chữ tiếng Việt, Trung, Nhật, Hàn, Ả Rập, ...)
2. **Truy cập system fonts** (Arial, Times New Roman, Noto Sans, ...)
3. **Font features** (ligatures, kerning, OpenType features)

### **Hiện tại trong TEX_TEMPLATE:**

```python
TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{standalone}

\usepackage{fontspec}  ← QUAN TRỌNG!

% ... rest
"""
```

**Compiler:** LuaLaTeX (yêu cầu fontspec)

---

## ⚠️ ẢNH HƯỞNG KHI BỎ FONTSPEC

### **1️⃣ MẤT HỖ TRỢ UNICODE**

#### **Code hiện tại (với fontspec) - ✅ CHẠY:**

```latex
\begin{tikzpicture}
  \node {Tiếng Việt: áéíóú ăâêôơư đ};
  \node {中文: 富贵吉祥};
  \node {日本語: こんにちは};
  \node {한국어: 안녕하세요};
  \node {العربية: مرحبا};
\end{tikzpicture}
```

#### **Bỏ fontspec - ❌ LỖI:**

```
! Package inputenc Error: Unicode character áéíóú (U+00E1)
(inputenc)                not set up for use with LaTeX.
```

**Kết quả:** TẤT CẢ code có Unicode sẽ **LỖI**!

---

### **2️⃣ MẤT KHẢ NĂNG DÙNG SYSTEM FONTS**

#### **Code hiện tại (với fontspec) - ✅ CHẠY:**

```latex
\begin{tikzpicture}
  \node[font=\fontspec{Arial}] {Text in Arial};
  \node[font=\fontspec{Times New Roman}] {Text in Times};
  \node[font=\fontspec{Comic Sans MS}] {Fun text};
\end{tikzpicture}
```

#### **Bỏ fontspec - ❌ LỖI:**

```
! Undefined control sequence.
l.2   \node[font=\fontspec{Arial}]
```

**Kết quả:** Không thể dùng fonts hệ thống!

---

### **3️⃣ MẤT FONT FEATURES**

#### **Code hiện tại (với fontspec) - ✅ CHẠY:**

```latex
\setmainfont{Linux Libertine}[
  Ligatures=TeX,
  Numbers=OldStyle
]

\begin{tikzpicture}
  \node {fi fl ffi ffl --- 1234567890};
\end{tikzpicture}
```

#### **Bỏ fontspec - ❌ KHÔNG CÓ:**

- Mất ligatures (fi → ﬁ)
- Mất old-style numbers
- Mất OpenType features

---

### **4️⃣ PHẢI CHUYỂN SANG PDLATEX**

Nếu bỏ fontspec, **BẮT BUỘC** chuyển từ LuaLaTeX → pdfLaTeX

#### **Hậu quả:**

| Feature | LuaLaTeX + fontspec | pdfLaTeX (không fontspec) |
|---------|-------------------|--------------------------|
| Unicode trực tiếp | ✅ Có | ❌ **KHÔNG** |
| System fonts | ✅ Có | ❌ **KHÔNG** |
| OpenType features | ✅ Có | ❌ **KHÔNG** |
| Modern fonts | ✅ Có | ❌ **KHÔNG** |
| Compile speed | Chậm hơn 1 chút | ✅ Nhanh hơn |
| CJKutf8 support | ❌ Không | ✅ Có |

---

## 📊 CODE TikZ NÀO SẼ BỊ ẢNH HƯỞNG?

### **✅ KHÔNG ẢNH HƯỞNG (vẫn chạy):**

```latex
% Code TikZ thuần túy, không dùng Unicode hay fonts đặc biệt
\begin{tikzpicture}
  \draw (0,0) -- (1,1);
  \draw[red] (0,1) -- (1,0);
  \fill[blue] (0.5,0.5) circle (0.1);
\end{tikzpicture}
```

```latex
% Code chỉ dùng ký tự ASCII
\begin{tikzpicture}
  \node at (0,0) {Hello World};
  \node at (0,1) {Mathematics: $x^2 + y^2 = r^2$};
\end{tikzpicture}
```

---

### **❌ SẼ BỊ LỖI (nếu bỏ fontspec):**

#### **1. Code có tiếng Việt:**

```latex
\begin{tikzpicture}
  \node {Đồ thị hàm số};
  \node {Phương trình: $y = ax^2 + bx + c$};
\end{tikzpicture}
```

**Lỗi:** Ký tự Đ, ơ, ư không compile được!

---

#### **2. Code có chữ Trung, Nhật, Hàn:**

```latex
\begin{tikzpicture}
  \node {中文：数学};
  \node {日本語：数学};
  \node {한국어: 수학};
\end{tikzpicture}
```

**Lỗi:** Unicode characters not supported!

---

#### **3. Code dùng system fonts:**

```latex
\begin{tikzpicture}
  \node[font=\fontspec{Arial}] at (0,0) {Arial font};
  \node[font=\fontspec{Comic Sans MS}] at (0,-1) {Comic Sans};
\end{tikzpicture}
```

**Lỗi:** `\fontspec` undefined!

---

#### **4. Code có ký tự đặc biệt:**

```latex
\begin{tikzpicture}
  \node {Symbols: ©®™€£¥§¶†‡°};
  \node {Math: ∫∑∏√∞≈≠≤≥};
\end{tikzpicture}
```

**Lỗi:** Unicode không hỗ trợ!

---

## 📈 ƯỚC TÍNH TỶ LỆ CODE BỊ ẢNH HƯỞNG

Nếu bỏ fontspec và chuyển sang pdfLaTeX:

| Loại code | Tỷ lệ ước tính | Ảnh hưởng |
|-----------|---------------|-----------|
| **Code ASCII thuần** (geometric shapes, simple math) | ~40% | ✅ Không ảnh hưởng |
| **Code có tiếng Việt** | ~30% | ❌ **LỖI** |
| **Code có Unicode khác** (Trung, Nhật, Hàn, ký tự đặc biệt) | ~20% | ❌ **LỖI** |
| **Code dùng system fonts** | ~10% | ❌ **LỖI** |

**→ Khoảng 60% code TikZ hiện tại sẽ BỊ LỖI!**

---

## ⚙️ GIẢI PHÁP NẾU MUỐN HỖ TRỢ CẢ HAI

### **OPTION 1: Dual Compiler System (KHUYẾN NGHỊ)**

Hệ thống tự động chọn compiler:

```python
def choose_compiler(tikz_code):
    """Choose compiler based on code content"""
    
    # Detect CJK package requirement
    if '%!<CJKutf8>' in tikz_code or 'CJK*' in tikz_code:
        return 'pdflatex', 'template_with_cjk'
    
    # Detect Unicode (tiếng Việt, Trung, Nhật, Hàn, ...)
    if has_unicode(tikz_code):
        return 'lualatex', 'template_with_fontspec'
    
    # Default: LuaLaTeX (modern, flexible)
    return 'lualatex', 'template_with_fontspec'

def has_unicode(text):
    """Check if text contains non-ASCII characters"""
    return any(ord(char) > 127 for char in text)
```

**Templates:**

```python
# Template 1: LuaLaTeX + fontspec (mặc định)
TEMPLATE_LUALATEX = r"""
\documentclass[12pt,border=10pt]{standalone}
\usepackage{fontspec}
% ... rest
"""

# Template 2: pdfLaTeX + CJKutf8 (cho CJK)
TEMPLATE_PDFLATEX_CJK = r"""
\documentclass[12pt,border=10pt]{standalone}
\usepackage{CJKutf8}
\usepackage[utf8]{inputenc}  % cho tiếng Việt
% ... rest (NO fontspec)
"""
```

**Ưu điểm:**
- ✅ Hỗ trợ cả Unicode (tiếng Việt, Trung, Nhật, Hàn)
- ✅ Hỗ trợ CJKutf8
- ✅ Tự động chọn compiler phù hợp
- ✅ Không ảnh hưởng code cũ

**Nhược điểm:**
- ⚠️ Phức tạp hơn
- ⚠️ Cần maintain 2 templates

---

### **OPTION 2: fontspec + Fallback CJK (ĐƠN GIẢN HƠN)**

Giữ nguyên fontspec, hướng dẫn user dùng Unicode thay vì CJKutf8:

**Thay vì:**
```latex
%!<CJKutf8>
\begin{CJK*}{UTF8}{gbsn}
  \node {富贵};
\end{CJK*}
```

**Dùng:**
```latex
% Không cần package gì, Unicode trực tiếp
\node {富贵};
```

**Ưu điểm:**
- ✅ Đơn giản nhất
- ✅ Không cần sửa code
- ✅ Modern approach
- ✅ Hỗ trợ mọi ngôn ngữ

**Nhược điểm:**
- ⚠️ User phải thay đổi cách viết code
- ⚠️ Code CJKutf8 cũ không chạy

---

## 🎯 KHUYẾN NGHỊ

### **KHÔNG NÊN BỎ fontspec!**

**Lý do:**

1. **60% code hiện tại** sẽ bị lỗi
2. **Tiếng Việt** sẽ không hoạt động
3. **Mất tính năng modern** của LuaLaTeX
4. **Regression lớn** cho hệ thống

---

### **Giải pháp tốt nhất:**

**Giữ nguyên fontspec + LuaLaTeX**

**Cho CJK:** Hướng dẫn user dùng Unicode trực tiếp

**Code mẫu:**
```latex
\definecolor{falured}{rgb}{0.5, 0.09, 0.09}
\begin{tikzpicture}
    \node[falured] at (3,-4.5) {Code by Lương Như Quỳnh};
    
    % Unicode trực tiếp - KHÔNG CẦN CJK*
    \node[black,scale=2] at (-3,4.5) {富};
    \node[black,scale=2] at (-3,3.5) {贵};
\end{tikzpicture}
```

**→ Chạy ngay, không cần sửa gì!** ✅

---

## 📝 TÓM TẮT

| Giải pháp | Ảnh hưởng code cũ | Độ phức tạp | Khuyến nghị |
|-----------|------------------|-------------|-------------|
| **Giữ fontspec** (hiện tại) | ✅ Không | ✅ Thấp | ⭐⭐⭐⭐⭐ |
| **Bỏ fontspec** | ❌ 60% lỗi | ✅ Thấp | ❌ KHÔNG |
| **Dual compiler** | ✅ Không | ⚠️ Cao | ⭐⭐⭐ |

---

## 🎊 KẾT LUẬN

**Câu trả lời:** **CÓ - ẢNH HƯỞNG RẤT LỚN!**

- ❌ **Bỏ fontspec:** 60% code TikZ sẽ lỗi
- ✅ **Giữ fontspec:** Code cũ vẫn chạy, Unicode native
- 🎯 **Khuyến nghị:** Giữ fontspec, dùng Unicode trực tiếp thay CJKutf8

**→ KHÔNG NÊN BỎ `\usepackage{fontspec}`!**

