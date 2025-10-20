# Image Caption Feature - Hướng dẫn Triển khai

## 📋 Tổng quan

Tính năng Image Caption cho phép người tạo ảnh SVG thêm mô tả chi tiết cho ảnh của họ, với hỗ trợ hiển thị công thức toán học qua MathJax.

**Tính năng chính:**
- ✅ Thêm/chỉnh sửa caption cho ảnh SVG
- ✅ Hỗ trợ LaTeX/MathJax: `$x^2$`, `$$\int_{0}^{1} x dx$$`
- ✅ Chỉ chủ sở hữu mới có quyền chỉnh sửa
- ✅ Lưu trữ an toàn trong database
- ✅ Responsive design cho mọi thiết bị
- ✅ Chuẩn bị cho tính năng comments

---

## 🗂️ Database Schema

### Bảng `svg_image` - Thêm cột `caption`

```sql
ALTER TABLE svg_image 
ADD COLUMN caption TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
AFTER keywords;
```

**Chi tiết cột:**
- **Type**: `TEXT` - Cho phép nội dung dài
- **Charset**: `utf8mb4_unicode_ci` - Hỗ trợ đầy đủ Unicode
- **Default**: `NULL` - Ảnh cũ không bắt buộc có caption
- **Vị trí**: Sau cột `keywords`

**Migration Script:** `add_image_caption_column.sql`

---

## 🔧 Backend Implementation

### 1. Cập nhật Route `/view_svg/<filename>`

**File:** `app.py`

**Thay đổi:**
```python
@app.route('/view_svg/<filename>')
def view_svg(filename):
    # ... existing code ...
    
    try:
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)

        # ✅ UPDATED: Add caption to SELECT query
        cursor.execute("""
            SELECT tikz_code, user_id, caption
            FROM svg_image 
            WHERE filename = %s 
            LIMIT 1
        """, (filename,))
        row = cursor.fetchone()

        if row:
            tikz_code = row['tikz_code']
            user_id = row['user_id']
            caption = row.get('caption', '')  # ✅ NEW
            
            # ... existing user lookup code ...
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] in /view_svg DB lookup: {e}", flush=True)

    # ✅ UPDATED: Pass caption to template
    return render_template(
        "view_svg.html",
        svg_url=svg_url,
        png_url=png_url,
        tikz_code=tikz_code,
        filename=filename,
        display_name=display_name,
        caption=caption,  # ✅ NEW
        user_email=user_email,
        username=username,
        avatar=avatar
    )
```

### 2. Tạo API Endpoint mới: `POST /api/update_caption/<filename>`

**File:** `app.py`

```python
@app.route('/api/update_caption/<filename>', methods=['POST'])
@login_required
def update_caption(filename):
    """
    Update caption for an SVG image.
    Only the owner can update the caption.
    """
    try:
        data = request.get_json()
        new_caption = data.get('caption', '').strip()
        
        # Validate caption length (max 5000 characters)
        if len(new_caption) > 5000:
            return jsonify({
                'success': False,
                'error': 'Caption quá dài. Tối đa 5000 ký tự.'
            }), 400
        
        # Sanitize input (remove dangerous HTML tags, keep LaTeX)
        # Basic sanitization - you may want to use bleach library
        import re
        # Allow only LaTeX math delimiters and plain text
        # Remove script tags, etc.
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'on\w+\s*=',  # onclick, onload, etc.
        ]
        for pattern in dangerous_patterns:
            new_caption = re.sub(pattern, '', new_caption, flags=re.IGNORECASE | re.DOTALL)
        
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Check ownership
        cursor.execute("""
            SELECT user_id 
            FROM svg_image 
            WHERE filename = %s
        """, (filename,))
        
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy ảnh.'
            }), 404
        
        if row['user_id'] != current_user.id:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Bạn không có quyền chỉnh sửa caption của ảnh này.'
            }), 403
        
        # Update caption
        cursor.execute("""
            UPDATE svg_image 
            SET caption = %s 
            WHERE filename = %s AND user_id = %s
        """, (new_caption, filename, current_user.id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Caption đã được cập nhật thành công!',
            'caption': new_caption
        })
        
    except Exception as e:
        print(f"[ERROR] update_caption: {e}", flush=True)
        return jsonify({
            'success': False,
            'error': 'Lỗi server. Vui lòng thử lại.'
        }), 500
```

