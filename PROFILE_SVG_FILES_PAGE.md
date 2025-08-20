# Trang Profile SVG Files - Profile SVG Files Page

## 📋 Tổng quan

File `templates/profile_svg_files.html` là trang hiển thị profile của người dùng với danh sách các file SVG đã tạo. Trang này hỗ trợ cả chế độ xem profile của chính mình (owner) và xem profile của người khác (public profile) với đầy đủ tính năng tương tác.

## 🎯 Mục đích

- Hiển thị thông tin profile người dùng (avatar, username, bio, follower count)
- Danh sách các file SVG đã tạo với đầy đủ tính năng
- Hỗ trợ follow/unfollow người dùng khác
- Tương tác với file SVG (like, share, copy, view code, delete)
- Responsive design cho mobile và desktop
- Tích hợp authentication và authorization

## 🏗️ Cấu trúc Trang

### 1. **Header Section**
```html
<head>
    <title>File SVG của tôi - TikZ to SVG</title>
    <meta property="og:title" content="File SVG của tôi - TikZ to SVG" />
    <meta property="og:description" content="Quản lý và xem các file SVG đã tạo từ TikZ code" />
    <meta property="og:type" content="website" />
    <meta property="og:locale" content="vi_VN" />
</head>
```

### 2. **Public Profile Header**
```html
<div class="public-profile-header">
    <!-- Avatar Section -->
    <div class="avatar-section">
        <img src="{{ url_for('static', filename='avatars/' ~ avatar) }}" alt="Avatar">
        <h2>{{ username or user_email.split('@')[0] }}</h2>
        <div class="follower-count">👥 {{ follower_count }} followers</div>
    </div>
    
    <!-- Bio Section -->
    {% if bio %}
    <div class="bio-container">{{ bio | safe }}</div>
    {% endif %}
    
    <!-- Contact Info -->
    <div class="contact-info">
        <strong>Email liên hệ:</strong> {{ user_email }}
    </div>
    
    <!-- Follow Button (for non-owners) -->
    {% if current_user.is_authenticated and not is_owner %}
    <div class="follow-section">
        {% if is_followed %}
        <button class="btn btn-secondary follow-btn" onclick="unfollowUser({{ user_id }})">
            👥 Bỏ theo dõi
        </button>
        {% else %}
        <button class="btn btn-primary follow-btn" onclick="followUser({{ user_id }})">
            👥 Theo dõi
        </button>
        {% endif %}
    </div>
    {% endif %}
</div>
```

### 3. **SVG Files Section**
```html
<section class="svg-files-section">
    <h3>
        {% if is_owner %}
            📂 Các file SVG bạn đã tạo
        {% else %}
            📂 Danh sách các file SVG đã tạo
        {% endif %}
    </h3>
    
    <div class="files-grid">
        {% for file in svg_files %}
        <div class="file-card" data-id="{{ file.id }}">
            <!-- File content -->
        </div>
        {% endfor %}
    </div>
</section>
```

### 4. **File Card Structure**
Mỗi file card bao gồm:
- **Action Toggle Button**: Nút "⋯" để mở menu
- **SVG Preview**: Hình ảnh SVG với like button
- **Action Menu**: Các nút tương tác (hover/click)
- **File Info**: Thông tin file và creator
- **TikZ Code Section**: Code TikZ với CodeMirror editor

## 🎨 CSS Styling

### 1. **Public Profile Header**
```css
.public-profile-header {
    text-align: center;
    margin-bottom: 40px;
    padding: 10px;
    background: #1e3a8a;
    border-radius: 16px;
    color: white;
    box-shadow: 0 4px 20px rgba(30, 58, 138, 0.3);
    border: 1px solid #1e40af;
}

.avatar-section {
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 15px;
    flex-wrap: wrap;
}

.bio-container {
    margin-bottom: 20px;
    font-style: italic;
    font-size: 16px;
    opacity: 0.9;
}
```

### 2. **File Cards**
```css
.file-card {
    position: relative;
    min-height: 260px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
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

### 3. **Action Menu**
```css
.file-action-container {
    display: none;
    opacity: 0;
    pointer-events: none;
    transform: translateX(-10px);
    transition: opacity 0.3s, transform 0.3s;
    position: absolute;
    left: 12px;
    top: 2px;
    z-index: 300;
}

.Btn {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    width: 35px;
    height: 35px;
    border: none;
    border-radius: 50%;
    background: linear-gradient(-50deg, rgb(39, 107, 255), rgb(112, 186, 255), rgb(39, 107, 255));
    transition: all 0.3s ease;
}
```

### 4. **Like Button**
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

@keyframes heartBeat {
    0% { transform: scale(1); }
    50% { transform: scale(1.3); }
    100% { transform: scale(1); }
}
```

