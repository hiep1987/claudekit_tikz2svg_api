# Trang Kết quả Tìm kiếm - Search Results Page

## 📋 Tổng quan

File `templates/search_results.html` là trang hiển thị kết quả tìm kiếm SVG images dựa trên từ khóa. Trang này được tạo để cung cấp trải nghiệm tìm kiếm hoàn chỉnh với giao diện giống hệt trang chủ.

## 🎯 Mục đích

- Hiển thị kết quả tìm kiếm SVG images theo từ khóa
- Cung cấp giao diện nhất quán với trang chủ
- Cho phép tương tác với các file SVG (like, share, copy, view code)
- Hỗ trợ responsive design cho mobile và desktop

## 🏗️ Cấu trúc Trang

### 1. **Header Section**
```html
<!-- Search Results Header -->
<div class="container" style="margin-top: 20px;">
    <div class="search-results-header">
        <h1>🔍 Kết quả tìm kiếm</h1>
        <div class="search-query">Từ khóa: "{{ search_query }}"</div>
        <div style="margin-top: 10px; font-size: 0.9rem;">
            Tìm thấy {{ results_count }} kết quả
        </div>
        <a href="/" class="back-to-home">
            <i class="fas fa-arrow-left"></i> Về trang chủ
        </a>
    </div>
</div>
```

### 2. **Search Results Section**
```html
<!-- Search Results Section -->
<div class="container files-section" data-is-owner="{{ 'true' if logged_in else 'false' }}">
    <div id="search-results-container" class="files-grid">
        <!-- File cards rendered here -->
    </div>
</div>
```

### 3. **File Card Structure**
Mỗi file card bao gồm:
- **User Info**: Username và timestamp
- **SVG Preview**: Hình ảnh SVG
- **Like Button**: Nút like với counter
- **Action Menu**: Các nút tương tác (hover/click)
- **TikZ Code Section**: Code TikZ với CodeMirror editor

## 🎨 CSS Styling

### 1. **Search Results Header**
```css
.search-results-header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
}
```

### 2. **File Cards**
```css
.file-card {
    position: relative;
    min-height: 260px;
    display: flex;
    flex-direction: column;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    transition: transform 0.2s ease;
}
```

### 3. **Action Buttons**
```css
.Btn {
    display: flex;
    align-items: center;
    width: 35px;
    height: 35px;
    border: none;
    border-radius: 50%;
    background: linear-gradient(-50deg, rgb(39, 107, 255), rgb(112, 186, 255), rgb(39, 107, 255));
    transition: all 0.3s ease;
}
```

### 4. **TikZ Code Section**
```css
.tikz-code-block {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    padding: 10px;
}

.tikz-code-block .CodeMirror {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #ddd;
    border-radius: 4px;
}
```

## 🔧 JavaScript Functionality

### 1. **Like Button System**
```javascript
function initializeSearchResults() {
    // Initialize like buttons if user is logged in
    if ({{ 'true' if logged_in else 'false' }}) {
        document.querySelectorAll('input[id^="heart-"]').forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                // Handle like/unlike functionality
            });
        });
    }
}
```

### 2. **Action Button Handlers**
```javascript
function initializeActionButtons() {
    // Facebook share buttons
    document.querySelectorAll('.fb-share-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            // Handle Facebook sharing
        });
    });
    
    // Copy link buttons
    document.querySelectorAll('.file-copy-link-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            // Handle link copying
        });
    });
}
```

### 3. **TikZ Code Toggle**
```javascript
function toggleTikzCode(btn) {
    const card = btn.closest('.file-card');
    const codeBlock = card.querySelector('.tikz-code-block');
    
    if (codeBlock.style.display === 'none') {
        codeBlock.style.display = 'block';
        // Initialize CodeMirror when showing
        initializeCodeMirror(codeBlock);
    } else {
        codeBlock.style.display = 'none';
    }
}
```

### 4. **Copy TikZ Code**
```javascript
function copyTikzCode(btn) {
    const card = btn.closest('.file-card');
    const textarea = card.querySelector('.tikz-cm');
    
    // Get code from CodeMirror or textarea
    let code = textarea.CodeMirror ? textarea.CodeMirror.getValue() : textarea.value;
    
    // Copy to clipboard with feedback
    navigator.clipboard.writeText(code).then(function() {
        btn.textContent = '✅ Đã copy!';
        setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000);
    });
}
```

