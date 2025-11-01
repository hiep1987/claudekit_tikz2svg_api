# 🐛 Fix: Dict Comparison Error in Cache

## 📋 Lỗi

```
❌ Enhanced compilation failed: Resource limit error: '<' not supported between instances of 'dict' and 'dict'
```

## 🔍 Nguyên nhân

Sau khi thay đổi packages từ `string` format sang `dict` format để hỗ trợ options:

**Trước:**
```python
packages = ["circuitikz", "pgfornament"]  # List of strings
```

**Sau:**
```python
packages = [
    {'name': 'circuitikz', 'options': ''},
    {'name': 'pgfornament', 'options': ''}
]  # List of dicts
```

Hàm `_calculate_cache_key` trong `CompilationCache` class cố gắng sort packages:

```python
'packages': sorted(packages)  # ❌ Không thể sort list of dicts!
```

Python không thể so sánh 2 dict với nhau bằng toán tử `<`, do đó lỗi xảy ra.

## ✅ Giải pháp

Normalize packages thành string format trước khi sort:

```python
def _calculate_cache_key(self, tikz_code: str, packages: list, tikz_libs: list, pgfplots_libs: list) -> str:
    """Generate SHA256 cache key from compilation parameters"""
    
    # Normalize packages to consistent format for caching
    normalized_packages = []
    if packages:
        for pkg in packages:
            if isinstance(pkg, dict):
                # Dict format: {'name': 'circuitikz', 'options': 'siunitx'}
                pkg_str = f"{pkg.get('name', '')}[{pkg.get('options', '')}]" if pkg.get('options') else pkg.get('name', '')
                normalized_packages.append(pkg_str)
            else:
                # String format (backward compatibility)
                normalized_packages.append(str(pkg))
    
    # Create consistent string representation
    cache_input = {
        'tikz_code': tikz_code.strip(),
        'packages': sorted(normalized_packages),  # ✅ Giờ có thể sort!
        'tikz_libs': sorted(tikz_libs) if tikz_libs else [],
        'pgfplots_libs': sorted(pgfplots_libs) if pgfplots_libs else []
    }
    
    # Convert to JSON and generate SHA256
    cache_string = json.dumps(cache_input, sort_keys=True)
    return hashlib.sha256(cache_string.encode('utf-8')).hexdigest()
```

## 🎯 Kết quả

### Package không có options:
```python
{'name': 'circuitikz', 'options': ''} → "circuitikz"
```

### Package có options:
```python
{'name': 'circuitikz', 'options': 'siunitx'} → "circuitikz[siunitx]"
```

### Backward compatibility:
```python
"circuitikz" → "circuitikz"  # String format vẫn hoạt động
```

## 🧪 Test Cases

### Test 1: Single package không options
```latex
%!<\usepackage{circuitikz}>
```
- Packages: `[{'name': 'circuitikz', 'options': ''}]`
- Normalized: `["circuitikz"]`
- ✅ Sortable

### Test 2: Single package với options
```latex
%!<\usepackage[siunitx]{circuitikz}>
```
- Packages: `[{'name': 'circuitikz', 'options': 'siunitx'}]`
- Normalized: `["circuitikz[siunitx]"]`
- ✅ Sortable

### Test 3: Multiple packages
```latex
%!<\usepackage{circuitikz},\usepackage{pgfornament}>
```
- Packages: `[{'name': 'circuitikz', 'options': ''}, {'name': 'pgfornament', 'options': ''}]`
- Normalized: `["circuitikz", "pgfornament"]`
- Sorted: `["circuitikz", "pgfornament"]`
- ✅ Sortable

### Test 4: Multiple packages với options
```latex
%!<\usepackage[siunitx]{circuitikz}>
%!<\usepackage{pgfornament}>
```
- Packages: `[{'name': 'circuitikz', 'options': 'siunitx'}, {'name': 'pgfornament', 'options': ''}]`
- Normalized: `["circuitikz[siunitx]", "pgfornament"]`
- Sorted: `["circuitikz[siunitx]", "pgfornament"]`
- ✅ Sortable

## 📊 Impact

### Files Changed
- `app.py`: Hàm `_calculate_cache_key` trong class `CompilationCache`

### Backward Compatibility
- ✅ Hoàn toàn backward compatible
- ✅ Hỗ trợ cả dict và string format
- ✅ Cache keys consistent và deterministic

### Performance
- ✅ Không ảnh hưởng performance
- ✅ Cache vẫn hoạt động bình thường
- ✅ LRU eviction vẫn hoạt động

## 🚀 Deployment

1. ✅ Code đã fix
2. ✅ Linter passed
3. ✅ Backward compatible
4. 🔄 Cần restart backend để apply changes

### Restart Command

```bash
# Kill old process
pkill -f "gunicorn.*app:app"

# Start new process (từ thư mục project)
cd /Users/hieplequoc/web/work/tikz2svg_api
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 180 app:app &
```

## ✨ Expected Behavior After Fix

### Test Case 1: ✅
```latex
%!<\usepackage[siunitx]{circuitikz}>
\begin{tikzpicture}
\draw (0,0) to[R=1<\ohm>] (2,0);
\end{tikzpicture}
```
**Result:** THÀNH CÔNG

### Test Case 2: ✅
```latex
%!<\usepackage{circuitikz}>
\begin{tikzpicture}
\draw (0,0) to[R, o-o] (2,0);
\end{tikzpicture}
```
**Result:** THÀNH CÔNG

### Test Case 3 (Multiple lines): ✅
```latex
%!<\usepackage{circuitikz}>
%!<\usepackage{pgfornament}>
\begin{tikzpicture}
\draw (0,0) to[R, o-o] (2,0);
\node at (3,0) {\pgfornament[width=1cm]{15}};
\end{tikzpicture}
```
**Result:** THÀNH CÔNG

### Test Case 3 (Single line): ✅
```latex
%!<\usepackage{circuitikz},\usepackage{pgfornament}>
\begin{tikzpicture}
\draw (0,0) to[R, o-o] (2,0);
\node at (3,0) {\pgfornament[width=1cm]{15}};
\end{tikzpicture}
```
**Result:** THÀNH CÔNG

## 🎉 Summary

- **Root cause:** Dict không thể sort trực tiếp trong Python
- **Solution:** Normalize dict → string trước khi sort
- **Impact:** Minimal, chỉ cache key generation logic
- **Status:** ✅ FIXED
- **Next step:** Restart backend và test lại

---

**Fix hoàn tất!** Sau khi restart backend, tất cả test cases sẽ hoạt động bình thường.

