# Comments Feature - Quy trình Triển khai

**Date:** 2025-10-22  
**Component:** View SVG Page - Comments System  
**Predecessor:** Image Caption Feature  
**Status:** 📋 Planning Phase

---

## 📋 Tổng quan

Phát triển hệ thống bình luận cho trang `templates/view_svg.html`, cho phép người dùng thảo luận và tương tác về các ảnh SVG.

### 🎯 Tính năng chính:

- ✅ Đăng bình luận trên ảnh SVG
- ✅ Hiển thị danh sách bình luận theo thứ tự thời gian
- ✅ Chỉnh sửa/xóa bình luận của chính mình
- ✅ Reply to comment (nested comments - level 1)
- ✅ Hỗ trợ LaTeX/MathJax: `$x^2$`, `$$\int_{0}^{1} x dx$$`
- ✅ Like/Unlike comments
- ✅ Real-time updates (polling hoặc WebSocket)
- ✅ Pagination cho danh sách comments
- ✅ Sanitize input để tránh XSS
- ✅ Rate limiting để chống spam
- 🔜 Mention users (@username) - Phase 2
- 🔜 Notifications - Phase 2

---

## 🗂️ PHASE 1: DATABASE SCHEMA

### 1.1. Bảng `svg_comments` - Bảng chính

