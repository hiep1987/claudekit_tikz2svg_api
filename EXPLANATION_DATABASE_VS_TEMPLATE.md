# 📋 GIẢI THÍCH: supported_packages vs TEX_TEMPLATE

## ❓ CÂU HỎI CỦA BẠN

> **"Tại sao bạn nói có sẵn trong supported_packages thì không cần điều chỉnh app.py?"**

## ✅ TRẢ LỜI ĐÚNG: **BẠN NÓI ĐÚNG - TÔI ĐÃ GIẢI THÍCH CHƯA RÕ!**

Tôi xin lỗi vì đã gây nhầm lẫn. Để rõ ràng:

---

## 🔍 2 KHÁI NIỆM HOÀN TOÀN KHÁC NHAU

### **1️⃣ supported_packages (DATABASE)**

**Vai trò:** DANH SÁCH packages CHO PHÉP dùng

**Chức năng:**
- ✅ Kiểm tra xem package có được PHÉP dùng không
- ✅ Bảo mật: Chỉ packages trong list mới được inject
- ❌ **KHÔNG** tự động thêm vào LaTeX code
- ❌ **KHÔNG** có trong template mặc định

**Ví dụ:**
```sql
SELECT * FROM supported_packages WHERE package_name = 'CJKutf8';
-- Kết quả: id=93, status='manual'
```

**Ý nghĩa:**
- Database có CJKutf8 → Hệ thống **CHO PHÉP** dùng
- User **PHẢI** khai báo: `%!<CJKutf8>` hoặc `%!<\usepackage{CJKutf8}>`
- Hệ thống sẽ **TỰ ĐỘNG INJECT** vào LaTeX khi compile

---

### **2️⃣ TEX_TEMPLATE (app.py)**

**Vai trò:** Template LaTeX MẶC ĐỊNH

**Chức năng:**
- ✅ Packages trong này **CÓ SẴN**, không cần khai báo
- ✅ Luôn được load mỗi lần compile
- ✅ User KHÔNG CẦN `%!<..>` cho các gói này

**Ví dụ:**
```python
TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{standalone}
\usepackage{fontspec}   ← Có SẴN
\usepackage{tikz}       ← Có SẴN
\usepackage{amsmath}    ← Có SẴN
% ==== EXTRA AUTO-INJECT START ====
% (Packages từ %!<..> sẽ được chèn ở đây)
% ==== EXTRA AUTO-INJECT END ====
\begin{document}
{tikz_code}
\end{document}
"""
```

---

## 🔄 QUY TRÌNH HOẠT ĐỘNG THỰC TẾ

### **Kịch bản 1: Package CÓ trong TEX_TEMPLATE**

**Ví dụ: tikz**

```latex
\begin{tikzpicture}
  \draw (0,0) -- (1,1);
\end{tikzpicture}
```

**Quy trình:**
1. User gõ code, KHÔNG CẦN `%!<tikz>`
2. Template đã có `\usepackage{tikz}`
3. ✅ Compile thành công ngay

---

### **Kịch bản 2: Package KHÔNG CÓ trong TEX_TEMPLATE, NHƯNG CÓ trong supported_packages**

**Ví dụ: CJKutf8 (id=93 trong database)**

#### **CÁCH SAI (sẽ lỗi):**
```latex
\begin{CJK*}{UTF8}{gbsn}
  \node {富贵};
\end{CJK*}
```

**Quy trình:**
1. User gõ code, KHÔNG khai báo `%!<CJKutf8>`
2. Template KHÔNG có `\usepackage{CJKutf8}`
3. ❌ Compile lỗi: "CJK undefined"

#### **CÁCH ĐÚNG:**
```latex
%!<CJKutf8>

\begin{CJK*}{UTF8}{gbsn}
  \node {富贵};
\end{CJK*}
```

**Quy trình:**
1. User khai báo `%!<CJKutf8>`
2. Hệ thống kiểm tra database: CJKutf8 có ID=93 → ✅ Cho phép
3. Hệ thống tự động INJECT vào template:
   ```latex
   % ==== EXTRA AUTO-INJECT START ====
   \usepackage{CJKutf8}  ← Được thêm tự động!
   % ==== EXTRA AUTO-INJECT END ====
   ```
4. Dòng `%!<CJKutf8>` bị XÓA khỏi TikZ code
5. ✅ Compile thành công

---

### **Kịch bản 3: Package KHÔNG CÓ trong cả 2**

**Ví dụ: malicious-package**

```latex
%!<malicious-package>

\begin{tikzpicture}
  \draw (0,0) -- (1,1);
\end{tikzpicture}
```

**Quy trình:**
1. User khai báo `%!<malicious-package>`
2. Hệ thống kiểm tra database: KHÔNG TÌM THẤY
3. ❌ Package bị BỎ QUA (bảo mật)
4. Compile với template cơ bản
5. ⚠️ Có thể lỗi nếu code dùng package này

---

## 📊 BẢNG SO SÁNH