### 3. Cập nhật các hàm helper

**Cập nhật `get_svg_files()` và `get_svg_files_with_likes()`:**

```python
def get_svg_files():
    """Lấy danh sách các SVG đã lưu trong MySQL"""
    # ... existing code ...
    
    cursor.execute("""
        SELECT 
            s.id, 
            s.filename, 
            s.tikz_code, 
            s.keywords,
            s.caption,  -- ✅ NEW
            s.created_at,
            -- ... rest of query
    """, (current_user_id,))
    
    # ... rest of function
```

---

## 🎨 Frontend Implementation

### 1. Cập nhật Template `templates/view_svg.html`

**Thêm MathJax CDN vào `base.html` hoặc trong block `extra_js`:**

```html
{% block extra_js %}
<!-- MathJax Configuration and CDN -->
<script>
window.MathJax = {
    tex: {
        inlineMath: [['$', '$']],
        displayMath: [['$$', '$$']],
        processEscapes: true,
        processEnvironments: true
    },
    options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
    },
    startup: {
        pageReady: () => {
            return MathJax.startup.defaultPageReady().then(() => {
                console.log('MathJax initial typesetting complete');
            });
        }
    }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>

<!-- Application JavaScript -->
<script src="{{ url_for('static', filename='js/view_svg.js', v='2.0') }}"></script>
{% endblock %}
```

**Thêm section caption sau `.view-svg-container`:**

```html
{% block content %}

<!-- View SVG Section -->
<div class="view-svg-container">
    <h2 class="view-svg-title">{{ display_name }}</h2>
    
    <div id="view-mode-row">
        <!-- ... existing SVG preview and actions ... -->
    </div>
</div>

<!-- ✅ NEW: Image Caption Section -->
<div class="image-caption-section">
    <h3 class="caption-section-title">
        <span class="caption-icon">📝</span> Mô tả ảnh
    </h3>
    
    <!-- Caption Display Mode -->
    <div id="caption-display" class="caption-content" {% if not caption %}style="display: none;"{% endif %}>
        <div class="caption-text">{{ caption|safe if caption else '' }}</div>
    </div>
    
    <!-- Empty State (when no caption) -->
    <div id="caption-empty" class="caption-empty" {% if caption %}style="display: none;"{% endif %}>
        <p class="caption-empty-text">
            {% if user_email and user_id == current_user.id %}
                Chưa có mô tả. Nhấn nút bên dưới để thêm mô tả cho ảnh.
            {% else %}
                Ảnh này chưa có mô tả.
            {% endif %}
        </p>
    </div>
    
    <!-- Edit Form (only visible when editing) -->
    <div id="caption-edit-form" class="caption-edit-form" style="display: none;">
        <textarea 
            id="caption-input" 
            class="caption-textarea"
            placeholder="Thêm mô tả cho ảnh của bạn. Hỗ trợ công thức toán: $x^2$, $$\int_{0}^{1} x dx$$"
            maxlength="5000"
        >{{ caption if caption else '' }}</textarea>
        <div class="caption-form-footer">
            <div class="caption-char-count">
                <span id="caption-char-current">{{ caption|length if caption else 0 }}</span>/5000 ký tự
            </div>
            <div class="caption-actions">
                <button id="cancel-caption-btn" class="caption-btn caption-btn-cancel">
                    ❌ Hủy
                </button>
                <button id="save-caption-btn" class="caption-btn caption-btn-save">
                    ✅ Lưu
                </button>
            </div>
        </div>
        <div class="caption-preview">
            <h4>Preview (với MathJax):</h4>
            <div id="caption-preview-content" class="caption-preview-content"></div>
        </div>
    </div>
    
    <!-- Edit Button (only for owner) -->
    {% if user_email and user_id == current_user.id %}
    <button id="edit-caption-btn" class="edit-caption-btn">
        <span class="edit-icon">✏️</span> 
        <span class="edit-text">{{ 'Chỉnh sửa mô tả' if caption else 'Thêm mô tả' }}</span>
    </button>
    {% endif %}
    
    <!-- Messages -->
    <div id="caption-message" class="caption-message"></div>
</div>

<!-- Inject data for JavaScript -->
<script id="caption-data-json" type="application/json">
{
    "filename": {{ filename|tojson|safe }},
    "caption": {{ caption|tojson|safe }},
    "isOwner": {% if user_email and user_id == current_user.id %}true{% else %}false{% endif %}
}
</script>

{% endblock %}
```

