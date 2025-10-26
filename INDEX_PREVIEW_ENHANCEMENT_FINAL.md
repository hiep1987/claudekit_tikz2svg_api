# Index Preview Enhancement - Improved UX

**Date:** 2025-10-23  
**Feature:** Giữ lại SVG cũ khi đang cập nhật code mới  
**Status:** ✅ Implemented

---

## 🎯 MỤC TIÊU

Cải thiện trải nghiệm người dùng khi chỉnh sửa code TikZ bằng cách:
- **Giữ lại SVG cũ** khi đang cập nhật code mới
- **Làm mờ ảnh** và hiển thị overlay thông báo trạng thái
- **Không bị gián đoạn** bởi thông báo lỗi đột ngột

---

## 🔍 VẤN ĐỀ TRƯỚC ĐÂY

### Hành vi cũ:
Khi người dùng thay đổi code từ:
```latex
\filldraw [red] (0,0) circle (4pt);
```
sang:
```latex
\filldraw [red] (0,-1) circle (4pt);
```

**Trong quá trình gõ** (ví dụ: `0,` → `0,-` → `0,-1`):
- ❌ SVG cũ biến mất ngay lập tức
- ❌ Hiển thị thông báo lỗi: "Code có lỗi - vui lòng sửa"
- ❌ Người dùng mất tham chiếu trực quan

### Vấn đề UX:
- Người dùng không thể so sánh với ảnh cũ
- Gây khó chịu khi ảnh preview nhấp nháy liên tục
- Không rõ là đang cập nhật hay lỗi thật sự

---

## ✅ GIẢI PHÁP MỚI

### Hành vi mới:

#### 1. **Khi bắt đầu cập nhật code:**
- ✅ SVG cũ **vẫn hiển thị**
- ✅ Ảnh bị làm mờ (`opacity: 0.3`, `blur: 2px`)
- ✅ Hiện overlay màu xanh: **"Đang cập nhật code mới..."**

#### 2. **Khi code có lỗi tạm thời:**
- ✅ SVG cũ **vẫn giữ nguyên** nhưng mờ hơn (`opacity: 0.2`, `blur: 3px`)
- ✅ Overlay chuyển sang màu đỏ: **"Code có lỗi - vui lòng sửa"**
- ✅ Người dùng vẫn thấy ảnh cũ để tham khảo

#### 3. **Khi code mới hợp lệ:**
- ✅ Overlay biến mất
- ✅ SVG mới xuất hiện với `opacity: 1` và `filter: none`
- ✅ Transition mượt mà

---

## 📁 FILES CHANGED

### `static/js/index.js`

**Function:** `updateInputPreview(tikzCode)`

**Changes:**
1. **Thêm biến tracking:** `hasExistingImage`
2. **Khi có ảnh cũ:** Giữ lại và làm mờ
3. **Tạo overlay động:** với styling inline
4. **Cập nhật overlay:** theo trạng thái (đang cập nhật / lỗi / thành công)
5. **Xóa overlay:** khi preview thành công

---

## 🎨 VISUAL STATES

### State 1: Đang cập nhật
```
┌─────────────────────────────────┐
│  [SVG cũ - mờ, blur 2px]        │
│                                  │
│     ╔═══════════════════════╗   │
│     ║ Đang cập nhật code... ║   │
│     ╚═══════════════════════╝   │
│  (Màu xanh #2563eb)             │
└─────────────────────────────────┘
```

### State 2: Code có lỗi
```
┌─────────────────────────────────┐
│  [SVG cũ - rất mờ, blur 3px]    │
│                                  │
│     ╔═══════════════════════╗   │
│     ║ Code có lỗi - vui     ║   │
│     ║ lòng sửa              ║   │
│     ╚═══════════════════════╝   │
│  (Màu đỏ #dc2626)               │
└─────────────────────────────────┘
```

### State 3: Thành công
```
┌─────────────────────────────────┐
│  [SVG mới - rõ nét, không blur] │
│                                  │
│  (Không overlay)                 │
│                                  │
└─────────────────────────────────┘
```

---

## 🔧 TECHNICAL DETAILS

### Overlay Styling
```javascript
overlay.style.cssText = `
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.95);
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    font-weight: 600;
    color: #2563eb;
    z-index: 10;
    pointer-events: none;
    backdrop-filter: blur(4px);
`;
```

### Image States

| State           | Opacity | Blur  | Overlay Color       | Message                      |
|-----------------|---------|-------|---------------------|------------------------------|
| **Updating**    | 0.3     | 2px   | Blue (rgba white)   | "Đang cập nhật code mới..."  |
| **Error**       | 0.2     | 3px   | Red (rgba pink)     | "Code có lỗi - vui lòng sửa" |
| **Success**     | 1.0     | none  | -                   | -                            |

---

## 🚀 USER BENEFITS

### Trước:
1. User nhập code → ❌ Ảnh biến mất
2. User nhập tiếp → ❌ Hiện lỗi
3. User hoàn thành → ✅ Ảnh mới xuất hiện

**Problem:** Mất tham chiếu trực quan, gây khó chịu

### Sau:
1. User nhập code → ✅ Ảnh cũ mờ + "Đang cập nhật..."
2. User nhập tiếp → ✅ Ảnh cũ vẫn còn + "Code có lỗi..."
3. User hoàn thành → ✅ Ảnh mới rõ nét

**Benefit:** Luôn có tham chiếu, smooth transition, clear feedback

---

## 🧪 TEST SCENARIOS

### Test 1: Thay đổi số từ 0 → -1
```latex
Before: \filldraw [red] (0,0) circle (4pt);
During: \filldraw [red] (0,  ← gõ đến đây
Status: ✅ Ảnh cũ mờ + overlay xanh
```

### Test 2: Code có lỗi syntax
```latex
Before: \draw (0,0) -- (1,1);
During: \draw (0,0) -  ← thiếu dấu -
Status: ✅ Ảnh cũ rất mờ + overlay đỏ
```

### Test 3: Hoàn thành code mới
```latex
Before: \draw (0,0) -- (1,1);
After:  \draw (0,0) -- (2,2);
Status: ✅ Ảnh mới rõ nét, không overlay
```

### Test 4: Lỗi kết nối
```latex
Status: ✅ Ảnh cũ rất mờ + overlay đỏ "Lỗi kết nối"
```

---

## 📊 PERFORMANCE IMPACT

- **Minimal:** Chỉ thêm 1 DOM element (overlay) khi cần
- **Memory:** Overlay được tái sử dụng, không tạo mới liên tục
- **Rendering:** Sử dụng CSS `opacity` và `filter` (GPU-accelerated)
- **Network:** Không thay đổi, vẫn debounce 1 giây

---

## 🔮 FUTURE IMPROVEMENTS

### Potential enhancements:
1. **Smooth fade transition:** Thêm CSS transition cho opacity
2. **Loading spinner:** Icon loading quay tròn thay vì chỉ text
3. **Progress indicator:** Hiển thị % khi code phức tạp
4. **Diff highlight:** Highlight phần code đang thay đổi
5. **Error position:** Chỉ ra dòng/cột bị lỗi trong overlay

---

## ✅ CONCLUSION

Tính năng này cải thiện đáng kể UX của trang index:
- ✅ Người dùng không bị "blind" khi chỉnh sửa
- ✅ Feedback rõ ràng về trạng thái preview
- ✅ Smooth transition giữa các states
- ✅ Giữ được context trực quan trong suốt quá trình

**Impact:** High UX improvement với minimal code changes! 🎉

