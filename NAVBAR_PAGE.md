# Thanh Điều Hướng - Navigation Bar

## 📋 Tổng quan

File `templates/_navbar.html` là component thanh điều hướng chính của ứng dụng TikZ to SVG, cung cấp giao diện navigation responsive với đầy đủ tính năng authentication, user profile và mobile menu.

## 🎯 Mục đích

- Cung cấp navigation chính cho toàn bộ ứng dụng
- Hiển thị trạng thái đăng nhập và thông tin user
- Responsive design cho desktop và mobile
- Tích hợp authentication và user management
- Cung cấp quick access đến các trang chính

## 🏗️ Cấu trúc Component

### 1. **Main Navigation Bar**
```html
<nav class="w-full max-w-7xl mx-auto bg-white/80 backdrop-blur shadow-lg rounded-2xl p-3 flex items-center justify-between mb-8">
    <!-- Logo Section -->
    <!-- Menu Section -->
    <!-- User Section -->
</nav>
```

### 2. **Logo Section**
```html
<div class="flex items-center gap-2 flex-shrink-0">
    <span class="bg-gradient-to-br from-blue-500 to-yellow-400 p-1.5 rounded-lg">
        <i class="fa-solid fa-meteor text-white text-lg"></i>
    </span>
    <span class="text-lg font-bold text-gray-800">TikZ to SVG</span>
</div>
```

### 3. **Desktop Menu**
```html
<div class="hidden md:flex flex-grow mx-4 justify-center">
    <ul id="main-menu" class="flex items-center gap-6 font-medium text-gray-700">
        <li class="menu-item relative px-2 py-1 cursor-pointer transition hover:text-blue-600">
            <a href="/" class="block text-base">Trang chủ</a>
            <div class="menu-underline"></div>
        </li>
        <!-- Conditional menu items for authenticated users -->
    </ul>
</div>
```

### 4. **User Section**
```html
<div class="flex items-center gap-2 flex-shrink-0">
    {% if current_user.is_authenticated %}
        <!-- User Avatar & Info -->
        <!-- Logout Button -->
    {% else %}
        <!-- Login Button -->
    {% endif %}
    <!-- Mobile Hamburger -->
</div>
```

### 5. **Mobile Scrollable Menu**
```html
<div id="scrollable-menu" class="md:hidden w-full max-w-7xl mx-auto mb-8">
    <ul id="scrollable-menu-list" class="flex items-center gap-6 font-medium text-gray-700 px-3">
        <!-- Mobile menu items -->
    </ul>
</div>
```

### 6. **Mobile Side Menu**
```html
<div id="mobile-menu" class="fixed top-0 left-0 w-full h-full bg-black/50 z-400 hidden">
    <div class="absolute right-0 top-0 w-60 bg-white h-full shadow-lg flex flex-col p-6 gap-3">
        <!-- Mobile side menu content -->
    </div>
</div>
```

## 🎨 CSS Styling

### 1. **Main Navigation**
```css
/* Glass morphism effect */
.bg-white/80 { background-color: rgba(255, 255, 255, 0.8); }
.backdrop-blur { backdrop-filter: blur(8px); }
.shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
.rounded-2xl { border-radius: 1rem; }
```

### 2. **Logo Styling**
```css
/* Gradient background for logo icon */
.bg-gradient-to-br { background-image: linear-gradient(to bottom right, var(--tw-gradient-stops)); }
.from-blue-500 { --tw-gradient-from: #3b82f6; }
.to-yellow-400 { --tw-gradient-to: #fbbf24; }
```

### 3. **Menu Items**
```css
/* Menu item hover effects */
.menu-item {
    position: relative;
    cursor: pointer;
    transition: color 0.3s;
}

.menu-item:hover {
    color: #2563eb;
}

/* Animated underline */
.menu-underline {
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    height: 3px;
    width: 0;
    background: linear-gradient(90deg, #fbbf24, #38bdf8);
    border-radius: 2px;
    margin: 0 auto;
    position: absolute;
    bottom: -2px;
    left: 50%;
    transform: translateX(-50%);
}

.menu-item:hover .menu-underline {
    width: 80%;
}
```

### 4. **User Avatar**
```css
/* Avatar container */
.bg-gray-100 { background-color: #f3f4f6; }
.rounded-lg { border-radius: 0.5rem; }

/* Avatar image */
.w-6 { width: 1.5rem; }
.h-6 { height: 1.5rem; }
.rounded-full { border-radius: 9999px; }

/* Fallback avatar */
.bg-gradient-to-br.from-blue-500.to-purple-600 {
    background-image: linear-gradient(to bottom right, #3b82f6, #9333ea);
}
```

