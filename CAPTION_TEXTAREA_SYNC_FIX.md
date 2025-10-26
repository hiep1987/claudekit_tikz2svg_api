# Caption Textarea Sync Bug Fix

**Date:** 2025-10-21  
**Component:** View SVG Page - Caption Edit Feature  
**Issue:** Textarea không cập nhật sau khi lưu caption mới  
**Status:** ✅ Fixed

---

## 📋 Vấn đề

### User Flow gây lỗi:

1. Trang có caption ban đầu: **"123"**
2. User bấm "Chỉnh sửa mô tả" → textarea hiển thị "123" ✅
3. User sửa thành **"1234"** → bấm "Lưu" ✅
4. Caption hiển thị **"1234"** ✅
5. User bấm "Chỉnh sửa mô tả" lại → textarea vẫn hiển thị **"123"** ❌
6. User bấm "Hủy" → caption hiển thị lại **"1234"** ✅

### Hành vi mong muốn:

Ở bước 5, textarea phải hiển thị **"1234"** (giá trị mới sau khi lưu).

---

## 🔍 Root Cause Analysis

### 1. Data Flow trong Caption Feature

```
HTML Template
    ↓
<script id="caption-data-json" type="application/json">
{
    "filename": "...",
    "caption": "123",  ← Initial value from backend
    "isOwner": true
}
</script>
    ↓
JavaScript: getCaptionData()
    ↓
Parse JSON → Return object
    ↓
enableCaptionEdit() → Read caption value
```

### 2. Vấn đề #1: `enableCaptionEdit()` không đọc từ `captionData`

**Code cũ:**
```javascript
function enableCaptionEdit() {
  const captionInput = document.getElementById('caption-input');
  if (captionInput) {
    captionInput.focus();  // ❌ Không set value
    
    // Preview uses textarea's existing value
    const text = captionInput.value || '(Preview sẽ hiển thị ở đây)';
    // ...
  }
}
```

**Vấn đề:** Textarea giữ nguyên value từ HTML ban đầu ("123"), không được cập nhật từ JavaScript.

### 3. Vấn đề #2: `saveCaptionHandler()` chỉ update local variable

**Code cũ:**
```javascript
async function saveCaptionHandler() {
  // ...
  if (result.success) {
    // Update caption data first
    captionData.caption = newCaption;  // ❌ Only local variable
    // ...
  }
}
```

**Vấn đề:** 
- `captionData` là **local variable** được return từ `getCaptionData()`
- Mỗi lần gọi `getCaptionData()` sẽ **parse lại JSON từ DOM**
- Update local variable **không ảnh hưởng** đến lần parse tiếp theo
- Khi `enableCaptionEdit()` được gọi lại → `getCaptionData()` vẫn trả về giá trị cũ từ DOM

### Data Flow sau khi lưu (cũ):

```
User saves "1234"
    ↓
captionData.caption = "1234"  (local variable only)
    ↓
DOM element <script id="caption-data-json"> vẫn chứa "123"  ❌
    ↓
User clicks Edit again
    ↓
enableCaptionEdit() → getCaptionData() → Parse DOM
    ↓
Return { caption: "123" }  ❌
    ↓
Textarea shows "123"  ❌
```

---

## ✅ Giải pháp

### Fix #1: Update textarea value trong `enableCaptionEdit()`

**File:** `static/js/view_svg.js`

**Before:**
```javascript
function enableCaptionEdit() {
  // ...
  const captionInput = document.getElementById('caption-input');
  if (captionInput) {
    captionInput.focus();  // ❌ Missing value update
    
    const text = captionInput.value || '(Preview sẽ hiển thị ở đây)';
    // ...
  }
}
```

**After:**
```javascript
function enableCaptionEdit() {
  const captionData = getCaptionData();  // ✅ Get latest data
  // ...
  const captionInput = document.getElementById('caption-input');
  if (captionInput) {
    // ✅ Update textarea value from current caption data
    captionInput.value = captionData.caption || '';
    captionInput.focus();
    
    const text = captionInput.value || '(Preview sẽ hiển thị ở đây)';
    // ...
  }
}
```

### Fix #2: Update DOM element sau khi lưu

**File:** `static/js/view_svg.js`

**Before:**
```javascript
if (result.success) {
  // Update caption data first
  captionData.caption = newCaption;  // ❌ Only local
  
  // Update display elements
  // ...
}
```