```sql
CREATE TABLE `svg_comments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `svg_filename` VARCHAR(255) NOT NULL,
  `user_id` INT NOT NULL,
  `parent_comment_id` INT DEFAULT NULL,
  `comment_text` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_edited` TINYINT(1) DEFAULT 0,
  `edited_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` DATETIME DEFAULT NULL,
  `likes_count` INT DEFAULT 0,
  `replies_count` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_svg_filename` (`svg_filename`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_parent_comment_id` (`parent_comment_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_deleted_at` (`deleted_at`),
  FOREIGN KEY (`svg_filename`) REFERENCES `svg_image`(`filename`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`parent_comment_id`) REFERENCES `svg_comments`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Chi tiết các trường:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | INT AUTO_INCREMENT | Primary key |
| `svg_filename` | VARCHAR(255) | Reference đến `svg_image.filename` |
| `user_id` | INT | Reference đến `user.id` |
| `parent_comment_id` | INT NULL | NULL = top-level, có giá trị = reply |
| `comment_text` | TEXT utf8mb4 | Nội dung bình luận, hỗ trợ LaTeX |
| `is_edited` | TINYINT(1) | Flag đã chỉnh sửa hay chưa |
| `edited_at` | DATETIME | Thời gian chỉnh sửa lần cuối |
| `created_at` | DATETIME | Thời gian tạo comment |
| `deleted_at` | DATETIME | Soft delete (NULL = chưa xóa) |
| `likes_count` | INT | Số lượt like (denormalized) |
| `replies_count` | INT | Số lượt reply (denormalized) |

**Indexes:**
- `idx_svg_filename`: Query comments theo ảnh (most common)
- `idx_user_id`: Query comments của user
- `idx_parent_comment_id`: Query replies
- `idx_created_at`: Sắp xếp theo thời gian
- `idx_deleted_at`: Filter comments đã xóa

**Foreign Keys:**
- Cascade delete: Xóa ảnh → xóa comments
- Cascade delete: Xóa user → xóa comments
- Cascade delete: Xóa parent comment → xóa replies

---

### 1.2. Bảng `svg_comment_likes` - Lưu likes

```sql
CREATE TABLE `svg_comment_likes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `comment_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_comment_like` (`comment_id`, `user_id`),
  KEY `idx_comment_id` (`comment_id`),
  KEY `idx_user_id` (`user_id`),
  FOREIGN KEY (`comment_id`) REFERENCES `svg_comments`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Chi tiết:**
- `UNIQUE KEY`: Mỗi user chỉ like 1 lần/comment
- Foreign keys cascade: Xóa comment/user → xóa likes

---

### 1.3. Thêm cột `comments_count` vào `svg_image`

```sql
ALTER TABLE svg_image 
ADD COLUMN comments_count INT DEFAULT 0 AFTER caption;

-- Add filename index for fast lookups (IMPORTANT for Comments queries)
CREATE INDEX idx_filename ON svg_image(filename);

-- Add comments_count index for sorting
CREATE INDEX idx_comments_count ON svg_image(comments_count);
```

**Mục đích:** 
- `comments_count`: Denormalized count để hiển thị nhanh trên gallery/profile
- `idx_filename`: **Critical** - Comments sẽ query theo filename rất nhiều

---

### 1.4. Migration Script

**File:** `add_comments_system.sql`

```sql
-- Migration script for Comments System
-- Date: 2025-10-22
-- Author: TikZ2SVG Dev Team

-- Step 1: Create svg_comments table
CREATE TABLE IF NOT EXISTS `svg_comments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `svg_filename` VARCHAR(255) NOT NULL,
  `user_id` INT NOT NULL,
  `parent_comment_id` INT DEFAULT NULL,
  `comment_text` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_edited` TINYINT(1) DEFAULT 0,
  `edited_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `deleted_at` DATETIME DEFAULT NULL,
  `likes_count` INT DEFAULT 0,
  `replies_count` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_svg_filename` (`svg_filename`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_parent_comment_id` (`parent_comment_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_deleted_at` (`deleted_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 2: Add foreign keys (after table creation)
ALTER TABLE `svg_comments`
ADD CONSTRAINT `fk_comments_svg_filename` 
  FOREIGN KEY (`svg_filename`) REFERENCES `svg_image`(`filename`) ON DELETE CASCADE,
ADD CONSTRAINT `fk_comments_user_id` 
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
ADD CONSTRAINT `fk_comments_parent` 
  FOREIGN KEY (`parent_comment_id`) REFERENCES `svg_comments`(`id`) ON DELETE CASCADE;

-- Step 3: Create svg_comment_likes table
CREATE TABLE IF NOT EXISTS `svg_comment_likes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `comment_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_comment_like` (`comment_id`, `user_id`),
  KEY `idx_comment_id` (`comment_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 4: Add foreign keys for likes
ALTER TABLE `svg_comment_likes`
ADD CONSTRAINT `fk_comment_likes_comment` 
  FOREIGN KEY (`comment_id`) REFERENCES `svg_comments`(`id`) ON DELETE CASCADE,
ADD CONSTRAINT `fk_comment_likes_user` 
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE;

-- Step 5: Add comments_count to svg_image and indexes
ALTER TABLE `svg_image` 
ADD COLUMN `comments_count` INT DEFAULT 0 AFTER `caption`;

-- Add filename index for fast comment lookups (CRITICAL)
CREATE INDEX idx_filename ON svg_image(filename);

-- Add comments_count index for sorting by popularity
CREATE INDEX idx_comments_count ON svg_image(comments_count);

-- Step 6: Verification
SELECT 'Comments system tables created successfully!' AS Status;
DESCRIBE svg_comments;
DESCRIBE svg_comment_likes;
SHOW COLUMNS FROM svg_image WHERE Field = 'comments_count';

-- Rollback instructions (if needed):
-- DROP TABLE svg_comment_likes;
-- DROP TABLE svg_comments;
-- ALTER TABLE svg_image DROP COLUMN comments_count;
```

---

### 1.5. Update DATABASE_DOCUMENTATION.md

Thêm section mới:

```markdown
## 7. Hệ thống Comments

### 7.1. Lấy comments cho một ảnh SVG (với pagination)

```sql
SELECT 
    c.id, c.svg_filename, c.user_id, c.parent_comment_id,
    c.comment_text, c.is_edited, c.edited_at, c.created_at,
    c.likes_count, c.replies_count,
    u.username, u.avatar, u.identity_verified,
    -- Check if current user has liked this comment
    (SELECT COUNT(*) FROM svg_comment_likes 
     WHERE comment_id = c.id AND user_id = ? ) AS user_has_liked
FROM svg_comments c
JOIN user u ON c.user_id = u.id
WHERE c.svg_filename = ? 
  AND c.deleted_at IS NULL
  AND c.parent_comment_id IS NULL  -- Top-level comments only
ORDER BY c.created_at DESC
LIMIT ? OFFSET ?;
```

### 7.2. Lấy replies cho một comment

```sql
SELECT 
    c.id, c.svg_filename, c.user_id, c.parent_comment_id,
    c.comment_text, c.is_edited, c.edited_at, c.created_at,
    c.likes_count,
    u.username, u.avatar, u.identity_verified,
    (SELECT COUNT(*) FROM svg_comment_likes 
     WHERE comment_id = c.id AND user_id = ? ) AS user_has_liked
FROM svg_comments c
JOIN user u ON c.user_id = u.id
WHERE c.parent_comment_id = ?
  AND c.deleted_at IS NULL
ORDER BY c.created_at ASC;  -- Replies show oldest first
```

### 7.3. Tạo comment mới

```sql
INSERT INTO svg_comments 
(svg_filename, user_id, parent_comment_id, comment_text, created_at)
VALUES (?, ?, ?, ?, NOW());

-- Update counts
UPDATE svg_image 
SET comments_count = comments_count + 1 
WHERE filename = ?;

-- If it's a reply, update parent's replies_count
UPDATE svg_comments 
SET replies_count = replies_count + 1 
WHERE id = ?;
```

### 7.4. Chỉnh sửa comment

```sql
UPDATE svg_comments 
SET comment_text = ?, is_edited = 1, edited_at = NOW()
WHERE id = ? AND user_id = ? AND deleted_at IS NULL;
```

### 7.5. Xóa comment (soft delete)

```sql
UPDATE svg_comments 
SET deleted_at = NOW()
WHERE id = ? AND user_id = ?;

-- Update counts
UPDATE svg_image 
SET comments_count = comments_count - 1 
WHERE filename = (SELECT svg_filename FROM svg_comments WHERE id = ?);

-- If it's a reply, update parent's replies_count
UPDATE svg_comments 
SET replies_count = replies_count - 1 
WHERE id = (SELECT parent_comment_id FROM svg_comments WHERE id = ?);
```

### 7.6. Like/Unlike comment

```sql
-- Like
INSERT INTO svg_comment_likes (comment_id, user_id, created_at)
VALUES (?, ?, NOW())
ON DUPLICATE KEY UPDATE comment_id = comment_id;

UPDATE svg_comments SET likes_count = likes_count + 1 WHERE id = ?;

-- Unlike
DELETE FROM svg_comment_likes 
WHERE comment_id = ? AND user_id = ?;

UPDATE svg_comments SET likes_count = likes_count - 1 WHERE id = ?;
```

### 7.7. Thống kê comments

```sql
-- Total comments per SVG
SELECT svg_filename, COUNT(*) as total_comments
FROM svg_comments
WHERE deleted_at IS NULL
GROUP BY svg_filename
ORDER BY total_comments DESC;

-- Most active commenters
SELECT u.username, COUNT(*) as comment_count
FROM svg_comments c
JOIN user u ON c.user_id = u.id
WHERE c.deleted_at IS NULL
GROUP BY u.id, u.username
ORDER BY comment_count DESC
LIMIT 10;

-- Comments with most likes
SELECT c.id, c.comment_text, c.likes_count, u.username
FROM svg_comments c
JOIN user u ON c.user_id = u.id
WHERE c.deleted_at IS NULL
ORDER BY c.likes_count DESC
LIMIT 10;
```
```

---

## 🔧 PHASE 2: BACKEND API

### 2.1. Cập nhật Route `/view_svg/<filename>`

**File:** `app.py`

```python
@app.route('/view_svg/<filename>')
def view_svg(filename):
    # ... existing code lấy svg_url, tikz_code, caption ...
    
    # ✅ NEW: Lấy comments_count
    comments_count = 0
    try:
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT tikz_code, user_id, caption, comments_count
            FROM svg_image 
            WHERE filename = %s 
            LIMIT 1
        """, (filename,))
        row = cursor.fetchone()
        
        if row:
            tikz_code = row['tikz_code']
            caption = row.get('caption', '')
            comments_count = row.get('comments_count', 0)  # ✅ NEW
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] in /view_svg: {e}", flush=True)
    
    return render_template(
        "view_svg.html",
        # ... existing params ...
        caption=caption,
        comments_count=comments_count  # ✅ NEW
    )
```

---

### 2.2. API Endpoint: `GET /api/comments/<filename>`

**Mục đích:** Lấy danh sách comments cho một ảnh SVG (với pagination).

```python
@app.route('/api/comments/<filename>', methods=['GET'])
def get_comments(filename):
    """
    Get comments for an SVG image with pagination.
    
    Query params:
    - page: int (default=1)
    - per_page: int (default=10, max=50)
    - sort: str ('newest' or 'oldest', default='newest')
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        sort = request.args.get('sort', 'newest')
        offset = (page - 1) * per_page
        
        # Get current user ID (if logged in)
        current_user_id = current_user.id if current_user.is_authenticated else None
        
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM svg_comments
            WHERE svg_filename = %s 
              AND deleted_at IS NULL
              AND parent_comment_id IS NULL
        """, (filename,))
        total = cursor.fetchone()['total']
        
        # Get comments with user info and like status
        order_by = 'c.created_at DESC' if sort == 'newest' else 'c.created_at ASC'
        
        query = f"""
            SELECT 
                c.id, c.svg_filename, c.user_id, c.parent_comment_id,
                c.comment_text, c.is_edited, c.edited_at, c.created_at,
                c.likes_count, c.replies_count,
                u.username, u.avatar, u.identity_verified
        """
        
        if current_user_id:
            query += f""",
                (SELECT COUNT(*) FROM svg_comment_likes 
                 WHERE comment_id = c.id AND user_id = {current_user_id}) AS user_has_liked
            """
        else:
            query += ", 0 AS user_has_liked"
        
        query += f"""
            FROM svg_comments c
            JOIN user u ON c.user_id = u.id
            WHERE c.svg_filename = %s 
              AND c.deleted_at IS NULL
              AND c.parent_comment_id IS NULL
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (filename, per_page, offset))
        comments = cursor.fetchall()
        
        # Format datetime for JSON
        for comment in comments:
            comment['created_at'] = comment['created_at'].isoformat() if comment['created_at'] else None
            comment['edited_at'] = comment['edited_at'].isoformat() if comment['edited_at'] else None
            comment['is_owner'] = (current_user_id == comment['user_id']) if current_user_id else False
            comment['user_has_liked'] = bool(comment['user_has_liked'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'comments': comments,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        print(f"[ERROR] get_comments: {e}", flush=True)
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500
```

---

### 2.3. API Endpoint: `GET /api/comments/<comment_id>/replies`

**Mục đích:** Lấy replies cho một comment.

```python
@app.route('/api/comments/<int:comment_id>/replies', methods=['GET'])
def get_comment_replies(comment_id):
    """
    Get replies for a specific comment.
    """
    try:
        current_user_id = current_user.id if current_user.is_authenticated else None
        
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                c.id, c.svg_filename, c.user_id, c.parent_comment_id,
                c.comment_text, c.is_edited, c.edited_at, c.created_at,
                c.likes_count,
                u.username, u.avatar, u.identity_verified
        """
        
        if current_user_id:
            query += f""",
                (SELECT COUNT(*) FROM svg_comment_likes 
                 WHERE comment_id = c.id AND user_id = {current_user_id}) AS user_has_liked
            """
        else:
            query += ", 0 AS user_has_liked"
        
        query += """
            FROM svg_comments c
            JOIN user u ON c.user_id = u.id
            WHERE c.parent_comment_id = %s
              AND c.deleted_at IS NULL
            ORDER BY c.created_at ASC
        """
        
        cursor.execute(query, (comment_id,))
        replies = cursor.fetchall()
        
        for reply in replies:
            reply['created_at'] = reply['created_at'].isoformat() if reply['created_at'] else None
            reply['edited_at'] = reply['edited_at'].isoformat() if reply['edited_at'] else None
            reply['is_owner'] = (current_user_id == reply['user_id']) if current_user_id else False
            reply['user_has_liked'] = bool(reply['user_has_liked'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'replies': replies})
        
    except Exception as e:
        print(f"[ERROR] get_comment_replies: {e}", flush=True)
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500
```

---

### 2.4. API Endpoint: `POST /api/comments/<filename>`

**Mục đích:** Tạo comment mới (hoặc reply).

```python
@app.route('/api/comments/<filename>', methods=['POST'])
@login_required
def create_comment(filename):
    """
    Create a new comment (or reply to existing comment).
    
    Request body:
    {
        "comment_text": "...",
        "parent_comment_id": 123 (optional, null for top-level)
    }
    """
    try:
        data = request.get_json()
        comment_text = data.get('comment_text', '').strip()
        parent_comment_id = data.get('parent_comment_id')
        
        # Validation
        if not comment_text:
            return jsonify({'success': False, 'message': 'Comment không được để trống'}), 400
        
        if len(comment_text) > 5000:
            return jsonify({'success': False, 'message': 'Comment quá dài (tối đa 5000 ký tự)'}), 400
        
        # Sanitize input (remove dangerous HTML but keep LaTeX)
        comment_text = re.sub(r'<script[^>]*>.*?</script>', '', comment_text, flags=re.IGNORECASE | re.DOTALL)
        comment_text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', comment_text, flags=re.IGNORECASE | re.DOTALL)
        comment_text = re.sub(r'\bon\w+\s*=\s*["\'].*?["\']', '', comment_text, flags=re.IGNORECASE)
        
        # Check if SVG exists
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT filename FROM svg_image WHERE filename = %s", (filename,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Ảnh không tồn tại'}), 404
        
        # If it's a reply, check if parent comment exists
        if parent_comment_id:
            cursor.execute("""
                SELECT id, svg_filename 
                FROM svg_comments 
                WHERE id = %s AND deleted_at IS NULL
            """, (parent_comment_id,))
            parent = cursor.fetchone()
            
            if not parent:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Comment cha không tồn tại'}), 404
            
            if parent['svg_filename'] != filename:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Comment không thuộc ảnh này'}), 400
        
        # Insert comment
        cursor.execute("""
            INSERT INTO svg_comments 
            (svg_filename, user_id, parent_comment_id, comment_text, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (filename, current_user.id, parent_comment_id, comment_text))
        
        comment_id = cursor.lastrowid
        
        # Update counts
        cursor.execute("""
            UPDATE svg_image 
            SET comments_count = comments_count + 1 
            WHERE filename = %s
        """, (filename,))
        
        if parent_comment_id:
            cursor.execute("""
                UPDATE svg_comments 
                SET replies_count = replies_count + 1 
                WHERE id = %s
            """, (parent_comment_id,))
        
        conn.commit()
        
        # Get the created comment with user info
        cursor.execute("""
            SELECT 
                c.id, c.svg_filename, c.user_id, c.parent_comment_id,
                c.comment_text, c.is_edited, c.edited_at, c.created_at,
                c.likes_count, c.replies_count,
                u.username, u.avatar, u.identity_verified
            FROM svg_comments c
            JOIN user u ON c.user_id = u.id
            WHERE c.id = %s
        """, (comment_id,))
        
        new_comment = cursor.fetchone()
        new_comment['created_at'] = new_comment['created_at'].isoformat()
        new_comment['is_owner'] = True
        new_comment['user_has_liked'] = False
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Bình luận đã được đăng',
            'comment': new_comment
        })
        
    except Exception as e:
        print(f"[ERROR] create_comment: {e}", flush=True)
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500
```

---

### 2.5. API Endpoint: `PUT /api/comments/<int:comment_id>`

**Mục đích:** Chỉnh sửa comment.

```python
@app.route('/api/comments/<int:comment_id>', methods=['PUT'])
@login_required
def update_comment(comment_id):
    """
    Update a comment (owner only).
    
    Request body:
    {
        "comment_text": "..."
    }
    """
    try:
        data = request.get_json()
        comment_text = data.get('comment_text', '').strip()
        
        # Validation
        if not comment_text:
            return jsonify({'success': False, 'message': 'Comment không được để trống'}), 400
        
        if len(comment_text) > 5000:
            return jsonify({'success': False, 'message': 'Comment quá dài'}), 400
        
        # Sanitize
        comment_text = re.sub(r'<script[^>]*>.*?</script>', '', comment_text, flags=re.IGNORECASE | re.DOTALL)
        comment_text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', comment_text, flags=re.IGNORECASE | re.DOTALL)
        comment_text = re.sub(r'\bon\w+\s*=\s*["\'].*?["\']', '', comment_text, flags=re.IGNORECASE)
        
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)
        
        # Check ownership
        cursor.execute("""
            SELECT user_id FROM svg_comments 
            WHERE id = %s AND deleted_at IS NULL
        """, (comment_id,))
        
        comment = cursor.fetchone()
        if not comment:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Comment không tồn tại'}), 404
        
        if comment['user_id'] != current_user.id:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Bạn không có quyền chỉnh sửa'}), 403
        
        # Update
        cursor.execute("""
            UPDATE svg_comments 
            SET comment_text = %s, is_edited = 1, edited_at = NOW()
            WHERE id = %s
        """, (comment_text, comment_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Bình luận đã được cập nhật',
            'comment_text': comment_text,
            'edited_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[ERROR] update_comment: {e}", flush=True)
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500
```

---

### 2.6. API Endpoint: `DELETE /api/comments/<int:comment_id>`

**Mục đích:** Xóa comment (soft delete).

```python
@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """
    Soft delete a comment (owner only).
    """
    try:
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)
        
        # Check ownership and get info
        cursor.execute("""
            SELECT user_id, svg_filename, parent_comment_id 
            FROM svg_comments 
            WHERE id = %s AND deleted_at IS NULL
        """, (comment_id,))
        
        comment = cursor.fetchone()
        if not comment:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Comment không tồn tại'}), 404
        
        if comment['user_id'] != current_user.id:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Bạn không có quyền xóa'}), 403
        
        # Soft delete
        cursor.execute("""
            UPDATE svg_comments 
            SET deleted_at = NOW()
            WHERE id = %s
        """, (comment_id,))
        
        # Update counts
        cursor.execute("""
            UPDATE svg_image 
            SET comments_count = comments_count - 1 
            WHERE filename = %s
        """, (comment['svg_filename'],))
        
        if comment['parent_comment_id']:
            cursor.execute("""
                UPDATE svg_comments 
                SET replies_count = replies_count - 1 
                WHERE id = %s
            """, (comment['parent_comment_id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Bình luận đã được xóa'
        })
        
    except Exception as e:
        print(f"[ERROR] delete_comment: {e}", flush=True)
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500
```

---

### 2.7. API Endpoint: `POST /api/comments/<int:comment_id>/like`

**Mục đích:** Like/Unlike comment.

```python
@app.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@login_required
def toggle_comment_like(comment_id):
    """
    Toggle like on a comment.
    """
    try:
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)
        
        # Check if comment exists
        cursor.execute("""
            SELECT id FROM svg_comments 
            WHERE id = %s AND deleted_at IS NULL
        """, (comment_id,))
        
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Comment không tồn tại'}), 404
        
        # Check if already liked
        cursor.execute("""
            SELECT id FROM svg_comment_likes 
            WHERE comment_id = %s AND user_id = %s
        """, (comment_id, current_user.id))
        
        already_liked = cursor.fetchone()
        
        if already_liked:
            # Unlike
            cursor.execute("""
                DELETE FROM svg_comment_likes 
                WHERE comment_id = %s AND user_id = %s
            """, (comment_id, current_user.id))
            
            cursor.execute("""
                UPDATE svg_comments 
                SET likes_count = GREATEST(0, likes_count - 1)
                WHERE id = %s
            """, (comment_id,))
            
            action = 'unliked'
        else:
            # Like
            cursor.execute("""
                INSERT INTO svg_comment_likes (comment_id, user_id, created_at)
                VALUES (%s, %s, NOW())
            """, (comment_id, current_user.id))
            
            cursor.execute("""
                UPDATE svg_comments 
                SET likes_count = likes_count + 1
                WHERE id = %s
            """, (comment_id,))
            
            action = 'liked'
        
        conn.commit()
        
        # Get updated likes count
        cursor.execute("""
            SELECT likes_count FROM svg_comments WHERE id = %s
        """, (comment_id,))
        
        likes_count = cursor.fetchone()['likes_count']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'action': action,
            'likes_count': likes_count
        })
        
    except Exception as e:
        print(f"[ERROR] toggle_comment_like: {e}", flush=True)
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500
```

---

## 🎨 PHASE 3: FRONTEND - HTML STRUCTURE

### 3.1. Cập nhật `templates/view_svg.html`

Thêm section comments sau phần caption:

```html
<!-- Image Caption Section (existing) -->
<div class="image-caption-section">
    <!-- ... existing caption code ... -->