### 2. CSS Styling `static/css/view_svg.css`

**Thêm styles cho caption section:**

```css
/* ===== IMAGE CAPTION SECTION ===== */

.tikz-app .image-caption-section {
    background: var(--glass-bg-strong);
    backdrop-filter: var(--glass-blur-medium);
    padding: var(--spacing-8);
    margin-top: var(--spacing-6);
    margin-bottom: var(--spacing-8);
    border-radius: var(--radius-xl);
    box-shadow: var(--glass-shadow);
    position: relative;
    overflow: hidden;
}

/* Add subtle background pattern */
.tikz-app .image-caption-section::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, 
                rgb(255 255 255 / 10%) 0%, 
                transparent 50%, 
                rgb(255 255 255 / 10%) 100%);
    border-radius: inherit;
    pointer-events: none;
}

.tikz-app .caption-section-title {
    position: relative;
    z-index: 1;
    color: var(--primary-color);
    margin-bottom: var(--spacing-4);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
}

.tikz-app .caption-icon {
    font-size: 1.2em;
}

/* Caption Display Mode */
.tikz-app .caption-content {
    position: relative;
    z-index: 1;
    background: #fff;
    border-radius: var(--radius-md);
    padding: var(--spacing-6);
    margin-bottom: var(--spacing-4);
    box-shadow: var(--shadow-sm);
    border: 1.5px solid var(--border-light);
}

.tikz-app .caption-text {
    color: var(--text-primary);
    font-size: var(--font-size-base);
    line-height: 1.7;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

/* MathJax styling */
.tikz-app .caption-text mjx-container {
    margin: var(--spacing-1) 0;
}

/* Empty State */
.tikz-app .caption-empty {
    position: relative;
    z-index: 1;
    padding: var(--spacing-6);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
}

.tikz-app .caption-empty-text {
    margin: 0;
}

/* Edit Form */
.tikz-app .caption-edit-form {
    position: relative;
    z-index: 1;
    background: #fff;
    border-radius: var(--radius-md);
    padding: var(--spacing-6);
    margin-bottom: var(--spacing-4);
    box-shadow: var(--shadow-sm);
    border: 1.5px solid var(--border-light);
}

.tikz-app .caption-textarea {
    width: 100%;
    min-height: 150px;
    padding: var(--spacing-4);
    border: 1.5px solid var(--border-light);
    border-radius: var(--radius-md);
    font-family: inherit;
    font-size: var(--font-size-base);
    line-height: 1.6;
    resize: vertical;
    transition: border-color var(--transition-fast);
}

.tikz-app .caption-textarea:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgb(25 118 210 / 10%);
}

.tikz-app .caption-form-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--spacing-3);
    flex-wrap: wrap;
    gap: var(--spacing-3);
}

.tikz-app .caption-char-count {
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
}

.tikz-app .caption-actions {
    display: flex;
    gap: var(--spacing-3);
}

.tikz-app .caption-btn {
    padding: var(--spacing-3) var(--spacing-5);
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-semibold);
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
}

.tikz-app .caption-btn-save {
    background: linear-gradient(90deg, #28a745 0%, #218838 100%);
    color: white;
}

.tikz-app .caption-btn-save:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgb(40 167 69 / 30%);
}

.tikz-app .caption-btn-cancel {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-light);
}

.tikz-app .caption-btn-cancel:hover {
    background: var(--bg-tertiary);
    transform: translateY(-1px);
}

/* Preview */
.tikz-app .caption-preview {
    margin-top: var(--spacing-4);
    padding-top: var(--spacing-4);
    border-top: 1px solid var(--border-light);
}

.tikz-app .caption-preview h4 {
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
    margin-bottom: var(--spacing-2);
}

.tikz-app .caption-preview-content {
    background: var(--bg-secondary);
    padding: var(--spacing-4);
    border-radius: var(--radius-sm);
    min-height: 60px;
    font-size: var(--font-size-base);
    line-height: 1.7;
}

/* Edit Button */
.tikz-app .edit-caption-btn {
    position: relative;
    z-index: 1;
    background: linear-gradient(90deg, #1976d2 0%, #1565c0 100%);
    color: white;
    padding: var(--spacing-3) var(--spacing-5);
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    margin: 0 auto;
}

.tikz-app .edit-caption-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgb(25 118 210 / 30%);
}

.tikz-app .edit-icon {
    font-size: 1.1em;
}

/* Messages */
.tikz-app .caption-message {
    position: relative;
    z-index: 1;
    margin-top: var(--spacing-3);
    padding: var(--spacing-3) var(--spacing-4);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    text-align: center;
    display: none;
}

.tikz-app .caption-message.success {
    display: block;
    background: rgb(40 167 69 / 10%);
    color: #28a745;
    border: 1px solid rgb(40 167 69 / 30%);
}

.tikz-app .caption-message.error {
    display: block;
    background: rgb(220 53 69 / 10%);
    color: #dc3545;
    border: 1px solid rgb(220 53 69 / 30%);
}

/* ===== RESPONSIVE BREAKPOINTS ===== */

@media (width < 576px) {
    .tikz-app .image-caption-section {
        padding: var(--spacing-4);
    }
    
    .tikz-app .caption-section-title {
        font-size: var(--font-size-lg);
    }
    
    .tikz-app .caption-content,
    .tikz-app .caption-edit-form {
        padding: var(--spacing-4);
    }
    
    .tikz-app .caption-textarea {
        min-height: 120px;
        font-size: var(--font-size-sm);
    }
    
    .tikz-app .caption-form-footer {
        flex-direction: column;
        align-items: stretch;
    }
    
    .tikz-app .caption-actions {
        width: 100%;
        justify-content: stretch;
    }
    
    .tikz-app .caption-btn {
        flex: 1;
        justify-content: center;
    }
}

@media (width >= 768px) {
    .tikz-app .caption-textarea {
        min-height: 180px;
    }
}
```

