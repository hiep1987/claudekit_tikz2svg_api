# Comments Feature - Quy trình Thực hiện Chi tiết

**Date:** 2025-10-22  
**Project:** TikZ2SVG API  
**Feature:** Comments System for View SVG Page  
**Estimated Time:** 30-42 hours (4-5 working days)

---

## 🎯 Tổng quan

Triển khai hệ thống bình luận hoàn chỉnh cho trang `view_svg.html`, bao gồm:
- ✅ Post, edit, delete comments
- ✅ Reply to comments (1 level)
- ✅ Like/unlike comments
- ✅ MathJax support
- ✅ Real-time updates
- ✅ Responsive design

---

## 📋 QUY TRÌNH 10 BƯỚC

### BƯỚC 1: CHUẨN BỊ (1 hour)

#### 1.1. Review Documents

**Files cần đọc:**
```
✓ COMMENTS_FEATURE_IMPLEMENTATION_PLAN.md    (Full roadmap)
✓ DATABASE_STATUS_REPORT.md                  (Current state)
✓ DATABASE_SCHEMA_CONSISTENCY_CHECK.md       (Validation)
✓ IMAGE_CAPTION_FEATURE_GUIDE.md             (Reference)
```

**Checklist:**
- [ ] Đọc hiểu toàn bộ architecture
- [ ] Hiểu rõ 10 phases
- [ ] Note các điểm quan trọng
- [ ] Chuẩn bị môi trường dev

#### 1.2. Setup Development Environment

**Terminal commands:**
```bash
cd /Users/hieplequoc/web/work/tikz2svg_api

# Check current branch
git branch --show-current

# Create feature branch
git checkout -b feature/comments-system

# Verify database connection
mysql -u hiep1987 -p96445454 tikz2svg_local -e "SELECT COUNT(*) FROM svg_image;"

# Check if venv is active
which python3

# If not, activate venv
source venv/bin/activate
```

**Checklist:**
- [ ] Git branch created: `feature/comments-system`
- [ ] Database accessible
- [ ] Python venv active
- [ ] Development server can start

---

### BƯỚC 2: DATABASE MIGRATION (2-3 hours)

#### 2.1. Create Migration Script

**File:** `add_comments_system.sql`

**Copy from:** `COMMENTS_FEATURE_IMPLEMENTATION_PLAN.md` Section 1.4 (lines 127-210)

**Terminal:**
```bash
# Create file
touch add_comments_system.sql

# Copy content from Section 1.4
# (Use your editor to copy the SQL script)
```

**Checklist:**
- [ ] File `add_comments_system.sql` created
- [ ] Contains all 6 steps
- [ ] Includes verification queries
- [ ] Has rollback instructions

#### 2.2. Backup Database

**Terminal:**
```bash
# Create backup
mysqldump -u hiep1987 -p96445454 tikz2svg_local > backup_before_comments_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_before_comments_*.sql
```

**Checklist:**
- [ ] Backup file created
- [ ] File size > 0 bytes
- [ ] Filename contains timestamp

#### 2.3. Test Migration (Dry Run)

**Terminal:**
```bash
# Check SQL syntax (optional)
mysql -u hiep1987 -p96445454 tikz2svg_local --execute="source add_comments_system.sql" --verbose
```

**Expected output:**
```
Creating svg_comments...
Creating svg_comment_likes...
Adding foreign keys...
Updating svg_image...
Verification complete!
```

**Checklist:**
- [ ] No SQL syntax errors
- [ ] All tables created
- [ ] Foreign keys added
- [ ] Indexes created

#### 2.4. Run Migration

**Terminal:**
```bash
# Execute migration
mysql -u hiep1987 -p96445454 tikz2svg_local < add_comments_system.sql
```

**Checklist:**
- [ ] Migration completed without errors
- [ ] See success messages

#### 2.5. Verify Migration

**Terminal:**
```bash
# Check new tables
mysql -u hiep1987 -p96445454 tikz2svg_local -e "SHOW TABLES LIKE 'svg_comment%';"

# Verify svg_comments structure
mysql -u hiep1987 -p96445454 tikz2svg_local -e "DESCRIBE svg_comments;" 2>&1 | grep -v Warning

# Verify svg_comment_likes structure
mysql -u hiep1987 -p96445454 tikz2svg_local -e "DESCRIBE svg_comment_likes;" 2>&1 | grep -v Warning

# Check new column in svg_image
mysql -u hiep1987 -p96445454 tikz2svg_local -e "SHOW COLUMNS FROM svg_image WHERE Field = 'comments_count';" 2>&1 | grep -v Warning

# Check indexes
mysql -u hiep1987 -p96445454 tikz2svg_local -e "SHOW INDEX FROM svg_image WHERE Key_name IN ('idx_filename', 'idx_comments_count');" 2>&1 | grep -v Warning

# Check foreign keys
mysql -u hiep1987 -p96445454 tikz2svg_local -e "
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    REFERENCED_TABLE_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'tikz2svg_local'
  AND CONSTRAINT_NAME LIKE 'fk_comment%';
" 2>&1 | grep -v Warning
```

