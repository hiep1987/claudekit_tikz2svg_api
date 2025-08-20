# Trang Cài đặt Hồ sơ - Profile Settings Page

## 📋 Tổng quan

File `templates/profile_settings.html` là trang cài đặt và quản lý hồ sơ cá nhân của người dùng. Trang này cho phép người dùng cập nhật thông tin cá nhân, avatar, và bio với giao diện thân thiện và các tính năng chỉnh sửa nâng cao.

## 🎯 Mục đích

- Quản lý thông tin cá nhân (username, email, bio)
- Upload và chỉnh sửa avatar với crop tool
- Rich text editor cho bio với định dạng HTML
- Responsive design cho mobile và desktop
- Tích hợp authentication và validation
- Flash messages cho feedback

## 🏗️ Cấu trúc Trang

### 1. **Header Section**
```html
<head>
    <title>Cài đặt hồ sơ - TikZ to SVG</title>
    <meta property="og:title" content="Cài đặt hồ sơ - TikZ to SVG" />
    <meta property="og:description" content="Cài đặt và quản lý hồ sơ người dùng TikZ to SVG" />
    <meta property="og:type" content="website" />
    <meta property="og:locale" content="vi_VN" />
</head>
```

### 2. **Main Container**
```html
<div class="container">
    <div id="profile-content" class="profile-content show">
        <!-- Header -->
        <div class="header">
            <h1>👤 Hồ sơ cá nhân</h1>
            <p>Quản lý thông tin tài khoản của bạn</p>
        </div>
        
        <!-- Flash Messages -->
        <div class="flash-messages">
            <!-- Success/Error messages -->
        </div>
        
        <!-- Profile Form -->
        <form method="POST" enctype="multipart/form-data">
            <!-- Profile content -->
        </form>
    </div>
</div>
```

### 3. **Profile Section Layout**
```html
<div class="profile-section">
    <!-- Avatar Section -->
    <div class="avatar-section">
        <div class="avatar-container">
            <!-- Avatar display -->
        </div>
        <div class="avatar-upload">
            <!-- File upload -->
        </div>
    </div>
    
    <!-- Info Section -->
    <div class="info-section">
        <!-- Form fields -->
    </div>
</div>
```

### 4. **Form Fields**
- **Email**: Read-only field với verification status
- **Username**: Editable text field
- **Bio**: Rich text editor với Quill.js
- **Avatar**: File upload với crop functionality

## 🎨 CSS Styling

### 1. **Container và Layout**
```css
.container {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    max-width: 1280px;
    margin: 0 auto;
}

.profile-section {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 40px;
    margin-bottom: 40px;
}
```

### 2. **Avatar Section**
```css
.avatar-section {
    text-align: center;
}

.avatar-container {
    position: relative;
    display: inline-block;
    margin-bottom: 20px;
}

.avatar,
.avatar-placeholder {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    object-fit: cover;
    border: 4px solid #e0e0e0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.avatar-placeholder {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 48px;
    font-weight: bold;
}
```

### 3. **Form Fields**
```css
.info-group {
    margin-bottom: 25px;
}

.info-group label {
    display: block;
    font-weight: bold;
    color: #333;
    margin-bottom: 8px;
    font-size: 14px;
}

.info-group input,
.info-group textarea {
    width: 100%;
    padding: 12px;
    border: 2px solid #ddd;
    border-radius: 6px;
    font-size: 16px;
    box-sizing: border-box;
}

.info-group input:focus,
.info-group textarea:focus {
    outline: none;
    border-color: #1976d2;
}

.info-group .readonly {
    background: #f5f5f5;
    color: #666;
    cursor: not-allowed;
    border-color: #ddd;
}
```

### 4. **Quill Editor Styling**
```css
/* Quill Editor Toolbar */
.ql-toolbar.ql-snow {
    background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
    border: 1px solid #1565c0 !important;
    border-radius: 8px 8px 0 0 !important;
    color: white !important;
}

/* Bio Editor Container */
#bio-editor.ql-container.ql-snow {
    background: #1e3a8a !important;
    border: 1px solid #1e40af !important;
    border-radius: 8px !important;
    min-height: 120px !important;
}

/* Editor Content */
div#bio-editor .ql-editor {
    background: #1e3a8a !important;
    background-color: #1e3a8a !important;
    color: white !important;
}
```

