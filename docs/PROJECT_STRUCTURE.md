# Project Structure and Documentation

## File Structure

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
└── deployment/           # Deployment scripts
```

## Documentation Files

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

## Main Pages & Routes

### Public Pages
- `/` (index.html) - TikZ editor với CodeMirror, search bar, recent SVGs
- `/docs` (docs.html) - Comprehensive documentation với sidebar TOC
- `/packages` (packages.html) - Package listing (Active & Manual packages)
- `/packages/request` (package_request.html) - Package request form
- `/search` (search_results.html) - Search results với dual-mode (keywords/username)
- `/view_svg.html?filename=...` - SVG detail page với comments system
- `/privacy_policy` - Privacy policy
- `/terms_of_service` - Terms of service

### User Pages (Authentication Required)
- `/profile/<user_id>` (profile_svg_files.html) - User profile với SVG gallery
- `/profile/<user_id>/settings` (profile_settings.html) - Profile settings, avatar upload
- `/profile/<user_id>/followed_posts` (profile_followed_posts.html) - Feed từ followed users
- `/profile/verification` (profile_verification.html) - Email verification flow

### Admin Pages (Admin Only)
- `/admin/packages` (admin/packages.html) - Package management panel
- `/admin/analytics` (admin/analytics.html) - Analytics dashboard

### API Endpoints
- GET `/api/svg/<svg_id>/likes` - Paginated likes list (20 per page)
- GET `/api/keywords/search?q=...` - Keyword auto-suggestions
- POST `/api/comments/` - Create new comment
- PUT `/api/comments/<id>` - Edit comment
- DELETE `/api/comments/<id>` - Delete comment
- POST `/api/comments/<id>/like` - Like/unlike comment
- POST `/api/comments/<id>/reply` - Reply to comment

### Email Templates (Zoho SMTP)
- `emails/welcome.html` - Welcome email for new users
- `emails/account_verification.html` - Email verification code
- `emails/profile_settings_verification.html` - Profile verification
- `emails/notification.html` - General notifications
- `emails/svg_verification.html` - SVG-related notifications
- `emails/identity_verification.html` - Identity verification