**Expected results:**
```
✓ 2 tables: svg_comments, svg_comment_likes
✓ svg_comments has 11 columns
✓ svg_comment_likes has 4 columns
✓ svg_image has comments_count column
✓ idx_filename exists on svg_image
✓ idx_comments_count exists on svg_image
✓ 5 foreign key constraints exist
```

**Checklist:**
- [ ] `svg_comments` table exists
- [ ] `svg_comment_likes` table exists
- [ ] `svg_image.comments_count` column exists
- [ ] `svg_image.idx_filename` index exists
- [ ] All 5 foreign keys exist
- [ ] No errors in verification

#### 2.6. Update DATABASE_DOCUMENTATION.md

**File:** `DATABASE_DOCUMENTATION.md`

**Add after Caption section:**

Copy Section "7. Hệ thống Comments" from `COMMENTS_FEATURE_IMPLEMENTATION_PLAN.md` (lines ~257-450)

**Checklist:**
- [ ] Added section 7 with SQL queries
- [ ] Documented all CRUD operations
- [ ] Added statistics queries
- [ ] Updated changelog

#### 2.7. Git Commit

**Terminal:**
```bash
git add add_comments_system.sql DATABASE_DOCUMENTATION.md
git commit -m "feat(database): Add comments system schema

- Add svg_comments table (11 columns, 5 indexes, 3 FKs)
- Add svg_comment_likes table (4 columns, 3 indexes, 2 FKs)
- Add comments_count to svg_image
- Add idx_filename to svg_image for performance
- Update DATABASE_DOCUMENTATION.md with Comments queries

Migration tested and verified in tikz2svg_local database."
```

**Checklist:**
- [ ] Migration script committed
- [ ] Documentation updated
- [ ] Commit message descriptive

---

### BƯỚC 3: BACKEND API - PART 1 (3-4 hours)

#### 3.1. Update `/view_svg/<filename>` Route

**File:** `app.py`

**Location:** Find `@app.route('/view_svg/<filename>')`

**Changes:**

1. Update SELECT query to include `comments_count`:
```python
cursor.execute("""
    SELECT tikz_code, user_id, caption, comments_count
    FROM svg_image 
    WHERE filename = %s 
    LIMIT 1
""", (filename,))
```

2. Extract `comments_count`:
```python
comments_count = row.get('comments_count', 0)
```

3. Pass to template:
```python
return render_template(
    "view_svg.html",
    # ... existing params ...
    caption=caption,
    comments_count=comments_count  # NEW
)
```

**Checklist:**
- [ ] SELECT query updated
- [ ] `comments_count` extracted
- [ ] Passed to template
- [ ] No syntax errors

#### 3.2. Create API Endpoint: `GET /api/comments/<filename>`

**File:** `app.py`

**Location:** After caption update endpoint

**Copy code from:** `COMMENTS_FEATURE_IMPLEMENTATION_PLAN.md` Section 2.2 (lines ~260-350)

**Key features:**
- Pagination support (page, per_page)
- Sort by newest/oldest
- Check if user has liked
- Return user info (username, avatar, verified badge)

**Checklist:**
- [ ] Function `get_comments(filename)` created
- [ ] Query params parsed (page, per_page, sort)
- [ ] SQL query with pagination
- [ ] User like status checked
- [ ] Datetime formatted to ISO
- [ ] Returns JSON response

#### 3.3. Create API Endpoint: `GET /api/comments/<id>/replies`

**File:** `app.py`

**Copy code from:** Section 2.3 (lines ~352-420)

**Key features:**
- Load replies for a comment
- Ordered by created_at ASC
- Include user info and like status

**Checklist:**
- [ ] Function `get_comment_replies(comment_id)` created
- [ ] Query replies by parent_comment_id
- [ ] Returns formatted JSON

#### 3.4. Test Endpoints

**Terminal:**
```bash
# Start dev server
python3 app.py

# In another terminal, test GET comments (empty)
curl -s http://localhost:5173/api/comments/115852900894156127858_060414240825.svg | python3 -m json.tool
```

**Expected response:**
```json
{
  "success": true,
  "comments": [],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 0,
    "total_pages": 0
  }
}
```

**Checklist:**
- [ ] Server starts without errors
- [ ] `/api/comments/<filename>` returns 200
- [ ] Response structure correct
- [ ] Empty comments array (expected)

#### 3.5. Git Commit