### 5. **Buttons và Actions**
```css
.btn {
    padding: 12px 30px;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s;
    margin: 0 10px;
}

.btn-primary {
    background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
    color: white;
}

.btn-primary:hover {
    background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%);
}
```

### 6. **Flash Messages**
```css
.flash {
    padding: 12px 20px;
    border-radius: 6px;
    margin-bottom: 10px;
    font-weight: bold;
    transition: opacity 0.3s ease;
}

.flash-success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.flash-error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}
```

## 🔧 JavaScript Functionality

### 1. **Avatar Cropper Integration**
```javascript
let cropper = null;
let selectedFile = null;

function openCropperModal(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const maxSize = 5 * 1024 * 1024; // 5MB
        
        // File validation
        if (file.size > maxSize) {
            alert('File quá lớn! Vui lòng chọn file nhỏ hơn 5MB.');
            input.value = '';
            return;
        }
        
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            alert('Chỉ chấp nhận file ảnh: JPG, PNG, GIF');
            input.value = '';
            return;
        }
        
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.getElementById('cropper-image');
            img.src = e.target.result;
            document.getElementById('avatar-cropper-modal').style.display = 'flex';
            
            // Initialize cropper
            if (cropper) cropper.destroy();
            cropper = new Cropper(img, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                background: false,
                guides: false,
                autoCropArea: 1,
                movable: true,
                zoomable: true,
                rotatable: false,
                scalable: false,
                cropBoxResizable: false,
                cropBoxMovable: false,
                minContainerWidth: 220,
                minContainerHeight: 220
            });
        };
        reader.readAsDataURL(file);
    }
}
```

### 2. **Avatar Crop Processing**
```javascript
document.getElementById('crop-avatar-btn').addEventListener('click', function() {
    if (cropper) {
        // Get cropped canvas
        const canvas = cropper.getCroppedCanvas({ 
            width: 300, 
            height: 300, 
            imageSmoothingQuality: 'high' 
        });
        
        // Create circular canvas
        const circleCanvas = document.createElement('canvas');
        circleCanvas.width = 300;
        circleCanvas.height = 300;
        const ctx = circleCanvas.getContext('2d');
        
        ctx.save();
        ctx.beginPath();
        ctx.arc(150, 150, 150, 0, 2 * Math.PI);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(canvas, 0, 0, 300, 300);
        ctx.restore();
        
        // Update preview
        const avatarPreview = document.getElementById('avatar-preview');
        if (avatarPreview) {
            avatarPreview.src = circleCanvas.toDataURL('image/png');
        } else {
            // Replace placeholder if no preview exists
            const avatarPlaceholder = document.getElementById('avatar-placeholder');
            if (avatarPlaceholder) {
                const newImg = document.createElement('img');
                newImg.src = circleCanvas.toDataURL('image/png');
                newImg.alt = 'Avatar Preview';
                newImg.className = 'avatar';
                newImg.id = 'avatar-preview';
                avatarPlaceholder.parentNode.replaceChild(newImg, avatarPlaceholder);
            }
        }
        
        // Create blob for form submission
        circleCanvas.toBlob(function(blob) {
            let hiddenInput = document.getElementById('avatar-cropped-blob');
            if (!hiddenInput) {
                hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'avatar_cropped';
                hiddenInput.id = 'avatar-cropped-blob';
                document.querySelector('form').appendChild(hiddenInput);
            }
            
            const reader = new FileReader();
            reader.onloadend = function() {
                hiddenInput.value = reader.result;
            };
            reader.readAsDataURL(blob);
        }, 'image/png');
        
        closeCropperModal();
    }
});
```

