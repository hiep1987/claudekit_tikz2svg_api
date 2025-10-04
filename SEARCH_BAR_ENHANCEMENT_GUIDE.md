# Hướng dẫn Search Bar nâng cao - TikZ2SVG

## 📝 Tổng quan

Search Bar đã được nâng cấp với khả năng tìm kiếm theo hai loại:
- **Từ khóa**: Tìm kiếm SVG files theo keywords (chức năng gốc)
- **Tên tài khoản**: Tìm kiếm SVG files theo username của người tạo

## 🎯 Tính năng mới

### 1. Radio Button Selection
- Người dùng có thể chọn kiểu tìm kiếm bằng radio buttons
- Giao diện trực quan với glass morphism design
- Tự động thay đổi placeholder text theo loại tìm kiếm

### 2. Smart Search Logic
- **Từ khóa**: Hiển thị suggestions từ keywords có sẵn
- **Tên tài khoản**: Không hiển thị suggestions, tìm kiếm trực tiếp

### 3. Dynamic UI Updates
- Placeholder text thay đổi theo search type
- Clear search input khi đổi search type
- Hide suggestions khi chuyển sang username search

## 🛠️ Triển khai kỹ thuật

### Frontend Changes

#### HTML Template (`templates/index.html`)
```html
<!-- Search Type Selection -->
<div class="search-type-selector">
    <label class="search-type-option">
        <input type="radio" name="search-type" value="keywords" id="search-type-keywords" checked>
        <span class="radio-label">Từ khóa</span>
    </label>
    <label class="search-type-option">
        <input type="radio" name="search-type" value="username" id="search-type-username">
        <span class="radio-label">Tên tài khoản</span>
    </label>
</div>
```

#### CSS Styles (`static/css/index.css`)
- Glass morphism design cho radio buttons
- Responsive layout
- Hover effects và transitions
- CSS Foundation System compliance

#### JavaScript Logic (`static/js/index.js`)
```javascript
// Helper functions
function getCurrentSearchType() {
    return usernameRadio && usernameRadio.checked ? 'username' : 'keywords';
}

function navigateToSearch(query) {
    const searchType = getCurrentSearchType();
    const url = `/search?q=${encodeURIComponent(query)}&type=${searchType}`;
    window.location.href = url;
}
```

### Backend Changes

#### Route Handler (`app.py`)
```python
@app.route('/search')
def search_results():
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'keywords')

    if search_type == 'username':
        # Search by username
        cursor.execute("""
            SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            WHERE u.username LIKE %s COLLATE utf8mb4_general_ci
            ORDER BY s.created_at DESC
        """, (get_user_id_from_session() or 0, f"%{query}%"))
    else:
        # Default: Search by keywords
        cursor.execute("""
            SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            JOIN svg_image_keyword sik ON s.id = sik.svg_image_id
            JOIN keyword k ON sik.keyword_id = k.id
            WHERE k.word LIKE %s COLLATE utf8mb4_general_ci
            ORDER BY s.created_at DESC
        """, (get_user_id_from_session() or 0, f"%{query}%"))
```

#### Template Updates (`templates/search_results.html`)
- Dynamic search type description
- Context-aware error messages

## 🧪 Testing Guide

### 1. Keyword Search Testing
1. Mở trang chủ `http://localhost:5173/`
2. Đảm bảo radio button "Từ khóa" được chọn
3. Nhập từ khóa (ví dụ: "graph", "tree")
4. Kiểm tra suggestions hiển thị
5. Nhấn Enter hoặc click suggestion
6. Verify kết quả tìm kiếm đúng

### 2. Username Search Testing
1. Chọn radio button "Tên tài khoản"
2. Kiểm tra placeholder đổi thành "Tìm theo tên tài khoản..."
3. Nhập username (ví dụ: "admin", "user123")
4. Verify không có suggestions hiển thị
5. Nhấn Enter để tìm kiếm
6. Kiểm tra kết quả hiển thị SVG files của user đó

### 3. Edge Cases Testing
- Tìm kiếm với query rỗng
- Tìm kiếm với username không tồn tại
- Tìm kiếm với keyword không có kết quả
- Chuyển đổi search type trong khi đang gõ
- Test trên mobile/tablet devices

## 📱 Responsive Design

- Radio buttons responsive trên mobile
- Touch-friendly interface
- Glass morphism effects maintained
- Consistent với design system

## 🔧 Troubleshooting

### Vấn đề thường gặp:

1. **Radio buttons không hiển thị đúng**
   - Kiểm tra CSS Foundation System đã load
   - Verify master-variables.css load trước

2. **JavaScript errors**
   - Check browser console
   - Verify DOM elements exist
   - Check for null radio button references

3. **Search không hoạt động**
   - Verify backend route parameters
   - Check database connection
   - Validate SQL queries

## 🚀 Future Enhancements

1. **Advanced Search**
   - Combine keyword + username search
   - Date range filtering
   - File type filtering

2. **Search Analytics**
   - Track search patterns
   - Popular searches
   - Search success rates

3. **Auto-complete**
   - Username suggestions từ database
   - Recent searches history
   - Search filters preservation

## 📚 API Documentation

### Search Endpoint
```
GET /search?q={query}&type={search_type}
```

**Parameters:**
- `q`: Search query string
- `type`: Either "keywords" or "username" (default: "keywords")

**Response:**
- Renders `search_results.html` template
- Includes search metadata và results

### URL Examples:
```
/search?q=graph&type=keywords
/search?q=admin&type=username
```

## ✅ Implementation Checklist

- [x] Radio button UI design
- [x] CSS styling với glass morphism
- [x] JavaScript event handlers
- [x] Backend route logic
- [x] Database queries cho username search
- [x] Template updates
- [x] Placeholder text updates
- [x] Error handling
- [x] Responsive design
- [x] Testing scenarios
- [x] Documentation

## 🎉 Kết luận

Search Bar enhancement đã được triển khai thành công với:
- UI/UX cải thiện
- Dual search functionality
- Maintainable code structure
- Comprehensive testing coverage
- Complete documentation

Người dùng giờ có thể dễ dàng tìm kiếm cả theo keywords và username với giao diện trực quan và responsive.