| Package | Trong TEX_TEMPLATE? | Trong Database? | Cần khai báo %!<..>? | Kết quả |
|---------|-------------------|-----------------|---------------------|---------|
| **tikz** | ✅ Có | ✅ Có | ❌ Không | ✅ Chạy ngay |
| **amsmath** | ✅ Có | ✅ Có | ❌ Không | ✅ Chạy ngay |
| **CJKutf8** | ❌ Không | ✅ Có (id=93) | ✅ **BẮT BUỘC** | ✅ Chạy sau khi khai báo |
| **pgfornament** | ❌ Không | ✅ Có | ✅ **BẮT BUỘC** | ✅ Chạy sau khi khai báo |
| **malicious** | ❌ Không | ❌ Không | - | ❌ Bị chặn |

---

## ⚠️ VẤN ĐỀ VỚI CJKutf8

### **Tại sao CJKutf8 vẫn không chạy dù có trong database?**

```latex
%!<CJKutf8>

\begin{CJK*}{UTF8}{gbsn}
  \node {富贵};
\end{CJK*}
```

**XUNG ĐỘT:**
```
TEX_TEMPLATE có: \usepackage{fontspec}
User muốn dùng: \usepackage{CJKutf8}

→ CJKutf8 KHÔNG tương thích với fontspec!
→ Compile sẽ LỖI dù inject đúng!
```

**NGUYÊN NHÂN:**
- ❌ CJKutf8 chỉ hoạt động với **pdfLaTeX**
- ❌ Hệ thống dùng **LuaLaTeX** + **fontspec**
- ❌ 2 thứ này KHÔNG thể chung sống!

---

## ✅ GIẢI PHÁP ĐÚNG ĐẮN

### **Option A: BỎ CJKutf8, dùng fontspec (KHUYẾN NGHỊ)**

**Không cần khai báo gì, Unicode trực tiếp:**
```latex
\begin{tikzpicture}
  \node {富贵};  ← Chữ Trung trực tiếp, KHÔNG CẦN CJK*
\end{tikzpicture}
```

**Lý do:**
- ✅ fontspec ĐÃ CÓ trong template
- ✅ LuaLaTeX hỗ trợ Unicode native
- ✅ Không cần thêm package nào

---

### **Option B: Thêm CJKutf8 vào TEX_TEMPLATE + Chuyển sang pdfLaTeX**

**Bước 1: Sửa app.py**
```python
TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{standalone}

% BỎ fontspec
% \usepackage{fontspec}  ← Comment dòng này

% THÊM CJKutf8 vào template mặc định
\usepackage{CJKutf8}  ← Thêm dòng này

% ... rest của template
"""
```

**Bước 2: Đổi compiler**
```python
# Tìm subprocess.run (line ~653)
subprocess.run([
    "pdflatex",  # ← Đổi từ lualatex
    "-interaction=nonstopmode",
    # ...
])
```

**Kết quả:**
- ✅ CJKutf8 CÓ SẴN trong template → Không cần `%!<..>`
- ✅ pdfLaTeX tương thích với CJKutf8
- ⚠️ NHƯNG mất fontspec → Ảnh hưởng code khác!

---

## 🎯 KẾT LUẬN

### **Câu hỏi:** *"Tại sao có trong supported_packages thì không cần sửa app.py?"*

### **Trả lời:**

1. **Database `supported_packages`:**
   - Chỉ là DANH SÁCH cho phép
   - User **PHẢI** khai báo `%!<package>`
   - Hệ thống sẽ **TỰ ĐỘNG INJECT** khi compile
   
2. **`TEX_TEMPLATE` trong app.py:**
   - Là template MẶC ĐỊNH
   - Packages ở đây **CÓ SẴN**, không cần khai báo
   
3. **CJKutf8 trường hợp đặc biệt:**
   - ✅ Có trong database (id=93)
   - ✅ Sẽ được inject khi dùng `%!<CJKutf8>`
   - ❌ **NHƯNG** xung đột với fontspec trong template
   - 🎯 **Giải pháp:** Bỏ CJKutf8, dùng Unicode trực tiếp!

---

## 📝 CODE ĐÚNG CHO BẠN

**KHÔNG CẦN sửa app.py, KHÔNG CẦN %!<CJKutf8>:**

```latex
\definecolor{falured}{rgb}{0.5, 0.09, 0.09}
\begin{tikzpicture}[line join=round, line cap=round,scale=1,transform shape]
    \node[falured,scale=.7,inner sep=0,align=left,
    font=\fontfamily{qag}\selectfont] at (3,-4.5) 
    {Code by Lương Như Quỳnh};
    
    % Chữ Trung - TRỰC TIẾP, không cần CJK*
    \node[black,scale=2,inner sep=0,align=left] at (-3,4.5) {富};
    \node[black,scale=2,inner sep=0,align=left] at (-3,3.5) {贵};
\end{tikzpicture}
```

**→ Chạy ngay trên http://localhost:5173!** ✅