**After:**
```javascript
if (result.success) {
  // ✅ Update caption data in DOM (so next getCaptionData() returns updated value)
  const captionDataElement = document.getElementById('caption-data-json');
  if (captionDataElement) {
    try {
      const data = JSON.parse(captionDataElement.textContent);
      data.caption = newCaption;
      captionDataElement.textContent = JSON.stringify(data);
    } catch (e) {
      console.error('Error updating caption data:', e);
    }
  }
  
  // Update local reference
  captionData.caption = newCaption;
  
  // Update display elements
  // ...
}
```

### Data Flow sau khi lưu (mới):

```
User saves "1234"
    ↓
Update DOM: <script id="caption-data-json"> ✅
    {
        "filename": "...",
        "caption": "1234",  ← Updated
        "isOwner": true
    }
    ↓
Update local: captionData.caption = "1234" ✅
    ↓
User clicks Edit again
    ↓
enableCaptionEdit() → getCaptionData() → Parse DOM
    ↓
Return { caption: "1234" } ✅
    ↓
captionInput.value = "1234" ✅
    ↓
Textarea shows "1234" ✅
```

---

## 📊 Testing Checklist

### Manual Testing:

- [x] **Initial load**: Caption "123" hiển thị đúng
- [x] **First edit**: Click "Chỉnh sửa" → textarea = "123" ✅
- [x] **Save**: Sửa thành "1234" → Save → hiển thị "1234" ✅
- [x] **Second edit**: Click "Chỉnh sửa" → textarea = "1234" ✅ (FIXED)
- [x] **Cancel**: Click "Hủy" → hiển thị "1234" ✅
- [x] **Third edit**: Click "Chỉnh sửa" → textarea = "1234" ✅
- [x] **Multiple saves**: Sửa nhiều lần liên tiếp → always shows latest value ✅

### Edge Cases:

- [x] Empty caption → Save → Edit → textarea empty ✅
- [x] Multiline caption → Save → Edit → textarea preserves line breaks ✅
- [x] MathJax formula → Save → Edit → textarea preserves LaTeX ✅
- [x] Very long caption → Save → Edit → textarea scrollable ✅

---

## 🎓 Bài học

### 1. JavaScript Object Reference vs Value

```javascript
// ❌ WRONG: Update local object
const data = getCaptionData();  // Returns NEW object each time
data.caption = "new value";     // Only affects local copy

// ✅ CORRECT: Update source data
const element = document.getElementById('data-json');
const data = JSON.parse(element.textContent);
data.caption = "new value";
element.textContent = JSON.stringify(data);  // Persist to DOM
```

### 2. DOM as Single Source of Truth

Khi data được inject từ backend vào DOM:
```html
<script id="caption-data-json" type="application/json">
{ "caption": "{{ caption|tojson|safe }}" }
</script>
```

JavaScript nên treat DOM element này là **single source of truth**:
- ✅ **Read**: Parse JSON từ DOM
- ✅ **Write**: Update JSON trong DOM
- ❌ **DON'T**: Rely on local JavaScript variables across function calls

### 3. Form Element State Management

Khi working with form elements (`<input>`, `<textarea>`):
- **Initial render**: HTML attribute `value="..."` set từ backend
- **After user edit**: Element's `.value` property changes (không ảnh hưởng HTML attribute)
- **After save**: Phải **explicitly update** `.value` property nếu muốn reset/change

```javascript
// ❌ WRONG: Assume textarea auto-updates
<textarea>{{ caption }}</textarea>
// User edits → saves → textarea still shows old value

// ✅ CORRECT: Explicitly update programmatically
const textarea = document.getElementById('caption-input');
textarea.value = newCaption;  // Force update
```

---

## 📁 Files Modified

1. **`static/js/view_svg.js`**
   - Line 438: Added `const captionData = getCaptionData();` in `enableCaptionEdit()`
   - Line 460: Added `captionInput.value = captionData.caption || '';`
   - Lines 544-554: Added DOM update logic in `saveCaptionHandler()`

---

## 🔗 Related Issues

- **Original Feature**: `IMAGE_CAPTION_FEATURE_GUIDE.md`
- **Previous Fix**: Caption display/edit mode switching
- **Related**: Line break preservation in preview (`white-space: pre-wrap`)

---

## ✅ Summary

| Issue | Before | After |
|-------|--------|-------|
| Textarea value after save | Shows old value ❌ | Shows new value ✅ |
| Data persistence | Local variable only ❌ | DOM element updated ✅ |
| Multiple edits | Inconsistent ❌ | Always synced ✅ |

**Fix ensures:**
- ✅ Textarea always shows latest saved caption
- ✅ Data persists correctly between edit sessions
- ✅ No need for page refresh
- ✅ Consistent state management

---

**Last Updated:** 2025-10-21  
**Status:** ✅ Complete  
**Testing:** Manual testing passed all scenarios