### 3. **Quill Editor Initialization**
```javascript
let quill;
const bioEditor = document.getElementById('bio-editor');
if (bioEditor) {
    quill = new Quill('#bio-editor', {
        theme: 'snow',
        modules: {
            toolbar: [
                ['bold', 'italic', 'underline', 'strike'],
                [{ 'header': [1, 2, 3, false] }],
                [{ list: 'ordered' }, { list: 'bullet' }],
                [{ 'align': [] }],
                [{
                    color: [
                        '#ffffff', // Trắng (mặc định)
                        '#ffeb3b', // Vàng chanh
                        '#ff9800', // Cam
                        '#ff5722', // Đỏ cam
                        '#e91e63', // Hồng
                        '#9c27b0', // Tím
                        '#673ab7', // Tím đậm
                        '#3f51b5', // Xanh tím
                        '#2196f3', // Xanh dương nhạt
                        '#00bcd4', // Cyan
                        '#009688', // Teal
                        '#4caf50', // Xanh lá
                        '#8bc34a', // Xanh lá nhạt
                        '#cddc39', // Vàng xanh
                        '#ffc107', // Vàng đậm
                        '#795548', // Nâu
                        '#9e9e9e', // Xám
                        '#607d8b'  // Xanh xám
                    ]
                }],
                ['clean']
            ]
        },
        placeholder: 'Viết gì đó về bản thân...'
    });
    
    // Sync with hidden input
    quill.on('text-change', function () {
        const bioHidden = document.getElementById('bio-hidden');
        if (bioHidden) bioHidden.value = quill.root.innerHTML;
    });
}
```

### 4. **Form Submission**
```javascript
const profileForm = document.querySelector('form[method="POST"]');
if (profileForm) {
    profileForm.addEventListener('submit', function () {
        if (quill) {
            const bioHidden = document.getElementById('bio-hidden');
            if (bioHidden) bioHidden.value = quill.root.innerHTML;
        }
        // Form submits normally, page reloads to show updates
        console.log('Profile form submitted - page will reload to update username');
    });
}
```

### 5. **Color Management for Bio Editor**
```javascript
// Set default text color
setTimeout(function() {
    const editor = document.querySelector('#bio-editor .ql-editor');
    if (editor && !editor.style.color) {
        editor.style.color = '#495057';
    }
}, 100);

// Observer to handle color changes
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
            const target = mutation.target;
            // Only set dark gray color if no specific color is set
            if (target.style.color === '' || target.style.color === 'black' || target.style.color === 'rgb(0, 0, 0)') {
                target.style.color = '#495057';
            }
        }
    });
});

// Start observing
const editor = document.querySelector('#bio-editor .ql-editor');
if (editor) {
    observer.observe(editor, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style']
    });
}
```

## 📱 Responsive Design

### 1. **Desktop Layout**
- **Grid layout**: Avatar section (1fr) + Info section (2fr)
- **Full functionality**: All features available
- **Large avatar**: 150px x 150px

### 2. **Tablet Layout**
```css
@media (max-width: 768px) {
    .profile-section {
        grid-template-columns: 1fr;
        gap: 20px;
    }
    
    .container {
        padding: 20px;
    }
}
```

### 3. **Mobile Layout**
```css
@media (max-width: 600px) {
    .container {
        padding: 4vw;
    }
    
    .avatar, .avatar-placeholder {
        width: 80px;
        height: 80px;
        font-size: 32px;
    }
    
    .btn, .btn-primary, .btn-secondary {
        width: 100%;
        font-size: 17px;
        margin: 8px 0;
        padding: 14px 0;
    }
}
```

## 🔗 Integration

### 1. **Backend Integration**
- **Route**: `/profile/settings`
- **Form handling**: POST method với multipart/form-data
- **File upload**: Avatar processing và storage
- **Database updates**: User profile information

### 2. **Frontend Integration**
- **Cropper.js**: Image cropping functionality
- **Quill.js**: Rich text editor cho bio
- **Bootstrap**: UI components và responsive grid
- **Font Awesome**: Icons và visual elements

### 3. **Authentication Integration**
- **User validation**: Kiểm tra trạng thái đăng nhập
- **Session management**: User data persistence
- **Security**: CSRF protection và input validation

## 📊 Data Flow

### 1. **Profile Load Process**
```
Page Request → Authentication Check → Database Query → Template Rendering → Form Population
```

### 2. **Avatar Upload Process**
```
File Selection → Validation → Cropper Modal → Image Cropping → Preview Update → Form Submission
```

### 3. **Form Submission Process**
```
Form Data → Validation → File Processing → Database Update → Flash Message → Page Reload
```

## 🎯 User Experience Features

### 1. **Profile Management**
- ✅ Avatar upload với crop tool
- ✅ Username editing
- ✅ Rich text bio editor
- ✅ Email verification status

