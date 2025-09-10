# CLAUDE.md

Tệp này cung cấp hướng dẫn cho Claude Code (claude.ai/code) khi hỗ trợ phát triển dự án tikz2svg_api trong repository này.

---

## 📝 Tổng quan dự án

**Tên dự án:** tikz2svg_api  
**Mục tiêu:** Cung cấp một ứng dụng web cho phép người dùng chuyển đổi mã TikZ thành SVG, quản lý tài khoản, chia sẻ và tương tác với các file SVG.

**Thành phần chính:**
- **Backend:** Flask (Python) + MySQL + Gunicorn
- **Frontend:** HTML/CSS/JavaScript (Server-side rendering với Jinja2)
- **Xác thực:** Google OAuth2 + Flask-Login
- **Email:** Flask-Mail với Zoho SMTP
- **File Processing:** CairoSVG, PIL (Pillow), lualatex
- **TikZ Processing:** Tự động phát hiện packages và libraries
- **Triển khai:** Production-ready với rate limiting và security
- **External Libraries:** CodeMirror, Quill.js, Cropper.js

---

## 🛠️ Kiến trúc

### Backend
- **Framework:** Flask 3.1.1 với Gunicorn cho production
- **Database:** MySQL với mysql-connector-python
- **Authentication:** Google OAuth2 + Flask-Login + Flask-Dance
- **TikZ Processing:** 
  - Tự động phát hiện `\usepackage` và `\usetikzlibrary`
  - Sử dụng lualatex để biên dịch .tex → PDF
  - CairoSVG + Pillow để chuyển đổi PDF/SVG → PNG/JPEG
- **Email Service:** Flask-Mail với Zoho SMTP
- **Rate Limiting:** Custom implementation cho email và API
- **Static Files:** Flask static folder với persistent storage
- **File Management:** Unique naming cho SVG files và avatars

### Frontend
- **Template Engine:** Jinja2 với partials (reusable components)
- **CSS Architecture:** CSS Foundation System với master variables
  - **Foundation Files:** `master-variables.css`, `global-base.css`
  - **Design System:** Colors, spacing, typography, glass morphism variables
  - **Migration Status:** 6/10 priority files completed (index.css, profile_*.css)
  - **Load Order:** Foundation → Global Base → Component CSS
- **JavaScript:** Vanilla JS (ES6+) với AJAX/Fetch API
- **External Libraries:**
  - **CodeMirror:** Trình soạn thảo code cho TikZ
  - **Quill.js:** Rich text editor cho user bio
  - **Cropper.js:** Cắt và chỉnh sửa ảnh đại diện
- **UI Components:** Modal dialogs, file upload, real-time interactions
- **Design Features:** Glass morphism, responsive design, accessibility compliance
- **Real-time Features:** Polling cho likes, follows, new posts

### Database Schema
- **Users:** id, email, username, avatar, bio, identity_verified
- **SVG Files:** user_id, filename, original_tikz, created_at, likes, views, keywords
- **User Interactions:** follows, likes, comments
- **Email Logs:** Tracking email sending và delivery
- **Rate Limit Logs:** Monitoring API usage

### File Structure
```
tikz2svg_api/
├── app.py                 # Main Flask application (3821 lines)
├── requirements.txt       # Python dependencies
├── static/               # Static files (CSS, JS, images, avatars)
│   ├── css/              # Component-based CSS files
│   │   ├── foundation/   # CSS Foundation System
│   │   │   ├── master-variables.css  # Design system variables
│   │   │   └── global-base.css       # Global base styles
│   │   ├── index.css     # Main page styles (migrated)
│   │   ├── profile_*.css # Profile pages (migrated)  
│   │   ├── file_card.css # File components
│   │   └── navigation.css # Navigation styles
│   ├── js/               # JavaScript modules
│   ├── images/           # Generated SVG files
│   └── avatars/          # User profile images
├── templates/            # Jinja2 templates
│   ├── partials/         # Reusable template components
│   ├── emails/           # Email templates
│   └── *.html            # Main page templates
├── email_service.py      # Email functionality
├── verification_service.py # Identity verification
├── *.md                  # Documentation files
└── deployment/           # Deployment scripts
```

