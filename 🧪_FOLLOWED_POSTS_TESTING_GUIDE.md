# 🧪 TESTING GUIDE: Profile Followed Posts Optimization

**Date:** October 31, 2025  
**Feature:** Pagination + Lazy Loading for Followed Posts Page

---

## 📋 Pre-Test Setup

### 1. Ensure Development Environment is Ready

```bash
cd /Users/hieplequoc/web/work/tikz2svg_api
source venv/bin/activate
python app.py
```

**Expected Output:**
```
✅ Pagination configured: 50 items per page
🔧 Rate Limiting: DEVELOPMENT mode
⚡ Limits: {'api_likes_preview': '100 per minute', ...}
```

### 2. Access the Followed Posts Page

**URL Pattern:** `http://localhost:5173/profile/<user_id>/followed-posts`

**Requirements:**
- You must be logged in
- You must be viewing YOUR OWN profile (owner access only)
- You must be following at least 1 user who has posted content

---

## 🎯 Test Case 1: Pagination UI Visibility

### Scenario A: Less than 50 Followed Posts

**Steps:**
1. Ensure you have < 50 followed posts
2. Navigate to followed posts page
3. Scroll to bottom of page

**Expected Results:**
- ✅ No pagination UI appears
- ✅ Page shows text like "Hiển thị X / X bài đăng" (where X < 50)
- ✅ All posts visible on single page

---

### Scenario B: More than 50 Followed Posts

**Setup:**
- Ensure you have > 50 followed posts (follow more users if needed)

**Steps:**
1. Navigate to followed posts page
2. Scroll to bottom of page
3. Observe pagination UI

**Expected Results:**
- ✅ Pagination UI appears at bottom
- ✅ Shows "Trang 1 / N" where N = total pages
- ✅ Shows "Hiển thị 50 / X bài đăng" where X = total posts
- ✅ Previous button is disabled (grayed out)
- ✅ Next button is active and clickable
- ✅ Page numbers display (e.g., "1 2 3 ... 10")

---

## 🎯 Test Case 2: Pagination Navigation

### Test 2.1: Next/Previous Buttons

**Steps:**
1. On page 1, click "Sau →" button
2. Verify page 2 loads
3. Click "← Trước" button
4. Verify page 1 loads again

**Expected Results:**
- ✅ URL updates to `?page=2` when clicking Next
- ✅ URL updates to `?page=1` when clicking Previous
- ✅ Page content changes (different posts shown)
- ✅ Pagination info updates correctly
- ✅ Previous button is disabled on page 1
- ✅ Next button is disabled on last page

---

### Test 2.2: Direct Page Number Clicks

**Steps:**
1. Click on page number "3"
2. Verify page 3 loads
3. Click on page number "5"
4. Verify page 5 loads

**Expected Results:**
- ✅ URL updates to `?page=3`, then `?page=5`
- ✅ Correct page content loads
- ✅ Active page number is highlighted (blue background)
- ✅ Other page numbers are white/gray

---

### Test 2.3: Ellipsis Page Numbers

**Setup:** Requires > 100 followed posts (10+ pages)

**Steps:**
1. Navigate to followed posts page
2. Observe page numbers
3. Click on different pages and observe how ellipsis changes

**Expected Behavior:**
```
Page 1:   1 2 3 4 5 6 7 8 9 10 ... 15
Page 5:   1 2 3 4 5 6 7 8 9 10 ... 15
Page 8:   1 ... 5 6 7 8 9 10 11 12 13 ... 15
Page 15:  1 ... 7 8 9 10 11 12 13 14 15
```

**Expected Results:**
- ✅ Ellipsis (...) appears when pages are skipped
- ✅ First page always visible
- ✅ Last page always visible
- ✅ Current page and neighbors visible (±4 pages)
- ✅ Maximum 10 page numbers shown at once

---

## 🎯 Test Case 3: Lazy Loading - Images

### Test 3.1: Initial Page Load

**Steps:**
1. Open followed posts page
2. **Before scrolling**, open browser DevTools (F12)
3. Go to Network tab, filter by "Images"
4. Clear network log
5. Reload page
6. Count how many SVG images load immediately

**Expected Results:**
- ✅ Only ~10-15 images load initially (those visible in viewport)
- ✅ Not all 50 images load at once
- ✅ Network waterfall shows staggered image loading

**Visual Indicators:**
- ✅ Skeleton shimmer animation appears on cards below the fold
- ✅ Images fade in smoothly as they load

---

### Test 3.2: Scroll Lazy Loading

**Steps:**
1. Scroll down slowly through the page
2. Observe image loading behavior in Network tab
3. Continue scrolling to bottom

