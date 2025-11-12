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

Before working on this codebase, **YOU MUST** read these 4 critical documentation files. They contain essential information about the project architecture, database schema, API endpoints, and comprehensive feature documentation.

### 📊 Quick Reference Table

| File | Purpose | Key Information | Lines | Status |
|------|---------|----------------|-------|--------|
| **DATABASE_DOCUMENTATION.md** | Database schema & queries | 19 tables, relationships, SQL examples | 1,390+ | ✅ Complete |
| **API_ENDPOINTS_DOCUMENTATION.md** | REST API reference | 80+ endpoints, rate limits, security | 1,700+ | ✅ Complete |
| **DOCS_CONTENT_COMPILATION.md** | User documentation | 437+ docs sections, features guide | 1,357+ | ✅ Complete |
| **WORKFLOW_GUIDE.md** | Deployment & configuration | VPS setup, Redis, static files | 517+ | ✅ Complete |

---

### 📁 DATABASE_DOCUMENTATION.md

**File Path:** `/Users/hieplequoc/Projects/claudekit_tikz2svg_api/DATABASE_DOCUMENTATION.md`

**What's Inside:**
- **19 Database Tables:** Complete schema with CREATE statements, field descriptions, indexes, and foreign keys
- **Table Categories:**
  - Core: `user`, `svg_image`, `keyword`, `svg_image_keyword`
  - Social: `svg_like`, `user_follow`, `svg_comments`, `svg_comment_likes`
  - Notifications: `notifications`, `email_notifications`, `email_log`
  - Security: `verification_tokens`, `user_action_log`, `svg_action_log`
  - Packages: `supported_packages`, `package_requests`, `package_changelog`, `package_usage_stats`
  - Admin: `admin_permissions`
- **Relationships Diagram:** Entity-relationship mapping with cardinality
- **Essential Queries:** 60+ SQL query examples for common operations
- **Database Report:** Real-time statistics with 10 users, 48 SVGs, 10 comments

**When to Read:**
- ✅ Before implementing any database-related feature
- ✅ When adding new tables or modifying schema
- ✅ When debugging data-related issues
- ✅ When writing SQL queries or ORM operations
- ✅ When planning migrations or schema changes

**Key Sections:**
```bash
# Jump to specific sections
grep "### 1. Bảng" DATABASE_DOCUMENTATION.md    # User table
grep "### 2. Bảng" DATABASE_DOCUMENTATION.md    # SVG images
grep "### 13. Bảng" DATABASE_DOCUMENTATION.md   # Notifications
grep "### 14. Bảng" DATABASE_DOCUMENTATION.md   # Comments
grep "## Các truy vấn chính" DATABASE_DOCUMENTATION.md  # Query examples
```

**Critical Insights:**
- Profile verification uses **5-reuse limit** for codes (10-minute window)
- Comments system supports **nested replies** (1 level)
- Package usage tracking with **denormalized counters** for performance
- Email logs track **success/failure** with error messages

---

### 📡 API_ENDPOINTS_DOCUMENTATION.md

**File Path:** `/Users/hieplequoc/Projects/claudekit_tikz2svg_api/API_ENDPOINTS_DOCUMENTATION.md`

**What's Inside:**
- **80+ REST API Endpoints:** Complete reference with request/response examples
- **11 Endpoint Categories:**
  1. System Info & Status (7 endpoints) - Platform info, health checks, metrics
  2. TikZ Compilation (3 endpoints) - Compile, cache, debug
  3. User Authentication (3 endpoints) - Login status, verification
  4. Social Features (9 endpoints) - Likes, follows, follower counts
  5. Comments System (6 endpoints) - CRUD, likes, replies
  6. Search & Discovery (3 endpoints) - Search files, keyword suggestions
  7. Package Management (7 endpoints) - List, request, stats, popular
  8. File Management (4 endpoints) - Save, convert, caption, delete
  9. Notifications (4 endpoints) - Unread count, list, mark read
  10. Admin APIs (6 endpoints) - Metrics, requests, cache control
  11. Rate Limits & Security - Comprehensive security documentation

**When to Read:**
- ✅ Before implementing new API endpoints
- ✅ When integrating frontend with backend
- ✅ When troubleshooting API errors or rate limits
- ✅ When adding authentication/authorization
- ✅ When planning API versioning or changes