</div>

<!-- ✅ NEW: Comments Section -->
<div class="comments-section" id="comments-section">
    <!-- Header -->
    <div class="comments-header">
        <h3 class="comments-title">
            <span class="comments-icon">💬</span>
            Bình luận 
            <span class="comments-count" id="comments-total-count">{{ comments_count or 0 }}</span>
        </h3>
        
        <!-- Sort options -->
        <div class="comments-sort">
            <label for="comments-sort-select">Sắp xếp:</label>
            <select id="comments-sort-select" class="comments-sort-select">
                <option value="newest" selected>Mới nhất</option>
                <option value="oldest">Cũ nhất</option>
            </select>
        </div>
    </div>
    
    <!-- Comment Form (logged in users only) -->
    {% if current_user.is_authenticated %}
    <div class="comment-form-wrapper">
        <div class="comment-form">
            <div class="comment-form-avatar">
                <img src="{{ current_user.avatar or '/static/images/default-avatar.png' }}" 
                     alt="Your avatar" 
                     class="comment-avatar">
            </div>
            <div class="comment-form-content">
                <textarea 
                    id="new-comment-input" 
                    class="comment-textarea" 
                    placeholder="Viết bình luận... (Hỗ trợ LaTeX: $x^2$)"
                    maxlength="5000"
                    rows="3"></textarea>
                
                <div class="comment-form-footer">
                    <div class="comment-char-count">
                        <span id="comment-char-current">0</span> / 5000
                    </div>
                    
                    <div class="comment-form-actions">
                        <button type="button" 
                                id="comment-preview-btn" 
                                class="comment-btn comment-btn-secondary">
                            👁️ Preview
                        </button>
                        <button type="button" 
                                id="comment-submit-btn" 
                                class="comment-btn comment-btn-primary">
                            📝 Đăng bình luận
                        </button>
                    </div>
                </div>
                
                <!-- Preview area -->
                <div id="comment-preview" class="comment-preview" style="display: none;">
                    <div class="comment-preview-label">Preview:</div>
                    <div id="comment-preview-content" class="comment-preview-content"></div>
                </div>
            </div>
        </div>
    </div>
    {% else %}
    <!-- Login prompt -->
    <div class="comment-login-prompt">
        <p>
            <span class="prompt-icon">🔒</span>
            <a href="#" id="comment-login-link" class="login-link">Đăng nhập</a> 
            để tham gia thảo luận
        </p>
    </div>
    {% endif %}
    
    <!-- Comments List -->
    <div id="comments-list" class="comments-list">
        <!-- Comments will be loaded here via JavaScript -->
        <div class="comments-loading">
            <span class="loading-spinner">⏳</span>
            Đang tải bình luận...
        </div>
    </div>
    
    <!-- Pagination -->
    <div id="comments-pagination" class="comments-pagination" style="display: none;">
        <!-- Pagination controls will be generated by JavaScript -->
    </div>
    
    <!-- Message area -->
    <div id="comments-message" class="comments-message" style="display: none;"></div>