## 📱 Responsive Design

### 1. **Desktop Layout**
- File cards in grid layout
- Hover effects for action buttons
- Full CodeMirror editor for TikZ code

### 2. **Mobile Layout**
- Single column layout
- Touch-friendly buttons
- 2-tap system for action buttons
- Scrollable CodeMirror

### 3. **Breakpoints**
```css
@media (max-width: 768px) {
    .files-grid {
        grid-template-columns: 1fr;
    }
    
    .search-results-header h1 {
        font-size: 1.5rem;
    }
}
```

## 🔗 Integration

### 1. **Backend Integration**
- Route: `/search?q=keyword`
- Database query for keyword matching
- User authentication status
- Like/unlike functionality

### 2. **Frontend Integration**
- Navigation from search bar
- Consistent styling with index page
- Shared JavaScript functions
- CodeMirror integration

## 📊 Data Flow

### 1. **Search Process**
```
User Input → Search Bar → API Call → Database Query → Results → Template Rendering
```

### 2. **File Card Data**
```python
{
    'id': file_id,
    'filename': filename,
    'url': f"/static/{filename}",
    'creator_username': username,
    'creator_id': user_id,
    'created_time_vn': formatted_time,
    'like_count': like_count,
    'is_liked_by_current_user': bool,
    'tikz_code': tikz_code
}
```

## 🎯 User Experience Features

### 1. **Search Results Header**
- ✅ Hiển thị từ khóa tìm kiếm
- ✅ Số lượng kết quả tìm thấy
- ✅ Nút quay về trang chủ
- ✅ Gradient background đẹp mắt

### 2. **File Cards**
- ✅ Thông tin người tạo
- ✅ Preview hình ảnh SVG
- ✅ Like button với counter
- ✅ Action menu với hover effects

### 3. **Interactive Features**
- ✅ Like/unlike SVG images
- ✅ Share on Facebook
- ✅ Copy direct link
- ✅ View TikZ code with syntax highlighting
- ✅ Copy TikZ code with feedback

### 4. **CodeMirror Integration**
- ✅ Syntax highlighting cho TikZ
- ✅ Line numbers
- ✅ Material theme
- ✅ Responsive design
- ✅ Copy functionality

## 🔒 Security Features

### 1. **Authentication**
- Kiểm tra trạng thái đăng nhập
- Hiển thị/ẩn features dựa trên quyền
- Secure API calls

### 2. **Input Validation**
- Sanitize search query
- Validate file IDs
- Prevent XSS attacks

## 🚀 Performance Optimizations

### 1. **Lazy Loading**
- CodeMirror chỉ khởi tạo khi cần
- Images load on demand
- Efficient DOM manipulation

### 2. **Caching**
- CodeMirror instances cached
- Event listeners optimized
- Minimal re-renders

## 🐛 Error Handling

### 1. **No Results**
```html
<div class="no-files">
    <div class="no-files-icon">🔍</div>
    <h4>Không tìm thấy kết quả</h4>
    <p>Không có ảnh SVG nào khớp với từ khóa "{{ search_query }}"</p>
</div>
```

### 2. **API Errors**
- Graceful fallback for failed requests
- User-friendly error messages
- Console logging for debugging

## 📈 Analytics & Monitoring

### 1. **Search Analytics**
- Track search queries
- Monitor result counts
- User engagement metrics

### 2. **Performance Monitoring**
- Page load times
- API response times
- User interaction tracking

## 🔄 Maintenance

### 1. **Code Organization**
- Modular CSS classes
- Reusable JavaScript functions
- Consistent naming conventions

### 2. **Updates**
- Regular dependency updates
- Security patches
- Feature enhancements

## 📝 Future Enhancements

### 1. **Advanced Search**
- Multiple keyword search
- Filter by date range
- Sort by popularity/date

### 2. **Enhanced UI**
- Infinite scroll
- Advanced filtering
- Search suggestions

### 3. **Performance**
- Image optimization
- CDN integration
- Progressive loading

---

*Tài liệu này mô tả trang search_results.html được tạo để hỗ trợ tính năng tìm kiếm SVG images theo từ khóa. Trang được thiết kế để cung cấp trải nghiệm nhất quán với trang chủ và hỗ trợ đầy đủ các tính năng tương tác.*