**Quick Access Commands:**
```bash
# Find specific endpoint categories
grep "## 1. System Info" API_ENDPOINTS_DOCUMENTATION.md
grep "## 2. TikZ Compilation" API_ENDPOINTS_DOCUMENTATION.md
grep "## 5. Comments System" API_ENDPOINTS_DOCUMENTATION.md
grep "## 11. Rate Limits" API_ENDPOINTS_DOCUMENTATION.md

# Search for specific endpoints
grep "POST /compile" API_ENDPOINTS_DOCUMENTATION.md
grep "GET /api/svg" API_ENDPOINTS_DOCUMENTATION.md
grep "POST /api/comments" API_ENDPOINTS_DOCUMENTATION.md
```

**Rate Limiting Rules:**
| Endpoint Category | Limit | Window | Applies To |
|------------------|-------|--------|------------|
| General API | 1000 requests | 1 minute | All endpoints |
| Package Requests | 3 requests | 1 hour | Per user |
| Email Verification | 5 emails | 1 hour | Per user |
| Comments | 20 comments | 1 hour | Per user |
| Compilation | 5 concurrent | - | Global |
| File Upload | 10 files | 1 day | Per user |

**Security Features:**
- ✅ 25+ dangerous pattern detection for LaTeX
- ✅ Package whitelist enforcement (50+ packages)
- ✅ Resource limits: 45s timeout, 300MB memory, 5 concurrent
- ✅ Redis-based rate limiting with ProxyFix
- ✅ XSS protection via HTML escaping

---

### 📚 DOCS_CONTENT_COMPILATION.md

**File Path:** `/Users/hieplequoc/Projects/claudekit_tikz2svg_api/DOCS_CONTENT_COMPILATION.md`

**What's Inside:**
- **437+ Documentation Sections:** Complete user guide for all features
- **11 Major Topics:**
  1. Introduction & Overview - Platform description, tech stack
  2. Quick Start Guide - Registration, first TikZ conversion
  3. TikZ Compilation Details - Auto-detection, Unicode support, manual packages
  4. File Management & Actions - Card UI, menu actions, likes system
  5. Format Conversion - SVG → PNG/JPEG with DPI customization
  6. Comments System - LaTeX math, TikZ code blocks, nested replies
  7. Profile & Social - Follow/unfollow, profile settings, social feed
  8. Identity Verification - Email verification, security, unlocked features
  9. Search & Keywords - Dual-mode search, auto-suggestions
  10. Error Handling & Troubleshooting - Common issues, solutions
  11. Tips & Best Practices - Code examples, multi-device usage

**When to Read:**
- ✅ Before implementing user-facing features
- ✅ When writing UI/UX code or templates
- ✅ When debugging user workflow issues
- ✅ When creating help documentation or FAQs
- ✅ When planning new features that affect user experience

**Feature Highlights:**
```bash
# Navigate to key sections
grep "## 3. 🔧 Chức năng biên dịch" DOCS_CONTENT_COMPILATION.md
grep "### 3.3 🌏 Unicode" DOCS_CONTENT_COMPILATION.md
grep "### 3.4 📦 Manual Package" DOCS_CONTENT_COMPILATION.md
grep "## 6. 💬 Hệ thống Comments" DOCS_CONTENT_COMPILATION.md
grep "## 8. 🛡️ Xác thực danh tính" DOCS_CONTENT_COMPILATION.md
```

**User Workflows:**
1. **First-time User:** Registration → First SVG → Save → Like → Search
2. **Power User:** Advanced TikZ → Manual packages → Comments → Follow → Feed
3. **Verified User:** Email verification → Follow users → View followed posts
4. **Content Creator:** Multiple SVGs → Keywords → Engagement → Profile customization

**Critical User Limits:**
- SVG files: Max **10MB** per file, **10 files/day**
- Comments: Max **5000 characters**, rate limit **20/hour**
- Images: Max **60MP** (60,000,000 pixels), max **2000 DPI**
- Package requests: **3 requests/hour**

---

### 🔧 WORKFLOW_GUIDE.md

**File Path:** `/Users/hieplequoc/Projects/claudekit_tikz2svg_api/WORKFLOW_GUIDE.md`

