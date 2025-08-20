# Trang Xem SVG - View SVG Page

## 📋 Tổng quan

File `templates/view_svg.html` là trang hiển thị chi tiết một file SVG cụ thể với đầy đủ tính năng xem, tải xuống, xuất ảnh và quay về chỉnh sửa. Trang này được thiết kế để cung cấp trải nghiệm xem SVG hoàn chỉnh với giao diện responsive.

## 🎯 Mục đích

- Hiển thị file SVG với chất lượng cao
- Cung cấp các tính năng tải xuống và chia sẻ
- Xuất ảnh PNG/JPEG với tùy chỉnh tham số
- Quay về trang chỉnh sửa với code TikZ
- Hỗ trợ responsive design cho mobile và desktop
- Tích hợp SEO và Open Graph meta tags

## 🏗️ Cấu trúc Trang

### 1. **Header Section**
```html
<head>
    <title>Xem SVG - {{ display_name }}</title>
    <meta property="og:title" content="TikZ to SVG - {{ display_name }}" />
    <meta property="og:type" content="website" />
    <meta property="og:image" content="{{ request.host_url.rstrip('/') ~ png_url }}" />
    <meta property="og:url" content="{{ request.host_url.rstrip('/') ~ url_for('view_svg', filename=filename) }}" />
    <meta property="og:description" content="Xem và chia sẻ hình TikZ SVG trực tuyến." />
</head>
```

### 2. **Main Content Layout**
```html
<div class="container">
    <h2>{{ display_name }}</h2>
    <div id="view-mode-row">
        <!-- SVG Preview Column -->
        <div class="view-col">
            <div id="view-svg-preview">
                <img id="view-svg-img" src="{{ svg_url }}" alt="Xem trước hình ảnh SVG">
            </div>
            <div id="view-svg-actions">
                <!-- Action buttons -->
            </div>
        </div>
        <!-- Actions Column -->
        <div class="view-col">
            <!-- Back to edit button -->
            <!-- Export section -->
        </div>
    </div>
</div>
```

### 3. **SVG Preview Section**
- **High-quality SVG display** với responsive sizing
- **Action buttons** (Copy Link, Download SVG)
- **Hover effects** và visual feedback

### 4. **Actions Section**
- **Back to Edit button** - Quay về trang chỉnh sửa
- **Export form** - Xuất PNG/JPEG với tùy chỉnh
- **Responsive layout** cho mobile và desktop

## 🎨 CSS Styling

### 1. **Main Container**
```css
.container {
    max-width: 1000px;
    margin: 30px auto;
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    padding: 32px;
}
```

### 2. **View Mode Row Layout**
```css
#view-mode-row {
    display: flex;
    gap: 32px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.view-col {
    flex: 1 1 300px;
    min-width: 280px;
    box-sizing: border-box;
}
```

### 3. **SVG Preview Block**
```css
#view-svg-preview {
    background: #fff;
    border: 1.5px solid #eee;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 320px;
    height: 400px;
    width: 100%;
    box-sizing: border-box;
}

#view-svg-preview img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
    margin: 0 auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
```

### 4. **Action Buttons**
```css
#view-svg-actions {
    margin-top: 16px;
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
}

#view-svg-actions .view-action-btn {
    background: #ffc107;
    color: #212529;
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    text-decoration: none;
    box-shadow: 0 2px 8px rgba(255,193,7,0.2);
    transition: all 0.2s;
}
```

### 5. **Export Section**
```css
.export-section {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    padding: 20px;
    margin-top: 24px;
}

#view-export-form {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
    align-items: start;
    margin-bottom: 16px;
}
```

## 🔧 JavaScript Functionality

### 1. **Copy to Clipboard**
```javascript
function copyToClipboard(text, button, originalText) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            button.textContent = '✅ Đã copy!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
        });
    } else {
        // Fallback cho các trình duyệt cũ
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = 0;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        button.textContent = '✅ Đã copy!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }
}
```