```bash
git add app.py
git commit -m "feat(api): Add GET endpoints for comments

- GET /api/comments/<filename> with pagination
- GET /api/comments/<id>/replies for nested comments
- Include user info and like status
- Support sorting by newest/oldest"
```

---

### BƯỚC 4: BACKEND API - PART 2 (3-4 hours)

#### 4.1. Create API Endpoint: `POST /api/comments/<filename>`

**File:** `app.py`

**Copy code from:** Section 2.4 (lines ~422-550)

**Key features:**
- Create top-level comment or reply
- Input validation (length, required fields)
- XSS sanitization
- Update denormalized counts

**Checklist:**
- [ ] Function `create_comment(filename)` created
- [ ] `@login_required` decorator
- [ ] Validation: empty check, max length
- [ ] Sanitization: remove `<script>`, `<iframe>`, `on*` handlers
- [ ] Check SVG exists
- [ ] Check parent comment exists (for replies)
- [ ] INSERT comment
- [ ] UPDATE `svg_image.comments_count`
- [ ] UPDATE `parent_comment.replies_count` (if reply)
- [ ] Return created comment

#### 4.2. Create API Endpoint: `PUT /api/comments/<id>`

**File:** `app.py`

**Copy code from:** Section 2.5 (lines ~552-620)

**Key features:**
- Edit existing comment
- Ownership check
- Mark as edited

**Checklist:**
- [ ] Function `update_comment(comment_id)` created
- [ ] `@login_required` decorator
- [ ] Validation & sanitization
- [ ] Ownership check: `user_id == current_user.id`
- [ ] UPDATE with `is_edited = 1`, `edited_at = NOW()`
- [ ] Return updated text

#### 4.3. Create API Endpoint: `DELETE /api/comments/<id>`

**File:** `app.py`

**Copy code from:** Section 2.6 (lines ~622-690)

**Key features:**
- Soft delete (set deleted_at)
- Ownership check
- Update counts

**Checklist:**
- [ ] Function `delete_comment(comment_id)` created
- [ ] Ownership check
- [ ] Soft delete: `UPDATE deleted_at = NOW()`
- [ ] UPDATE `svg_image.comments_count--`
- [ ] UPDATE `parent_comment.replies_count--` (if reply)

#### 4.4. Create API Endpoint: `POST /api/comments/<id>/like`

**File:** `app.py`

**Copy code from:** Section 2.7 (lines ~692-770)

**Key features:**
- Toggle like/unlike
- Prevent duplicate likes (UNIQUE constraint)
- Update likes_count

**Checklist:**
- [ ] Function `toggle_comment_like(comment_id)` created
- [ ] Check if already liked
- [ ] If liked: DELETE from svg_comment_likes, likes_count--
- [ ] If not: INSERT into svg_comment_likes, likes_count++
- [ ] Return action ('liked' or 'unliked') and new count

#### 4.5. Add Input Sanitization Function

**File:** `app.py`

**Add helper function:**

```python
import re

def sanitize_comment(text):
    """
    Sanitize comment text to prevent XSS while preserving LaTeX.
    """
    # Remove dangerous HTML tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<object[^>]*>.*?</object>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<embed[^>]*>.*?</embed>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers
    text = re.sub(r'\bon\w+\s*=\s*["\'].*?["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bon\w+\s*=\s*[^"\'\s>]+', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text.strip()
```

Use in create/update endpoints:
```python
comment_text = sanitize_comment(data.get('comment_text', '').strip())
```

**Checklist:**
- [ ] `sanitize_comment()` function added
- [ ] Used in `create_comment()`
- [ ] Used in `update_comment()`

#### 4.6. Add Rate Limiting

**Install Flask-Limiter:**
```bash
pip install Flask-Limiter
```

**Update requirements.txt:**
```bash
pip freeze | grep Flask-Limiter >> requirements.txt
```

**Add to app.py:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to comment creation
@app.route('/api/comments/<filename>', methods=['POST'])
@login_required
@limiter.limit("10 per minute")  # Max 10 comments per minute
def create_comment(filename):
    # ... existing code ...
```

**Checklist:**
- [ ] Flask-Limiter installed
- [ ] Added to requirements.txt
- [ ] Limiter initialized
- [ ] Applied to POST `/api/comments/<filename>`
- [ ] Rate: 10 comments per minute

#### 4.7. Test All Endpoints

**Terminal (with server running):**

```bash
# Test POST comment (requires auth - will fail for now)
curl -X POST http://localhost:5173/api/comments/test.svg \
  -H "Content-Type: application/json" \
  -d '{"comment_text": "Test comment"}'

# Should return 401 Unauthorized (expected - need login)
```

**Checklist:**
- [ ] POST returns 401 (expected, need auth)
- [ ] PUT returns 401 (expected)
- [ ] DELETE returns 401 (expected)
- [ ] Like returns 401 (expected)
- [ ] No 500 errors
- [ ] No syntax errors in logs

#### 4.8. Git Commit

```bash
git add app.py requirements.txt
git commit -m "feat(api): Add POST/PUT/DELETE endpoints for comments

