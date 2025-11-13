# CLAUDE.md

Tệp này cung cấp hướng dẫn cho Claude Code (claude.ai/code) khi hỗ trợ phát triển dự án tikz2svg_api trong repository này.

---

## 📝 Tổng quan dự án

**Tên dự án:** tikz2svg_api  
**Mục tiêu:** Cung cấp một ứng dụng web cho phép người dùng chuyển đổi mã TikZ thành SVG, quản lý tài khoản, chia sẻ và tương tác với các file SVG trong môi trường cộng đồng học thuật.

**Thành phần chính:**
- **Backend:** Flask (Python) + MySQL + Gunicorn
- **Frontend:** HTML/CSS/JavaScript (Server-side rendering với Jinja2)
- **Xác thực:** Google OAuth2 + Flask-Login
- **Email:** Flask-Mail với Zoho SMTP
- **File Processing:** CairoSVG, PIL (Pillow), lualatex, pdf2svg
- **TikZ Processing:** 
  - Tự động phát hiện packages và libraries
  - Manual package specification với cú pháp `%!<\usepackage{...}>`
  - Package request system cho người dùng
- **Comments System:** LaTeX math + TikZ code sharing với MathJax
- **Triển khai:** Production-ready với rate limiting, caching và security
- **External Libraries:** CodeMirror, Quill.js, Cropper.js, MathJax

---

## ⚠️ CRITICAL: Read These Files First

**Before working on this codebase, YOU MUST read:**

1. **DATABASE_DOCUMENTATION.md** - 19 database tables, schema, queries
2. **API_ENDPOINTS_DOCUMENTATION.md** - 80+ REST API endpoints, rate limits, security
3. **DOCS_CONTENT_COMPILATION.md** - 437+ user documentation sections, workflows
4. **WORKFLOW_GUIDE.md** - VPS deployment, Redis setup, troubleshooting

**Reference:** See `docs/CRITICAL_DOCS_REFERENCE.md` for detailed implementation patterns.

**Quick verification:**
```bash
wc -l DATABASE_DOCUMENTATION.md API_ENDPOINTS_DOCUMENTATION.md DOCS_CONTENT_COMPILATION.md WORKFLOW_GUIDE.md
# Should show: ~1390, ~1700, ~1357, ~517 lines respectively
```

---

## ✨ Tính năng chính

### 1. TikZ Processing System
- **Auto-detection:** Tự động phát hiện 50+ LaTeX packages, TikZ libraries, PGFPlots libraries
- **Manual Specification:** Cú pháp `%!<\usepackage{...}>` cho packages đặc biệt
- **Package Options:** Hỗ trợ `\usepackage[options]{package}`
- **Unicode Support:** LuaLaTeX + fontspec cho tiếng Việt, CJK characters
- **Compilation:** lualatex → PDF → SVG (pdf2svg)
- **Error Handling:** Chi tiết log lỗi LaTeX với line numbers
- **Timeout Protection:** 30 giây timeout cho compilation

### 2. Package Management System
- **Package Listing:** Xem danh sách packages được hỗ trợ tại `/packages`
- **Package Request:** Người dùng gửi yêu cầu thêm package mới
- **Status Tracking:** Pending → Under Review → Approved/Rejected
- **Priority Levels:** Thấp, Trung bình, Cao, Khẩn cấp
- **Email Notifications:** Thông báo khi request được xử lý
- **Rate Limiting:** 3 requests/giờ để tránh spam

### 3. Comments System
- **LaTeX Math:** Inline `$...$` và display `$$...$$` với MathJax
- **TikZ Code Blocks:** `\code{...}` với copy button
- **Nested Replies:** Parent comments và replies
- **Like/Unlike:** Đánh giá chất lượng comments
- **Edit/Delete:** Chỉnh sửa và xóa comments của mình
- **Real-time Preview:** MathJax rendering khi gõ
- **Security:** XSS protection với HTML escaping