</div>

<!-- Inject comments data for JavaScript -->
<script id="comments-data-json" type="application/json">
{
    "filename": {{ filename|tojson|safe }},
    "currentUserId": {% if current_user.is_authenticated %}{{ current_user.id }}{% else %}null{% endif %},
    "currentUserAvatar": {% if current_user.is_authenticated %}{{ current_user.avatar|tojson|safe }}{% else %}null{% endif %},
    "commentsCount": {{ comments_count or 0 }}
}
</script>
```

---

## 💅 PHASE 4: FRONTEND - CSS STYLING

### 4.1. Tạo file `static/css/comments.css`

```css
/* =================================================================
   COMMENTS SECTION - View SVG Page
   ================================================================= */

/* Container */
.tikz-app .comments-section {
    margin-top: var(--spacing-12);
    padding: var(--spacing-8);
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border-radius: var(--border-radius-lg);
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow-sm);
}

/* Header */
.tikz-app .comments-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-6);
    padding-bottom: var(--spacing-4);
    border-bottom: 2px solid var(--border-light);
}

.tikz-app .comments-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
}

.tikz-app .comments-icon {
    font-size: 1.75rem;
}

.tikz-app .comments-count {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    background: var(--primary-color);
    color: white;
    border-radius: var(--border-radius-full);
    font-size: 0.875rem;
    font-weight: 600;
}

.tikz-app .comments-sort {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.tikz-app .comments-sort-select {
    padding: 0.375rem 0.75rem;
    border: 1px solid var(--border-light);
    border-radius: var(--border-radius-md);
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: var(--transition-fast);
}

.tikz-app .comments-sort-select:hover {
    border-color: var(--primary-color);
}

.tikz-app .comments-sort-select:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}

/* Comment Form */
.tikz-app .comment-form-wrapper {
    margin-bottom: var(--spacing-8);
}

.tikz-app .comment-form {
    display: flex;
    gap: var(--spacing-4);
}

.tikz-app .comment-form-avatar {
    flex-shrink: 0;
}

.tikz-app .comment-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--border-light);
}

.tikz-app .comment-form-content {
    flex: 1;
}

.tikz-app .comment-textarea {
    width: 100%;
    padding: var(--spacing-3);
    border: 1px solid var(--border-light);
    border-radius: var(--border-radius-md);
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: inherit;
    font-size: 0.9375rem;
    line-height: 1.5;
    resize: vertical;
    min-height: 80px;
    transition: var(--transition-fast);
}

.tikz-app .comment-textarea:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgb(59 130 246 / 10%);
}

.tikz-app .comment-textarea::placeholder {
    color: var(--text-muted);
}

.tikz-app .comment-form-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--spacing-3);
}

.tikz-app .comment-char-count {
    font-size: 0.8125rem;
    color: var(--text-muted);
}

.tikz-app .comment-form-actions {
    display: flex;
    gap: var(--spacing-2);
}

.tikz-app .comment-btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: var(--border-radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition-fast);
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.tikz-app .comment-btn-primary {
    background: var(--primary-color);
    color: white;
}

.tikz-app .comment-btn-primary:hover {
    background: var(--primary-dark);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.tikz-app .comment-btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-light);
}

.tikz-app .comment-btn-secondary:hover {
    background: var(--bg-tertiary);
}

