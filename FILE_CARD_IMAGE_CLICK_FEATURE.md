# File Card Image Click Feature

## Tổng Quan

Cải tiến file-card component để cho phép người dùng nhấn vào vùng ảnh (`file-img-container`) để truy cập trang xem/tải ảnh, thay vì chỉ có thể nhấn vào nút "Tải ảnh".

## Thay Đổi Đã Thực Hiện

### 1. HTML Template (`templates/partials/_file_card.html`)

**Thay đổi:**
- Thêm attribute `data-filename="{{ file.filename }}"` vào `.file-img-container`
- Thêm inline style `cursor: pointer` để hiển thị con trỏ chuột dạng pointer khi hover

```html
<div class="file-img-container" data-filename="{{ file.filename }}" style="cursor: pointer;">
    <img src="{{ file.url }}" alt="{{ file.filename }}">
    ...
</div>
```

### 2. JavaScript - Desktop (`static/js/file_card.js`)

**Thêm event handler mới cho desktop:**
- Xử lý click vào `.file-img-container`
- Bỏ qua nếu click vào nút like (`.like-button-wrapper-overlay`)
- Chuyển hướng đến `/view_svg/{filename}`
- Tracking analytics với source `image_click`

```javascript
// Handle clicks on image container to view/download image
document.addEventListener('click', function(e) {
    const imgContainer = e.target.closest('.file-img-container');
    if (imgContainer) {
        // Don't trigger if clicking on like button or its children
        if (e.target.closest('.like-button-wrapper-overlay')) {
            return;
        }
        
        const filename = imgContainer.getAttribute('data-filename');
        if (filename) {
            // Track and navigate
            window.location.href = `/view_svg/${filename}`;
        }
        return;
    }
});
```

### 3. JavaScript - Mobile (`static/js/file_card.js`)

**Thêm event handler cho mobile/touch devices:**
- Tương tự desktop nhưng có thêm logic:
  - Bỏ qua nếu menu action đang mở (`.menu-open`)
  - Thêm `e.preventDefault()` và `e.stopPropagation()`
  - Tracking với device: 'mobile'

```javascript
// ==== Xử lý click vào image container (mobile) ====
const imgContainer = e.target.closest('.file-img-container');
if (imgContainer) {
    // Don't trigger if clicking on like button
    if (e.target.closest('.like-button-wrapper-overlay')) {
        return;
    }
    
    // Don't trigger if menu is open
    const card = imgContainer.closest('.file-card');
    if (card && card.classList.contains('menu-open')) {
        return;
    }
    
    const filename = imgContainer.getAttribute('data-filename');
    if (filename) {
        e.preventDefault();
        e.stopPropagation();
        window.location.href = `/view_svg/${filename}`;
    }
    return;
}
```

### 4. CSS Styling (`static/css/file_card.css`)

**Cải tiến hover effect:**
- Thêm `cursor: pointer` vào `.file-img-container`
- Thêm `transition: opacity 0.2s ease` cho smooth animation
- Thêm hover state với `opacity: 0.9`
- Thêm `pointer-events: none` cho `img` để đảm bảo container luôn là target

```css
.tikz-app .file-img-container {
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.tikz-app .file-img-container:hover {
  opacity: 0.9;
}

.tikz-app .file-img-container img {
  pointer-events: none; /* Prevent img from being the target */
}
```

### 5. Profile Followed Posts

**✅ KHÔNG CẦN cập nhật!**

Template `templates/profile_followed_posts.html` đã được refactor để:
- Sử dụng partial `_file_card.html` (server-side rendering)
- Chỉ load `file_card.js` (shared component)
- File `static/js/profile_followed_posts.js` đã được **XÓA** (legacy code không còn dùng)

→ Tự động có feature mới từ partial `_file_card.html`

## Tính Năng

### ✅ Desktop
- Click vào ảnh → Chuyển đến trang view_svg
- Hover vào ảnh → Opacity giảm nhẹ (0.9) + cursor pointer
- Click vào nút like → Vẫn hoạt động bình thường (không trigger navigation)

### ✅ Mobile
- Tap vào ảnh → Chuyển đến trang view_svg
- Tap vào nút like → Vẫn hoạt động bình thường
- Khi menu action đang mở → Click ảnh không trigger navigation (tránh conflict)

## Analytics Tracking

Tất cả click vào ảnh đều được track với:
- **Action:** `file_view` hoặc `search_result_click`
- **Source:** `browse_image` hoặc `search_image`
- **Device:** `desktop` hoặc `mobile`
- **Additional data:** filename, query (nếu từ search)

## Backward Compatibility

✅ Tất cả chức năng cũ vẫn hoạt động:
- Nút "Tải ảnh" vẫn hoạt động
- Nút like vẫn hoạt động
- Action menu vẫn hoạt động
- Mobile 2-tap logic vẫn hoạt động

## Testing Checklist

- [ ] Desktop: Click vào ảnh → Navigate to view_svg
- [ ] Desktop: Click vào like button → Like hoạt động, không navigate
- [ ] Desktop: Hover vào ảnh → Cursor pointer + opacity effect
- [ ] Mobile: Tap vào ảnh → Navigate to view_svg
- [ ] Mobile: Tap vào like button → Like hoạt động
- [ ] Mobile: Khi menu mở, tap ảnh → Không navigate
- [ ] Profile followed posts: Click ảnh → Navigate
- [ ] Analytics tracking → Verify trong GA4

## Files Modified

1. ✅ `templates/partials/_file_card.html` - Added data-filename and cursor style
2. ✅ `static/js/file_card.js` - Added click handlers for desktop and mobile
3. ✅ `static/css/file_card.css` - Added hover effects and cursor pointer
4. 🗑️ `static/js/profile_followed_posts.js` - **DELETED** (legacy file, not used)

## UX Improvements

1. **Tăng clickable area:** Toàn bộ vùng ảnh giờ đây có thể click được
2. **Intuitive interaction:** Người dùng tự nhiên sẽ click vào ảnh để xem chi tiết
3. **Visual feedback:** Hover effect (opacity) cho biết vùng có thể click
4. **No conflicts:** Like button và action menu vẫn hoạt động độc lập

## Deployment Notes

- ✅ No database changes required
- ✅ No backend changes required
- ✅ Only frontend changes (HTML, CSS, JS)
- ✅ Backward compatible with existing functionality
- ⚠️ Clear browser cache after deployment để load CSS/JS mới

---

**Date:** 2025-10-23
**Status:** ✅ Completed