### 5. **Button Styling**
```css
/* Login button */
.bg-gradient-to-r.from-blue-400.to-yellow-400 {
    background-image: linear-gradient(to right, #60a5fa, #fbbf24);
}

/* Logout button */
.bg-gradient-to-r.from-red-400.to-red-600 {
    background-image: linear-gradient(to right, #f87171, #dc2626);
}

/* Button hover effects */
.hover\:scale-105:hover { transform: scale(1.05); }
.transition { transition: all 0.3s ease; }
```

## ⚡ JavaScript Functionality

### 1. **Mobile Menu Toggle**
```javascript
// Mobile menu functionality (handled in parent pages)
const menuToggle = document.getElementById('menu-toggle');
const mobileMenu = document.getElementById('mobile-menu');
const closeMenu = document.getElementById('close-menu');

menuToggle.addEventListener('click', () => {
    mobileMenu.classList.remove('hidden');
});

closeMenu.addEventListener('click', () => {
    mobileMenu.classList.add('hidden');
});

// Close menu when clicking outside
mobileMenu.addEventListener('click', e => {
    if (e.target === mobileMenu) {
        mobileMenu.classList.add('hidden');
    }
});
```

### 2. **Active Menu Highlighting**
```javascript
// Highlight current page in menu
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.menu-item a');
    
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.closest('.menu-item').classList.add('active');
        }
    });
}
```

### 3. **Avatar Error Handling**
```html
<!-- Fallback for broken avatar images -->
<img src="{{ url_for('static', filename='avatars/' ~ current_avatar) }}" 
     alt="Avatar" class="w-6 h-6 rounded-full"
     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
```

## 🔧 Tính năng Chi tiết

### 1. **Authentication Integration**
- **Conditional Rendering**: Menu items hiển thị khác nhau cho user đã đăng nhập và chưa đăng nhập
- **User Info Display**: Avatar, username, email
- **Login/Logout Buttons**: Direct integration với Google OAuth

### 2. **Responsive Design**
- **Desktop**: Full menu với horizontal layout
- **Mobile**: Hamburger menu với side panel
- **Tablet**: Adaptive layout với scrollable menu

### 3. **Navigation Links**
- **Trang chủ**: Link đến homepage
- **Hồ sơ**: User profile settings (authenticated only)
- **File SVG**: User's SVG files (authenticated only)
- **Bài đăng**: Followed posts feed (authenticated only)

### 4. **User Experience**
- **Smooth Transitions**: Hover effects và animations
- **Visual Feedback**: Button states và loading indicators
- **Accessibility**: Proper ARIA labels và keyboard navigation

## 📱 Mobile Support

### 1. **Mobile Menu Structure**
```html
<!-- Scrollable horizontal menu for tablets -->
<div id="scrollable-menu" class="md:hidden">
    <ul id="scrollable-menu-list" class="flex items-center gap-6">
        <!-- Touch-friendly menu items -->
    </ul>
</div>

<!-- Full-screen overlay menu for mobile -->
<div id="mobile-menu" class="fixed top-0 left-0 w-full h-full bg-black/50 z-400 hidden">
    <div class="absolute right-0 top-0 w-60 bg-white h-full">
        <!-- Side panel menu -->
    </div>
</div>
```

### 2. **Touch Optimization**
```css
/* Touch-friendly button sizes */
.p-1\.5 { padding: 0.375rem; }
.rounded-lg { border-radius: 0.5rem; }

/* Touch hover states */
@media (hover: none), (pointer: coarse) {
    .hover\:bg-blue-100:hover {
        background-color: transparent;
    }
}
```

### 3. **Mobile-specific Features**
- **Hamburger Menu**: 3-line icon cho mobile navigation
- **Side Panel**: Slide-in menu từ bên phải
- **Overlay Background**: Semi-transparent overlay khi menu mở
- **Touch Gestures**: Swipe to close functionality

## 🔒 Security Features

### 1. **Authentication Checks**
```html
{% if current_user.is_authenticated %}
    <!-- Protected menu items -->
    <li class="menu-item">
        <a href="/profile/{{ current_user.id }}/settings">Hồ sơ</a>
    </li>
{% endif %}
```

### 2. **User Data Protection**
- **Safe User Display**: Username fallback nếu không có display name
- **Avatar Error Handling**: Fallback avatar nếu image không load được
- **Email Privacy**: Chỉ hiển thị phần local của email

### 3. **Session Management**
- **Logout Integration**: Secure logout với redirect
- **Session Validation**: Kiểm tra authentication status
- **CSRF Protection**: Form tokens cho logout