## 🔧 JavaScript Functionality

### 1. **Follow/Unfollow System**
```javascript
function followUser(userId) {
    fetch('/follow_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            user_id: userId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            const followBtn = document.querySelector(`[onclick="followUser(${userId})"]`);
            followBtn.outerHTML = `
                <button type="button" class="btn btn-secondary follow-btn" 
                        data-user-id="${userId}" 
                        onclick="unfollowUser(${userId})">
                    👥 Bỏ theo dõi
                </button>
            `;
            // Update follower count
            updateFollowerCount(data.new_follower_count);
        }
    });
}
```

### 2. **Like Button System**
```javascript
function initializeLikeButtons() {
    document.querySelectorAll('input[id^="heart-"]').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const fileId = this.id.replace('heart-', '');
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
                    // Update like count
                    const likeCount = data.like_count;
                    const likeButton = this.closest('.like-button');
                    likeButton.querySelector('.like-count.one').textContent = likeCount;
                    likeButton.querySelector('.like-count.two').textContent = likeCount;
                }
            });
        });
    });
}
```

### 3. **Delete File Functionality**
```javascript
function showDeleteModal(btn) {
    const card = btn.closest('.file-card');
    deleteCardElem = card;
    deleteSvgId = card.getAttribute('data-id');
    document.getElementById('delete-confirm-modal').style.display = 'flex';
}

// Handle delete confirmation
document.getElementById('confirm-delete-btn').addEventListener('click', function() {
    if (deleteSvgId && deleteCardElem) {
        fetch('/delete_svg', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                svg_image_id: deleteSvgId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                deleteCardElem.remove();
                document.getElementById('delete-confirm-modal').style.display = 'none';
                alert('Đã xóa ảnh thành công!');
            }
        });
    }
});
```

### 4. **Touch Events for Mobile**
```javascript
function initializeTouchBtnEvents() {
    if (!document.documentElement.classList.contains('is-touch')) return;

    document.addEventListener('click', function(e) {
        const actionToggleBtn = e.target.closest('.action-toggle-btn');
        if (actionToggleBtn) {
            const card = actionToggleBtn.closest('.file-card');
            if (card) {
                document.querySelectorAll('.file-card.active').forEach(other => {
                    if (other !== card) other.classList.remove('active');
                });
                card.classList.toggle('active');
            }
            return;
        }
        
        const btn = e.target.closest('.Btn');
        if (!btn) return;
        
        // 2-tap logic for mobile
        if (!btn.dataset.tapCount) btn.dataset.tapCount = '0';
        const currentTapCount = parseInt(btn.dataset.tapCount);
        
        if (currentTapCount === 0) {
            // First tap: highlight button
            e.preventDefault();
            btn.classList.add('individual-active', 'ready-to-execute');
            btn.dataset.tapCount = '1';
            
            setTimeout(() => {
                if (btn.dataset.tapCount === '1') {
                    btn.classList.remove('individual-active', 'ready-to-execute');
                    btn.dataset.tapCount = '0';
                }
            }, 5000);
        } else if (currentTapCount === 1) {
            // Second tap: execute action
            executeButtonAction(btn);
            btn.dataset.tapCount = '0';
            btn.classList.remove('individual-active', 'ready-to-execute');
        }
    });
}
```

### 5. **CodeMirror Integration**
```javascript
function initializeCodeMirror() {
    document.querySelectorAll('.tikz-cm').forEach(function(textarea) {
        if (!textarea.CodeMirror) {
            const codeBlock = textarea.closest('.tikz-code-block');
            if (codeBlock) {
                const existingCm = codeBlock.querySelector('.CodeMirror');
                if (existingCm) {
                    existingCm.remove();
                }
                
                if (typeof CodeMirror !== 'undefined') {
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
                    
                    setTimeout(() => {
                        cmInstance.refresh();
                    }, 100);
                }
            }
        }
    });
}
```

## 📱 Responsive Design

### 1. **Desktop Layout**
- **Grid layout**: File cards in responsive grid
- **Hover effects**: Action menu appears on hover
- **Full functionality**: All features available

### 2. **Tablet Layout**
```css
@media (min-width: 601px) and (max-width: 1040px) {
    .files-grid {
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
    }
    
    .container {
        padding: 30px;
    }
}
```

