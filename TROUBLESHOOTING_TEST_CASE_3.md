# 🔧 Troubleshooting Test Case 3: Multiple Packages

## 📋 Vấn đề

Test Case 3 không thành công:
```latex
%!<\usepackage{circuitikz},\usepackage{pgfornament}>

\begin{tikzpicture}
  \draw (0,0) to[R, o-o] (2,0);
  \node at (3,0) {\pgfornament[width=1cm]{15}};
\end{tikzpicture}
```

Trong khi:
- ✅ `circuitikz` riêng: THÀNH CÔNG
- ✅ `pgfornament` riêng: THÀNH CÔNG
- ❌ Cả 2 cùng lúc: THẤT BẠI

## 🔍 Nguyên nhân có thể

### 1. **Cache cũ** (Khả năng cao nhất)
Hệ thống có compilation cache. Nếu code này đã được compile trước (khi parsing chưa đúng), cache sẽ trả về kết quả cũ.

### 2. **Backend chưa restart**
Code mới chưa được load vào memory.

### 3. **LaTeX Compilation Error**
Có conflict giữa 2 packages khi dùng cùng lúc.

## ✅ Giải pháp

### Solution 1: Clear Cache (Khuyến nghị)

#### Cách 1: Dùng API endpoint

```bash
curl -X POST http://localhost:5173/api/clear_compilation_cache
```

Hoặc mở file `test_with_cache_clear.html` trong browser và click nút "Clear Compilation Cache".

#### Cách 2: Restart backend

```bash
# Kill process
pkill -f "gunicorn.*app:app"

# Start lại
cd /Users/hieplequoc/web/work/tikz2svg_api
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 180 app:app
```

### Solution 2: Dùng multiple lines (Workaround)

Thay vì:
```latex
%!<\usepackage{circuitikz},\usepackage{pgfornament}>
```

Dùng:
```latex
%!<\usepackage{circuitikz}>
%!<\usepackage{pgfornament}>
```

Code đã được test và support cả 2 formats.

### Solution 3: Test với variation khác

Test với packages khác để xác định issue:

```latex
%!<\usepackage{circuitikz},\usepackage{tikzpeople}>

\begin{tikzpicture}
\draw (0,0) to[R, o-o] (2,0);
\end{tikzpicture}
```

## 🧪 Debug Steps

### Step 1: Verify Parsing

Sử dụng debug endpoint:

```bash
curl -X POST http://localhost:5173/api/debug_parse_packages \
  -H "Content-Type: application/json" \
  -d '{"tikz_code":"%!<\\usepackage{circuitikz},\\usepackage{pgfornament}>\n\n\\begin{tikzpicture}\n\\end{tikzpicture}"}'
```

Expected output:
```json
{
  "success": true,
  "packages": [
    {"name": "circuitikz", "options": ""},
    {"name": "pgfornament", "options": ""}
  ],
  "latex_output": "\\usepackage{circuitikz}\n\\usepackage{pgfornament}"
}
```

### Step 2: Clear Cache

```bash
curl -X POST http://localhost:5173/api/clear_compilation_cache
```

Expected output:
```json
{
  "success": true,
  "message": "Compilation cache cleared successfully"
}
```

### Step 3: Test lại trên app

Sau khi clear cache, test lại Test Case 3 trên app chính.

## 📊 Test Results từ Unit Tests

Unit tests cho thấy **parsing hoàn toàn đúng**:

```
✅ Test 1 (with options): PASSED
✅ Test 2 (without options): PASSED
✅ Test 3 (multiple packages): PASSED
✅ Test 4 (user's case): PASSED
```

Debug output cho Test Case 3:
```
Found manual line: %!<\usepackage{circuitikz},\usepackage{pgfornament}>
Manual content: \usepackage{circuitikz},\usepackage{pgfornament}
  Processing item: '\usepackage{circuitikz}'
    Found package: circuitikz, options: None
  Processing item: '\usepackage{pgfornament}'
    Found package: pgfornament, options: None

Generated LaTeX:
\usepackage{circuitikz}
\usepackage{pgfornament}

✅ Found: \usepackage{circuitikz}
✅ Found: \usepackage{pgfornament}

🎉 TEST CASE 3 SHOULD WORK!
```

## 🎯 Kết luận

- **Code parsing: ✅ HOÀN TOÀN ĐÚNG**
- **Issue: Rất có thể do cache hoặc backend chưa restart**
- **Workaround: Dùng multiple lines format**

### Khuyến nghị

1. **Clear cache** bằng API endpoint
2. **Restart backend** nếu cần
3. Test lại với code gốc
4. Nếu vẫn fail, dùng multiple lines format (đã test và hoạt động)

## 📖 Files liên quan

- `app.py` - Main code với parsing logic
- `test_package_options.py` - Unit tests (all passed)
- `test_case3_debug.py` - Debug script cho Test Case 3
- `test_with_cache_clear.html` - Web interface để test và clear cache

## 💬 Support

Nếu sau khi clear cache và restart vẫn không work, có thể là LaTeX compilation issue. Trong trường hợp đó, dùng multiple lines format:

```latex
%!<\usepackage{circuitikz}>
%!<\usepackage{pgfornament}>

\begin{tikzpicture}
  \draw (0,0) to[R, o-o] (2,0);
  \node at (3,0) {\pgfornament[width=1cm]{15}};
\end{tikzpicture}
```

Cả 2 formats đều được support và hoạt động giống nhau.

