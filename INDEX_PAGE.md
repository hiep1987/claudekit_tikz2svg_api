# Trang Chủ - Index Page

## 📋 Tổng quan

File `templates/index.html` là trang chủ chính của ứng dụng TikZ to SVG, cung cấp giao diện hoàn chỉnh để chuyển đổi code TikZ thành SVG với đầy đủ tính năng tương tác, quản lý file và tìm kiếm.

## 🎯 Mục đích

- Cung cấp giao diện chuyển đổi TikZ sang SVG/PNG/JPEG
- Hiển thị danh sách file SVG đã lưu với tính năng tương tác
- Tìm kiếm file SVG theo từ khóa
- Quản lý profile và authentication
- Responsive design cho mobile và desktop
- Real-time preview và live updates

## 🏗️ Cấu trúc Trang

### 1. **Header Section**
```html
<head>
    <title>TikZ to SVG</title>
    <!-- Meta tags, CSS libraries, custom styles -->
    <!-- CodeMirror, Bootstrap, FontAwesome, Highlight.js -->
</head>
```

### 2. **Navigation Bar**
```html
{% include '_navbar.html' %}
<!-- Responsive navigation với user authentication -->
```

### 3. **Search Bar Section**
```html
<div class="container">
    <div class="search-container">
        <h3 class="search-title">Tìm kiếm ảnh SVG</h3>
        <div class="group">
            <!-- Search input với real-time suggestions -->
        </div>
    </div>
</div>
```

### 4. **Input-Preview Section (Block 2)**
```html
<div class="input-preview-section container">
    <h2>Chuyển đổi TikZ sang SVG/PNG/JPEG</h2>
    <div class="table-scroll-x">
        <div class="table-content">
            <div class="col">
                <!-- TikZ Code Editor với CodeMirror -->
                <form id="tikz-form">
                    <textarea id="code">...</textarea>
                    <div id="compile-save-row">
                        <button id="compile-btn">Biên dịch</button>
                        <button id="save-server-btn">💾 Lưu server</button>
                    </div>
                </form>
            </div>
            <div class="col">
                <!-- SVG Preview -->
            </div>
        </div>
    </div>
</div>
```

### 5. **Result Tools Section**
```html
<div id="result-tools-section">
    <div class="export-section">
        <!-- PNG/JPEG Export Form -->
    </div>
    <div class="code-section">
        <!-- SVG Code Display -->
    </div>
</div>
```

### 6. **Files Section (Block 3)**
```html
<div class="files-section-container">
    <h3>📁 Files đã lưu</h3>
    <div id="files-container" class="files-grid">
        <!-- Dynamic file cards -->
    </div>
</div>
```

## 🎨 CSS Styling

### 1. **Responsive Design**
```css
/* Mobile-first approach */
@media (max-width: 768px) {
    .table-scroll-x {
        min-width: calc(100vw - 40px);
        overflow-x: auto;
    }
}

@media (max-width: 480px) {
    .files-grid {
        grid-template-columns: 1fr;
    }
}
```

### 2. **File Card Styling**
```css
.file-card {
    position: relative;
    min-height: 260px;
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    transition: transform 0.2s ease;
}

.file-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
```

### 3. **Action Buttons**
```css
.Btn {
    display: flex;
    align-items: center;
    width: 35px;
    height: 35px;
    border-radius: 50%;
    background: linear-gradient(-50deg, rgb(39, 107, 255), rgb(112, 186, 255));
    transition: all 0.3s ease;
}

.Btn:hover {
    width: 140px;
    border-radius: 20px;
}
```

## ⚡ JavaScript Functionality

### 1. **Unified File Card System**
```javascript
// Tất cả file card functionality được consolidate trong file_card.js v1.2
// Bao gồm: search_results.js + file_card.js cũ
<script src="{{ url_for('static', filename='js/file_card.js', v='1.2') }}"></script>
```

**Features included:**
- Action buttons (download, share, copy, view code)
- Like/unlike functionality
- Touch events cho mobile
- Login modal integration
- CodeMirror initialization cho TikZ code
- Clipboard API với fallback

