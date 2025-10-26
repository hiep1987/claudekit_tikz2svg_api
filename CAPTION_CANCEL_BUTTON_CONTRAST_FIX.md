# Caption Cancel Button Contrast Fix

**Date:** 2025-10-21  
**Component:** View SVG Page - Caption Section  
**Issue:** Poor contrast in dark mode  
**Status:** ✅ Fixed

---

## 📋 Vấn đề

Nút **"Hủy"** (Cancel) trong phần caption trên trang `view_svg.html` có độ tương phản kém trong **dark mode**, không đạt chuẩn WCAG.

### CSS hiện tại:
```css
.tikz-app .caption-btn-cancel {
    background: var(--bg-secondary);
    color: var(--text-dark);  /* ❌ Vấn đề ở đây */
    border: 1px solid var(--border-light);
}
```

---

## 🔍 Phân tích độ tương phản

### Giá trị màu:

| Variable | Light Mode | Dark Mode |
|----------|-----------|-----------|
| `--bg-secondary` | `#f5f5f5` | `#2a2a2a` |
| `--text-dark` | `#1a1a1a` | `#1a1a1a` (không đổi) |
| `--text-primary` | `#333333` | `#e5e5e5` |

### Kết quả kiểm tra:

#### ❌ **TRƯỚC KHI SỬA** (`color: var(--text-dark)`):
```
Light mode: #f5f5f5 bg + #1a1a1a text
→ Contrast ratio: 15.96:1 ✅ WCAG AAA

Dark mode:  #2a2a2a bg + #1a1a1a text
→ Contrast ratio: 1.21:1 ❌ FAIL (cần ≥4.5:1 cho AA)
```

**Vấn đề:** `--text-dark` không thay đổi giá trị trong dark mode, vẫn giữ nguyên `#1a1a1a` (màu tối), dẫn đến text màu tối trên nền tối → độ tương phản cực kém (1.21:1).

#### ✅ **SAU KHI SỬA** (`color: var(--text-primary)`):
```
Light mode: #f5f5f5 bg + #333333 text
→ Contrast ratio: 11.59:1 ✅ WCAG AAA

Dark mode:  #2a2a2a bg + #e5e5e5 text  
→ Contrast ratio: 11.39:1 ✅ WCAG AAA
```

**Giải pháp:** `--text-primary` tự động thay đổi theo theme:
- Light mode: `#333333` (màu tối)
- Dark mode: `#e5e5e5` (màu sáng)

→ Đảm bảo độ tương phản tốt trong cả hai chế độ!

---

## ✅ Giải pháp

### Thay đổi CSS:

```css
.tikz-app .caption-btn-cancel {
    background: var(--bg-secondary);
    color: var(--text-primary);  /* ✅ Thay đổi từ --text-dark */
    border: 1px solid var(--border-light);
}
```

### File thay đổi:
- `static/css/view_svg.css` (line 1232)

---

## 📊 Kết quả

| Metric | Trước | Sau |
|--------|-------|-----|
| Light mode contrast | 15.96:1 ✅ | 11.59:1 ✅ |
| Dark mode contrast | **1.21:1** ❌ | **11.39:1** ✅ |
| WCAG AA (≥4.5:1) | Dark mode FAIL | **All PASS** ✅ |
| WCAG AAA (≥7:1) | Dark mode FAIL | **All PASS** ✅ |

---

## 🧪 Cách kiểm tra

### Script Python kiểm tra nhanh:

```python
def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lum(r, g, b):
    def c(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)

def ratio(c1, c2):
    l1, l2 = lum(*hex_to_rgb(c1)), lum(*hex_to_rgb(c2))
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

# Dark mode check
print(f"Dark mode: {ratio('#2a2a2a', '#e5e5e5'):.2f}:1")
# Output: 11.39:1 ✅
```

### Kiểm tra trực quan:

1. Mở `http://localhost:5173/view_svg/<any_svg_file>`
2. Trong phần caption, click "Thêm mô tả" hoặc "Chỉnh sửa mô tả"
3. Nhìn vào nút "❌ Hủy":
   - **Light mode**: Text màu `#333` trên nền `#f5f5f5` - rõ ràng ✅
   - **Dark mode**: Text màu `#e5e5e5` trên nền `#2a2a2a` - rõ ràng ✅

---

## 📚 Tài liệu liên quan

- **WCAG 2.1 Guidelines**: [Contrast (Minimum) - Level AA](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- **WCAG Contrast Ratio**: Minimum 4.5:1 for normal text (AA), 7:1 for AAA
- **CSS Variables**: `static/css/foundation/master-variables.css`
- **Component**: Image Caption Feature (`IMAGE_CAPTION_FEATURE_GUIDE.md`)

---

## 🎓 Bài học

### ⚠️ Tránh sử dụng `--text-dark` cho UI elements:

`--text-dark` được thiết kế cho các trường hợp đặc biệt và **không tự động thay đổi** theo dark mode:
```css
/* master-variables.css */
--text-dark: #1a1a1a;  /* Cố định, không đổi trong dark mode */
```

### ✅ Sử dụng `--text-primary` cho text chính:

`--text-primary` tự động adapt theo theme:
```css
/* Light mode */
--text-primary: #333;

/* Dark mode */
@media (prefers-color-scheme: dark) {
  --text-primary: #e5e5e5;
}
```

### 🔑 Best Practice:

Khi styling UI elements cần hiển thị trong cả light/dark mode:
- ✅ **DO**: Dùng `--text-primary`, `--text-secondary`, `--text-muted`
- ❌ **DON'T**: Dùng `--text-dark`, `--text-white`, `--text-black` (fixed colors)

---

## ✅ Checklist

- [x] Phát hiện vấn đề contrast trong dark mode
- [x] Kiểm tra độ tương phản bằng script Python
- [x] Xác định root cause: `--text-dark` không đổi trong dark mode
- [x] Thay đổi từ `--text-dark` → `--text-primary`
- [x] Verify contrast ratio: 11.39:1 (WCAG AAA) ✅
- [x] Test visual trong cả light/dark mode
- [x] Tạo documentation

---

**Note:** Cải tiến này đảm bảo accessibility tốt hơn cho người dùng, đặc biệt là người khiếm thị hoặc sử dụng dark mode trong môi trường ánh sáng yếu.