### 3. JavaScript Logic `static/js/view_svg.js`

**Thêm caption handling:**

```javascript
// ===== CAPTION MANAGEMENT =====

document.addEventListener('DOMContentLoaded', function() {
    // ... existing code ...
    
    initCaptionFeature();
});

function initCaptionFeature() {
    const captionData = getCaptionData();
    if (!captionData) return;
    
    const editBtn = document.getElementById('edit-caption-btn');
    const saveBtn = document.getElementById('save-caption-btn');
    const cancelBtn = document.getElementById('cancel-caption-btn');
    const captionInput = document.getElementById('caption-input');
    const captionDisplay = document.getElementById('caption-display');
    const captionEmpty = document.getElementById('caption-empty');
    const captionEditForm = document.getElementById('caption-edit-form');
    const charCurrent = document.getElementById('caption-char-current');
    const previewContent = document.getElementById('caption-preview-content');
    
    if (!captionData.isOwner) return;
    
    // Edit button click
    if (editBtn) {
        editBtn.addEventListener('click', function() {
            enableCaptionEdit();
        });
    }
    
    // Save button click
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            saveCaptionHandler();
        });
    }
    
    // Cancel button click
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            cancelCaptionEdit();
        });
    }
    
    // Character counter
    if (captionInput && charCurrent) {
        captionInput.addEventListener('input', function() {
            const length = this.value.length;
            charCurrent.textContent = length;
            
            // Update preview
            if (previewContent) {
                previewContent.textContent = this.value || '(Preview sẽ hiển thị ở đây)';
                if (window.MathJax) {
                    MathJax.typesetPromise([previewContent]).catch(err => {
                        console.error('MathJax typeset error:', err);
                    });
                }
            }
        });
    }
}

function getCaptionData() {
    const dataEl = document.getElementById('caption-data-json');
    if (!dataEl) return null;
    try {
        return JSON.parse(dataEl.textContent);
    } catch (e) {
        console.error('Error parsing caption data:', e);
        return null;
    }
}

function enableCaptionEdit() {
    const captionDisplay = document.getElementById('caption-display');
    const captionEmpty = document.getElementById('caption-empty');
    const captionEditForm = document.getElementById('caption-edit-form');
    const editBtn = document.getElementById('edit-caption-btn');
    
    if (captionDisplay) captionDisplay.style.display = 'none';
    if (captionEmpty) captionEmpty.style.display = 'none';
    if (captionEditForm) captionEditForm.style.display = 'block';
    if (editBtn) editBtn.style.display = 'none';
    
    // Focus on textarea
    const captionInput = document.getElementById('caption-input');
    if (captionInput) {
        captionInput.focus();
    }
}

function cancelCaptionEdit() {
    const captionData = getCaptionData();
    const captionDisplay = document.getElementById('caption-display');
    const captionEmpty = document.getElementById('caption-empty');
    const captionEditForm = document.getElementById('caption-edit-form');
    const editBtn = document.getElementById('edit-caption-btn');
    const captionInput = document.getElementById('caption-input');
    
    // Reset form
    if (captionInput && captionData) {
        captionInput.value = captionData.caption || '';
    }
    
    if (captionEditForm) captionEditForm.style.display = 'none';
    if (editBtn) editBtn.style.display = 'flex';
    
    if (captionData && captionData.caption) {
        if (captionDisplay) captionDisplay.style.display = 'block';
        if (captionEmpty) captionEmpty.style.display = 'none';
    } else {
        if (captionDisplay) captionDisplay.style.display = 'none';
        if (captionEmpty) captionEmpty.style.display = 'block';
    }
    
    hideMessage();
}

async function saveCaptionHandler() {
    const captionData = getCaptionData();
    if (!captionData) return;
    
    const captionInput = document.getElementById('caption-input');
    const saveBtn = document.getElementById('save-caption-btn');
    
    if (!captionInput || !saveBtn) return;
    
    const newCaption = captionInput.value.trim();
    
    // Disable button
    saveBtn.disabled = true;
    saveBtn.textContent = '⏳ Đang lưu...';
    
    try {
        const response = await fetch(`/api/update_caption/${captionData.filename}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ caption: newCaption })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update display
            const captionText = document.querySelector('.caption-text');
            if (captionText) {
                captionText.textContent = newCaption;
                
                // Trigger MathJax rendering
                if (window.MathJax) {
                    MathJax.typesetPromise([captionText]).catch(err => {
                        console.error('MathJax typeset error:', err);
                    });
                }
            }
            
            // Update edit button text
            const editBtn = document.getElementById('edit-caption-btn');
            if (editBtn) {
                const editText = editBtn.querySelector('.edit-text');
                if (editText) {
                    editText.textContent = newCaption ? 'Chỉnh sửa mô tả' : 'Thêm mô tả';
                }
            }
            
            // Update caption data
            captionData.caption = newCaption;
            
            // Hide edit form, show display
            cancelCaptionEdit();
            
            // Show success message
            showMessage(result.message, 'success');
        } else {
            showMessage(result.error || 'Có lỗi xảy ra', 'error');
        }
    } catch (error) {
        console.error('Error saving caption:', error);
        showMessage('Lỗi kết nối. Vui lòng thử lại.', 'error');
    } finally {
        // Re-enable button
        saveBtn.disabled = false;
        saveBtn.innerHTML = '✅ Lưu';
    }
}