---

## 🔑 Claude Instructions

Claude Code cần tuân theo các nguyên tắc sau khi hỗ trợ dự án:

### 1. Về tài liệu (Docs)
- Luôn cập nhật các file .md khi có thay đổi hoặc bổ sung tính năng
- Tạo file documentation mới cho các tính năng lớn
- Sử dụng tiếng Việt cho documentation khi phù hợp
- Cập nhật README.md khi có thay đổi quan trọng

### 2. Về code
- **Flask Routes:** Tuân thủ RESTful conventions
- **Database:** Sử dụng parameterized queries để tránh SQL injection
- **Error Handling:** Implement proper try-catch với logging
- **Security:** Validate input, sanitize data, implement CSRF protection
- **Performance:** Optimize database queries, implement caching khi cần
- **TikZ Processing:** Implement timeout và error handling cho lualatex
- **File Upload:** Validate file types, implement size limits
- **Real-time Updates:** Implement efficient polling mechanisms
- **Environment Variables:** Sử dụng `os.environ.get()` với default values
- **CSS Architecture:** Tuân thủ CSS Foundation migration methodology
  - **Variables First:** Luôn sử dụng `var(--variable-name)` thay vì hardcoded values
  - **Scoping:** Tất cả selectors phải có `.tikz-app` prefix
  - **No Conflicts:** Tránh duplicate html/body/:root rules
  - **Glass Morphism:** Sử dụng foundation glass variables cho UI transparency
  - **Responsive:** Foundation breakpoint variables cho consistency

### 3. Testing
- **Unit Tests:** Sử dụng pytest cho backend testing
- **Integration Tests:** Test API endpoints và database operations
- **Frontend Tests:** Test JavaScript functionality
- **TikZ Processing Tests:** Test conversion pipeline end-to-end
- **Email Tests:** Test email sending và templates
- **Rate Limiting Tests:** Test API throttling
- **CSS Regression Tests:** Visual testing sau migration
- **Accessibility Tests:** Contrast ratio ≥ 4.5:1, keyboard navigation
- **Coverage:** Mục tiêu ≥ 70% cho critical paths

### 4. Commit & PR
- Tuân thủ Conventional Commit format:
  - `feat:` - Tính năng mới
  - `fix:` - Sửa lỗi
  - `docs:` - Cập nhật documentation
  - `refactor:` - Refactor code
  - `test:` - Thêm/sửa tests
  - `chore:` - Maintenance tasks
- Không bao giờ thêm attribution AI trong code hoặc commits

### 5. Bảo mật
- **Environment Variables:** Sử dụng .env cho sensitive data
- **Database:** Không hardcode credentials
- **File Upload:** Validate file types và sizes
- **Rate Limiting:** Implement để tránh abuse
- **Input Validation:** Sanitize tất cả user input
- **Environment Access:** Claude nên đọc `.env` thay vì hardcode values

### 6. Performance
- **Database:** Optimize queries, use indexes
- **Static Files:** Implement caching headers
- **File Processing:** Async processing cho large files
- **Memory Management:** Cleanup temporary files

---

## 📦 Quy tắc phát triển

### Code Style
1. **Python:** PEP 8 compliance
2. **JavaScript:** ES6+ với proper error handling
3. **HTML/CSS:** Semantic HTML, responsive design
4. **Database:** Consistent naming conventions

### Development Workflow
1. Test locally trước khi commit
2. Check database migrations  
3. Verify email functionality với Zoho SMTP
4. Test TikZ conversion pipeline
5. Test file upload/processing
6. Validate rate limiting
7. Test real-time features (polling)
8. Verify responsive design trên mobile/desktop
9. **CSS Migration Verification:**
   - Check conflicts: `grep -rn ":root\|html.*{\|body.*{" static/css/`
   - Verify scoping: All selectors have `.tikz-app` prefix
   - Test accessibility: Contrast ratios meet WCAG standards
   - Visual regression: Compare before/after screenshots