### 4. Social Features
- **Like System:** Like/unlike SVG files với modal hiển thị danh sách
- **Follow System:** Follow/unfollow users (requires verification)
- **Profile Pages:** Public profiles với SVG gallery
- **Followed Posts:** Xem SVG mới từ người đã follow
- **Verification:** Email verification với 6-digit code

### 5. Search & Discovery
- **Dual-mode Search:** Tìm theo keywords hoặc username
- **Auto-suggestions:** Real-time suggestions cho keywords
- **Fuzzy Search:** Tìm kiếm gần đúng
- **Keyword Tagging:** Gắn thẻ cho SVG files

### 6. File Management
- **File Upload:** Tạo và lưu SVG files
- **Format Conversion:** SVG → PNG/JPEG với DPI customization
- **File Actions:** Download, share, copy link, delete
- **Keywords:** Tagging system cho dễ tìm kiếm
- **View Statistics:** Likes count, views count

### 7. Documentation
- **Comprehensive Docs:** Trang `/docs` với full documentation
- **Interactive TOC:** Sidebar navigation với smooth scrolling
- **Code Examples:** TikZ code examples với syntax highlighting
- **FAQ Section:** Câu hỏi thường gặp
- **User Guides:** Hướng dẫn chi tiết cho từng tính năng

---

## 🛠️ Kiến trúc

### Backend
- **Framework:** Flask 3.1.1 với Gunicorn cho production
- **Database:** MySQL với mysql-connector-python
- **Authentication:** Google OAuth2 + Flask-Login + Flask-Dance
- **TikZ Processing:** 
  - Tự động phát hiện `\usepackage`, `\usetikzlibrary`, `\usepgfplotslibrary`
  - Manual package specification: `%!<\usepackage{...}>` với options support
  - Sử dụng lualatex để biên dịch .tex → PDF → SVG (pdf2svg)
  - CairoSVG + Pillow để chuyển đổi SVG → PNG/JPEG
- **Package Management:**
  - Whitelist-based package system với 50+ packages
  - User package request system với status tracking
  - Admin approval workflow
- **Comments System:**
  - LaTeX math rendering với MathJax
  - TikZ code blocks với copy functionality
  - Nested replies support
- **Email Service:** Flask-Mail với Zoho SMTP
- **Rate Limiting:** Custom implementation cho email, API và package requests
- **Static Files:** Flask static folder với persistent storage
- **File Management:** Unique naming cho SVG files và avatars
- **API Endpoints:**
  - `/api/svg/<svg_id>/likes` - Lấy danh sách users đã like SVG (pagination)
  - `/api/keywords/search` - Auto-suggestions cho keywords
  - `/api/comments/` - CRUD operations cho comments
  - `/packages` - Package listing và request system
  - `/docs` - Comprehensive documentation page

### Frontend
- **Template Engine:** Jinja2 với partials (reusable components)
- **CSS Architecture:** CSS Foundation System với master variables
  - **Foundation Files:** `master-variables.css`, `global-base.css`
  - **Design System:** Colors, spacing, typography, glass morphism variables
  - **Migration Status:** 6/10 priority files completed (index.css, profile_*.css)
  - **Load Order:** Foundation → Global Base → Component CSS
  - **Optimization:** Pagination, lazy loading, optimistic UI updates
- **JavaScript:** Vanilla JS (ES6+) với AJAX/Fetch API
- **External Libraries:**
  - **CodeMirror:** Trình soạn thảo code cho TikZ với syntax highlighting
  - **MathJax:** Render LaTeX math trong comments
  - **Quill.js:** Rich text editor cho user bio
  - **Cropper.js:** Cắt và chỉnh sửa ảnh đại diện
- **UI Components:** 
  - Modal dialogs (login, likes, delete confirmation)
  - File upload với preview
  - Real-time interactions (likes, follows, comments)
  - Search bar với auto-suggestions
  - Mobile-friendly 2-tap menu system
- **Design Features:** 
  - Glass morphism với backdrop blur
  - Responsive design (mobile-first)
  - WCAG AAA accessibility compliance (contrast ≥ 6.2:1)
  - Smooth transitions và hover effects
