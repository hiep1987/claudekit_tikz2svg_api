# File Card - Comment Count Feature

## 📋 Tổng quan

Tính năng hiển thị số lượng comment trên file card, giúp người dùng biết được mức độ thảo luận của mỗi SVG file.

## ✅ Ngày hoàn thành

**24/10/2025** - Hoàn thành tích hợp comment count vào file card system

## 🎯 Mục tiêu

1. Hiển thị số lượng comment trên mỗi file card
2. Comment count icon đặt bên dưới like button
3. Click vào comment count sẽ chuyển đến trang view_svg và scroll đến comments section
4. Tương thích với cả user đã đăng nhập và chưa đăng nhập
5. Fallback gracefully nếu bảng `svg_comments` chưa tồn tại

## 📊 Cấu trúc Database

### Bảng `svg_comments`

Theo `DATABASE_DOCUMENTATION.md`, bảng comments có tên chính xác là **`svg_comments`** (không phải `svg_comment`):

```sql
CREATE TABLE `svg_comments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `svg_filename` VARCHAR(255) NOT NULL,
  `user_id` INT NOT NULL,
  `comment_text` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `parent_comment_id` INT DEFAULT NULL,
  `likes_count` INT DEFAULT 0,
  `replies_count` INT DEFAULT 0,
  `deleted_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX idx_svg_filename (svg_filename),
  INDEX idx_user_id (user_id),
  INDEX idx_parent_comment_id (parent_comment_id),
  INDEX idx_created_at_desc (created_at DESC),
  
  CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  CONSTRAINT fk_comments_svg_image FOREIGN KEY (svg_filename) REFERENCES svg_image(filename) ON DELETE CASCADE,
  CONSTRAINT fk_comments_parent FOREIGN KEY (parent_comment_id) REFERENCES svg_comments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Lưu ý quan trọng:**
- Bảng tên là `svg_comments` (có 's' ở cuối)
- Foreign key sử dụng `svg_filename` (VARCHAR) thay vì `svg_image_id` (INT)
- Có soft delete với field `deleted_at`

## 🔧 Các thay đổi

### 1. Backend - `app.py`

#### Hàm `get_svg_files_with_likes()` (dòng 591-651)

**Thay đổi:**
- Thêm subquery để đếm comment count từ bảng `svg_comments`
- Sử dụng `COALESCE()` để đảm bảo trả về 0 nếu không có comments
- Filter `deleted_at IS NULL` để chỉ đếm comments chưa bị xóa
- Thêm try-catch để fallback nếu bảng chưa tồn tại

**Query chính:**
```python
cursor.execute("""
    SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
           (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
           (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user,
           COALESCE((SELECT COUNT(*) FROM svg_comments WHERE svg_filename = s.filename AND deleted_at IS NULL), 0) as comment_count
    FROM svg_image s
    JOIN user u ON s.user_id = u.id
    ORDER BY s.created_at DESC
    LIMIT 100
""", (current_user_id or 0,))
```

**Fallback query (nếu bảng chưa tồn tại):**
```python
except mysql.connector.errors.ProgrammingError as e:
    if 'svg_comments' in str(e) and "doesn't exist" in str(e):
        print(f"[WARN] svg_comments table doesn't exist, using fallback query", flush=True)
        cursor.execute("""
            SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user,
                   0 as comment_count
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            ORDER BY s.created_at DESC
            LIMIT 100
        """, (current_user_id or 0,))
```

#### Hàm `get_public_svg_files()` (dòng 653-712)

**Thay đổi tương tự:**
- Thêm comment count subquery
- Fallback mechanism giống hệt `get_svg_files_with_likes()`

### 2. Frontend - HTML Template

#### File: `templates/partials/_file_card.html`

**Thêm comment count overlay:**
```html
<!-- Comment Count - Below like button -->
<div class="comment-count-wrapper-overlay">
    <a href="/view_svg/{{ file.filename }}#comments-section" class="comment-count-link">
        <i class="fas fa-comment"></i>
        <span class="comment-count">{{ file.comment_count|default(0) }}</span>
    </a>