**What's Inside:**
- **VPS Deployment Configuration:** Complete production setup guide
- **Key Topics:**
  - Static Files Configuration - Symbolic links, shared storage, file paths
  - Redis Server Setup - Rate limiting storage, installation, configuration
  - 502 Bad Gateway Troubleshooting - Symbolic link issues, avatar problems
  - File Storage Issues - WorkingDirectory, STATIC_ROOT, environment variables
  - Systemd Service Configuration - Environment files, service overrides
  - Monitoring & Verification - Health checks, cache stats, Redis monitoring

**When to Read:**
- ✅ Before deploying to production VPS
- ✅ When troubleshooting 502 errors or file storage issues
- ✅ When setting up Redis for rate limiting
- ✅ When configuring static file paths
- ✅ When debugging deployment-related issues

**Critical Configurations:**
```bash
# Redis Setup (REQUIRED for production)
sudo apt install redis-server
echo "REDIS_URL=redis://localhost:6379/0" >> /var/www/tikz2svg_api/shared/.env
sudo systemctl restart tikz2svg.service

# Static Files Configuration
ln -s /var/www/tikz2svg_api/shared/static /var/www/tikz2svg_api/current/static
echo "TIKZ_SVG_DIR=/var/www/tikz2svg_api/shared/static" >> /var/www/tikz2svg_api/shared/.env

# Verify Setup
redis-cli ping                    # Should return PONG
ls -la current/static            # Should show symlink → shared/static
python3 -c "import redis; ..."   # Test Redis connection
```

**Common Issues & Solutions:**
| Issue | Cause | Solution |
|-------|-------|----------|
| 502 Bad Gateway | Avatars symlink broken | Remove symlink, create real directory |
| Files saved wrong | STATIC_ROOT misconfigured | Set `TIKZ_SVG_DIR` in `.env` |
| Rate limiting broken | Redis not running | Install Redis, set `REDIS_URL` |
| Files lost on deploy | No symbolic links | Create symlink from current → shared |

**Deployment Checklist:**
- [ ] Redis server installed and running
- [ ] `REDIS_URL` set in `/var/www/tikz2svg_api/shared/.env`
- [ ] Systemd service configured with `EnvironmentFile`
- [ ] Static files symlink created (current → shared)
- [ ] `TIKZ_SVG_DIR` environment variable set
- [ ] Service restarted after configuration changes
- [ ] Health checks passing (logs show Redis storage)

---

### 🔗 Cross-Reference Patterns

**When implementing a new feature, check these files in order:**

1. **Planning Phase:**
   - Read `DOCS_CONTENT_COMPILATION.md` → Understand user requirements
   - Read `API_ENDPOINTS_DOCUMENTATION.md` → Plan API design
   - Read `DATABASE_DOCUMENTATION.md` → Design data schema

2. **Development Phase:**
   - Reference `DATABASE_DOCUMENTATION.md` → Write SQL queries
   - Reference `API_ENDPOINTS_DOCUMENTATION.md` → Implement endpoints
   - Reference `WORKFLOW_GUIDE.md` → Configure production settings

3. **Testing Phase:**
   - Verify against `API_ENDPOINTS_DOCUMENTATION.md` → Rate limits, responses
   - Verify against `DATABASE_DOCUMENTATION.md` → Data integrity
   - Test workflows from `DOCS_CONTENT_COMPILATION.md` → User flows

4. **Deployment Phase:**
   - Follow `WORKFLOW_GUIDE.md` → Production setup
   - Verify all checklist items → Ensure stability

**Example: Implementing Comments System**
```
Step 1: Read DOCS_CONTENT_COMPILATION.md § 6 (Comments System)
        → Understand: LaTeX math, TikZ code blocks, nested replies, like/unlike

Step 2: Read DATABASE_DOCUMENTATION.md § 14-15 (svg_comments, svg_comment_likes)
        → Schema: parent_comment_id, likes_count, content_hash, security fields

Step 3: Read API_ENDPOINTS_DOCUMENTATION.md § 5 (Comments System APIs)
        → Endpoints: GET/POST/PUT/DELETE, rate limits, authentication

Step 4: Implement backend → Test → Deploy following WORKFLOW_GUIDE.md
```

---

### ✅ Verification Checklist

Before starting development, confirm you've read:

- [ ] **DATABASE_DOCUMENTATION.md** - I understand the 19 tables, relationships, and key queries
- [ ] **API_ENDPOINTS_DOCUMENTATION.md** - I understand the 80+ endpoints, rate limits, and security
- [ ] **DOCS_CONTENT_COMPILATION.md** - I understand user workflows and feature requirements
- [ ] **WORKFLOW_GUIDE.md** - I understand deployment configuration and common issues