function showMessage(text, type = 'success') {
    const messageEl = document.getElementById('caption-message');
    if (!messageEl) return;
    
    messageEl.textContent = text;
    messageEl.className = 'caption-message ' + type;
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        hideMessage();
    }, 5000);
}

function hideMessage() {
    const messageEl = document.getElementById('caption-message');
    if (messageEl) {
        messageEl.style.display = 'none';
        messageEl.className = 'caption-message';
    }
}
```

---

## 🔒 Security Considerations

### 1. Input Sanitization
- Remove `<script>` tags
- Remove event handlers (`onclick`, `onload`, etc.)
- Keep LaTeX math delimiters
- Limit length to 5000 characters

### 2. Authorization
- Only owner can edit caption
- Verify `user_id` matches `current_user.id`
- Return 403 Forbidden for unauthorized access

### 3. XSS Protection
- Sanitize HTML before storing
- Use `|safe` filter carefully in Jinja2
- Configure MathJax to skip HTML tags

---

## 🧪 Testing Checklist

### Database
- [ ] Migration script chạy thành công
- [ ] Cột `caption` xuất hiện trong bảng `svg_image`
- [ ] Charset là `utf8mb4_unicode_ci`
- [ ] Default value là `NULL`

### Backend API
- [ ] `/view_svg/<filename>` trả về caption
- [ ] `/api/update_caption/<filename>` hoạt động với owner
- [ ] Non-owner nhận 403 error
- [ ] Validation length hoạt động
- [ ] Sanitization loại bỏ dangerous tags

### Frontend
- [ ] MathJax load và render công thức
- [ ] Edit button chỉ hiện với owner
- [ ] Form edit show/hide đúng
- [ ] Character counter hoạt động
- [ ] Preview real-time với MathJax
- [ ] Save thành công cập nhật UI
- [ ] Cancel khôi phục giá trị cũ

### Responsive
- [ ] Mobile (<576px): Layout stack vertical
- [ ] Tablet (576px-768px): Buttons responsive
- [ ] Desktop (>768px): Full layout

### MathJax
- [ ] Inline math `$x^2$` render
- [ ] Display math `$$\int$$` render
- [ ] Greek letters `$\alpha, \beta$` render
- [ ] Complex formulas render correctly

---

## 📊 Future Enhancements (Comments Feature)

### Database Schema for Comments

```sql
CREATE TABLE svg_image_comment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    svg_image_id INT NOT NULL,
    user_id INT NOT NULL,
    comment_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    parent_comment_id INT DEFAULT NULL,  -- For nested replies
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (svg_image_id) REFERENCES svg_image(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES svg_image_comment(id) ON DELETE CASCADE,
    INDEX idx_svg_image_id (svg_image_id),
    INDEX idx_user_id (user_id),
    INDEX idx_parent_comment_id (parent_comment_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### UI Placement
Caption section sẽ ở trên, comments section ở dưới:

```
┌─────────────────────────────┐
│   SVG Image Display         │
└─────────────────────────────┘
┌─────────────────────────────┐
│   Image Caption Section     │  ← Hiện tại
└─────────────────────────────┘
┌─────────────────────────────┐
│   Comments Section          │  ← Tương lai
│   - Add comment form        │
│   - List of comments        │
│   - Nested replies          │
│   - Like/Reply buttons      │
└─────────────────────────────┘
```

---

## 📝 Migration Checklist

### Pre-deployment
1. [ ] Backup database
2. [ ] Test migration script trên local
3. [ ] Review code changes
4. [ ] Test API endpoints
5. [ ] Test frontend functionality

### Deployment
1. [ ] Chạy migration: `add_image_caption_column.sql`
2. [ ] Deploy backend changes (app.py)
3. [ ] Deploy frontend changes (HTML, CSS, JS)
4. [ ] Clear cache nếu cần
5. [ ] Verify MathJax CDN loads

### Post-deployment
1. [ ] Test tạo caption mới
2. [ ] Test edit caption existing
3. [ ] Test MathJax rendering
4. [ ] Test responsive design
5. [ ] Monitor error logs
6. [ ] Collect user feedback

---

## 📚 Documentation Links

- **Database Schema**: `DATABASE_DOCUMENTATION.md`
- **Migration Script**: `add_image_caption_column.sql`
- **View SVG Page Doc**: `VIEW_SVG_PAGE.md`
- **MathJax Documentation**: https://docs.mathjax.org/

---

*Hướng dẫn này được tạo: October 20, 2025*
*Branch: `feature/base-template-migration`*