### 3. **Mobile Layout**
```css
@media (max-width: 600px) {
    .container {
        padding: 20px;
    }
    
    .files-grid {
        grid-template-columns: 1fr;
        gap: 15px;
    }
    
    .public-profile-header {
        padding: 15px;
    }
    
    .avatar-section {
        flex-direction: column;
        gap: 10px;
    }
}
```

## 🔗 Integration

### 1. **Backend Integration**
- **Route**: `/profile/<user_id>/svg-files`
- **Database queries** cho user info và SVG files
- **Authentication checks** cho owner vs public access
- **Follow/unfollow API** endpoints

### 2. **Frontend Integration**
- **Navigation** từ navbar và other pages
- **CodeMirror** cho TikZ code display
- **LocalStorage** cho pending actions
- **Real-time updates** via polling

### 3. **Authentication Integration**
- **Owner mode**: Full access to all features
- **Public mode**: Limited access based on authentication
- **Modal login** cho unauthenticated users
- **Session management** và redirect handling

## 📊 Data Flow

### 1. **Profile Load Process**
```
URL Request → Backend Route → User Validation → Database Queries → Template Rendering
```

### 2. **File Interaction Process**
```
User Action → Authentication Check → API Call → Database Update → UI Update
```

### 3. **Follow/Unfollow Process**
```
Button Click → API Call → Database Update → UI Update → Follower Count Update
```

## 🎯 User Experience Features

### 1. **Profile Display**
- ✅ Avatar và username display
- ✅ Bio với HTML formatting
- ✅ Follower count với real-time updates
- ✅ Follow/unfollow functionality

### 2. **File Management**
- ✅ Grid layout với responsive design
- ✅ Hover effects cho desktop
- ✅ Touch-friendly cho mobile
- ✅ Real-time like updates

### 3. **Interactive Features**
- ✅ Like/unlike SVG images
- ✅ Share on Facebook
- ✅ Copy direct link
- ✅ View TikZ code with syntax highlighting
- ✅ Delete files (owner only)

### 4. **Authentication Features**
- ✅ Login modal cho unauthenticated users
- ✅ Pending action preservation
- ✅ Session management
- ✅ Redirect handling

## 🔒 Security Features

### 1. **Authentication**
- Kiểm tra trạng thái đăng nhập
- Owner vs public access control
- Secure API calls với CSRF protection

### 2. **Authorization**
- File deletion chỉ cho owner
- Follow/unfollow chỉ cho authenticated users
- Like functionality chỉ cho authenticated users

### 3. **Input Validation**
- Sanitize user input
- Validate file IDs và user IDs
- Prevent XSS attacks

## 🚀 Performance Optimizations

### 1. **Real-time Updates**
- Polling cho like counts
- Polling cho follower counts
- Efficient DOM updates

### 2. **Code Optimization**
- Lazy loading cho CodeMirror
- Efficient event delegation
- Optimized CSS selectors

### 3. **Caching**
- Browser caching cho static assets
- API response caching
- LocalStorage cho user preferences

## 🐛 Error Handling

### 1. **Authentication Errors**
```javascript
function requireLogin(callback) {
    if (window.isLoggedIn) {
        callback();
    } else {
        showLoginModal();
    }
}
```

### 2. **API Error Handling**
```javascript
fetch('/like_svg', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // Handle success
    } else {
        console.error('API Error:', data.message);
        alert('Có lỗi xảy ra: ' + data.message);
    }
})
.catch(error => {
    console.error('Network Error:', error);
    alert('Lỗi kết nối!');
});
```

### 3. **File Not Found**
- Graceful handling cho missing files
- User-friendly error messages
- Fallback content

## 📈 Analytics & Monitoring

### 1. **User Analytics**
- Profile view tracking
- File interaction patterns
- Follow/unfollow statistics
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
- File organization và categorization
- Advanced search và filtering
- File sharing permissions
- Collaborative features

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
- **Danger**: #d32f2f (Red)
- **Background**: #f5f5f5 (Light Gray)

### 2. **Typography**
- **Font Family**: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- **Headings**: Bold weights
- **Body Text**: Regular weights
- **Buttons**: Semi-bold weights

### 3. **Spacing & Layout**
- **Container**: max-width 1280px
- **Padding**: 40px container, 20px mobile
- **Gap**: 20px between cards, 8px between elements
- **Border Radius**: 10px-16px for cards, 6px-8px for buttons

---

*Tài liệu này mô tả trang profile_svg_files.html được thiết kế để cung cấp trải nghiệm quản lý profile và file SVG hoàn chỉnh với đầy đủ tính năng tương tác, authentication và responsive design. Trang hỗ trợ cả chế độ owner và public viewing với các tính năng phù hợp cho từng trường hợp.*