**Quick verification commands:**
```bash
# Confirm file existence and size
ls -lh DATABASE_DOCUMENTATION.md API_ENDPOINTS_DOCUMENTATION.md DOCS_CONTENT_COMPILATION.md WORKFLOW_GUIDE.md

# Count lines to verify completeness
wc -l DATABASE_DOCUMENTATION.md    # Should be ~1390 lines
wc -l API_ENDPOINTS_DOCUMENTATION.md  # Should be ~1700 lines
wc -l DOCS_CONTENT_COMPILATION.md     # Should be ~1357 lines
wc -l WORKFLOW_GUIDE.md                # Should be ~517 lines

# Quick content scan
head -20 DATABASE_DOCUMENTATION.md    # See table list
head -20 API_ENDPOINTS_DOCUMENTATION.md  # See endpoint categories
head -20 DOCS_CONTENT_COMPILATION.md     # See feature overview
head -20 WORKFLOW_GUIDE.md               # See deployment topics
```

---

### 🚀 Example Development Workflows

**Workflow 1: Adding a New Database Table**
```bash
1. Read DATABASE_DOCUMENTATION.md § 1-19 (existing tables)
2. Design new table schema following existing patterns
3. Write migration SQL with proper indexes and foreign keys
4. Update DATABASE_DOCUMENTATION.md with new table documentation
5. Test queries and update § "Các truy vấn chính"
```

**Workflow 2: Creating a New API Endpoint**
```bash
1. Read API_ENDPOINTS_DOCUMENTATION.md (find similar endpoint)
2. Read DATABASE_DOCUMENTATION.md (understand data requirements)
3. Read DOCS_CONTENT_COMPILATION.md (understand user workflow)
4. Implement endpoint following REST conventions
5. Add rate limiting following § 11 (Rate Limits & Security)
6. Document in API_ENDPOINTS_DOCUMENTATION.md
```

**Workflow 3: Implementing a User-Facing Feature**
```bash
1. Read DOCS_CONTENT_COMPILATION.md (understand user requirements)
2. Read API_ENDPOINTS_DOCUMENTATION.md (plan backend API)
3. Read DATABASE_DOCUMENTATION.md (design data model)
4. Implement feature (backend + frontend)
5. Test following user workflows from DOCS_CONTENT_COMPILATION.md
6. Deploy following WORKFLOW_GUIDE.md checklist
```

**Workflow 4: Troubleshooting Production Issues**
```bash
1. Read WORKFLOW_GUIDE.md § "Troubleshooting" sections
2. Check logs: sudo journalctl -u tikz2svg.service --no-pager -n 50
3. Verify Redis: redis-cli KEYS "LIMITER*"
4. Check static files: ls -la /var/www/tikz2svg_api/current/static
5. Verify environment: cat /var/www/tikz2svg_api/shared/.env
6. Test endpoints from API_ENDPOINTS_DOCUMENTATION.md
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
```
tikz2svg_api/
├── app.py                 # Main Flask application (4000+ lines)
├── requirements.txt       # Python dependencies
├── static/               # Static files (CSS, JS, images, avatars)
│   ├── css/              # Component-based CSS files
│   │   ├── foundation/   # CSS Foundation System
│   │   │   ├── master-variables.css  # Design system variables
│   │   │   └── global-base.css       # Global base styles
│   │   ├── index.css     # Main page styles (migrated)
│   │   ├── docs.css      # Documentation page styles
│   │   ├── packages.css  # Package management page
│   │   ├── profile_*.css # Profile pages (migrated)  
│   │   ├── search_results.css # Search page styles
│   │   ├── file_card.css # File components
│   │   └── navigation.css # Navigation styles
│   ├── js/               # JavaScript modules
│   │   ├── index.js      # Main page logic
│   │   ├── file_card.js  # File card interactions (v1.3)
│   │   ├── navigation.js # Navigation và search
│   │   └── comments.js   # Comments system
│   ├── images/           # Generated SVG files
│   └── avatars/          # User profile images
├── templates/            # Jinja2 templates
│   ├── partials/         # Reusable template components
│   │   ├── _navbar.html  # Navigation bar
│   │   ├── _file_card.html # File card component
│   │   └── _login_modal.html # Login modal
│   ├── emails/           # Email templates (6 templates)
│   ├── admin/            # Admin panel templates
│   ├── index.html        # Main TikZ editor page
│   ├── docs.html         # Documentation page
│   ├── packages.html     # Package listing
│   ├── package_request.html # Package request form
│   ├── view_svg.html     # SVG detail với comments
│   ├── search_results.html # Search results page
│   ├── profile_*.html    # Profile pages
│   └── *.html            # Other page templates
├── email_service.py      # Email functionality
├── verification_service.py # Identity verification
├── *.md                  # Documentation files (15+ files)
│   ├── DOCS_CONTENT_COMPILATION.md # Full docs content
│   ├── CUOC_THI_VNFEAI_2025.md # Competition docs
│   ├── CSS_FOUNDATION_*.md # CSS architecture docs
│   └── USER_GUIDE_*.md   # User guides
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
- **Unit Tests:** Sử dụng pytest cho backend testing
- **Integration Tests:** Test API endpoints và database operations
- **Frontend Tests:** Test JavaScript functionality
- **TikZ Processing Tests:** 
  - Test conversion pipeline end-to-end
  - Test package auto-detection
  - Test manual package specification
  - Test package options parsing