</div>
```

**Vị trí:**
- Đặt ngay sau `like-button-wrapper-overlay`
- Trong `file-img-container`

### 3. Frontend - CSS

#### File: `static/css/file_card.css`

**Thêm styles cho comment count:**
```css
.tikz-app .comment-count-wrapper-overlay {
    position: absolute;
    bottom: 8px;
    right: 60px; /* Positioned next to like button */
    z-index: 200;
    display: flex;
    align-items: center;
}

.tikz-app .comment-count-link {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 10px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    text-decoration: none;
    color: #666;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tikz-app .comment-count-link:hover {
    background: rgba(255, 255, 255, 1);
    color: #1976d2;
    transform: translateY(-1px);
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
}

.tikz-app .comment-count-link i {
    font-size: 16px;
}

.tikz-app .comment-count {
    font-size: 13px;
    line-height: 1;
}
```

### 4. Frontend - JavaScript

#### File: `static/js/file_card.js`

**Cập nhật click handler để prevent conflict:**
```javascript
document.addEventListener('click', function(e) {
    const imgContainer = e.target.closest('.file-img-container');
    if (imgContainer) {
        // Don't trigger if clicking on like button or comment count
        if (e.target.closest('.like-button-wrapper-overlay') ||
            e.target.closest('.comment-count-wrapper-overlay')) {
            return;
        }
        // ... existing logic ...
    }
});
```

**Tương tự cho mobile touch events:**
```javascript
function initializeFileCardTouchEvents() {
    // ... existing code ...
    
    // Don't trigger if clicking on like button or comment count
    if (e.target.closest('.like-button-wrapper-overlay') ||
        e.target.closest('.comment-count-wrapper-overlay')) {
        return;
    }
    
    // ... existing logic ...
}
```

## 🎨 UI/UX Design

### Visual Design
- **Icon:** Font Awesome `fa-comment`
- **Position:** Bottom-right, next to like button (60px from right edge)
- **Style:** White rounded pill with shadow
- **Hover:** Slight lift effect + blue color

### Interaction
- **Click:** Navigate to `/view_svg/{filename}#comments-section`
- **Browser:** Auto-scroll to comments section using anchor link
- **Mobile:** Same behavior, no special handling needed

### Spacing
```
┌─────────────────────────────┐
│                             │
│      SVG Image              │
│                             │
│                             │
│              [💬 5] [❤️ 10] │ ← Bottom-right corner
└─────────────────────────────┘
   Comment    Like
   (60px)     (8px from right)
```

## 📝 Data Flow

### 1. Server-Side Rendering (SSR)
```
Database Query
    ↓
get_svg_files_with_likes() / get_public_svg_files()
    ↓
Add comment_count to each file object
    ↓
Render _file_card.html with comment_count
    ↓
HTML sent to browser
```

### 2. Client-Side Interaction
```
User clicks comment count
    ↓
Browser navigates to /view_svg/{filename}#comments-section
    ↓
Browser auto-scrolls to #comments-section anchor
    ↓
User sees comments
```

## 🔒 Security & Performance

### Security
- ✅ No SQL injection (using parameterized queries)
- ✅ XSS protection (Jinja2 auto-escaping)
- ✅ No sensitive data exposed

### Performance
- ✅ Single query with subquery (efficient)
- ✅ Index on `svg_filename` in `svg_comments` table
- ✅ Filter `deleted_at IS NULL` uses index
- ✅ `COALESCE()` ensures no NULL values

### Database Load
- **Query complexity:** O(n) where n = number of files
- **Subquery per file:** Indexed, fast lookup
- **Total queries:** 1 (no N+1 problem)

## 🧪 Testing

### Manual Testing Checklist

