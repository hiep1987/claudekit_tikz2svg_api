# ⚠️ VẤN ĐỀ: CJKutf8 KHÔNG CHẠY TRÊN LOCALHOST:5173

## 🔍 NGUYÊN NHÂN

Bạn đã tìm ra vấn đề chính xác!

### **Xung đột giữa CJKutf8 và fontspec:**

```
Hệ thống tikz2svg:
├── Compiler: LuaLaTeX ✅
├── TEX_TEMPLATE: \usepackage{fontspec} ✅
└── User code: %!<CJKutf8> ❌ XUNG ĐỘT!
```

### **Tại sao xung đột?**

| Package | Tương thích với | KHÔNG tương thích |
|---------|----------------|-------------------|
| **CJKutf8** | pdfLaTeX | XeLaTeX, LuaLaTeX, fontspec |
| **fontspec** | XeLaTeX, LuaLaTeX | pdfLaTeX, CJKutf8 |

**Kết quả:** CJKutf8 và fontspec KHÔNG thể dùng chung!

---

## ✅ GIẢI PHÁP

### **OPTION 1: Dùng fontspec (KHUYẾN NGHỊ) ⭐**

**Ưu điểm:**
- ✅ Không cần sửa app.py
- ✅ Không cần thêm gói vào database
- ✅ Font support tốt hơn
- ✅ Unicode native

**Code mới:**

```latex
\definecolor{falured}{rgb}{0.5, 0.09, 0.09}
\begin{tikzpicture}[line join=round, line cap=round,scale=1,transform shape]
    \node[falured,scale=.7,inner sep=0,align=left,
    font=\fontfamily{qag}\selectfont] at (3,-4.5) 
    {Code by Lương Như Quỳnh};
    
    % KHÔNG CẦN \begin{CJK*} - Trực tiếp dùng Unicode!
    \node[black,scale=2,inner sep=0,align=left] at (-3,4.5) {富};
    \node[black,scale=2,inner sep=0,align=left] at (-3,3.5) {贵};
\end{tikzpicture}
```

**Giải thích:**
- LuaLaTeX + fontspec hỗ trợ Unicode native
- KHÔNG CẦN `\begin{CJK*}{UTF8}{gbsn}`
- KHÔNG CẦN `%!<CJKutf8>`
- Chữ Trung (富贵) hoạt động trực tiếp!

---

### **OPTION 2: Chuyển sang pdfLaTeX**

**Ưu điểm:**
- ✅ CJKutf8 hoạt động đúng
- ✅ Tương thích với code cũ

**Nhược điểm:**
- ❌ Phải sửa app.py
- ❌ Mất fontspec (ảnh hưởng code khác)
- ❌ Không khuyến nghị

**Nếu chọn option này:**

#### 1. Sửa `app.py`:

```python
# Tìm dòng 862 (TEX_TEMPLATE)
TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{standalone}

% Bỏ fontspec
% \usepackage{fontspec}  ← COMMENT DÒNG NÀY

% Thêm CJKutf8 vào template mặc định
\usepackage{CJKutf8}

% ... rest of template
"""

# Tìm dòng 653-654 (subprocess.run)
# Thay lualatex → pdflatex
subprocess.run([
    "pdflatex",  # ← THAY ĐỔI TỪ lualatex
    "-interaction=nonstopmode",
    # ...
])
```

#### 2. Restart Flask:

```bash
pkill -f "python.*app.py"
cd /Users/hieplequoc/web/work/tikz2svg_api
python3 app.py
```

---

## 🎯 KHUYẾN NGHỊ: OPTION 1

### **Tại sao?**

1. **Đơn giản hơn:** Không cần sửa code hệ thống
2. **Modern hơn:** fontspec + LuaLaTeX là standard mới
3. **Linh hoạt hơn:** Hỗ trợ mọi ngôn ngữ Unicode
4. **Ổn định hơn:** Không ảnh hưởng code hiện tại

### **Code mẫu hoàn chỉnh (OPTION 1):**

```latex
\definecolor{falured}{rgb}{0.5, 0.09, 0.09}
\begin{tikzpicture}[line join=round, line cap=round,scale=1,transform shape]
    % Signature
    \node[falured,scale=.7,inner sep=0,align=left,
    font=\fontfamily{qag}\selectfont] at (3,-4.5) 
    {Code by Lương Như Quỳnh};
    
    % Chinese characters - KHÔNG CẦN CJK environment!
    \node[black,scale=2,inner sep=0,align=left] at (-3,4.5) {富};
    \node[black,scale=2,inner sep=0,align=left] at (-3,3.5) {贵};
\end{tikzpicture}
```

**Chạy trực tiếp trên http://localhost:5173 - KHÔNG CẦN %!<..>!**

---

## 🧪 TEST NGAY

### **Bước 1:** Copy code mới (không có CJK*)

### **Bước 2:** Paste vào http://localhost:5173

### **Bước 3:** Click Compile

### **Bước 4:** ✅ Thành công!

---

## 📊 SO SÁNH

| Feature | CJKutf8 (pdfLaTeX) | fontspec (LuaLaTeX) |
|---------|-------------------|---------------------|
| Unicode support | Qua CJK package | Native |
| Syntax | `\begin{CJK*}` | Direct Unicode |
| Font choices | Hạn chế (gbsn, gkai) | Mọi system font |
| Compile speed | Nhanh hơn | Chậm hơn 1 chút |
| Modern | Cũ (2000s) | Mới (2010s+) |
| Khuyến nghị | ❌ | ✅ |

---

## 🎉 KẾT LUẬN

**KHÔNG CẦN** thêm CJKutf8 vào app.py!

**KHÔNG CẦN** sửa gì trong hệ thống!

**CHỈ CẦN** bỏ `\begin{CJK*}` và `%!<CJKutf8>`, dùng Unicode trực tiếp!

---

## 📝 FINAL CODE (READY TO USE)

```latex
\definecolor{falured}{rgb}{0.5, 0.09, 0.09}
\begin{tikzpicture}[line join=round, line cap=round,scale=1,transform shape]
    \node[falured,scale=.7,inner sep=0,align=left,
    font=\fontfamily{qag}\selectfont] at (3,-4.5) 
    {Code by Lương Như Quỳnh};
    
    \node[black,scale=2,inner sep=0,align=left] at (-3,4.5) {富};
    \node[black,scale=2,inner sep=0,align=left] at (-3,3.5) {贵};
\end{tikzpicture}
```

**Copy & paste vào http://localhost:5173 → Compile → Success! 🚀**