- **Comments System Tests:**
  - Test LaTeX math rendering
  - Test TikZ code block parsing
  - Test XSS protection
  - Test nested replies
- **Email Tests:** Test email sending và templates
- **Rate Limiting Tests:** Test API throttling (email, package requests, comments)
- **CSS Regression Tests:** Visual testing sau migration
- **Accessibility Tests:** 
  - Contrast ratio ≥ 6.2:1 (WCAG AAA)
  - Keyboard navigation
  - Screen reader compatibility
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

### Core Documentation
- `DOCS_CONTENT_COMPILATION.md` - Tổng hợp đầy đủ nội dung cho trang /docs
- `CUOC_THI_VNFEAI_2025.md` - Tài liệu tham gia cuộc thi VNFEAI 2025
- `FACEBOOK_POST_TIKZ2SVG.md` - Marketing content cho Facebook

### Technical Documentation
- `EMAIL_SETUP_GUIDE.md` - Hướng dẫn setup email với Zoho
- `VERIFICATION_SYSTEM_GUIDE.md` - Hệ thống xác thực danh tính  
- `RATE_LIMIT_GUIDE.md` - Rate limiting cho API và email
- `WORKFLOW_GUIDE.md` - Quy trình phát triển
- `DATABASE_DOCUMENTATION.md` - Schema và queries
- `STATIC_FILES_CONFIGURATION.md` - Cấu hình static files

### Package System Documentation
- `MANUAL_PACKAGE_SPECIFICATION.md` - Hướng dẫn manual package spec
- `PACKAGE_DETECTION_IMPROVEMENT.md` - Package detection system
- `CHANGELOG_PACKAGE_OPTIONS.md` - Package options changelog
- `FINAL_SUMMARY_PACKAGE_OPTIONS.md` - Package system summary
- `README_PACKAGE_SYSTEM.md` - Package system overview
- `TROUBLESHOOTING_TEST_CASE_3.md` - Troubleshooting guide

### CSS Architecture Documentation
- `CSS_FOUNDATION_MIGRATION_SUMMARY.md` - Complete migration report
- `CSS_ARCHITECTURE_MIGRATION_STATUS.md` - Progress tracker (6/10 complete)
- `CSS_OVERRIDE_PREVENTION_GUIDE.md` - Prevention guidelines
- `CSS_REFACTOR_COMPLETE_REPORT.md` - Refactor report

### User Guides
- `USER_GUIDE_CJK_CHARACTERS.md` - Hướng dẫn sử dụng chữ CJK
- `CHINESE_CHARACTERS_ANALYSIS.md` - Phân tích Unicode support
- `FIX_DICT_COMPARISON_ERROR.md` - Troubleshooting guide

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

### Public Pages
- **`/` (index.html)** - TikZ editor với CodeMirror, search bar, recent SVGs
- **`/docs` (docs.html)** - Comprehensive documentation với sidebar TOC
- **`/packages` (packages.html)** - Package listing (Active & Manual packages)
- **`/packages/request` (package_request.html)** - Package request form
- **`/search` (search_results.html)** - Search results với dual-mode (keywords/username)
- **`/view_svg.html?filename=...`** - SVG detail page với comments system
- **`/privacy_policy`** - Privacy policy
- **`/terms_of_service`** - Terms of service

