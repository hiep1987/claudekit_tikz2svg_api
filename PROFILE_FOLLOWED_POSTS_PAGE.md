# Trang Bài đăng Theo dõi - Profile Followed Posts Page

## 📋 Tổng quan

File `templates/profile_followed_posts.html` là trang hiển thị các bài đăng SVG từ những người dùng mà người dùng hiện tại đang theo dõi. Trang này cung cấp tính năng feed xã hội với đầy đủ tính năng tương tác như like, share, copy link và xem code TikZ.

## 🎯 Mục đích

- Hiển thị feed các bài đăng SVG từ người dùng được follow
- Cung cấp tính năng tương tác xã hội (like, share, copy link)
- Xem và copy code TikZ của các bài đăng
- Real-time updates thông qua polling
- Responsive design cho mobile và desktop
- Tích hợp authentication và authorization

## 🏗️ Cấu trúc Trang

### 1. **Header Section**
```html
<head>
    <title>Bài đăng theo dõi - TikZ to SVG</title>
    <!-- Global JavaScript variables -->
    <script>
        window.isLoggedIn = {{ 'true' if current_user.is_authenticated else 'false' }};
        window.activeFeedbackCount = 0;
        window.isOwner = {{ 'true' if is_owner else 'false' }};
    </script>
</head>
```

### 2. **Navigation Bar**
```html
{% include '_navbar.html' %}
```
- Tích hợp navbar chung với các trang khác
- Hiển thị trạng thái đăng nhập và thông tin người dùng

### 3. **Main Content Section**
```html
<div class="container">
    <section class="followed-posts-section" data-is-owner="{{ 'true' if is_owner else 'false' }}">
        <h3>📰 Bài đăng từ người bạn theo dõi</h3>
        <div id="followed-posts-container" class="files-grid">
            <!-- Loading spinner và content -->
        </div>
    </section>
</div>
```

### 4. **Logout Modal**
```html
{% if user_email %}
<div id="logout-modal" style="display:none;">
    <!-- Modal xác nhận đăng xuất -->
</div>
{% endif %}
```

## 🎨 CSS Styling

### 1. **Tailwind-like Utility Classes**
```css
/* Production-ready utility classes */
.w-full { width: 100%; }
.max-w-7xl { max-width: 80rem; }
.mx-auto { margin-left: auto; margin-right: auto; }
.bg-white\/80 { background-color: rgba(255, 255, 255, 0.8); }
.backdrop-blur { backdrop-filter: blur(8px); }
```

### 2. **File Card Styling**
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