- POST /api/comments/<filename> - Create comment/reply
- PUT /api/comments/<id> - Edit comment (owner only)
- DELETE /api/comments/<id> - Soft delete (owner only)
- POST /api/comments/<id>/like - Toggle like/unlike
- Add sanitize_comment() for XSS prevention
- Add Flask-Limiter for rate limiting (10/min)
- Update denormalized counts on create/delete"
```

---

### BƯỚC 5: FRONTEND HTML (1-2 hours)

#### 5.1. Update `templates/view_svg.html`

**Location:** After `image-caption-section`

**Copy HTML from:** Section 3.1 (lines ~780-920)

**Structure:**
```html
<!-- Comments Section -->
<div class="comments-section" id="comments-section">
  <!-- Header with title and sort -->
  <!-- Comment form (logged in) or login prompt -->
  <!-- Comments list container -->
  <!-- Pagination -->
  <!-- Message area -->
</div>

<!-- Inject comments data JSON -->
<script id="comments-data-json" type="application/json">
{
  "filename": "...",
  "currentUserId": ...,
  "currentUserAvatar": "...",
  "commentsCount": 0
}
</script>
```

**Checklist:**
- [ ] HTML structure added after caption section
- [ ] Comments header with count
- [ ] Sort dropdown (newest/oldest)
- [ ] Comment form with textarea, preview, submit
- [ ] Character counter
- [ ] Login prompt for guests
- [ ] Comments list container
- [ ] Pagination container
- [ ] Message container
- [ ] JSON data script with filename, user info

#### 5.2. Include CSS

**File:** `templates/base.html`

**Add before `</head>`:**
```html
<!-- Comments CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/comments.css') }}">
```

**Checklist:**
- [ ] CSS link added to base.html
- [ ] After caption CSS, before closing head tag

#### 5.3. Include JavaScript

**File:** `templates/view_svg.html`

**Add before `</body>`:**
```html
<!-- Comments JavaScript -->
<script src="{{ url_for('static', filename='js/comments.js') }}" defer></script>
```

**Checklist:**
- [ ] JS script tag added
- [ ] Has `defer` attribute
- [ ] After caption JS

#### 5.4. Git Commit

```bash
git add templates/view_svg.html templates/base.html
git commit -m "feat(frontend): Add comments HTML structure

- Add comments section to view_svg.html
- Comment form with textarea, preview, character counter
- Login prompt for guests
- Comments list container
- Pagination controls
- JSON data injection for JavaScript
- Include comments.css and comments.js"
```

---

### BƯỚC 6: FRONTEND CSS (3-4 hours)

#### 6.1. Create `static/css/comments.css`

**Terminal:**
```bash
touch static/css/comments.css
```

**Copy CSS from:** Section 4.1 (lines ~930-1450)

**Sections to include:**
1. Container & Header (`.comments-section`, `.comments-header`)
2. Comment Form (`.comment-form`, `.comment-textarea`)
3. Form Footer & Actions (`.comment-form-footer`, `.comment-btn`)
4. Preview (`.comment-preview`)
5. Login Prompt (`.comment-login-prompt`)
6. Comments List (`.comments-list`, `.comment-item`)
7. Comment Card (`.comment-main`, `.comment-body`)
8. Comment Actions (`.comment-action-btn`, `.like-btn`)
9. Replies (`.comment-replies`, `.comment-reply-item`)
10. Pagination (`.comments-pagination`, `.pagination-btn`)
11. Messages (`.comments-message`)
12. Responsive breakpoints (@media queries)

**Key features:**
- Glass morphism design
- Smooth transitions
- Hover effects
- Focus states
- Loading states
- Responsive for mobile

**Checklist:**
- [ ] File created
- [ ] All 12 sections copied
- [ ] Responsive styles included
- [ ] Transitions defined
- [ ] Loading animations
- [ ] Button hover effects
- [ ] Mobile breakpoints

#### 6.2. Test Styling

**Browser:**
1. Start server: `python3 app.py`
2. Open: `http://localhost:5173/view_svg/<any_svg_file>`
3. Check comments section appears
4. Check styling looks good

**Checklist:**
- [ ] Comments section visible
- [ ] Glass morphism background
- [ ] Form styled correctly
- [ ] Buttons have hover effects
- [ ] Responsive on mobile (use DevTools)

#### 6.3. Git Commit

```bash
git add static/css/comments.css
git commit -m "style(comments): Add complete CSS styling

- Glass morphism design matching caption feature
- Comment form with textarea and buttons
- Comment cards with avatar and badges
- Nested replies styling
- Action buttons (like, reply, edit, delete)
- Pagination controls
- Loading states and animations
- Responsive design for mobile
- Smooth transitions and hover effects"
```