## 🎯 Performance Optimization

### 1. **Conditional Loading**
```html
<!-- Only load authenticated user features when needed -->
{% if current_user.is_authenticated %}
    <!-- User-specific content -->
{% else %}
    <!-- Public content -->
{% endif %}
```

### 2. **Image Optimization**
```html
<!-- Lazy loading cho avatar images -->
<img src="{{ url_for('static', filename='avatars/' ~ current_avatar) }}" 
     alt="Avatar" 
     loading="lazy"
     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
```

### 3. **CSS Optimization**
- **Utility Classes**: Tailwind-like utility classes
- **Minimal Custom CSS**: Tối ưu cho performance
- **Responsive Breakpoints**: Efficient media queries

## 🔄 Integration Points

### 1. **Flask Template Integration**
```html
<!-- Jinja2 template variables -->
{{ current_user.is_authenticated }}
{{ current_user.id }}
{{ current_username }}
{{ current_user_email }}
{{ current_avatar }}
```

### 2. **URL Routing**
```html
<!-- Dynamic URL generation -->
<a href="/profile/{{ current_user.id }}/settings">Hồ sơ</a>
<a href="/profile/{{ current_user.id }}/svg-files">File SVG</a>
<a href="/profile/{{ current_user.id }}/followed-posts">Bài đăng</a>
```

### 3. **Static Asset Integration**
```html
<!-- Avatar image serving -->
<img src="{{ url_for('static', filename='avatars/' ~ current_avatar) }}" alt="Avatar">

<!-- FontAwesome icons -->
<i class="fa-solid fa-meteor"></i>
<i class="fa-solid fa-bars"></i>
<i class="fa-solid fa-xmark"></i>
```

## 🎨 Design System

### 1. **Color Palette**
```css
/* Primary colors */
.text-gray-800 { color: #1f2937; }
.text-gray-700 { color: #374151; }
.text-blue-600 { color: #2563eb; }

/* Background colors */
.bg-white/80 { background-color: rgba(255, 255, 255, 0.8); }
.bg-gray-100 { background-color: #f3f4f6; }

/* Gradient colors */
.from-blue-500.to-yellow-400 { /* Blue to yellow gradient */ }
.from-red-400.to-red-600 { /* Red gradient */ }
```

### 2. **Typography**
```css
/* Font weights */
.font-bold { font-weight: 700; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }

/* Font sizes */
.text-lg { font-size: 1.125rem; }
.text-base { font-size: 1rem; }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
```

### 3. **Spacing & Layout**
```css
/* Flexbox layout */
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.justify-center { justify-content: center; }

/* Spacing */
.gap-2 { gap: 0.5rem; }
.gap-6 { gap: 1.5rem; }
.p-3 { padding: 0.75rem; }
.mb-8 { margin-bottom: 2rem; }
```

## 🚀 Accessibility Features

### 1. **Semantic HTML**
```html
<!-- Proper navigation structure -->
<nav class="w-full max-w-7xl mx-auto">
    <!-- Navigation content -->
</nav>

<!-- Proper button elements -->
<button id="menu-toggle" class="md:hidden">
    <i class="fa-solid fa-bars" aria-hidden="true"></i>
</button>
```

### 2. **ARIA Labels**
```html
<!-- Accessible button labels -->
<button id="menu-toggle" class="md:hidden" aria-label="Toggle mobile menu">
    <i class="fa-solid fa-bars"></i>
</button>

<button id="close-menu" aria-label="Close mobile menu">
    <i class="fa-solid fa-xmark"></i>
</button>
```

### 3. **Keyboard Navigation**
- **Tab Order**: Logical tab sequence
- **Focus States**: Visible focus indicators
- **Keyboard Shortcuts**: Enter/Space for button activation

## 🔧 Maintenance & Updates

### 1. **Template Variables**
```html
<!-- Required Flask context variables -->
current_user.is_authenticated
current_user.id
current_username
current_user_email
current_avatar
```

### 2. **Static Assets**
```html
<!-- Required static files -->
/static/avatars/ - Avatar images directory
FontAwesome CSS - Icon library
```

### 3. **JavaScript Dependencies**
```javascript
// Required JavaScript functions (defined in parent pages)
// - Mobile menu toggle functionality
// - Active page highlighting
// - User authentication status updates
```

---

*Tài liệu này mô tả component _navbar.html - thanh điều hướng chính của ứng dụng TikZ to SVG với đầy đủ tính năng responsive design, user authentication, và mobile optimization. Component được thiết kế để tích hợp seamlessly với tất cả các trang của ứng dụng.*
