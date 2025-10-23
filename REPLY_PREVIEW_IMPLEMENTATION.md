# ✅ Reply Preview Implementation

## 📋 Tóm tắt

Thêm preview (với MathJax) cho reply form, giống như main comment form.

---

## 🎯 Thay đổi

### 1️⃣ HTML - `templates/view_svg.html`

**Thêm preview section vào reply form:**

```html
<div class="comment-reply-form" style="display: none;">
    <textarea class="reply-textarea" placeholder="Viết câu trả lời..." maxlength="5000"></textarea>
    
    <!-- ✅ NEW: Preview section -->
    <div class="comment-preview">
        <h4>Preview (với MathJax):</h4>
        <div class="reply-preview-content">
            Nhập câu trả lời để xem preview...
        </div>
    </div>
    
    <div class="reply-form-actions">
        <button class="comment-btn comment-btn-cancel">Hủy</button>
        <button class="comment-btn comment-btn-submit">Gửi</button>
    </div>
</div>
```

### 2️⃣ JavaScript - `static/js/comments.js`

**Thêm preview functionality:**

```javascript
function handleReplyComment(commentDiv, parentComment) {
    const replyTextarea = replyForm.querySelector('.reply-textarea');
    const replyPreview = replyForm.querySelector('.reply-preview-content');
    
    // ✅ Update reply preview function (debounced)
    const updateReplyPreview = debounce(() => {
        if (!replyPreview) return;
        
        const text = replyTextarea.value.trim();
        
        if (!text) {
            replyPreview.textContent = 'Nhập câu trả lời để xem preview...';
            replyPreview.style.color = '#a0aec0';
            return;
        }
        
        // Escape HTML để tránh XSS
        const escapedText = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
        
        // Convert line breaks to <br>
        const htmlText = escapedText.replace(/\n/g, '<br>');
        
        replyPreview.innerHTML = htmlText;
        replyPreview.style.color = '#1a202c';
        
        // Render MathJax if available
        if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
            MathJax.typesetPromise([replyPreview]).catch((err) => {
                console.warn('MathJax rendering error:', err);
            });
        }
    }, 300);
    
    // ✅ Add preview listener
    replyTextarea.addEventListener('input', updateReplyPreview);
    
    // ✅ Clear preview on cancel
    cancelBtn.onclick = () => {
        replyForm.style.display = 'none';
        replyTextarea.value = '';
        if (replyPreview) {
            replyPreview.textContent = 'Nhập câu trả lời để xem preview...';
            replyPreview.style.color = '#a0aec0';
        }
        replyTextarea.removeEventListener('input', updateReplyPreview);
    };
    
    // ✅ Clear preview on successful submit
    if (result.success) {
        replyTextarea.value = '';
        if (replyPreview) {
            replyPreview.textContent = 'Nhập câu trả lời để xem preview...';
            replyPreview.style.color = '#a0aec0';
        }
        replyTextarea.removeEventListener('input', updateReplyPreview);
    }
}
```

### 3️⃣ CSS - `static/css/comments.css`

**Styling đã có sẵn từ `.comment-preview` và `.comment-preview-content`:**

- Glass morphism background
- MathJax rendering
- Responsive design

---

## ✅ Tính năng

| Feature | Status |
|---------|--------|
| Real-time preview | ✅ |
| MathJax rendering | ✅ |
| XSS protection (HTML escape) | ✅ |
| Line breaks → `<br>` | ✅ |
| Debouncing (300ms) | ✅ |
| Clear on cancel | ✅ |
| Clear on submit | ✅ |
| Event listener cleanup | ✅ |

---

## 🎨 User Experience

**Trước:**
```
[Reply textarea]
[Hủy] [Gửi]
```

**Sau:**
```
[Reply textarea]

Preview (với MathJax):
[Real-time preview với MathJax rendering]

[Hủy] [Gửi]
```

---

## 🔒 Security

1. **XSS Protection:**
   - HTML escape tất cả user input
   - Không eval() code
   
2. **Event Listener Cleanup:**
   - Remove listener khi cancel/submit
   - Tránh memory leaks

3. **Debouncing:**
   - Limit MathJax calls (300ms)
   - Better performance

---

## 📊 Consistency

Reply form giờ **hoàn toàn giống** main comment form:

| Feature | Main Comment | Reply Comment |
|---------|--------------|---------------|
| Preview section | ✅ | ✅ |
| MathJax rendering | ✅ | ✅ |
| XSS protection | ✅ | ✅ |
| Debouncing | ✅ | ✅ |
| Clear on submit | ✅ | ✅ |

---

**Generated:** 2025-10-22  
**Component:** Reply Preview  
**Status:** ✅ Complete