---

### BƯỚC 7: FRONTEND JAVASCRIPT (8-10 hours)

#### 7.1. Create `static/js/comments.js`

**Terminal:**
```bash
touch static/js/comments.js
```

**Copy JavaScript from:** Section 5.1 (lines ~1460-2300)

**Structure:**
```javascript
(function() {
  'use strict';

  // Configuration
  const CONFIG = { ... };

  // State
  let currentPage = 1;
  let currentSort = 'newest';
  // ...

  // Initialize
  function initComments() { ... }

  // Main functions
  function loadComments() { ... }
  function createCommentHTML() { ... }
  function handleSubmitComment() { ... }
  function handleLikeComment() { ... }
  function handleShowReplies() { ... }
  // ... more functions

  // Start
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initComments);
  } else {
    initComments();
  }
})();
```

**Checklist:**
- [ ] File created with IIFE pattern
- [ ] Configuration object defined
- [ ] State variables initialized
- [ ] `initComments()` function
- [ ] Event listeners setup

#### 7.2. Implement Core Functions

**Functions to implement:**

1. **`loadComments(page)`**
   - Fetch comments from API
   - Display loading state
   - Render comments
   - Handle pagination
   - Update total count

2. **`renderComments(comments)`**
   - Create HTML for each comment
   - Attach to DOM
   - Trigger MathJax

3. **`createCommentHTML(comment)`**
   - Build comment card HTML
   - Include avatar, username, badge
   - Format timestamp
   - Add action buttons

4. **`handleSubmitComment()`**
   - Get textarea value
   - Validate input
   - POST to API
   - Clear form
   - Reload comments

5. **`handleLikeComment(e)`**
   - POST to like API
   - Update like icon
   - Update like count

6. **`handleShowReplies(e)`**
   - Fetch replies from API
   - Render replies
   - Toggle visibility

**Checklist:**
- [ ] `loadComments()` implemented
- [ ] `renderComments()` implemented
- [ ] `createCommentHTML()` implemented
- [ ] `handleSubmitComment()` implemented
- [ ] `handleLikeComment()` implemented
- [ ] `handleShowReplies()` implemented

#### 7.3. Implement Helper Functions

**Helper functions:**

1. **`getCaptionData()`** → Parse JSON data
2. **`setupEventListeners()`** → Attach all listeners
3. **`togglePreview()`** → Show/hide preview
4. **`updateCharCount()`** → Update counter
5. **`formatTimestamp(date)`** → "2 giờ trước"
6. **`escapeHtml(text)`** → Prevent XSS, preserve breaks
7. **`showMessage(text, type)`** → Display feedback

**Checklist:**
- [ ] All helper functions implemented
- [ ] Data parsing works
- [ ] Event listeners attached
- [ ] Preview toggles correctly
- [ ] Character counter updates
- [ ] Timestamps formatted nicely
- [ ] HTML escaping works

#### 7.4. Implement Pagination

**Functions:**

1. **`renderPagination(pagination)`**
   - Create page buttons
   - Attach click handlers
   - Highlight current page

**Checklist:**
- [ ] Pagination rendered
- [ ] Page buttons clickable
- [ ] Current page highlighted
- [ ] Prev/Next buttons work

#### 7.5. Implement Real-time Polling

**Functions:**

1. **`startPolling()`** → setInterval every 30s
2. **`stopPolling()`** → clearInterval

**Checklist:**
- [ ] Polling starts on init (if logged in)
- [ ] Polling updates comments silently
- [ ] Polling stops on page unload

#### 7.6. Integrate MathJax

**Add to functions:**

```javascript
// After rendering comments/replies
if (window.MathJax) {
  window.MathJax.typesetPromise([container]).catch(err => {
    console.error('MathJax typeset error:', err);
  });
}
```

**Checklist:**
- [ ] MathJax called after `renderComments()`
- [ ] MathJax called after `renderReplies()`
- [ ] MathJax called in preview
- [ ] LaTeX formulas render correctly

#### 7.7. Test JavaScript Functionality

**Manual testing in browser:**

1. **Load comments:**
   - [ ] Page loads, shows "Đang tải..."
   - [ ] Shows "Chưa có bình luận" if empty
   - [ ] Displays comments if exist

2. **Submit comment (logged in):**
   - [ ] Type in textarea
   - [ ] Character counter updates
   - [ ] Preview button shows preview
   - [ ] MathJax renders in preview
   - [ ] Submit creates comment
   - [ ] Comment appears immediately
   - [ ] Form clears after submit

3. **Like comment:**
   - [ ] Click like button
   - [ ] Icon changes (🤍 → ❤️)
   - [ ] Count increments
   - [ ] Click again unlikes