.file-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
```

### 3. **Action Menu Styling**
```css
.file-action-container {
    display: none;
    opacity: 0;
    pointer-events: none;
    transform: translateX(-10px);
    transition: opacity 0.3s, transform 0.3s;
    position: absolute;
    left: 12px;
    top: 60px;
    z-index: 300;
}
```

### 4. **Like Button Styling**
```css
.like-button {
    position: relative;
    cursor: pointer;
    display: flex;
    align-items: center;
    height: 32px;
    width: 90px;
    border-radius: 8px;
    border: none;
    background-color: #2d2d2d;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    padding: 0 8px;
}
```

## 🔧 JavaScript Functionality

### 1. **Main Initialization**
```javascript
document.addEventListener('DOMContentLoaded', function () {
    // Touch device detection
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        document.documentElement.classList.add('is-touch');
    }
    
    // Load followed posts
    if (followedSection && followedSection.dataset.isOwner === 'true') {
        loadFollowedPosts();
        startFollowedPostsPolling();
    }
    
    // Initialize touch events
    initializeTouchBtnEvents();
    
    // Initialize CodeMirror
    if (typeof CodeMirror !== 'undefined') {
        initializeCodeMirror();
    }
});
```

### 2. **Load Followed Posts**
```javascript
function loadFollowedPosts() {
    fetch('/api/followed_posts')
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    // User not logged in
                    container.innerHTML = `
                        <div class="no-followed-posts">
                            <div class="no-followed-posts-icon">🔒</div>
                            <h4>Chưa đăng nhập</h4>
                            <p>Vui lòng đăng nhập để xem bài đăng từ người bạn theo dõi</p>
                        </div>
                    `;
                    return;
                }
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(posts => {
            // Render posts
            const postsHTML = posts.map(post => `
                <div class="file-card followed-post-card" data-post-id="${post.id}">
                    <!-- Post content -->
                </div>
            `).join('');
            
            container.innerHTML = postsHTML;
            initializeFollowedPostLikeButtons();
        });
}
```

### 3. **Touch Events for Mobile**
```javascript
function initializeTouchBtnEvents() {
    if (!document.documentElement.classList.contains('is-touch')) return;

    document.addEventListener('click', function(e) {
        // Handle action toggle button
        const actionToggleBtn = e.target.closest('.action-toggle-btn');
        if (actionToggleBtn) {
            const card = actionToggleBtn.closest('.file-card');
            if (card) {
                // Close other cards
                document.querySelectorAll('.file-card.active').forEach(other => {
                    if (other !== card) other.classList.remove('active');
                });
                // Toggle current card
                card.classList.toggle('active');
            }
            return;
        }
        
        // Handle action buttons with 2-tap logic
        const btn = e.target.closest('.Btn');
        if (!btn) return;
        
        // 2-tap logic implementation
        // ...
    }, true);
}
```

### 4. **Real-time Polling**
```javascript
function startFollowedPostsPolling() {
    const pollInterval = 15000; // 15 seconds
    
    setInterval(function() {
        fetch('/api/followed_posts')
            .then(response => response.json())
            .then(posts => {
                // Check for updates
                const hasNewPosts = posts.length !== currentPosts.length;
                const hasUpdates = posts.some((post, index) => {
                    const currentPost = currentPosts[index];
                    return !currentPost || 
                           currentPost.like_count !== post.like_count ||
                           currentPost.is_liked_by_current_user !== post.is_liked_by_current_user;
                });
                
                if (hasNewPosts || hasUpdates) {
                    loadFollowedPosts();
                }
            });
    }, pollInterval);
}
```

### 5. **Like Functionality**
```javascript
function initializeFollowedPostLikeButtons() {
    if (!window.isLoggedIn) return;
    
    document.querySelectorAll('input[id^="followed-heart-"]').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const fileId = this.id.replace('followed-heart-', '');
            const isLiked = this.checked;
            
            fetch('/like_svg', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    svg_id: fileId,
                    action: isLiked ? 'like' : 'unlike'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI
                    const newCount = data.like_count;
                    currentNumber.textContent = newCount;
                    moveNumber.textContent = newCount;
                    this.checked = data.is_liked;
                } else {
                    this.checked = !isLiked;
                }
            });
        });
    });
}
```

### 6. **CodeMirror Integration**
```javascript
function toggleTikzCode(btn) {
    const card = btn.closest('.file-card');
    const codeBlock = card.querySelector('.tikz-code-block');
    const textDiv = btn.querySelector('.text');
    
    if (codeBlock.style.display === 'none' || !codeBlock.style.display) {
        codeBlock.style.display = 'block';
        textDiv.textContent = 'Ẩn code';
        
        // Initialize CodeMirror
        setTimeout(() => {
            const textarea = codeBlock.querySelector('.tikz-cm');
            
            if (textarea && !textarea.CodeMirror) {
                const cmInstance = CodeMirror.fromTextArea(textarea, {
                    mode: 'stex',
                    theme: 'material',
                    lineNumbers: true,
                    readOnly: true,
                    lineWrapping: true,
                    foldGutter: true,
                    gutters: ['CodeMirror-linenumbers'],
                    viewportMargin: Infinity
                });
                
                setTimeout(() => cmInstance.refresh(), 100);
            }
        }, 50);
    } else {
        codeBlock.style.display = 'none';
        textDiv.textContent = 'Xem Code';
    }
}
```

## 📱 Responsive Design

### 1. **Mobile Breakpoints**
```css
@media (max-width: 768px) {
    .container {
        padding: 20px;
    }
    
    /* Ensure white text for mobile hover states */
    .file-card.active .file-action-container .Btn.individual-active .text,
    .file-card.active .file-action-container .Btn.ready-to-execute .text {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
        opacity: 1 !important;
    }
}
```

### 2. **Touch Device Detection**
```javascript
if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
    document.documentElement.classList.add('is-touch');
}
```

### 3. **Mobile Action Menu**
```css
@media (hover: none), (pointer: coarse) {
    .action-toggle-btn {
        display: block;
    }
    
    .file-card.active .file-action-container {
        display: block !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        transform: translateX(0) !important;
    }
}
```

## 🔐 Authentication & Authorization

### 1. **Login State Management**
```javascript
window.isLoggedIn = {{ 'true' if current_user.is_authenticated else 'false' }};
window.isOwner = {{ 'true' if is_owner else 'false' }};
```

### 2. **Protected Features**
- **Like functionality**: Chỉ hoạt động khi đã đăng nhập
- **View TikZ code**: Chỉ hiển thị khi đã đăng nhập
- **Real-time updates**: Chỉ hoạt động khi đã đăng nhập

### 3. **Login Modal**
```javascript
function showLoginModal() {
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
        loginModal.style.display = 'flex';
    } else {
        window.location.href = '/login/google';
    }
}
```

## 🔄 Real-time Features

### 1. **Polling System**
- **Followed Posts Polling**: 15 giây/lần
- **Like Count Polling**: 10 giây/lần
- **Real-time UI Updates**: Tự động cập nhật khi có thay đổi

### 2. **State Management**
```javascript
window.activeFeedbackCount = 0; // Prevent polling during feedback
let currentPosts = []; // Store current posts for comparison
```

### 3. **Update Detection**
```javascript
const hasNewPosts = posts.length !== currentPosts.length;
const hasUpdates = posts.some((post, index) => {
    const currentPost = currentPosts[index];
    return !currentPost || 
           currentPost.like_count !== post.like_count ||
           currentPost.is_liked_by_current_user !== post.is_liked_by_current_user;
});
```

## 📊 Data Flow

### 1. **API Endpoints**
- `/api/followed_posts`: Lấy danh sách bài đăng từ người follow
- `/api/like_counts`: Cập nhật số lượng like real-time
- `/like_svg`: Thực hiện like/unlike

### 2. **Data Structure**
```javascript
{
    id: "post_id",
    filename: "filename.svg",
    tikz_code: "TikZ code content",
    creator_id: "user_id",
    creator_username: "username",
    created_time_vn: "formatted_time",
    like_count: 5,
    is_liked_by_current_user: true,
    url: "static_url"
}
```

### 3. **Error Handling**
```javascript
.catch(error => {
    console.error('Error loading followed posts:', error);
    container.innerHTML = `
        <div class="no-followed-posts">
            <div class="no-followed-posts-icon">❌</div>
            <h4>Lỗi tải dữ liệu</h4>
            <p>Có lỗi xảy ra khi tải bài đăng. Vui lòng thử lại sau.</p>
        </div>
    `;
});
```

## 🎯 User Experience Features

### 1. **Loading States**
- Loading spinner khi tải dữ liệu
- Skeleton loading cho file cards
- Smooth transitions

### 2. **Feedback Systems**
- Visual feedback cho like actions
- Copy success messages
- Error notifications

### 3. **Accessibility**
- ARIA labels cho buttons
- Keyboard navigation support
- Screen reader friendly

### 4. **Performance Optimizations**
- Lazy loading cho images
- Debounced search
- Efficient DOM updates

## 🔧 Technical Implementation

### 1. **Event Delegation**
```javascript
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.Btn');
    if (!btn) return;
    
    // Handle button clicks
}, true);
```

### 2. **Memory Management**
```javascript
// Cleanup intervals
function stopFollowedPostsPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}
```

### 3. **Error Boundaries**
```javascript
try {
    // Risky operation
} catch (error) {
    console.error('Error:', error);
    // Fallback behavior
}
```

## 📈 Analytics & Monitoring

### 1. **User Engagement**
- Track like interactions
- Monitor post views
- Analyze user behavior

### 2. **Performance Metrics**
- Page load times
- API response times
- Real-time update frequency

### 3. **Error Tracking**
- JavaScript errors
- API failures
- User experience issues

## 🚀 Future Enhancements

### 1. **Planned Features**
- Infinite scroll
- Advanced filtering
- Push notifications
- Social sharing improvements

### 2. **Performance Improvements**
- Service Worker caching
- Image optimization
- Bundle size reduction

### 3. **User Experience**
- Dark mode support
- Customizable feed
- Advanced search

---

*Tài liệu này mô tả trang profile_followed_posts.html được thiết kế để cung cấp trải nghiệm feed xã hội hoàn chỉnh với các tính năng real-time updates, tương tác xã hội, và responsive design. Trang tích hợp nhiều thư viện JavaScript để tạo ra giao diện người dùng hiện đại và thân thiện.*