### 2. **Export PNG/JPEG**
```javascript
async function handleExport() {
    const format = document.getElementById('view-export-format').value;
    const widthVal = document.getElementById('view-export-width').value;
    const heightVal = document.getElementById('view-export-height').value;
    const dpiVal = document.getElementById('view-export-dpi').value;
    
    // Validation
    if ((widthVal && widthVal <= 0) || (heightVal && heightVal <= 0) || (dpiVal && dpiVal <= 0)) {
        msg.textContent = 'Width, Height, DPI phải là số dương!';
        return;
    }
    
    // API call
    const res = await fetch('/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            filename: filename,
            fmt: format,
            width: widthVal || undefined,
            height: heightVal || undefined,
            dpi: dpiVal || undefined
        })
    });
    
    // Handle response
    const data = await res.json();
    if (data.url) {
        // Display download link with file info
        msg.innerHTML = `
            <a href="${data.url}" download class="export-download-link">Tải về ${format.toUpperCase()}</a>
            <div style="margin-top: 8px; font-size: 12px; color: #666; text-align: center; font-weight: bold;">
                Dung lượng: ${(data.file_size / 1024).toFixed(1)} KB
                ${data.actual_size ? ` | Kích thước: ${data.actual_size}` : ''}
            </div>
        `;
    } else {
        msg.className = 'error';
        msg.textContent = data.error || 'Lỗi không xác định!';
    }
}
```

### 3. **Back to Edit Functionality**
```javascript
const backToEditBtn = document.getElementById('view-back-to-edit-btn');
if (backToEditBtn) {
    backToEditBtn.onclick = function() {
        requireLogin(() => {
            // Lấy code TikZ đã lưu
            let currentCode = window.currentViewTikzCode
                            || localStorage.getItem('tikz_code_for_edit')
                            || {{ tikz_code|default("")|tojson|safe }};
            
            // Lưu code vào localStorage để trang chủ có thể đọc
            localStorage.setItem('tikz_code_for_compile', currentCode);
            
            // Chuyển về trang chủ
            window.location.href = '/';
        });
    };
}
```

### 4. **Authentication Check**
```javascript
function requireLogin(callback) {
    if (isLoggedIn) {
        callback();
    } else {
        showLoginModal();
    }
}

function showLoginModal() {
    document.getElementById('login-modal').style.display = 'flex';
}
```

## 📱 Responsive Design

### 1. **Desktop Layout (1040px+)**
- **2-column layout**: SVG preview + Actions
- **Full-size SVG display** với action buttons
- **Export form** với grid layout

### 2. **Tablet Layout (601px - 1040px)**
```css
@media (min-width: 601px) and (max-width: 1040px) {
    #view-mode-row {
        display: flex;
        flex-wrap: nowrap;
        gap: 24px;
    }
    
    .view-col:first-child {
        flex: 1 1 auto;
        min-width: 300px;
    }
    
    .view-col:last-child {
        flex: 0 0 330px;
        max-width: 330px;
    }
}
```

### 3. **Mobile Layout (≤600px)**
```css
@media (max-width: 600px) {
    #view-mode-row {
        flex-direction: column;
        gap: 24px;
    }
    
    #view-export-form {
        grid-template-columns: 1fr;
        gap: 16px;
    }
    
    #view-svg-actions {
        flex-direction: column;
        gap: 10px;
    }
    
    #view-svg-actions .view-action-btn,
    #view-export-form .export-btn {
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
    }
}
```

## 🔗 Integration

### 1. **Backend Integration**
- **Route**: `/view_svg/<filename>`
- **Database query** để lấy thông tin SVG
- **File serving** từ static directory
- **Export API** cho PNG/JPEG conversion

### 2. **Frontend Integration**
- **Navigation** từ file cards
- **CodeMirror integration** cho TikZ code
- **LocalStorage** để truyền code TikZ
- **Authentication** checks

### 3. **SEO & Social Media**
- **Open Graph meta tags** cho Facebook sharing
- **Twitter Card** support
- **Structured data** cho search engines
- **Canonical URLs**

## 📊 Data Flow

### 1. **Page Load Process**
```
URL Request → Backend Route → Database Query → File Validation → Template Rendering
```

### 2. **Export Process**
```
User Input → Form Validation → API Call → Image Processing → Download Link
```

### 3. **Back to Edit Process**
```
Button Click → Authentication Check → Code Retrieval → LocalStorage → Navigation
```

## 🎯 User Experience Features