**Expected Results:**
- ✅ Images load as they enter viewport (before they're fully visible)
- ✅ Load trigger happens ~50px before card enters viewport
- ✅ Smooth loading without janky scrolling
- ✅ All 50 images eventually load after scrolling to bottom

**Performance Check:**
```javascript
// Console command to check lazy loading
document.querySelectorAll('.file-img-container img').forEach((img, i) => {
  console.log(`Image ${i+1}: ${img.complete ? '✅ Loaded' : '⏳ Loading'}`);
});
```

---

## 🎯 Test Case 4: Lazy Loading - Likes Preview

### Test 4.1: Initial API Calls

**Steps:**
1. Open followed posts page
2. Open browser DevTools → Network tab
3. Filter by "XHR" or "Fetch"
4. Clear network log
5. Reload page
6. Count API calls to `/api/svg/*/likes/preview`

**Expected Results:**
- ✅ Only ~10-12 likes preview API calls initially
- ✅ NOT 50 API calls at once (would hit rate limit)
- ✅ Calls correspond to visible cards only

**Console Output:**
```
🔭 Observing 50 file cards for lazy loading
👁️ Loading likes preview for SVG 123 (visible)
👁️ Loading likes preview for SVG 124 (visible)
... (only ~10-12 calls initially)
```

---

### Test 4.2: Scroll Loading Likes Preview

**Steps:**
1. Scroll down slowly
2. Watch Network tab for new API calls
3. Watch console for debug messages

**Expected Results:**
- ✅ New `/api/svg/*/likes/preview` calls as cards enter viewport
- ✅ Console shows "👁️ Loading likes preview for SVG X (visible)"
- ✅ Each card loads likes preview only ONCE (no duplicate calls)
- ✅ Smooth loading without blocking scroll

---

### Test 4.3: Rate Limit Protection

**Steps:**
1. Open followed posts page
2. Quickly scroll to bottom (all cards visible)
3. Reload page 3 times rapidly
4. Check console for errors

**Expected Results (Development Mode):**
- ✅ No 429 (TOO MANY REQUESTS) errors
- ✅ All likes previews load successfully
- ✅ Rate limit: 100 requests/minute (should be enough)

**If 429 Errors Occur:**
- ⚠️ This should NOT happen with lazy loading
- 🐛 Debug: Check if Intersection Observer is working
- 🔧 Verify rate limits in `app.py`: `RATE_LIMITS['api_likes_preview']`

---

## 🎯 Test Case 5: Browser Compatibility

### Test on Multiple Browsers:

1. **Chrome/Edge (Chromium):**
   - ✅ Pagination works
   - ✅ Lazy loading works
   - ✅ Intersection Observer works

2. **Firefox:**
   - ✅ Pagination works
   - ✅ Lazy loading works
   - ✅ Intersection Observer works

3. **Safari:**
   - ✅ Pagination works
   - ✅ Lazy loading works
   - ✅ Intersection Observer works
   - ⚠️ Check for any webkit-specific issues

---

## 🎯 Test Case 6: Mobile Responsive

### Test on Mobile Devices or Responsive Mode:

**Steps:**
1. Open DevTools → Toggle device toolbar (Ctrl+Shift+M)
2. Select mobile device (iPhone 12, Pixel 5, etc.)
3. Test pagination and lazy loading

**Expected Results:**
- ✅ Pagination buttons are larger and easier to tap
- ✅ Page numbers don't overflow (gap reduces to 0.25rem)
- ✅ Pagination info wraps nicely on narrow screens
- ✅ Lazy loading still works on mobile
- ✅ Smooth scrolling and loading

**CSS Media Query (600px breakpoint):**
```css
@media (max-width: 600px) {
    .tikz-app .pagination-btn {
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
        min-width: 36px;
    }
}
```

---

## 🎯 Test Case 7: Edge Cases

### Edge Case 1: Exactly 50 Followed Posts

**Expected:**
- ✅ No pagination UI (exactly 1 page)
- ✅ Shows "Hiển thị 50 / 50 bài đăng"

---

### Edge Case 2: 51 Followed Posts

**Expected:**
- ✅ Pagination UI appears
- ✅ Shows "Trang 1 / 2"
- ✅ Page 2 has only 1 post

---

### Edge Case 3: 0 Followed Posts

**Expected:**
- ✅ Shows "Chưa có bài đăng nào" message
- ✅ No pagination UI
- ✅ No errors in console

---

### Edge Case 4: Direct URL Access

**Steps:**
1. Navigate to `http://localhost:5173/profile/<user_id>/followed-posts?page=999`
2. Observe behavior

**Expected:**
- ✅ Should redirect to last valid page OR show empty page
- ✅ No errors in console
- ✅ Pagination info shows correct page

---

## 🎯 Test Case 8: Performance Metrics

### Measure Page Load Performance:

**Steps:**
1. Open DevTools → Performance tab
2. Start recording
3. Load followed posts page
4. Stop recording after page fully loads

**Expected Metrics:**
- ✅ First Contentful Paint (FCP): < 1s
- ✅ Largest Contentful Paint (LCP): < 2.5s
- ✅ Time to Interactive (TTI): < 3s
- ✅ Total Blocking Time (TBT): < 300ms

**Network Performance:**
```
Initial Load:
- ~10-12 likes preview API calls (not 50)
- ~10-15 SVG image loads (not 50)
- Total initial requests: ~30-40 (manageable)

After Scroll:
- Additional lazy loads as needed
- No rate limit errors
```

---

## 🎯 Test Case 9: Console Debugging

### Useful Console Commands:

**Check Intersection Observer:**
```javascript
// Should log cards being observed
console.log('File cards:', document.querySelectorAll('.file-card[data-file-id]').length);
```

**Check Loaded Likes Previews:**
```javascript
// Should show only visible cards initially
document.querySelectorAll('.likes-preview-text[data-svg-id]').forEach((el, i) => {
  const loaded = el.querySelector('.likes-preview-names') !== null;
  console.log(`Card ${i+1}: ${loaded ? '✅ Loaded' : '⏳ Not loaded'}`);
});
```

**Check Image Loading:**
```javascript
// Should show loading attribute on images
document.querySelectorAll('.file-img-container img').forEach((img, i) => {
  console.log(`Image ${i+1}: loading="${img.loading}" complete=${img.complete}`);
});
```

---

## ✅ Success Criteria

The optimization is successful if:

1. **Pagination:**
   - ✅ Works correctly for > 50 posts
   - ✅ Hidden for ≤ 50 posts
   - ✅ Navigation is smooth and intuitive
   - ✅ URL parameters work correctly

2. **Lazy Loading - Images:**
   - ✅ Only visible images load initially
   - ✅ Images load smoothly as you scroll
   - ✅ Skeleton animation appears
   - ✅ All 50 images eventually load

3. **Lazy Loading - Likes Preview:**
   - ✅ Only ~10-12 API calls initially (not 50)
   - ✅ Additional calls as you scroll
   - ✅ No duplicate calls per card
   - ✅ No rate limit errors

4. **Performance:**
   - ✅ Page loads in < 2 seconds
   - ✅ Smooth scrolling (60fps)
   - ✅ No memory leaks
   - ✅ Works on mobile

5. **Consistency:**
   - ✅ Same UX as index page
   - ✅ Same styling as index page
   - ✅ Same rate limits as index page

---

## 🐛 Troubleshooting

### Issue: Pagination UI not appearing

**Check:**
- Total posts count (must be > 50)
- `total_pages` variable in template
- CSS loaded correctly

**Debug:**
```jinja2
<!-- Add to template temporarily -->
<p>Debug: Total posts = {{ total_items }}, Total pages = {{ total_pages }}</p>
```

---

### Issue: Rate limit 429 errors

**Check:**
- Rate limit configuration in `app.py`
- Number of initial API calls (should be ~10-12)
- Intersection Observer working correctly

**Debug:**
```javascript
// Console: Check how many cards are being observed
console.log('Observing:', document.querySelectorAll('.file-card[data-file-id]').length);
```

---

### Issue: Lazy loading not working

**Check:**
- `file_card.js` loaded correctly
- Browser supports Intersection Observer (all modern browsers do)
- Console for JavaScript errors

**Debug:**
```javascript
// Console: Check if IntersectionObserver exists
console.log('IntersectionObserver:', typeof IntersectionObserver);
```

---

## 📊 Testing Report Template

```markdown
## Testing Report: Followed Posts Optimization

**Date:** [Date]
**Tester:** [Name]
**Browser:** [Chrome/Firefox/Safari] [Version]

### Test Results:

- [ ] Pagination UI displays correctly (> 50 posts)
- [ ] Pagination navigation works (Next/Previous/Numbers)
- [ ] Lazy loading - Images (~10-15 initial loads)
- [ ] Lazy loading - Likes preview (~10-12 initial API calls)
- [ ] No rate limit errors (429)
- [ ] Mobile responsive
- [ ] Performance acceptable (< 2s load)
- [ ] Consistent with index page

### Issues Found:
[List any issues here]

### Performance Metrics:
- FCP: [X]ms
- LCP: [X]ms
- Initial API calls: [X]
- Initial image loads: [X]

### Conclusion:
[Pass/Fail] - [Additional notes]
```

---

**Status:** 🧪 READY FOR TESTING

**Next Steps:**
1. Follow this guide to test the feature
2. Report any issues found
3. Verify performance improvements
4. Get user feedback

---

**Good luck testing! 🚀**

