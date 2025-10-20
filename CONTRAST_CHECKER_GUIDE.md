# WCAG Contrast Ratio Checker - Hướng dẫn sử dụng

**File:** `check_contrast_ratio.py`  
**Mục đích:** Kiểm tra độ tương phản giữa màu text và background theo chuẩn WCAG

## Cài đặt

Không cần cài thêm package, chỉ cần Python 3:

```bash
python3 check_contrast_ratio.py
```

## WCAG Standards

### WCAG AA (Minimum)
- **Normal text:** ≥ 4.5:1
- **Large text (18pt+):** ≥ 3:1

### WCAG AAA (Enhanced)
- **Normal text:** ≥ 7:1
- **Large text (18pt+):** ≥ 4.5:1

## Sử dụng cơ bản

### 1. Chạy test mặc định
```bash
python3 check_contrast_ratio.py
```

Output:
```
============================================================
WCAG CONTRAST RATIO CHECKER
============================================================

=== Login Modal Cancel Button (var(--text-primary)) ===

Light Mode:
  Background: (245, 245, 245)
  Text: (51, 51, 51)
  Contrast Ratio: 11.59:1
  WCAG AA (≥4.5): ✅ PASS
  WCAG AAA (≥7): ✅ PASS

Dark Mode:
  Background: (42, 42, 42)
  Text: (229, 229, 229)
  Contrast Ratio: 11.39:1
  WCAG AA (≥4.5): ✅ PASS
  WCAG AAA (≥7): ✅ PASS
```

### 2. Kiểm tra màu tùy chỉnh

Mở file `check_contrast_ratio.py` và thêm vào cuối hàm `main()`:

```python
# Thêm vào cuối hàm main()
print("\n=== Custom Color Check ===\n")

# Sử dụng RGB tuple
check_contrast((255, 255, 255), (0, 0, 0), "White bg + Black text")

# Hoặc sử dụng hex color
check_contrast("#f5f5f5", "#1a1a1a", "Custom Colors")
```

### 3. Sử dụng trong Python script khác

```python
from check_contrast_ratio import check_contrast, hex_to_rgb, contrast_ratio

# Kiểm tra và in kết quả
check_contrast("#ffffff", "#000000", "White & Black")

# Hoặc chỉ tính ratio
bg_rgb = hex_to_rgb("#f5f5f5")
text_rgb = hex_to_rgb("#333")
ratio = contrast_ratio(bg_rgb, text_rgb)
print(f"Contrast: {ratio:.2f}:1")
```

## Các hàm chính

### 1. `rgb_to_luminance(r, g, b)`
Chuyển đổi RGB sang relative luminance theo công thức WCAG

**Parameters:**
- `r`, `g`, `b`: Integer 0-255

**Returns:**
- `float`: Relative luminance value (0-1)

### 2. `contrast_ratio(rgb1, rgb2)`
Tính contrast ratio giữa 2 màu RGB

**Parameters:**
- `rgb1`, `rgb2`: Tuple (r, g, b)

**Returns:**
- `float`: Contrast ratio (1-21)

### 3. `hex_to_rgb(hex_color)`
Chuyển đổi hex color sang RGB tuple

**Parameters:**
- `hex_color`: String như "#fff", "#ffffff", "fff"

**Returns:**
- `tuple`: (r, g, b)

### 4. `check_contrast(bg_color, text_color, mode_name="")`
Kiểm tra và in kết quả contrast ratio

**Parameters:**
- `bg_color`: Hex string hoặc RGB tuple
- `text_color`: Hex string hoặc RGB tuple
- `mode_name`: Optional tên mode để hiển thị

**Returns:**
- `float`: Contrast ratio

## Ví dụ kiểm tra CSS variables

Để kiểm tra các CSS variables trong dự án:

```python
# Light Mode Colors
print("=== Light Mode ===\n")
check_contrast("#f5f5f5", "#333", "var(--bg-secondary) + var(--text-primary)")
check_contrast("#f5f5f5", "#1a1a1a", "var(--bg-secondary) + var(--text-dark)")
check_contrast("#ffffff", "#1976d2", "var(--bg-primary) + var(--primary-color)")

# Dark Mode Colors
print("\n=== Dark Mode ===\n")
check_contrast("#2a2a2a", "#e5e5e5", "var(--bg-secondary) + var(--text-primary)")
check_contrast("#1a1a1a", "#ffffff", "var(--bg-primary) + var(--text-white)")
check_contrast("#2a2a2a", "#1a1a1a", "var(--bg-secondary) + var(--text-dark) ⚠️")
```

## Khi nào nên kiểm tra?

✅ **Luôn kiểm tra khi:**
- Thêm màu mới vào design system
- Tạo component mới với background + text
- Hỗ trợ dark mode
- Thay đổi CSS variables liên quan đến màu
- Nhận feedback về khó đọc

## Quick Reference

| Contrast Ratio | Đánh giá | WCAG Level |
|----------------|----------|------------|
| < 3:1 | ❌ Fail (unacceptable) | - |
| 3:1 - 4.4:1 | ⚠️ Large text only | AA (Large) |
| 4.5:1 - 6.9:1 | ✅ Good | AA |
| 7:1 - 14:1 | ✅✅ Excellent | AAA |
| > 14:1 | ✅✅✅ Outstanding | AAA+ |

## Tips

1. **Aim for AAA (≥7:1)** cho normal text
2. **Avoid low contrast** (< 4.5:1) trong production
3. **Test both modes** nếu có light/dark theme
4. **Use CSS variables** để auto-adapt với themes
5. **Check hover states** cũng cần đủ contrast

## Troubleshooting

### Issue: Màu fail WCAG AA
**Solution:**
- Tăng độ tối của text (giảm RGB values)
- Tăng độ sáng của background (tăng RGB values)
- Hoặc ngược lại

### Issue: Dark mode fail nhưng light mode pass
**Solution:**
- Đổi từ `var(--text-dark)` sang `var(--text-primary)`
- `var(--text-primary)` tự động adapt: `#333` (light) → `#e5e5e5` (dark)

### Issue: Cả 2 modes đều fail
**Solution:**
- Xem lại color palette
- Sử dụng pure white (#fff) hoặc pure black (#000) nếu cần
- Tham khảo Material Design color system

## Related Files

- `static/css/foundation/master-variables.css` - CSS color variables
- `LOGIN_MODAL_CONTRAST_FIX.md` - Example contrast fix case study

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Color Oracle](https://colororacle.org/) - Simulate color blindness

---

**Created:** 2025-10-20  
**Last Updated:** 2025-10-20  
**Version:** 1.0