4. **Show replies:**
   - [ ] Click "Xem replies" button
   - [ ] Replies load and display
   - [ ] Click again hides replies

5. **Pagination:**
   - [ ] If > 10 comments, pagination shows
   - [ ] Click page 2 loads next 10
   - [ ] Current page highlighted

6. **Guest experience:**
   - [ ] Shows login prompt
   - [ ] Form disabled
   - [ ] Can view comments

**Checklist:**
- [ ] All tests passed
- [ ] No console errors
- [ ] Smooth animations
- [ ] Fast response times

#### 7.8. Git Commit

```bash
git add static/js/comments.js
git commit -m "feat(comments): Add complete JavaScript functionality

- Load comments with pagination
- Submit new comments
- Like/unlike comments
- Show/hide replies
- Real-time updates (30s polling)
- MathJax integration for LaTeX
- Character counter and preview
- Format timestamps (relative time)
- HTML escaping for security
- Loading states and error handling
- Responsive interaction"
```

---

### BƯỚC 8: TESTING & DEBUGGING (4-6 hours)

#### 8.1. Manual Testing Checklist

**Database:**
- [ ] Tables created correctly
- [ ] Foreign keys working
- [ ] Indexes present
- [ ] UTF8MB4 encoding correct

**API Endpoints:**

**GET `/api/comments/<filename>`:**
- [ ] Returns empty array for no comments
- [ ] Returns comments with pagination
- [ ] Sort by newest works
- [ ] Sort by oldest works
- [ ] User like status correct
- [ ] Pagination math correct

**GET `/api/comments/<id>/replies`:**
- [ ] Returns replies for comment
- [ ] Ordered by created_at ASC
- [ ] Empty if no replies

**POST `/api/comments/<filename>`:**
- [ ] Creates top-level comment
- [ ] Creates reply (with parent_comment_id)
- [ ] Validates empty input
- [ ] Validates max length (5000)
- [ ] Sanitizes XSS attempts
- [ ] Updates comments_count
- [ ] Updates replies_count (for replies)
- [ ] Returns created comment

**PUT `/api/comments/<id>`:**
- [ ] Updates comment text
- [ ] Only owner can edit
- [ ] Marks as edited (is_edited = 1)
- [ ] Updates edited_at timestamp

**DELETE `/api/comments/<id>`:**
- [ ] Soft deletes (sets deleted_at)
- [ ] Only owner can delete
- [ ] Updates comments_count
- [ ] Updates replies_count

**POST `/api/comments/<id>/like`:**
- [ ] Likes comment (first click)
- [ ] Unlikes comment (second click)
- [ ] Updates likes_count
- [ ] Prevents duplicate likes

**Frontend:**

**As Guest:**
- [ ] Can view comments
- [ ] Cannot submit
- [ ] See login prompt
- [ ] Can see like counts (not clickable)

**As Logged-in User:**
- [ ] Can submit comment
- [ ] Can like comments
- [ ] Can reply to comments
- [ ] Can edit own comments
- [ ] Can delete own comments
- [ ] Cannot edit others' comments

**UI/UX:**
- [ ] Glass morphism looks good
- [ ] Transitions smooth
- [ ] Buttons responsive
- [ ] Loading states clear
- [ ] Error messages helpful
- [ ] Success feedback shown

**MathJax:**
- [ ] Inline math renders: `$x^2$`
- [ ] Display math renders: `$$\int f(x)dx$$`
- [ ] Renders in comments
- [ ] Renders in preview
- [ ] Renders in replies

**Responsive:**
- [ ] Mobile (< 640px): Layout stacks
- [ ] Tablet (640-1024px): Two columns
- [ ] Desktop (> 1024px): Full width
- [ ] Touch targets large enough
- [ ] Text readable on all sizes

**Performance:**
- [ ] Comments load fast (< 500ms)
- [ ] Pagination smooth
- [ ] No lag when typing
- [ ] MathJax loads async (no block)

**Security:**
- [ ] XSS attempts blocked
- [ ] SQL injection prevented (parameterized)
- [ ] Rate limiting works (10/min)
- [ ] CSRF protection (Flask built-in)

#### 8.2. Test with Real Data

**Create test comments:**

```bash
# Use Postman or curl with auth cookies
# Or manually via browser when logged in
```

**Test scenarios:**
1. Create 15 comments → Test pagination
2. Create 5 replies on one comment → Test replies
3. Like multiple comments → Test like counts
4. Edit a comment → Test edit functionality
5. Delete a comment → Test soft delete
6. Try XSS: `<script>alert('xss')</script>` → Should be sanitized
7. Try long comment (5001 chars) → Should reject
8. Try LaTeX: `The formula is $x^2 + y^2 = z^2$` → Should render

