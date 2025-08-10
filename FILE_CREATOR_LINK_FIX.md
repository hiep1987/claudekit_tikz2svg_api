# Sửa lỗi link trong file-creator của profile_followed_posts.html

## Vấn đề
Khi nhấn vào link trong `class="file-creator"` của trang `profile_followed_posts.html`, không truy cập được đến `/profile/${post.creator_id}/svg-files`.

## Nguyên nhân
Link trong `file-creator` đang trỏ đến `/profile/${post.creator_id}` thay vì `/profile/${post.creator_id}/svg-files`.

## Giải pháp đã thực hiện

### 1. Sửa URL trong link
**Trước:**
```javascript
<a href="/profile/${post.creator_id}" style="text-decoration: none; color: #1976d2; font-weight: 700; font-size: 13px;">
```

**Sau:**
```javascript
<a href="/profile/${post.creator_id}/svg-files" style="text-decoration: none; color: #1976d2; font-weight: 700; font-size: 13px;" onclick="console.log('🔗 Clicked on creator link:', '${post.creator_username}', '->', '/profile/${post.creator_id}/svg-files');">
```

### 2. Thêm debug logging
- Thêm `onclick` handler để log khi click vào link
- Thêm event listener để debug việc click vào file-creator links

### 3. Debug event listeners
Thêm event listener để track clicks:
```javascript
// ==== Debug: Add event listener to track clicks on file-creator links ====
document.addEventListener('click', function(e) {
    const link = e.target.closest('.file-creator a');
    if (link) {
        console.log('🔗 Debug: Clicked on file-creator link:', link.href);
        console.log('🔗 Debug: Link target:', link);
        console.log('🔗 Debug: Event target:', e.target);
    }
});
```

## Kết quả mong đợi
- Link trong `file-creator` sẽ trỏ đến `/profile/${post.creator_id}/svg-files`
- Khi click vào link sẽ navigate đến trang SVG files của creator
- Console sẽ hiển thị debug logs khi click

## Cách test
1. Truy cập trang `/profile/1/followed-posts` (cần đăng nhập)
2. Tìm một followed post có creator
3. Click vào tên creator trong `file-creator`
4. Kiểm tra xem có navigate đến `/profile/{creator_id}/svg-files` không
5. Kiểm tra console logs

## Files đã sửa
- `tikz2svg_api/templates/profile_followed_posts.html` (dòng 1109) 