### File Management
1. **SVG Files:** Store in static/images/ với unique naming (timestamp + user_id)
2. **Avatars:** Store in static/avatars/ với Cropper.js processing
3. **Temporary Files:** Cleanup sau TikZ processing
4. **Backup:** Regular database backups
5. **Static Assets:** Optimize CSS/JS files cho production
6. **Email Templates:** Maintain HTML templates cho Zoho SMTP

---

## 🔍 Testing Strategy

### Backend Testing
```python
# Example test structure
def test_tikz_to_svg_conversion():
    # Test TikZ conversion functionality với lualatex
    
def test_package_detection():
    # Test automatic package và library detection
    
def test_user_authentication():
    # Test Google OAuth flow
    
def test_rate_limiting():
    # Test rate limiting implementation
    
def test_email_sending():
    # Test Zoho SMTP integration
```

### Frontend Testing
```javascript
// Example test structure
function testCodeMirrorIntegration() {
    // Test TikZ code editor functionality
}

function testFileUpload() {
    // Test file upload functionality
}

function testUserInteraction() {
    // Test like, follow, comment features
}

function testRealTimePolling() {
    // Test real-time updates
}

function testCropperIntegration() {
    // Test avatar cropping functionality
}
```

### Integration Testing
- Test complete user flows từ TikZ input đến SVG output
- Test email sending với Zoho SMTP
- Test file processing pipeline (TikZ → PDF → SVG → PNG/JPEG)
- Test rate limiting cho API và email
- Test real-time features (likes, follows, polling)
- Test responsive design trên multiple devices

---

## 🚫 Lưu ý quan trọng

### Security
- **Tuyệt đối không commit:** .env files, API keys, database credentials
- **File Upload:** Validate và sanitize tất cả uploaded files
- **SQL Injection:** Luôn sử dụng parameterized queries
- **XSS Protection:** Escape user input trong templates

### Performance
- **Large Files:** Implement timeout cho TikZ processing với lualatex
- **Memory:** Monitor memory usage với large SVG files và image processing
- **Database:** Optimize queries, use connection pooling
- **Caching:** Implement caching cho static assets
- **Real-time Updates:** Optimize polling frequency để giảm server load
- **File Processing:** Implement queue system cho large TikZ files

### Maintenance
- **Logs:** Implement proper logging cho debugging
- **Monitoring:** Monitor application health
- **Backup:** Regular database và file backups
- **Updates:** Keep dependencies updated

### Vietnamese Language Support
- **UTF-8:** Ensure proper encoding cho tiếng Việt
- **Email Templates:** Support Vietnamese content
- **User Interface:** Vietnamese labels và messages
- **Error Messages:** Vietnamese error messages

---

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Google OAuth2 credentials
- SMTP server configuration

### Environment Variables
Dự án sử dụng `python-dotenv` để tự động load file `.env`. Claude nên đọc file `.env` thay vì hardcode values.

**Các biến môi trường chính:**
```bash
# Database
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=tikz2svg

# Google OAuth2
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret

# Zoho SMTP
ZOHO_EMAIL=your_zoho_email
ZOHO_APP_PASSWORD=your_app_password
MAIL_SENDER_NAME=TikZ2SVG

# Application
TIKZ_SVG_DIR=/path/to/static/storage
FLASK_SECRET_KEY=your_secret_key
DAILY_SVG_LIMIT=10

# Optional
APP_URL=https://yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
```

**Lưu ý:** 
- File `.env` được load tự động bởi `load_dotenv()` trong `app.py`
- Không commit file `.env` vào git (đã có trong `.gitignore`)
- Claude nên đọc giá trị thực từ `.env` khi cần thiết

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install LaTeX dependencies (for TikZ processing)
# Ubuntu/Debian:
sudo apt-get install texlive-latex-base texlive-latex-extra lualatex