- **Real-time Features:** 
  - Polling cho likes, follows, new posts
  - Optimistic UI updates
  - Real-time MathJax preview trong comment editor
- **Search System:**
  - Dual-mode search (keywords/username)
  - Auto-suggestions cho keywords
  - Fuzzy search support
- **Comments System:**
  - LaTeX math inline `$...$` và display `$$...$$`
  - TikZ code blocks `\code{...}` với copy button
  - Nested replies support
  - Like/unlike comments
  - Edit/delete với confirmation

### Database Schema
- **Users:** id, email, username, avatar, bio, identity_verified, created_at
- **SVG Files:** user_id, filename, original_tikz, created_at, likes, views, keywords
- **User Interactions:** 
  - follows (follower_id, followed_id)
  - likes (user_id, svg_filename)
  - comments (id, user_id, svg_filename, parent_id, content, likes, edited)
- **Package Management:**
  - packages (name, type, is_active, requires_manual, options_support)
  - package_requests (user_id, package_name, justification, priority, status)
- **Email Logs:** Tracking email sending và delivery
- **Rate Limit Logs:** Monitoring API usage
- **Verification:** Email verification codes với expiry

### File Structure
**Reference:** See `docs/PROJECT_STRUCTURE.md` for complete file tree and documentation listing.

**Key directories:**
- `app.py` - Main Flask application (4000+ lines)
- `static/` - CSS, JS, images, avatars with CSS Foundation System
- `templates/` - Jinja2 templates with partials
- `docs/` - Separated documentation (this optimization)
- `*.md` - 15+ documentation files

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
- **Security:** 
  - Validate input, sanitize data, implement CSRF protection
  - XSS protection: HTML escaping cho user-generated content
  - Rate limiting cho all endpoints nhạy cảm
  - Whitelist-based package system
- **Performance:** 
  - Optimize database queries với indexes
  - Implement pagination (20 items per page)
  - Lazy loading và optimistic UI updates
  - Redis caching cho VPS deployment
- **TikZ Processing:** 
  - Implement timeout (30s) và error handling cho lualatex
  - Auto-detection packages với regex patterns
  - Manual package specification parsing `%!<...>`
  - Package options support `[option1,option2]`
- **File Upload:** Validate file types, implement size limits (10MB SVG, 60MP images)
- **Real-time Updates:** Implement efficient polling mechanisms với debouncing
- **Environment Variables:** Sử dụng `os.environ.get()` với default values
- **Comments System:**
  - MathJax rendering cho LaTeX math
  - Nested braces parsing cho TikZ code blocks
  - XSS protection với double escaping
  - Character limit (5000) với validation
- **CSS Architecture:** Tuân thủ CSS Foundation migration methodology
  - **Variables First:** Luôn sử dụng `var(--variable-name)` thay vì hardcoded values
  - **Scoping:** Tất cả selectors phải có `.tikz-app` prefix
  - **No Conflicts:** Tránh duplicate html/body/:root rules
  - **Glass Morphism:** Sử dụng foundation glass variables cho UI transparency
  - **Responsive:** Foundation breakpoint variables cho consistency
  - **Accessibility:** WCAG AAA compliance (contrast ≥ 6.2:1)

### 3. Testing
**Reference:** See `docs/TESTING_STRATEGY.md` for comprehensive testing approach.

**Key areas:**
- Unit tests with pytest
- Integration tests for APIs
- TikZ processing pipeline tests
- Comments system security tests
- Accessibility compliance (WCAG AAA)
- Target: ≥70% coverage for critical paths

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

**References:**
- `docs/PROJECT_STRUCTURE.md` - Complete file listing and organization
- `docs/DEVELOPMENT_BEST_PRACTICES.md` - Comprehensive development guidelines
- `docs/CSS_FOUNDATION_SYSTEM.md` - CSS architecture and migration guide