### 1. **SVG Display**
- ✅ High-quality SVG rendering
- ✅ Responsive sizing
- ✅ Proper aspect ratio maintenance
- ✅ Loading states

### 2. **Action Buttons**
- ✅ Copy link với feedback
- ✅ Download SVG trực tiếp
- ✅ Visual feedback cho tất cả actions
- ✅ Hover effects

### 3. **Export Functionality**
- ✅ PNG/JPEG export
- ✅ Customizable parameters (DPI, width, height)
- ✅ File size information
- ✅ Error handling

### 4. **Navigation**
- ✅ Back to edit với code preservation
- ✅ Authentication modal
- ✅ Responsive navigation

## 🔒 Security Features

### 1. **Authentication**
- Kiểm tra trạng thái đăng nhập
- Modal đăng nhập cho features cần auth
- Secure API calls

### 2. **Input Validation**
- Validate export parameters
- Sanitize file paths
- Prevent XSS attacks

### 3. **File Access Control**
- Validate file existence
- Check file permissions
- Secure file serving

## 🚀 Performance Optimizations

### 1. **Image Optimization**
- SVG compression
- Lazy loading cho large files
- Caching strategies

### 2. **Code Optimization**
- Minified CSS/JS
- Efficient DOM manipulation
- Optimized API calls

### 3. **Caching**
- Browser caching cho static assets
- API response caching
- LocalStorage cho user preferences

## 🐛 Error Handling

### 1. **File Not Found**
```html
<div class="error-message">
    <h3>File không tồn tại</h3>
    <p>File SVG bạn đang tìm kiếm không tồn tại hoặc đã bị xóa.</p>
    <a href="/" class="btn btn-primary">Về trang chủ</a>
</div>
```

### 2. **Export Errors**
```javascript
if (data.error) {
    msg.className = 'error';
    msg.textContent = data.error || 'Lỗi không xác định!';
    
    if (data.estimated_size_mb) {
        const small = document.createElement('small');
        small.style.color = '#666';
        small.textContent = `Dung lượng ước tính: ${data.estimated_size_mb}`;
        msg.appendChild(document.createElement('br'));
        msg.appendChild(small);
    }
}
```

### 3. **Network Errors**
- Graceful fallback cho offline mode
- Retry mechanisms
- User-friendly error messages

## 📈 Analytics & Monitoring

### 1. **User Analytics**
- Page view tracking
- Export usage statistics
- User interaction patterns
- Performance metrics

### 2. **Error Monitoring**
- JavaScript error tracking
- API error logging
- User experience monitoring
- Performance bottlenecks

## 🔄 Maintenance

### 1. **Code Organization**
- Modular CSS classes
- Reusable JavaScript functions
- Consistent naming conventions
- Clear separation of concerns

### 2. **Updates**
- Regular dependency updates
- Security patches
- Feature enhancements
- Performance improvements

## 📝 Future Enhancements

### 1. **Advanced Features**
- SVG editing capabilities
- Real-time collaboration
- Version history
- Advanced export options

### 2. **UI/UX Improvements**
- Dark mode support
- Customizable themes
- Advanced animations
- Accessibility enhancements

### 3. **Performance**
- Progressive loading
- Service worker integration
- Advanced caching
- CDN optimization

## 🎨 Visual Design

### 1. **Color Scheme**
- **Primary**: #1976d2 (Blue)
- **Secondary**: #ffc107 (Yellow)
- **Success**: #28a745 (Green)
- **Info**: #17a2b8 (Cyan)
- **Background**: #f5f5f5 (Light Gray)

### 2. **Typography**
- **Font Family**: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- **Headings**: Bold weights
- **Body Text**: Regular weights
- **Buttons**: Semi-bold weights

### 3. **Spacing & Layout**
- **Container**: max-width 1000px
- **Padding**: 32px container, 16px sections
- **Gap**: 32px between columns, 12px between elements
- **Border Radius**: 8px-10px for cards, 6px for buttons

---

*Tài liệu này mô tả trang view_svg.html được thiết kế để cung cấp trải nghiệm xem SVG hoàn chỉnh với đầy đủ tính năng tương tác, xuất ảnh và navigation. Trang được tối ưu cho cả desktop và mobile với responsive design và performance cao.*