.tikz-app .comment-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Preview */
.tikz-app .comment-preview {
    margin-top: var(--spacing-4);
    padding: var(--spacing-4);
    background: var(--bg-secondary);
    border-radius: var(--border-radius-md);
    border: 1px solid var(--border-light);
}

.tikz-app .comment-preview-label {
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-2);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.tikz-app .comment-preview-content {
    color: var(--text-primary);
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Login Prompt */
.tikz-app .comment-login-prompt {
    padding: var(--spacing-6);
    text-align: center;
    background: var(--bg-secondary);
    border-radius: var(--border-radius-md);
    margin-bottom: var(--spacing-6);
}

.tikz-app .comment-login-prompt p {
    margin: 0;
    font-size: 1rem;
    color: var(--text-secondary);
}

.tikz-app .prompt-icon {
    font-size: 1.5rem;
    display: block;
    margin-bottom: var(--spacing-2);
}

.tikz-app .login-link {
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 600;
}

.tikz-app .login-link:hover {
    text-decoration: underline;
}

/* Comments List */
.tikz-app .comments-list {
    margin-bottom: var(--spacing-6);
}

.tikz-app .comments-loading {
    padding: var(--spacing-8);
    text-align: center;
    color: var(--text-secondary);
}

.tikz-app .loading-spinner {
    display: inline-block;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    100% { transform: rotate(360deg); }
}

.tikz-app .comments-empty {
    padding: var(--spacing-8);
    text-align: center;
    color: var(--text-muted);
    font-style: italic;
}

/* Individual Comment */
.tikz-app .comment-item {
    padding: var(--spacing-5);
    margin-bottom: var(--spacing-4);
    background: var(--bg-primary);
    border-radius: var(--border-radius-md);
    border: 1px solid var(--border-light);
    transition: var(--transition-fast);
}

.tikz-app .comment-item:hover {
    box-shadow: var(--shadow-sm);
}

.tikz-app .comment-main {
    display: flex;
    gap: var(--spacing-3);
}

.tikz-app .comment-avatar-wrapper {
    flex-shrink: 0;
}

.tikz-app .comment-body {
    flex: 1;
    min-width: 0;
}

.tikz-app .comment-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    margin-bottom: var(--spacing-2);
    flex-wrap: wrap;
}

.tikz-app .comment-author {
    font-weight: 600;
    color: var(--text-primary);
    text-decoration: none;
}

.tikz-app .comment-author:hover {
    color: var(--primary-color);
}

.tikz-app .comment-verified-badge {
    display: inline-block;
    font-size: 0.875rem;
}

.tikz-app .comment-timestamp {
    font-size: 0.8125rem;
    color: var(--text-muted);
}

.tikz-app .comment-edited {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-style: italic;
}

.tikz-app .comment-text {
    color: var(--text-primary);
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin-bottom: var(--spacing-3);
}

/* Comment Actions */
.tikz-app .comment-actions {
    display: flex;
    gap: var(--spacing-4);
    align-items: center;
}

.tikz-app .comment-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 0.875rem;
    cursor: pointer;
    border-radius: var(--border-radius-sm);
    transition: var(--transition-fast);
}

.tikz-app .comment-action-btn:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
}

.tikz-app .comment-action-btn.liked {
    color: var(--error-color);
}

.tikz-app .comment-action-btn.liked:hover {
    color: var(--error-dark);
}

/* Replies */
.tikz-app .comment-replies {
    margin-top: var(--spacing-4);
    margin-left: calc(48px + var(--spacing-3));
    padding-left: var(--spacing-4);
    border-left: 2px solid var(--border-light);
}

.tikz-app .comment-reply-item {
    padding: var(--spacing-4);
    margin-bottom: var(--spacing-3);
    background: var(--bg-secondary);
    border-radius: var(--border-radius-md);
}

.tikz-app .show-replies-btn {
    margin-left: calc(48px + var(--spacing-3));
    margin-top: var(--spacing-3);
    padding: 0.5rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--border-radius-md);
    color: var(--text-primary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: var(--transition-fast);
}

.tikz-app .show-replies-btn:hover {
    background: var(--bg-tertiary);
}

/* Pagination */
.tikz-app .comments-pagination {
    display: flex;
    justify-content: center;
    gap: var(--spacing-2);
    margin-top: var(--spacing-6);
}