### 2. **CodeMirror Integration**
```javascript
function initCodeMirrorAndBindings() {
    cm = CodeMirror.fromTextArea(tikzCode, {
        mode: 'stex',
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        placeholder: 'Nhập code TikZ tại đây...'
    });
}
```

### 3. **Real-time Preview**
```javascript
async function updateInputPreview(tikzCode) {
    // AJAX request để cập nhật preview real-time
    const response = await fetch('/', {
        method: 'POST',
        body: `code=${encodeURIComponent(tikzCode)}`
    });
}
```

### 4. **File Management**
```javascript
async function loadSvgFiles() {
    const apiEndpoint = window.isLoggedIn ? '/api/files' : '/api/public/files';
    const response = await fetch(apiEndpoint);
    const data = await response.json();
    // Render file cards với unified functionality
}
```

### 5. **Search Functionality**
```javascript
function initializeSearch() {
    const searchInput = document.getElementById('main-search-input');
    searchInput.addEventListener('input', function() {
        // Fetch keyword suggestions
        fetch(`/api/keywords/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                // Display suggestions
            });
    });
}
```

### 6. **Data-Action Pattern**
```javascript
// Unified button handling với data-action attributes
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.Btn[data-action]');
    if (!btn) return;
    
    const action = btn.dataset.action;
    switch (action) {
        case 'download-image':
            // Handle download
            break;
        case 'share-facebook':
            // Handle Facebook share
            break;
        case 'copy-link':
            // Handle copy link
            break;
        case 'toggle-code':
            // Handle view TikZ code
            break;
    }
});
```

## 🔧 Tính năng Chi tiết

### 1. **TikZ Compilation**
- Real-time syntax highlighting với CodeMirror
- AJAX compilation không reload trang
- Error handling với detailed logs
- Auto-save functionality

### 2. **File Export**
- PNG/JPEG export với tùy chỉnh DPI, width, height
- SVG code display với syntax highlighting
- Copy functionality cho tất cả formats

### 3. **File Management (Unified)**
- Grid layout responsive
- Like/unlike functionality (consolidated)
- Share to Facebook (consolidated)
- Copy direct links (consolidated)
- View TikZ code với CodeMirror (consolidated)
- Delete files (owner only)

### 4. **Search & Discovery**
- Real-time keyword suggestions
- Search results page navigation
- Keyword-based file discovery

### 5. **User Authentication**
- Google OAuth integration
- Session management
- Login modal cho protected features
- Cross-tab login status sync

### 6. **Mobile Optimization**
- Touch-friendly interface
- 2-tap button activation (consolidated)
- Horizontal scroll support
- Responsive grid layouts
- Mobile-specific UI adjustments

## 🔄 Real-time Features

### 1. **Live Updates**
```javascript
function startFilesPolling() {
    pollingInterval = setInterval(function() {
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                // Compare with current files
                if (hasNewFiles || hasUpdates) {
                    loadFiles();
                }
            });
    }, 15000); // 15 seconds
}
```

### 2. **Login Status Polling**
```javascript
setInterval(() => {
    refreshLoginStatusAndLoadFiles();
}, 30000); // 30 seconds
```

### 3. **Cross-tab Synchronization**
```javascript
window.addEventListener('storage', (e) => {
    if (e.key === 'login_status') {
        refreshLoginStatusAndLoadFiles();
    }
});
```

## 📱 Mobile Support

### 1. **Touch Detection**
```javascript
if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
    document.documentElement.classList.add('is-touch');
}
```

### 2. **Mobile-specific Styling**
```css
@media (hover: none), (pointer: coarse) {
    .action-toggle-btn {
        display: block;
    }
    .file-img-container:hover + .file-action-container {
        display: none !important;
    }
}
```

### 3. **Horizontal Scroll**
```css
.table-scroll-x {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
}
```

## 🔒 Security Features

### 1. **Authentication Checks**
```javascript
function toggleTikzCode(btn) {
    if (!window.appState.loggedIn) {
        showLoginModal();
        return;
    }
    // Proceed with action
}
```

### 2. **CSRF Protection**
- Form tokens cho tất cả POST requests
- Session-based authentication
- Secure cookie handling

### 3. **Input Validation**
```javascript
function cleanControlChars(str) {
    return str.replace(/[^\x09\x0A\x20-\x7E\xA0-\uFFFF]/g, '');
}
```

## 🎯 Performance Optimization

### 1. **Lazy Loading**
- CodeMirror instances chỉ được tạo khi cần
- File cards được render on-demand
- Image lazy loading

### 2. **Debouncing**
```javascript
let inputPreviewTimer;
cm.on('change', function() {
    clearTimeout(inputPreviewTimer);
    inputPreviewTimer = setTimeout(() => {
        updateInputPreview(cm.getValue());
    }, 1000);
});
```

### 3. **Caching**
- LocalStorage cho user preferences
- Session caching cho file data
- Browser caching cho static assets

## 🔧 Error Handling

### 1. **Network Errors**
```javascript
.catch(error => {
    console.error('Error loading files:', error);
    container.innerHTML = `
        <div class="no-files">
            <p>Không thể tải danh sách files. Vui lòng thử lại sau.</p>
        </div>
    `;
});
```

### 2. **Compilation Errors**
```javascript
function displayCompileError(message, fullLog) {
    const section = document.createElement('div');
    section.className = 'result-section';
    section.innerHTML = `<div class="error">${message}</div>`;
    // Display with detailed logs
}
```

### 3. **Fallback Mechanisms**
```javascript
function fallbackCopyToClipboard(url, btn) {
    const textArea = document.createElement('textarea');
    textArea.value = url;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
}
```

## 📊 Analytics & Monitoring

### 1. **User Interaction Tracking**
- Button click events
- File view/download counts
- Search query analytics
- Error rate monitoring

### 2. **Performance Metrics**
- Page load times
- API response times
- Real-time update frequency
- Mobile vs desktop usage

## 🔄 Integration Points

### 1. **Backend APIs**
- `/api/files` - Private files
- `/api/public/files` - Public files
- `/api/keywords/search` - Keyword suggestions
- `/like_svg` - Like/unlike functionality
- `/save_svg` - Save file with keywords

### 2. **External Services**
- Google OAuth
- Facebook Share API
- CodeMirror CDN
- Bootstrap CDN
- FontAwesome CDN

### 3. **Database Integration**
- MySQL cho file storage
- Session management
- User authentication
- Keyword indexing

## 🚀 Deployment Considerations

### 1. **Static Assets**
- CDN optimization
- Asset compression
- Cache headers
- Version control

### 2. **Security Headers**
- CSP (Content Security Policy)
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options
- X-Content-Type-Options

### 3. **Monitoring**
- Error logging
- Performance monitoring
- User analytics
- Server health checks

## 🔄 Recent Updates (Latest)

### **JavaScript Consolidation (v1.2)**
- **Merged:** `search_results.js` vào `file_card.js` v1.2
- **Deleted:** `static/js/search_results.js` (83 lines)
- **Fixed:** ReferenceError `updateButtonStates is not defined`
- **Removed:** Duplicate functions và old debug code
- **Fixed:** JavaScript loading order issues
- **Reduced:** `index.html` từ 2,301 → 1,879 lines (-422 lines)

### **Unified File Card System**
- **Consolidated:** Tất cả file card functionality vào `file_card.js`
- **Standardized:** Data-action pattern cho buttons
- **Improved:** Touch events và mobile support
- **Enhanced:** Login modal integration
- **Optimized:** CodeMirror initialization

### **Performance Improvements**
- **Reduced:** Total codebase by 1,006 lines
- **Eliminated:** Function conflicts và duplicate code
- **Improved:** JavaScript loading order
- **Enhanced:** Error handling và fallback mechanisms

---

*Tài liệu này mô tả trang index.html - trang chủ chính của ứng dụng TikZ to SVG với đầy đủ tính năng chuyển đổi, quản lý file, tìm kiếm và tương tác xã hội. Trang được thiết kế responsive và tối ưu cho cả desktop và mobile với real-time updates và cross-platform synchronization. Gần đây đã được cập nhật với unified JavaScript system để cải thiện maintainability và performance.*