### 2. **Visual Feedback**
- ✅ Flash messages cho success/error
- ✅ Real-time preview cho avatar
- ✅ Form validation feedback
- ✅ Loading states

### 3. **Interactive Features**
- ✅ Image cropping với circular output
- ✅ Rich text formatting cho bio
- ✅ Color picker cho text
- ✅ Responsive design

### 4. **File Handling**
- ✅ File type validation (JPG, PNG, GIF)
- ✅ File size validation (max 5MB)
- ✅ Image cropping và optimization
- ✅ Base64 encoding cho form submission

## 🔒 Security Features

### 1. **File Upload Security**
- File type validation
- File size limits
- Image processing và sanitization
- Secure file storage

### 2. **Form Security**
- CSRF protection
- Input validation và sanitization
- SQL injection prevention
- XSS protection

### 3. **Authentication**
- Session validation
- User authorization
- Secure data transmission
- Access control

## 🚀 Performance Optimizations

### 1. **Image Processing**
- Client-side cropping để giảm server load
- Optimized image quality settings
- Efficient canvas operations
- Base64 encoding cho immediate preview

### 2. **Editor Performance**
- Lazy loading cho Quill.js
- Efficient DOM manipulation
- Optimized event handling
- Memory management

### 3. **Responsive Optimization**
- CSS Grid cho layout efficiency
- Optimized media queries
- Touch-friendly interactions
- Mobile-first approach

## 🐛 Error Handling

### 1. **File Upload Errors**
```javascript
// File size validation
if (file.size > maxSize) {
    alert('File quá lớn! Vui lòng chọn file nhỏ hơn 5MB.');
    input.value = '';
    return;
}

// File type validation
if (!allowedTypes.includes(file.type)) {
    alert('Chỉ chấp nhận file ảnh: JPG, PNG, GIF');
    input.value = '';
    return;
}
```

### 2. **Form Validation**
- Required field validation
- Email format validation
- Username length limits
- Bio content validation

### 3. **Network Errors**
- Connection timeout handling
- Server error responses
- Graceful degradation
- User-friendly error messages

## 📈 Analytics & Monitoring

### 1. **User Analytics**
- Profile update frequency
- Avatar upload patterns
- Bio editing behavior
- Form completion rates

### 2. **Performance Monitoring**
- Page load times
- Image processing performance
- Editor responsiveness
- Mobile usage patterns

## 🔄 Maintenance

### 1. **Code Organization**
- Modular CSS classes
- Reusable JavaScript functions
- Clear separation of concerns
- Consistent naming conventions

### 2. **Dependencies**
- Regular updates cho Cropper.js
- Quill.js version management
- Bootstrap compatibility
- Security patches

## 📝 Future Enhancements

### 1. **Advanced Features**
- Multiple avatar options
- Profile themes và customization
- Social media integration
- Advanced bio formatting

### 2. **UI/UX Improvements**
- Drag-and-drop file upload
- Advanced image filters
- Real-time collaboration
- Accessibility enhancements

### 3. **Performance**
- Progressive image loading
- Advanced caching strategies
- Service worker integration
- CDN optimization

## 🎨 Visual Design

### 1. **Color Scheme**
- **Primary**: #1976d2 (Blue)
- **Secondary**: #1565c0 (Dark Blue)
- **Success**: #4caf50 (Green)
- **Error**: #f44336 (Red)
- **Background**: #f5f5f5 (Light Gray)

### 2. **Typography**
- **Font Family**: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- **Headings**: Bold weights
- **Body Text**: Regular weights
- **Form Labels**: Semi-bold weights

### 3. **Spacing & Layout**
- **Container**: max-width 1280px
- **Padding**: 40px desktop, 20px mobile
- **Gap**: 40px between sections, 25px between form groups
- **Border Radius**: 12px container, 6px buttons, 50% avatar

---

*Tài liệu này mô tả trang profile_settings.html được thiết kế để cung cấp trải nghiệm quản lý hồ sơ cá nhân hoàn chỉnh với các tính năng upload avatar, rich text editor, và responsive design. Trang tích hợp nhiều thư viện JavaScript để tạo ra giao diện người dùng hiện đại và thân thiện.*
