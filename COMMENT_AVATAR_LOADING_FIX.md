# ✅ Comment Avatar Loading Fix

## 🐛 Vấn đề

Comments từ API không hiển thị avatar, chỉ show fallback letter:

```html
<!-- Comment form có avatar -->
<img src="/static/avatars/avatar_d88cda2132b548b1b3adda08760fb785.png" ...>

<!-- Nhưng rendered comments có src rỗng -->
<img src="" alt="" class="comment-avatar" style="display: none;">
<div class="comment-user-avatar-fallback" style="display: flex;">Q</div>
```

---

## 🔍 Root Cause Analysis

### Backend (comments_routes.py):

API trả về field `avatar` từ database:

```python
cursor.execute("""
    SELECT 
        ...
        u.avatar,     # ← Field này có thể NULL hoặc empty string
        ...
    FROM svg_comments c
    JOIN user u ON c.user_id = u.id
""")
```

**Giá trị có thể:**
- `NULL` (Python converts to `None`)
- `''` (empty string)
- `'None'` (string "None" - từ database legacy)
- `'avatar_xxx.png'` (just filename)
- `'/static/avatars/avatar_xxx.png'` (full path)

### Frontend (comments.js) - BUG:

**Logic cũ (quá strict):**

```javascript
if (comment.avatar && comment.avatar.includes('/avatars/')) {
    // ❌ CHỈ pass nếu có '/avatars/' trong string
    avatarImg.src = comment.avatar;
    // ...
}
```

**Vấn đề:**
1. ❌ `comment.avatar = ''` → truthy nhưng `.includes('/avatars/')` = false → dùng fallback
2. ❌ `comment.avatar = 'avatar_xxx.png'` → không có '/avatars/' → dùng fallback  
3. ❌ `comment.avatar = 'None'` → không có '/avatars/' → dùng fallback
4. ✅ `comment.avatar = '/static/avatars/...'` → OK (nhưng hiếm khi có)

---

## 🔧 Fix

### **Trước:**

```javascript
if (comment.avatar && comment.avatar.includes('/avatars/')) {
    avatarImg.src = comment.avatar;
    // ...
} else {
    // Fallback
}
```

### **Sau:**

```javascript
// Check if avatar exists and is not empty
const hasValidAvatar = comment.avatar && 
                       comment.avatar.trim() !== '' && 
                       comment.avatar !== 'None';

if (hasValidAvatar) {
    // Use avatar image - handle both full path and filename
    const avatarPath = comment.avatar.startsWith('/static/') 
        ? comment.avatar 
        : `/static/avatars/${comment.avatar}`;
    
    avatarImg.src = avatarPath;
    avatarImg.alt = comment.username || 'User';
    avatarImg.style.display = 'block';
    avatarFallback.style.display = 'none';
} else {
    // Use fallback with first letter
    avatarImg.style.display = 'none';
    avatarFallback.textContent = (comment.username || comment.email || 'U')[0].toUpperCase();
    avatarFallback.style.display = 'flex';
}
```

---

## ✅ Improvements

| Case | Old Behavior | New Behavior |
|------|-------------|--------------|
| `null` | ❌ Fallback | ✅ Fallback |
| `''` | ❌ Fallback | ✅ Fallback |
| `'None'` | ❌ Fallback | ✅ Fallback |
| `'avatar_xxx.png'` | ❌ Fallback | ✅ **Show image!** |
| `'/static/avatars/avatar_xxx.png'` | ✅ Show image | ✅ Show image |

---

## 📊 Validation Checks

New logic validates:

1. **Exists:** `comment.avatar` truthy
2. **Not empty:** `.trim() !== ''`
3. **Not "None":** `!== 'None'`
4. **Path handling:**
   - Has `/static/` → use as-is
   - No `/static/` → prepend `/static/avatars/`

---

## 🎯 Kết quả

**Giờ comments sẽ hiển thị:**

✅ Avatar image nếu user đã upload  
✅ Fallback letter (Q, H) nếu chưa có avatar  
✅ Xử lý đúng cả full path và filename  
✅ Không bị lỗi với `null`, `''`, hoặc `'None'`

---

**Generated:** 2025-10-22  
**Issue:** Comments không hiển thị avatar  
**Root Cause:** Logic kiểm tra avatar quá strict (`includes('/avatars/')`)  
**Fix:** Validate properly và handle cả full path + filename  
**Status:** ✅ Fixed