**Checklist:**
- [ ] All test scenarios passed
- [ ] No bugs found
- [ ] Edge cases handled

#### 8.3. Fix Bugs

**Common issues to check:**

1. **Comments not loading:**
   - Check API endpoint URL
   - Check filename parameter
   - Check CORS if applicable

2. **Like button not working:**
   - Check auth status
   - Check API response
   - Check event listener attached

3. **MathJax not rendering:**
   - Check if MathJax CDN loaded
   - Check typesetPromise called
   - Check selector correct

4. **Form not submitting:**
   - Check event listener
   - Check API URL
   - Check request body format

**Checklist:**
- [ ] All bugs fixed
- [ ] Retested after fixes
- [ ] No new issues introduced

#### 8.4. Performance Testing

**Use browser DevTools:**

1. **Network tab:**
   - [ ] API calls < 500ms
   - [ ] Images lazy loaded
   - [ ] MathJax cached

2. **Performance tab:**
   - [ ] No long tasks
   - [ ] Smooth scrolling
   - [ ] No memory leaks

3. **Lighthouse:**
   - [ ] Performance > 90
   - [ ] Accessibility > 90
   - [ ] Best Practices > 90

**Checklist:**
- [ ] Performance acceptable
- [ ] No bottlenecks found
- [ ] Mobile performance good

#### 8.5. Git Commit

```bash
git add .
git commit -m "test: Add comprehensive tests and bug fixes

- Manual testing checklist completed
- All API endpoints tested
- Frontend functionality verified
- Security measures tested
- Performance optimized
- Bug fixes applied"
```

---

### BƯỚC 9: DOCUMENTATION (2-3 hours)

#### 9.1. Create Feature Guide

**File:** `COMMENTS_FEATURE_GUIDE.md`

**Contents:**
1. Overview
2. User guide (how to use)
3. API reference
4. Database schema
5. Frontend components
6. Security measures
7. Troubleshooting

**Checklist:**
- [ ] Guide created
- [ ] All sections filled
- [ ] Screenshots added (optional)
- [ ] Examples provided

#### 9.2. Update README.md

**Add to features list:**
```markdown
### Comments System
- Post, edit, and delete comments on SVG images
- Reply to comments (1 level deep)
- Like/unlike comments
- MathJax support for mathematical formulas
- Real-time updates via polling
- Pagination for large discussions
```

**Checklist:**
- [ ] README updated
- [ ] Features list includes comments
- [ ] Examples added

#### 9.3. Create Deployment Guide

**File:** `COMMENTS_DEPLOYMENT_GUIDE.md`

**Contents:**
1. Prerequisites
2. Migration steps for VPS
3. Environment variables
4. Testing checklist
5. Rollback procedure

**Checklist:**
- [ ] Deployment guide created
- [ ] VPS-specific instructions
- [ ] Rollback plan documented

#### 9.4. Git Commit

```bash
git add COMMENTS_FEATURE_GUIDE.md README.md COMMENTS_DEPLOYMENT_GUIDE.md
git commit -m "docs: Add comprehensive comments feature documentation

- COMMENTS_FEATURE_GUIDE.md with user guide and API reference
- Update README.md with features list
- COMMENTS_DEPLOYMENT_GUIDE.md for VPS deployment
- Include troubleshooting and rollback procedures"
```

---

### BƯỚC 10: DEPLOYMENT (2-3 hours)

#### 10.1. Prepare for Deployment

**Checklist:**
- [ ] All tests passed
- [ ] All commits made
- [ ] Documentation complete
- [ ] Migration script ready
- [ ] Backup plan ready

#### 10.2. Merge to Main

**Terminal:**
```bash
# Switch to main
git checkout main

# Merge feature branch
git merge feature/comments-system

# Review changes
git log --oneline -10
```

**Checklist:**
- [ ] Feature branch merged
- [ ] No merge conflicts
- [ ] Commits look good

#### 10.3. Push to GitHub

```bash
# Push to remote
git push origin main

# Push feature branch too
git push origin feature/comments-system
```

**Checklist:**
- [ ] Pushed to GitHub
- [ ] Branch visible on GitHub
- [ ] All commits present

#### 10.4. Deploy to VPS (when ready)

**SSH to VPS:**
```bash
ssh user@your-vps-ip
cd /path/to/tikz2svg_api
```

**Backup production database:**
```bash
mysqldump -u user -p tikz2svg_production > backup_before_comments_$(date +%Y%m%d_%H%M%S).sql
```

**Pull latest code:**
```bash
git pull origin main
```

**Run migration:**
```bash
mysql -u user -p tikz2svg_production < add_comments_system.sql
```

**Verify migration:**
```bash
mysql -u user -p tikz2svg_production -e "SHOW TABLES LIKE 'svg_comment%';"
```