### User Pages (Authentication Required)
- **`/profile/<user_id>` (profile_svg_files.html)** - User profile với SVG gallery
- **`/profile/<user_id>/settings` (profile_settings.html)** - Profile settings, avatar upload
- **`/profile/<user_id>/followed_posts` (profile_followed_posts.html)** - Feed từ followed users
- **`/profile/verification` (profile_verification.html)** - Email verification flow

### Admin Pages (Admin Only)
- **`/admin/packages` (admin/packages.html)** - Package management panel
- **`/admin/analytics` (admin/analytics.html)** - Analytics dashboard

### API Endpoints
- **GET `/api/svg/<svg_id>/likes`** - Paginated likes list (20 per page)
- **GET `/api/keywords/search?q=...`** - Keyword auto-suggestions
- **POST `/api/comments/`** - Create new comment
- **PUT `/api/comments/<id>`** - Edit comment
- **DELETE `/api/comments/<id>`** - Delete comment
- **POST `/api/comments/<id>/like`** - Like/unlike comment
- **POST `/api/comments/<id>/reply`** - Reply to comment

### Email Templates (Zoho SMTP)
- **`emails/welcome.html`** - Welcome email for new users
- **`emails/account_verification.html`** - Email verification code
- **`emails/profile_settings_verification.html`** - Profile verification
- **`emails/notification.html`** - General notifications
- **`emails/svg_verification.html`** - SVG-related notifications
- **`emails/identity_verification.html`** - Identity verification

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

---

## 🎯 Best Practices khi phát triển

### Khi thêm tính năng mới
1. **Đọc documentation trước:** Kiểm tra `DOCS_CONTENT_COMPILATION.md` để hiểu hệ thống
2. **Tuân thủ patterns hiện có:** Follow existing code patterns và conventions
3. **Security first:** Validate input, escape output, implement rate limiting
4. **Update documentation:** Cập nhật các file .md liên quan
5. **Test thoroughly:** Unit tests, integration tests, manual testing
6. **CSS Foundation:** Sử dụng design system variables, không hardcode
7. **Accessibility:** Đảm bảo WCAG AAA compliance
8. **Mobile-first:** Test trên mobile trước khi desktop

### Khi sửa bugs
1. **Reproduce bug:** Xác nhận bug trên local environment
2. **Check related code:** Tìm code liên quan có thể bị ảnh hưởng
3. **Fix root cause:** Sửa nguyên nhân gốc, không chỉ symptoms
4. **Test regressions:** Đảm bảo fix không gây lỗi mới
5. **Update tests:** Thêm test cases cho bug đã fix
6. **Document fix:** Ghi rõ trong commit message và changelog

### Khi làm việc với TikZ Processing
1. **Test với nhiều cases:** Simple, complex, edge cases
2. **Handle errors gracefully:** Proper error messages cho users
3. **Timeout protection:** Không để compilation chạy vô hạn
4. **Package whitelist:** Chỉ allow packages đã được approve
5. **Security validation:** Validate all user-provided LaTeX code
6. **Memory management:** Cleanup temp files sau compilation

### Khi làm việc với Comments System
1. **XSS protection:** Always escape HTML, double-escape code blocks
2. **MathJax testing:** Test với complex LaTeX formulas
3. **Nested braces:** Test TikZ code với nhiều levels của {}
4. **Character limits:** Enforce 5000 char limit
5. **Rate limiting:** Prevent comment spam
6. **Real-time preview:** Ensure MathJax renders correctly

### Khi làm việc với CSS
1. **Foundation first:** Check master-variables.css trước
2. **No hardcoding:** Use var(--variable-name) always
3. **Scoping:** Prefix với .tikz-app
4. **Responsive:** Test breakpoints (mobile, tablet, desktop)
5. **Accessibility:** Check contrast ratios
6. **Browser testing:** Chrome, Firefox, Safari, Edge

### Khi deploy
1. **Backup database:** Luôn backup trước khi deploy
2. **Test staging:** Deploy to staging environment first
3. **Check logs:** Monitor error logs sau deploy
4. **Performance:** Check page load times, API response times
5. **Redis:** Ensure Redis running cho rate limiting
6. **Static files:** Verify symbolic links working
7. **SSL:** Ensure HTTPS certificates valid

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