**Key documentation in root:**
- `DOCS_CONTENT_COMPILATION.md` - User-facing feature documentation (437+ sections)
- `DATABASE_DOCUMENTATION.md` - Database schema and queries (19 tables)
- `API_ENDPOINTS_DOCUMENTATION.md` - REST API reference (80+ endpoints)
- `WORKFLOW_GUIDE.md` - VPS deployment and configuration

## 🚀 Deployment

### Production Environment
- **VPS Setup:** Sử dụng symbolic links cho static files
- **Database:** MySQL với connection pooling
- **Web Server:** Gunicorn với multiple workers (4 workers recommended)
- **Static Files:** Persistent storage với shared directory
- **Caching:** Redis cho session và rate limiting
- **Backup:** Automated database và file backups
- **Security:** 
  - HTTPS với SSL certificate
  - Rate limiting với Redis backend
  - IP tracking với ProxyFix middleware
  - CSRF protection enabled

### Development Environment
- **Local Setup:** Flask development server (`python app.py`)
- **Database:** Local MySQL instance
- **Email:** Zoho SMTP sandbox
- **File Storage:** Local static directory
- **Testing:** pytest với coverage reports

### Recent Updates (2024)
- **Nov 2024:** Package request system, documentation page
- **Oct 2024:** Likes modal pagination, enhanced search, timezone fixes
- **Sep 2024:** Profile verification, follow/unfollow, CSS foundation migration
- **Aug 2024:** Package options support, comments system, rate limiting improvements

Claude nên tham khảo các file documentation này khi hỗ trợ development.

---

## 📄 Main Pages & Routes

**Reference:** See `docs/PROJECT_STRUCTURE.md` for complete route and template listing.

**Key endpoints:**
- **Public:** `/`, `/docs`, `/packages`, `/search`, `/view_svg`
- **User:** `/profile/*`, `/profile/verification`
- **Admin:** `/admin/*`
- **API:** `/api/svg/*`, `/api/comments/*`, `/api/keywords/search`
- **Email:** 6 Zoho SMTP templates in `templates/emails/`

---

## 🎨 CSS Foundation System

**Reference:** See `docs/CSS_FOUNDATION_SYSTEM.md` for complete architecture guide.

**Key requirements:**
- Load order: master-variables.css → global-base.css → component.css
- Use `var(--variable-name)` instead of hardcoded values
- All selectors must have `.tikz-app` prefix
- Migration status: 6/10 files completed
- Accessibility: WCAG AAA compliance (contrast ≥ 6.2:1)

---

## 🎯 Development Best Practices

**Reference:** See `docs/DEVELOPMENT_BEST_PRACTICES.md` for comprehensive guidelines.

**Core principles:**
- **Security first:** Validate input, escape output, rate limiting
- **Documentation:** Update .md files with changes
- **Testing:** Unit, integration, and manual testing
- **CSS Foundation:** Use design variables, no hardcoding
- **Accessibility:** WCAG AAA compliance
- **Mobile-first:** Responsive design approach

**Critical workflows:**
- TikZ processing: Package whitelist, timeout protection, memory management
- Comments system: XSS protection, MathJax rendering, character limits
- CSS development: Foundation variables, scoping, cross-browser testing
- Deployment: Staging testing, Redis verification, backup database

---

## 📞 Support & Communication

### Khi cần giúp đỡ
- **Documentation:** Check `DOCS_CONTENT_COMPILATION.md` first
- **Troubleshooting:** Xem `TROUBLESHOOTING_TEST_CASE_3.md`
- **Package Issues:** Check `PACKAGE_DETECTION_IMPROVEMENT.md`
- **CSS Issues:** Check `CSS_OVERRIDE_PREVENTION_GUIDE.md`
- **Workflow:** Follow `WORKFLOW_GUIDE.md`

### Reporting Issues
- **Bug reports:** Include reproduction steps, screenshots, logs
- **Feature requests:** Explain use case và benefit
- **Security issues:** Report privately, không public

### Contributing
- **Fork & PR:** Follow git workflow
- **Code review:** Wait for review trước khi merge
- **Tests:** All PRs must include tests
- **Documentation:** Update docs trong cùng PR