**Install dependencies:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Restart application:**
```bash
sudo systemctl restart tikz2svg
# or
sudo supervisorctl restart tikz2svg
```

**Test on production:**
```bash
curl https://your-domain.com/api/comments/some_file.svg
```

**Checklist:**
- [ ] Database backed up
- [ ] Code pulled
- [ ] Migration successful
- [ ] Dependencies installed
- [ ] Application restarted
- [ ] Smoke test passed

#### 10.5. Monitor

**Check logs:**
```bash
tail -f /var/log/tikz2svg/error.log
tail -f /var/log/tikz2svg/access.log
```

**Monitor for:**
- [ ] No 500 errors
- [ ] API responses normal
- [ ] Comments loading correctly
- [ ] Users can post comments

**Checklist:**
- [ ] No errors in logs
- [ ] Application stable
- [ ] Users can use feature

#### 10.6. Final Git Commit

```bash
git tag -a v1.0.0-comments -m "Release Comments Feature v1.0.0"
git push origin v1.0.0-comments
```

---

## ✅ COMPLETION CHECKLIST

### Phase 1: Database
- [ ] Migration script created
- [ ] Database backed up
- [ ] Migration executed
- [ ] Tables verified
- [ ] Indexes verified
- [ ] Foreign keys verified
- [ ] Documentation updated

### Phase 2: Backend API
- [ ] GET endpoints implemented
- [ ] POST endpoints implemented
- [ ] PUT endpoint implemented
- [ ] DELETE endpoint implemented
- [ ] Like endpoint implemented
- [ ] Input sanitization added
- [ ] Rate limiting added
- [ ] All endpoints tested

### Phase 3: Frontend HTML
- [ ] Comments section added
- [ ] Form created
- [ ] Lists containers added
- [ ] Pagination added
- [ ] JSON data injection
- [ ] CSS/JS included

### Phase 4: Frontend CSS
- [ ] comments.css created
- [ ] All sections styled
- [ ] Responsive design
- [ ] Animations added
- [ ] Tested on mobile

### Phase 5: Frontend JavaScript
- [ ] comments.js created
- [ ] All functions implemented
- [ ] Event listeners attached
- [ ] MathJax integrated
- [ ] Polling implemented
- [ ] Tested thoroughly

### Phase 6: Testing
- [ ] Manual tests passed
- [ ] Security tests passed
- [ ] Performance tests passed
- [ ] Bugs fixed
- [ ] Edge cases handled

### Phase 7: Documentation
- [ ] Feature guide created
- [ ] README updated
- [ ] Deployment guide created
- [ ] API documented

### Phase 8: Deployment
- [ ] Merged to main
- [ ] Pushed to GitHub
- [ ] Deployed to VPS (when ready)
- [ ] Monitored for issues

---

## 📊 PROGRESS TRACKING

| Phase | Estimated | Actual | Status |
|-------|-----------|--------|--------|
| 1. Database Migration | 2-3h | ___ | ⏳ |
| 2. Backend API Part 1 | 3-4h | ___ | ⏳ |
| 3. Backend API Part 2 | 3-4h | ___ | ⏳ |
| 4. Frontend HTML | 1-2h | ___ | ⏳ |
| 5. Frontend CSS | 3-4h | ___ | ⏳ |
| 6. Frontend JavaScript | 8-10h | ___ | ⏳ |
| 7. Testing & Debugging | 4-6h | ___ | ⏳ |
| 8. Documentation | 2-3h | ___ | ⏳ |
| 9. Deployment | 2-3h | ___ | ⏳ |
| **Total** | **30-42h** | **___** | ⏳ |

---

## 🎯 SUCCESS CRITERIA

**Feature is complete when:**

✅ Users can post comments on SVG images  
✅ Users can reply to comments (1 level)  
✅ Users can like/unlike comments  
✅ Users can edit their own comments  
✅ Users can delete their own comments  
✅ MathJax renders LaTeX formulas  
✅ Comments load with pagination  
✅ Real-time updates work (polling)  
✅ Mobile responsive  
✅ XSS attacks prevented  
✅ Rate limiting active  
✅ All tests passed  
✅ Documentation complete  
✅ Deployed successfully  

---

## 📞 Support & References

**Documents:**
- `COMMENTS_FEATURE_IMPLEMENTATION_PLAN.md` - Full technical spec
- `DATABASE_STATUS_REPORT.md` - Database analysis
- `DATABASE_SCHEMA_CONSISTENCY_CHECK.md` - Schema validation
- `IMAGE_CAPTION_FEATURE_GUIDE.md` - Similar feature reference

**Get Help:**
- Check console for JavaScript errors
- Check network tab for API errors
- Check server logs for backend errors
- Review documentation for examples

---

**Last Updated:** 2025-10-22  
**Version:** 1.0  
**Status:** Ready to start implementation 🚀