#### Backend
- [x] Query returns correct comment count
- [x] Query handles files with 0 comments
- [x] Query filters deleted comments (`deleted_at IS NULL`)
- [x] Fallback works when `svg_comments` table doesn't exist
- [x] No errors in console

#### Frontend
- [x] Comment count displays correctly
- [x] Icon renders properly
- [x] Link navigates to correct URL
- [x] Anchor scroll works
- [x] Hover effect works
- [x] Mobile responsive

#### Integration
- [x] Works on index page
- [x] Works on search results page
- [x] Works on profile SVG files page
- [x] Works for logged-in users
- [x] Works for anonymous users

### Test Cases

#### Case 1: File with comments
```
Input: SVG file with 5 comments
Expected: Display "💬 5"
Result: ✅ Pass
```

#### Case 2: File with no comments
```
Input: SVG file with 0 comments
Expected: Display "💬 0"
Result: ✅ Pass
```

#### Case 3: Table doesn't exist
```
Input: Database without svg_comments table
Expected: Display "💬 0" (fallback)
Result: ✅ Pass
```

#### Case 4: Click navigation
```
Input: Click on comment count
Expected: Navigate to /view_svg/{filename}#comments-section
Result: ✅ Pass
```

## 🐛 Known Issues & Limitations

### Current Limitations
1. **No real-time updates:** Comment count không tự động cập nhật khi có comment mới (cần refresh page)
2. **No differentiation:** Không phân biệt giữa top-level comments và replies
3. **No loading state:** Không có loading indicator khi navigate

### Future Improvements
1. **Real-time updates:** Sử dụng WebSocket hoặc polling để cập nhật real-time
2. **Detailed count:** Hiển thị số lượng top-level comments vs replies
3. **Tooltip:** Hover để xem preview 2-3 comments đầu tiên
4. **Animation:** Smooth scroll animation khi navigate đến comments section

## 📚 Related Documentation

- `DATABASE_DOCUMENTATION.md` - Chi tiết về bảng `svg_comments`
- `COMMENTS_IMPLEMENTATION_ROADMAP.md` - Roadmap tổng thể cho comments system
- `FILE_CARD_IMAGE_CLICK_FEATURE.md` - Tính năng click vào image để download
- `FILE_CARD_RENDERING_ANALYSIS.md` - Phân tích cách render file cards

## 🔄 Migration Guide

### Nếu bạn đang chạy local development:

1. **Kiểm tra bảng `svg_comments` đã tồn tại chưa:**
```sql
SHOW TABLES LIKE 'svg_comments';
```

2. **Nếu chưa có, chạy migration:**
```bash
mysql -u hiep1987 -p tikz2svg_local < migrate_comments_system.sql
```

3. **Verify migration:**
```sql
DESCRIBE svg_comments;
SELECT COUNT(*) FROM svg_comments;
```

4. **Restart Flask app:**
```bash
# App sẽ tự động detect bảng và sử dụng query đúng
```

### Nếu bảng chưa tồn tại:
- ✅ App vẫn hoạt động bình thường
- ✅ Comment count hiển thị là 0
- ✅ Không có error trong console
- ✅ Warning log: `[WARN] svg_comments table doesn't exist, using fallback query`

## ✨ Summary

### What Changed
- ✅ Backend: Thêm `comment_count` vào 2 hàm query (`get_svg_files_with_likes`, `get_public_svg_files`)
- ✅ Frontend HTML: Thêm comment count overlay vào `_file_card.html`
- ✅ Frontend CSS: Thêm styles cho comment count
- ✅ Frontend JS: Cập nhật click handlers để prevent conflict

### What Works
- ✅ Comment count hiển thị chính xác
- ✅ Click navigate đến comments section
- ✅ Fallback gracefully nếu table chưa tồn tại
- ✅ No breaking changes
- ✅ Backward compatible

### What's Next
- 🔜 Real-time comment count updates
- 🔜 Comment preview on hover
- 🔜 Detailed comment/reply breakdown
- 🔜 Comment count animation
