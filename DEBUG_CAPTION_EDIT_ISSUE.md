# Debug Caption Edit Button Issue

## Vấn đề
Khi truy cập lại trang có caption, click "Chỉnh sửa mô tả" không mở form edit.

## Changes Made

### 1. Template Fix (`view_svg.html`)
**Problem:** Template check `{% if caption %}` không đủ, cần check `.strip()`

**Fix:**
```jinja
<!-- Before -->
{% if not caption %}style="display: none;"{% endif %}

<!-- After -->
{% if not caption or not caption.strip() %}style="display: none;"{% endif %}
```

### 2. JavaScript MathJax Timing (`view_svg.js`)
**Problem:** MathJax có thể chưa load khi script chạy

**Fix:**
- Thêm check `window.MathJax.typesetPromise` exists
- Thêm fallback với `setTimeout(500ms)`
- Render cho cả owner và non-owner

### 3. Debug Logging
Added console logs to trace the issue:
- `enableCaptionEdit called`
- `Edit button found, adding click listener`
- `Edit button clicked!`
- Element existence checks

## Testing Steps

### Step 1: Clear Browser Cache
```
Chrome: Ctrl+Shift+Delete → Clear cached images and files
Firefox: Ctrl+Shift+Delete → Cached Web Content
Safari: Cmd+Option+E
```

### Step 2: Hard Refresh
```
Windows: Ctrl+F5 or Ctrl+Shift+R
Mac: Cmd+Shift+R
```

### Step 3: Open Developer Console
```
Windows: F12 or Ctrl+Shift+I
Mac: Cmd+Option+I
```

### Step 4: Navigate to Image with Caption
```
http://localhost:5173/view_svg/115852900894156127858_060414240825.svg
```

### Step 5: Check Console Logs

Expected logs when page loads:
```
Edit button found, adding click listener
```

Expected logs when clicking "Chỉnh sửa mô tả":
```
Edit button clicked! Event {…}
enableCaptionEdit called
Elements found: {captionDisplay: true, captionEmpty: true, captionEditForm: true, editBtn: true}
```

### Step 6: What to Look For

#### ✅ Good Scenario:
```
1. Page loads
2. Console shows: "Edit button found, adding click listener"
3. Click edit button
4. Console shows: "Edit button clicked!"
5. Console shows: "enableCaptionEdit called"
6. Form appears
```

#### ❌ Bad Scenario 1 - Button Not Found:
```
1. Page loads
2. Console shows: "Edit button NOT found!"
→ Problem: Template condition hiding button
→ Check: Is user the owner? Is user logged in?
```

#### ❌ Bad Scenario 2 - Click Not Working:
```
1. Page loads
2. Console shows: "Edit button found, adding click listener"
3. Click edit button
4. Nothing happens, no console log
→ Problem: Event listener not attached
→ Check: JavaScript errors in console?
```

#### ❌ Bad Scenario 3 - Elements Not Found:
```
1. Click works
2. Console shows: "Elements found: {captionDisplay: false, ...}"
→ Problem: HTML elements missing or wrong IDs
→ Check: View page source, verify element IDs
```

## Common Issues & Solutions

### Issue 1: "Edit button NOT found!"
**Cause:** Template condition wrong or user not owner

**Check:**
```javascript
// In console, run:
document.getElementById('edit-caption-btn')
// Should return: <button id="edit-caption-btn">...</button>
// If null, button not in DOM
```

**Solution:**
- Verify you're logged in as the image owner
- Check template condition: `{% if user_email and user_id and current_user.is_authenticated and user_id == current_user.id %}`

### Issue 2: Click does nothing
**Cause:** JavaScript error preventing event listener attachment

**Check:**
```javascript
// In console before page load, watch for errors:
// Look for red error messages
```

**Solution:**
- Check for JavaScript syntax errors
- Verify `view_svg.js` loaded: `curl http://localhost:5173/static/js/view_svg.js`

### Issue 3: Form appears but empty
**Cause:** `captionInput.value` not set

**Check:**
```javascript
// In console after clicking edit:
document.getElementById('caption-input').value
// Should show current caption
```

**Solution:**
- Verify `captionData.caption` has value
- Check JSON data injection in HTML

## Files Modified

1. ✅ `templates/view_svg.html` - Template logic fix
2. ✅ `static/js/view_svg.js` - MathJax timing + debug logs

## Verification Checklist

- [ ] Clear browser cache
- [ ] Hard refresh page (Ctrl+Shift+R)
- [ ] Open Developer Console (F12)
- [ ] Navigate to image with caption
- [ ] Check console for "Edit button found" message
- [ ] Click "Chỉnh sửa mô tả"
- [ ] Check console for "Edit button clicked!" message
- [ ] Verify form appears
- [ ] Verify form has caption text pre-filled
- [ ] Edit caption
- [ ] Click "Lưu"
- [ ] Verify caption updates without refresh

## If Still Not Working

### Debug Script
Run this in browser console:
```javascript
// Check all elements
console.log('=== Caption Debug Info ===');
console.log('Edit button:', document.getElementById('edit-caption-btn'));
console.log('Caption display:', document.getElementById('caption-display'));
console.log('Caption empty:', document.getElementById('caption-empty'));
console.log('Caption form:', document.getElementById('caption-edit-form'));
console.log('Caption input:', document.getElementById('caption-input'));

// Check data
const dataEl = document.getElementById('caption-data-json');
if (dataEl) {
  console.log('Caption data:', JSON.parse(dataEl.textContent));
} else {
  console.log('Caption data JSON not found!');
}

// Check display state
const display = document.getElementById('caption-display');
if (display) {
  console.log('Caption display style:', display.style.display);
  console.log('Caption text:', display.querySelector('.caption-text').textContent);
}
```

### Manual Test
```javascript
// Force open edit form manually:
document.getElementById('caption-display').style.display = 'none';
document.getElementById('caption-empty').style.display = 'none';
document.getElementById('caption-edit-form').style.display = 'block';
document.getElementById('edit-caption-btn').style.display = 'none';
document.getElementById('caption-input').focus();
```

If manual test works, problem is in event listener attachment.

## Report Issue

If still not working, provide:
1. Console logs (copy/paste)
2. Network tab (check if JS loaded)
3. Elements tab (check HTML structure)
4. User status (logged in? owner?)
5. Browser & version

---

*Debug guide created: October 20, 2025*
*Status: Testing in progress*