.tikz-app .pagination-btn {
    padding: 0.5rem 1rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: var(--border-radius-md);
    color: var(--text-primary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: var(--transition-fast);
}

.tikz-app .pagination-btn:hover:not(:disabled) {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.tikz-app .pagination-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.tikz-app .pagination-btn.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.tikz-app .pagination-info {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
}

/* Message */
.tikz-app .comments-message {
    padding: var(--spacing-4);
    border-radius: var(--border-radius-md);
    margin-top: var(--spacing-4);
    text-align: center;
}

.tikz-app .comments-message.success {
    background: rgb(34 197 94 / 10%);
    color: var(--success-color);
    border: 1px solid var(--success-color);
}

.tikz-app .comments-message.error {
    background: rgb(239 68 68 / 10%);
    color: var(--error-color);
    border: 1px solid var(--error-color);
}

/* Responsive */
@media (width < 640px) {
    .tikz-app .comments-section {
        padding: var(--spacing-4);
    }
    
    .tikz-app .comments-header {
        flex-direction: column;
        align-items: flex-start;
        gap: var(--spacing-3);
    }
    
    .tikz-app .comment-form {
        flex-direction: column;
    }
    
    .tikz-app .comment-avatar {
        width: 40px;
        height: 40px;
    }
    
    .tikz-app .comment-replies {
        margin-left: 0;
        padding-left: var(--spacing-3);
    }
    
    .tikz-app .show-replies-btn {
        margin-left: 0;
    }
}
```

---

### 4.2. Include CSS trong `base.html`

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/comments.css') }}">
```

---

## ⚙️ PHASE 5: FRONTEND - JAVASCRIPT

### 5.1. Tạo file `static/js/comments.js`

```javascript
// Comments System for View SVG Page
(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    commentsPerPage: 10,
    pollInterval: 30000, // 30 seconds for real-time updates
    maxCommentLength: 5000
  };

  // State
  let currentPage = 1;
  let currentSort = 'newest';
  let totalPages = 1;
  let isLoading = false;
  let pollTimer = null;

  // Initialize
  function initComments() {
    const commentsSection = document.getElementById('comments-section');
    if (!commentsSection) return;

    const commentsData = getCommentsData();
    if (!commentsData || !commentsData.filename) return;

    setupEventListeners();
    loadComments();
    
    // Start polling for updates if user is logged in
    if (commentsData.currentUserId) {
      startPolling();
    }
  }

  function getCommentsData() {
    try {
      const dataElement = document.getElementById('comments-data-json');
      if (!dataElement) return null;
      return JSON.parse(dataElement.textContent);
    } catch (e) {
      console.error('Error parsing comments data:', e);
      return null;
    }
  }

  function setupEventListeners() {
    // Submit new comment
    const submitBtn = document.getElementById('comment-submit-btn');
    if (submitBtn) {
      submitBtn.addEventListener('click', handleSubmitComment);
    }

    // Preview comment
    const previewBtn = document.getElementById('comment-preview-btn');
    if (previewBtn) {
      previewBtn.addEventListener('click', togglePreview);
    }

    // Character counter
    const commentInput = document.getElementById('new-comment-input');
    if (commentInput) {
      commentInput.addEventListener('input', updateCharCount);
    }

    // Sort change
    const sortSelect = document.getElementById('comments-sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', handleSortChange);
    }

    // Login link
    const loginLink = document.getElementById('comment-login-link');
    if (loginLink) {
      loginLink.addEventListener('click', (e) => {
        e.preventDefault();
        showLoginModal();
      });
    }
  }

  function showLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) modal.style.display = 'flex';
  }

  // Load comments
  async function loadComments(page = 1) {
    if (isLoading) return;
    isLoading = true;

    const commentsData = getCommentsData();
    const commentsList = document.getElementById('comments-list');
    
    commentsList.innerHTML = '<div class="comments-loading"><span class="loading-spinner">⏳</span> Đang tải bình luận...</div>';

    try {
      const response = await fetch(
        `/api/comments/${commentsData.filename}?page=${page}&per_page=${CONFIG.commentsPerPage}&sort=${currentSort}`
      );
      
      const result = await response.json();

      if (result.success) {
        currentPage = result.pagination.page;
        totalPages = result.pagination.total_pages;
        
        renderComments(result.comments);
        renderPagination(result.pagination);
        
        // Update total count
        const totalCountElement = document.getElementById('comments-total-count');
        if (totalCountElement) {
          totalCountElement.textContent = result.pagination.total;
        }
      } else {
        commentsList.innerHTML = '<div class="comments-empty">Không thể tải bình luận</div>';
      }
    } catch (error) {
      console.error('Error loading comments:', error);
      commentsList.innerHTML = '<div class="comments-empty">Lỗi kết nối</div>';
    } finally {
      isLoading = false;
    }
  }

  function renderComments(comments) {
    const commentsList = document.getElementById('comments-list');
    
    if (comments.length === 0) {
      commentsList.innerHTML = '<div class="comments-empty">📝 Chưa có bình luận nào. Hãy là người đầu tiên!</div>';
      return;
    }

    commentsList.innerHTML = comments.map(comment => createCommentHTML(comment)).join('');
    
    // Attach event listeners
    attachCommentEventListeners();
    
    // Render MathJax
    if (window.MathJax) {
      window.MathJax.typesetPromise([commentsList]).catch(err => {
        console.error('MathJax typeset error:', err);
      });
    }
  }

  function createCommentHTML(comment) {
    const commentsData = getCommentsData();
    const isOwner = commentsData.currentUserId === comment.user_id;
    const verifiedBadge = comment.identity_verified ? '<span class="comment-verified-badge" title="Đã xác minh">✓</span>' : '';
    
    const timestamp = formatTimestamp(comment.created_at);
    const editedText = comment.is_edited ? `<span class="comment-edited">(đã chỉnh sửa)</span>` : '';

    return `
      <div class="comment-item" data-comment-id="${comment.id}">
        <div class="comment-main">
          <div class="comment-avatar-wrapper">
            <img src="${comment.avatar || '/static/images/default-avatar.png'}" 
                 alt="${comment.username}" 
                 class="comment-avatar">
          </div>
          
          <div class="comment-body">
            <div class="comment-header">
              <a href="/profile/${comment.username}" class="comment-author">
                ${comment.username}
              </a>
              ${verifiedBadge}
              <span class="comment-timestamp">${timestamp}</span>
              ${editedText}
            </div>
            
            <div class="comment-text">${escapeHtml(comment.comment_text)}</div>
            
            <div class="comment-actions">
              <button class="comment-action-btn like-btn ${comment.user_has_liked ? 'liked' : ''}" 
                      data-comment-id="${comment.id}"
                      ${commentsData.currentUserId ? '' : 'disabled'}>
                <span class="like-icon">${comment.user_has_liked ? '❤️' : '🤍'}</span>
                <span class="like-count">${comment.likes_count}</span>
              </button>
              
              <button class="comment-action-btn reply-btn" 
                      data-comment-id="${comment.id}"
                      ${commentsData.currentUserId ? '' : 'disabled'}>
                💬 Trả lời
              </button>
              
              ${isOwner ? `
                <button class="comment-action-btn edit-btn" data-comment-id="${comment.id}">
                  ✏️ Sửa
                </button>
                <button class="comment-action-btn delete-btn" data-comment-id="${comment.id}">
                  🗑️ Xóa
                </button>
              ` : ''}
            </div>
            
            ${comment.replies_count > 0 ? `
              <button class="show-replies-btn" data-comment-id="${comment.id}">
                💬 Xem ${comment.replies_count} trả lời
              </button>
              <div class="comment-replies" id="replies-${comment.id}" style="display: none;"></div>
            ` : `
              <div class="comment-replies" id="replies-${comment.id}" style="display: none;"></div>
            `}
          </div>
        </div>
      </div>
    `;
  }

  function attachCommentEventListeners() {
    // Like buttons
    document.querySelectorAll('.like-btn').forEach(btn => {
      btn.addEventListener('click', handleLikeComment);
    });

    // Reply buttons
    document.querySelectorAll('.reply-btn').forEach(btn => {
      btn.addEventListener('click', handleReplyComment);
    });

    // Edit buttons
    document.querySelectorAll('.edit-btn').forEach(btn => {
      btn.addEventListener('click', handleEditComment);
    });

    // Delete buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', handleDeleteComment);
    });

    // Show replies buttons
    document.querySelectorAll('.show-replies-btn').forEach(btn => {
      btn.addEventListener('click', handleShowReplies);
    });
  }

  // Submit new comment
  async function handleSubmitComment() {
    const commentsData = getCommentsData();
    const commentInput = document.getElementById('new-comment-input');
    const submitBtn = document.getElementById('comment-submit-btn');
    
    const commentText = commentInput.value.trim();
    
    if (!commentText) {
      showMessage('Vui lòng nhập nội dung bình luận', 'error');
      return;
    }

    if (commentText.length > CONFIG.maxCommentLength) {
      showMessage(`Bình luận quá dài (tối đa ${CONFIG.maxCommentLength} ký tự)`, 'error');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '⏳ Đang đăng...';

    try {
      const response = await fetch(`/api/comments/${commentsData.filename}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          comment_text: commentText,
          parent_comment_id: null
        })
      });

      const result = await response.json();

      if (result.success) {
        commentInput.value = '';
        updateCharCount();
        hidePreview();
        showMessage('Bình luận đã được đăng!', 'success');
        
        // Reload comments
        await loadComments(1);
      } else {
        showMessage(result.message || 'Không thể đăng bình luận', 'error');
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
      showMessage('Lỗi kết nối', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '📝 Đăng bình luận';
    }
  }

  // Like/Unlike comment
  async function handleLikeComment(e) {
    const btn = e.currentTarget;
    const commentId = btn.dataset.commentId;
    
    btn.disabled = true;

    try {
      const response = await fetch(`/api/comments/${commentId}/like`, {
        method: 'POST'
      });

      const result = await response.json();

      if (result.success) {
        const likeIcon = btn.querySelector('.like-icon');
        const likeCount = btn.querySelector('.like-count');
        
        if (result.action === 'liked') {
          btn.classList.add('liked');
          likeIcon.textContent = '❤️';
        } else {
          btn.classList.remove('liked');
          likeIcon.textContent = '🤍';
        }
        
        likeCount.textContent = result.likes_count;
      } else {
        showMessage(result.message || 'Không thể thực hiện', 'error');
      }
    } catch (error) {
      console.error('Error liking comment:', error);
      showMessage('Lỗi kết nối', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  // Show replies
  async function handleShowReplies(e) {
    const btn = e.currentTarget;
    const commentId = btn.dataset.commentId;
    const repliesContainer = document.getElementById(`replies-${commentId}`);
    
    if (repliesContainer.style.display === 'block') {
      repliesContainer.style.display = 'none';
      btn.textContent = `💬 Xem ${btn.textContent.match(/\d+/)[0]} trả lời`;
      return;
    }

    btn.disabled = true;
    btn.textContent = '⏳ Đang tải...';

    try {
      const response = await fetch(`/api/comments/${commentId}/replies`);
      const result = await response.json();

      if (result.success) {
        repliesContainer.innerHTML = result.replies.map(reply => createReplyHTML(reply)).join('');
        repliesContainer.style.display = 'block';
        btn.textContent = '🔼 Ẩn trả lời';
        
        // Render MathJax for replies
        if (window.MathJax) {
          window.MathJax.typesetPromise([repliesContainer]).catch(err => {
            console.error('MathJax typeset error:', err);
          });
        }
        
        // Attach event listeners for reply actions
        attachReplyEventListeners(repliesContainer);
      } else {
        showMessage('Không thể tải trả lời', 'error');
      }
    } catch (error) {
      console.error('Error loading replies:', error);
      showMessage('Lỗi kết nối', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  function createReplyHTML(reply) {
    const commentsData = getCommentsData();
    const isOwner = commentsData.currentUserId === reply.user_id;
    const verifiedBadge = reply.identity_verified ? '<span class="comment-verified-badge">✓</span>' : '';
    const timestamp = formatTimestamp(reply.created_at);
    const editedText = reply.is_edited ? `<span class="comment-edited">(đã chỉnh sửa)</span>` : '';

    return `
      <div class="comment-reply-item" data-comment-id="${reply.id}">
        <div class="comment-main">
          <div class="comment-avatar-wrapper">
            <img src="${reply.avatar || '/static/images/default-avatar.png'}" 
                 alt="${reply.username}" 
                 class="comment-avatar">
          </div>
          
          <div class="comment-body">
            <div class="comment-header">
              <a href="/profile/${reply.username}" class="comment-author">${reply.username}</a>
              ${verifiedBadge}
              <span class="comment-timestamp">${timestamp}</span>
              ${editedText}
            </div>
            
            <div class="comment-text">${escapeHtml(reply.comment_text)}</div>
            
            <div class="comment-actions">
              <button class="comment-action-btn like-btn ${reply.user_has_liked ? 'liked' : ''}" 
                      data-comment-id="${reply.id}"
                      ${commentsData.currentUserId ? '' : 'disabled'}>
                <span class="like-icon">${reply.user_has_liked ? '❤️' : '🤍'}</span>
                <span class="like-count">${reply.likes_count}</span>
              </button>
              
              ${isOwner ? `
                <button class="comment-action-btn edit-btn" data-comment-id="${reply.id}">
                  ✏️ Sửa
                </button>
                <button class="comment-action-btn delete-btn" data-comment-id="${reply.id}">
                  🗑️ Xóa
                </button>
              ` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function attachReplyEventListeners(container) {
    container.querySelectorAll('.like-btn').forEach(btn => {
      btn.addEventListener('click', handleLikeComment);
    });

    container.querySelectorAll('.edit-btn').forEach(btn => {
      btn.addEventListener('click', handleEditComment);
    });

    container.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', handleDeleteComment);
    });
  }

  // Reply to comment
  async function handleReplyComment(e) {
    const btn = e.currentTarget;
    const commentId = btn.dataset.commentId;
    
    // TODO: Implement reply form (inline or modal)
    showMessage('Reply feature coming soon!', 'info');
  }

  // Edit comment
  async function handleEditComment(e) {
    const btn = e.currentTarget;
    const commentId = btn.dataset.commentId;
    
    // TODO: Implement edit form (inline)
    showMessage('Edit feature coming soon!', 'info');
  }

  // Delete comment
  async function handleDeleteComment(e) {
    const btn = e.currentTarget;
    const commentId = btn.dataset.commentId;
    
    if (!confirm('Bạn có chắc muốn xóa bình luận này?')) {
      return;
    }

    btn.disabled = true;

    try {
      const response = await fetch(`/api/comments/${commentId}`, {
        method: 'DELETE'
      });

      const result = await response.json();

      if (result.success) {
        showMessage('Bình luận đã được xóa', 'success');
        await loadComments(currentPage);
      } else {
        showMessage(result.message || 'Không thể xóa bình luận', 'error');
      }
    } catch (error) {
      console.error('Error deleting comment:', error);
      showMessage('Lỗi kết nối', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  // Pagination
  function renderPagination(pagination) {
    const paginationContainer = document.getElementById('comments-pagination');
    
    if (pagination.total_pages <= 1) {
      paginationContainer.style.display = 'none';
      return;
    }

    paginationContainer.style.display = 'flex';
    
    let html = '';
    
    // Previous button
    html += `
      <button class="pagination-btn" 
              data-page="${pagination.page - 1}" 
              ${pagination.page === 1 ? 'disabled' : ''}>
        « Trước
      </button>
    `;
    
    // Page numbers
    for (let i = 1; i <= pagination.total_pages; i++) {
      if (
        i === 1 || 
        i === pagination.total_pages || 
        (i >= pagination.page - 2 && i <= pagination.page + 2)
      ) {
        html += `
          <button class="pagination-btn ${i === pagination.page ? 'active' : ''}" 
                  data-page="${i}">
            ${i}
          </button>
        `;
      } else if (i === pagination.page - 3 || i === pagination.page + 3) {
        html += '<span class="pagination-info">...</span>';
      }
    }
    
    // Next button
    html += `
      <button class="pagination-btn" 
              data-page="${pagination.page + 1}" 
              ${pagination.page === pagination.total_pages ? 'disabled' : ''}>
        Sau »
      </button>
    `;
    
    paginationContainer.innerHTML = html;
    
    // Attach event listeners
    paginationContainer.querySelectorAll('.pagination-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const page = parseInt(btn.dataset.page);
        if (page >= 1 && page <= pagination.total_pages) {
          loadComments(page);
        }
      });
    });
  }

  // Sort change
  function handleSortChange(e) {
    currentSort = e.target.value;
    loadComments(1);
  }

  // Preview
  function togglePreview() {
    const preview = document.getElementById('comment-preview');
    const previewContent = document.getElementById('comment-preview-content');
    const commentInput = document.getElementById('new-comment-input');
    
    if (preview.style.display === 'block') {
      preview.style.display = 'none';
      return;
    }
    
    const text = commentInput.value.trim();
    if (!text) {
      showMessage('Vui lòng nhập nội dung trước', 'error');
      return;
    }
    
    previewContent.textContent = text;
    preview.style.display = 'block';
    
    // Render MathJax
    if (window.MathJax) {
      window.MathJax.typesetPromise([previewContent]).catch(err => {
        console.error('MathJax typeset error:', err);
      });
    }
  }

  function hidePreview() {
    const preview = document.getElementById('comment-preview');
    preview.style.display = 'none';
  }

  // Character counter
  function updateCharCount() {
    const commentInput = document.getElementById('new-comment-input');
    const charCurrent = document.getElementById('comment-char-current');
    
    if (commentInput && charCurrent) {
      charCurrent.textContent = commentInput.value.length;
    }
  }

  // Show message
  function showMessage(text, type = 'info') {
    const messageContainer = document.getElementById('comments-message');
    if (!messageContainer) return;
    
    messageContainer.className = `comments-message ${type}`;
    messageContainer.textContent = text;
    messageContainer.style.display = 'block';
    
    setTimeout(() => {
      messageContainer.style.display = 'none';
    }, 5000);
  }

  // Polling for updates
  function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    
    pollTimer = setInterval(() => {
      // Silently reload current page to check for updates
      loadComments(currentPage);
    }, CONFIG.pollInterval);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  // Utilities
  function formatTimestamp(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;
    
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initComments);
  } else {
    initComments();
  }

  // Cleanup on page unload
  window.addEventListener('beforeunload', stopPolling);

})();
```

---

### 5.2. Include JavaScript trong `view_svg.html`

```html
<script src="{{ url_for('static', filename='js/comments.js') }}" defer></script>
```

---

## 🔒 PHASE 6: SECURITY & VALIDATION

### 6.1. Input Sanitization

**Backend (`app.py`):**

```python
import re
import html

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

---

### 6.2. Rate Limiting

**Install Flask-Limiter:**

```bash
pip install Flask-Limiter
```

**Config (`app.py`):**

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to comment endpoints
@app.route('/api/comments/<filename>', methods=['POST'])
@login_required
@limiter.limit("10 per minute")  # Max 10 comments per minute
def create_comment(filename):
    # ... existing code ...
```

---

## 🧪 PHASE 7: TESTING

### 7.1. Manual Testing Checklist

**Database:**
- [ ] Tables created successfully
- [ ] Foreign keys working
- [ ] Indexes created
- [ ] UTF8MB4 encoding correct

**API Endpoints:**
- [ ] GET comments - pagination works
- [ ] GET comments - sorting works
- [ ] POST comment - validation works
- [ ] POST comment - ownership check works
- [ ] PUT comment - only owner can edit
- [ ] DELETE comment - soft delete works
- [ ] POST like - toggle works
- [ ] GET replies - nested comments work

**Frontend:**
- [ ] Comments load correctly
- [ ] New comment form works
- [ ] LaTeX renders with MathJax
- [ ] Line breaks preserved
- [ ] Like button toggles
- [ ] Reply button works
- [ ] Edit button (owner only)
- [ ] Delete button (owner only)
- [ ] Pagination works
- [ ] Sort dropdown works
- [ ] Real-time updates (polling)
- [ ] Login prompt for guests
- [ ] Responsive on mobile

**Security:**
- [ ] XSS attacks blocked
- [ ] SQL injection prevented
- [ ] Rate limiting enforced
- [ ] CSRF protection enabled

**Performance:**
- [ ] Queries optimized with indexes
- [ ] Pagination limits data load
- [ ] MathJax loads async
- [ ] No N+1 query problems

---

## 📚 PHASE 8: DOCUMENTATION

### 8.1. Update Documentation Files

**Files to update:**

1. `DATABASE_DOCUMENTATION.md`
   - Add comments system schema
   - Add SQL queries for comments CRUD
   - Add statistics queries

2. `COMMENTS_FEATURE_GUIDE.md` (this file)
   - Implementation guide
   - API reference
   - Frontend integration

3. `README.md`
   - Add comments feature to feature list
   - Update screenshots

4. `DEPLOYMENT_GUIDE_VPS.md`
   - Add comments migration steps

---

## 🚀 PHASE 9: DEPLOYMENT

### 9.1. VPS Deployment Steps

```bash
# 1. Backup database
mysqldump -u root -p tikz2svg > backup_before_comments_$(date +%Y%m%d).sql

# 2. Run migration
mysql -u root -p tikz2svg < add_comments_system.sql

# 3. Verify migration
mysql -u root -p tikz2svg -e "DESCRIBE svg_comments; DESCRIBE svg_comment_likes; SHOW COLUMNS FROM svg_image WHERE Field = 'comments_count';"

# 4. Deploy code
git pull origin main

# 5. Install dependencies (if needed)
pip install Flask-Limiter

# 6. Restart application
sudo systemctl restart tikz2svg

# 7. Test
curl http://localhost:5000/view_svg/<some_filename>
```

---

## 🔮 PHASE 10: FUTURE ENHANCEMENTS (Phase 2)

### 10.1. Planned Features

1. **Mention System (@username)**
   - Parse @username in comments
   - Link to user profiles
   - Send notifications

2. **Notifications**
   - New reply notification
   - Mention notification
   - Like notification
   - Email digest

3. **Rich Text Editor**
   - WYSIWYG editor
   - Better LaTeX input
   - Code syntax highlighting

4. **Comment Moderation**
   - Report inappropriate comments
   - Admin moderation panel
   - Auto-moderation (spam detection)

5. **Reactions**
   - Beyond likes: 👍 👎 😂 ❤️ 🎉
   - Reaction counts

6. **Search Comments**
   - Full-text search
   - Filter by user
   - Filter by date range

7. **Real-time with WebSocket**
   - Replace polling with WebSocket
   - Live comment updates
   - Typing indicators

8. **Comment Analytics**
   - Most commented SVGs
   - Most active commenters
   - Engagement metrics

---

## ✅ IMPLEMENTATION CHECKLIST

### Database (Phase 1)
- [ ] Create `svg_comments` table
- [ ] Create `svg_comment_likes` table
- [ ] Add `comments_count` to `svg_image`
- [ ] Test foreign keys
- [ ] Test indexes
- [ ] Update `DATABASE_DOCUMENTATION.md`

### Backend (Phase 2)
- [ ] Update `/view_svg/<filename>` route
- [ ] Create `GET /api/comments/<filename>`
- [ ] Create `GET /api/comments/<id>/replies`
- [ ] Create `POST /api/comments/<filename>`
- [ ] Create `PUT /api/comments/<id>`
- [ ] Create `DELETE /api/comments/<id>`
- [ ] Create `POST /api/comments/<id>/like`
- [ ] Add input sanitization
- [ ] Add rate limiting
- [ ] Test all endpoints with Postman/curl

### Frontend HTML (Phase 3)
- [ ] Add comments section to `view_svg.html`
- [ ] Add comment form
- [ ] Add comments list container
- [ ] Add pagination container
- [ ] Add data JSON script
- [ ] Test HTML structure

### Frontend CSS (Phase 4)
- [ ] Create `static/css/comments.css`
- [ ] Style comments section
- [ ] Style comment form
- [ ] Style comment items
- [ ] Style replies
- [ ] Style pagination
- [ ] Add responsive styles
- [ ] Include CSS in `base.html`

### Frontend JavaScript (Phase 5)
- [ ] Create `static/js/comments.js`
- [ ] Implement loadComments()
- [ ] Implement createComment()
- [ ] Implement likeComment()
- [ ] Implement showReplies()
- [ ] Implement editComment()
- [ ] Implement deleteComment()
- [ ] Implement pagination
- [ ] Implement real-time polling
- [ ] Integrate MathJax
- [ ] Include JS in `view_svg.html`

### Testing (Phase 7)
- [ ] Manual test all user flows
- [ ] Test as owner
- [ ] Test as guest
- [ ] Test as other user
- [ ] Test on mobile
- [ ] Test MathJax rendering
- [ ] Test XSS prevention
- [ ] Test rate limiting
- [ ] Performance testing

### Documentation (Phase 8)
- [ ] Create this guide
- [ ] Update DATABASE_DOCUMENTATION.md
- [ ] Update README.md
- [ ] Create API documentation
- [ ] Add screenshots

### Deployment (Phase 9)
- [ ] Backup production database
- [ ] Run migration on VPS
- [ ] Deploy code to VPS
- [ ] Test on production
- [ ] Monitor for errors

---

## 📊 Estimated Timeline

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Database | Schema design, migration script | 2-3 hours |
| Phase 2: Backend API | 7 endpoints, validation, security | 6-8 hours |
| Phase 3: Frontend HTML | Template structure | 1-2 hours |
| Phase 4: Frontend CSS | Styling, responsive design | 3-4 hours |
| Phase 5: Frontend JS | All interactions, polling | 8-10 hours |
| Phase 6: Security | Sanitization, rate limiting | 2-3 hours |
| Phase 7: Testing | Manual testing, bug fixes | 4-6 hours |
| Phase 8: Documentation | Guides, API docs | 2-3 hours |
| Phase 9: Deployment | VPS deployment, monitoring | 2-3 hours |

**Total: 30-42 hours** (approximately 4-5 working days)

---

## 🎯 Success Criteria

**The Comments Feature is considered complete when:**

✅ Users can post, edit, and delete their own comments  
✅ Users can reply to comments (1 level deep)  
✅ Users can like/unlike comments  
✅ MathJax formulas render correctly in comments  
✅ Comments load with pagination (10 per page)  
✅ Real-time updates work (30-second polling)  
✅ Mobile responsive design works perfectly  
✅ XSS attacks are prevented  
✅ Rate limiting prevents spam  
✅ All database queries are optimized  
✅ Documentation is complete  
✅ Successfully deployed to production  

---

**Last Updated:** 2025-10-22  
**Status:** 📋 Planning Phase  
**Next Step:** Begin Phase 1 (Database Schema)