# macOS:
brew install texlive

# Run application
python app.py
# or for production:
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📚 Documentation Files

Dự án này có nhiều file documentation chi tiết:
- `README.md` - Tổng quan dự án
- `EMAIL_SETUP_GUIDE.md` - Hướng dẫn setup email với Zoho
- `VERIFICATION_SYSTEM_GUIDE.md` - Hệ thống xác thực danh tính  
- `RATE_LIMIT_GUIDE.md` - Rate limiting cho API và email
- `WORKFLOW_GUIDE.md` - Quy trình phát triển
- `CSS_REFACTOR_COMPLETE_REPORT.md` - Báo cáo refactor CSS
- `DATABASE_DOCUMENTATION.md` - Schema và queries
- `STATIC_FILES_CONFIGURATION.md` - Cấu hình static files
- **CSS Foundation Migration Documentation:**
  - `CSS_FOUNDATION_MIGRATION_SUMMARY.md` - Complete migration report
  - `CSS_ARCHITECTURE_MIGRATION_STATUS.md` - Progress tracker
  - `CSS_OVERRIDE_PREVENTION_GUIDE.md` - Prevention guidelines

## 🚀 Deployment

### Production Environment
- **VPS Setup:** Sử dụng symbolic links cho static files
- **Database:** MySQL với connection pooling
- **Web Server:** Gunicorn với multiple workers
- **Static Files:** Persistent storage với shared directory
- **Backup:** Automated database và file backups

### Development Environment
- **Local Setup:** Flask development server
- **Database:** Local MySQL instance
- **Email:** Zoho SMTP sandbox
- **File Storage:** Local static directory

Claude nên tham khảo các file này khi hỗ trợ development.

---

## 🎨 CSS Foundation System Guide

### Architecture Overview
Dự án sử dụng CSS Foundation System để đảm bảo consistency và maintainability:

#### **Load Order (Critical):**
```html
1. master-variables.css  <!-- MUST BE FIRST -->
2. global-base.css      <!-- Base styles -->  
3. component.css        <!-- Individual components -->
```

#### **Design System Variables:**
```css
/* Colors */
--primary-color: #1976d2;
--text-on-glass: #2d3436;
--text-header-glass: #1e3a8a;

/* Glass Morphism */
--glass-bg-light: rgba(255, 255, 255, 0.95);
--glass-bg-strong: rgba(248, 249, 250, 0.92);
--glass-blur-medium: blur(12px);
--glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);

/* Spacing (8px base) */
--spacing-4: 0.5rem;    /* 8px */
--spacing-8: 1rem;      /* 16px */  
--spacing-16: 2rem;     /* 32px */
```

#### **Migration Rules:**
1. **Backup First:** `cp file.css file.css.backup_migration`
2. **Remove Conflicts:** Delete duplicate html/body/:root rules
3. **Add Scoping:** Prefix all selectors với `.tikz-app`
4. **Replace Values:** Hardcoded → `var(--variable-name)`
5. **Test Thoroughly:** Visual regression + accessibility

#### **Migration Status (6/10 Complete):**
- ✅ `index.css` - Main page (latest)
- ✅ `profile_svg_files.css` - Profile pages
- ✅ `profile_settings.css` - Settings & modals
- ✅ `profile_verification.css` - Verification system
- ✅ `profile_followed_posts.css` - User interactions
- ⏳ `file_card.css` - Next priority
- ⏳ `navigation.css` - Global navigation

#### **Quality Standards:**
- **Accessibility:** Contrast ratio ≥ 4.5:1 (achieved ≥ 6.2:1)
- **Performance:** No CSS redundancy, optimized loading
- **Maintainability:** Single source of truth for design tokens
- **Cross-browser:** webkit-backdrop-filter + backdrop-filter
