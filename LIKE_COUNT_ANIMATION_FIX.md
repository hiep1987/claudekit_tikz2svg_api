# Like Count Animation Fix

## 🐛 Vấn đề

Khi user đã like (checkbox checked), cả 2 số count (`.like-count.one` và `.like-count.two`) đều hiển thị cùng lúc và nằm dính liền với icon heart, thay vì chỉ hiển thị 1 số như khi chưa like.

### HTML Structure:
```html
<label class="like">
    <svg class="like-icon">...</svg>
    <span class="like-count one">4</span>  <!-- ❌ Cả 2 đều hiện -->
    <span class="like-count two">4</span>  <!-- ❌ Nằm dính liền -->
</label>
```

### Nguyên nhân:
- `.like-count.two` có `position: absolute` với `right: 10px`
- Không có container relative để anchor
- Design mới (rounded pill) thay đổi layout, cần điều chỉnh positioning

## ✅ Giải pháp

### 1. Thêm Container cho Like Counts

**File: `templates/partials/_file_card.html`**

**Before:**
```html
<label class="like">
    <svg class="like-icon">...</svg>
    <span class="like-count one">{{ file.like_count }}</span>
    <span class="like-count two">{{ file.like_count }}</span>
</label>
```

**After:**
```html
<label class="like">
    <svg class="like-icon">...</svg>
    <div class="like-count-container">
        <span class="like-count one">{{ file.like_count }}</span>
        <span class="like-count two">{{ file.like_count }}</span>
    </div>
</label>
```

### 2. Add CSS for Container

**File: `static/css/file_card.css`**

**New Addition (after `.like` style):**
```css
/* Like count container for animation */
.tikz-app .like-count-container {
    position: relative;
    display: inline-block;
    min-width: 16px;
    text-align: center;
}
```

### 3. Fix Like Count Positioning

**Before:**
```css
.tikz-app .like-count.two {
    position: absolute;
    right: 10px;          /* ❌ Relative to parent, không đúng */
    transform: translateY(20px);
    opacity: 0;
}

.tikz-app .like-count.one {
    position: relative;
}
```

**After:**
```css
.tikz-app .like-count.two {
    position: absolute;
    top: 0;              /* ✅ Anchor to container */
    left: 0;             /* ✅ Full width */
    right: 0;            /* ✅ Full width */
    transform: translateY(20px);
    opacity: 0;
}

.tikz-app .like-count.one {
    position: relative;
    display: block;      /* ✅ Block level for proper height */
}
```

## 🎬 Animation Behavior

### Default State (Not Liked)
```
┌─────────────┐
│ ❤️  4       │  ← .like-count.one visible (opacity: 1)
│             │  ← .like-count.two hidden below (opacity: 0, translateY(20px))
└─────────────┘
```

### When Clicking to Like
```
Animation sequence:
1. .like-count.one → translateY(-20px), opacity: 0  (flies up & fades)
2. .like-count.two → translateY(0), opacity: 1      (flies in from below)
3. Heart beats (scale animation)

Result:
┌─────────────┐
│ ❤️  5       │  ← .like-count.two now visible
└─────────────┘
```

### Liked State
```
┌─────────────┐
│ ❤️  5       │  ← .like-count.two showing (red color)
│             │  ← .like-count.one hidden above (opacity: 0, translateY(-20px))
└─────────────┘
```

## 📊 Layout Structure

### Container Hierarchy
```
.like-button
  └── .like (flex container)
      ├── .like-icon (svg)
      └── .like-count-container (relative positioning context)
          ├── .like-count.one (relative, visible by default)
          └── .like-count.two (absolute, positioned within container)
```

### Why This Works
1. **`.like-count-container`** provides relative positioning context
2. **`.like-count.one`** takes up space (relative + block)
3. **`.like-count.two`** overlays on top (absolute, top/left/right: 0)
4. Both numbers occupy same space, only one visible at a time
5. Animation transitions smoothly between them

## 🎨 Visual Result

### Before Fix (Broken)
```
When liked:
❤️ 4 4  ← Both numbers showing, stacked weirdly
```

### After Fix (Working)
```
Not liked:
❤️ 4    ← Only .one showing

Liked:
❤️ 5    ← Only .two showing (red)
```

## 🧪 Testing

### Test Cases
1. **Default state (not liked):**
   - [x] Only `.like-count.one` visible
   - [x] Number aligned properly with icon
   - [x] No overlapping text

2. **Click to like:**
   - [x] `.like-count.one` flies up and fades
   - [x] `.like-count.two` flies in from below
   - [x] Heart beats animation
   - [x] Number increments by 1

3. **Liked state:**
   - [x] Only `.like-count.two` visible
   - [x] Number is red (`#ff4757`)
   - [x] No overlapping text

4. **Click to unlike:**
   - [x] Reverse animation
   - [x] Number decrements by 1
   - [x] Heart returns to gray

## 🔧 Technical Details

### CSS Positioning Explanation

**Problem with old approach:**
```css
.like-count.two {
    position: absolute;
    right: 10px;  /* ❌ Relative to .like-button, not aligned with .one */
}
```
- Absolute to `.like-button` parent
- `right: 10px` doesn't match `.like-count.one` position
- Creates misalignment

**Solution with container:**
```css
.like-count-container {
    position: relative;  /* ✅ New positioning context */
}

.like-count.two {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;  /* ✅ Fills container, perfectly aligned with .one */
}
```
- Absolute to `.like-count-container`
- `top/left/right: 0` fills entire container
- Perfect alignment with `.like-count.one`

## ✨ Summary

### Changes Made
1. ✅ Added `.like-count-container` div wrapper in HTML
2. ✅ Added CSS for `.like-count-container` (relative positioning)
3. ✅ Fixed `.like-count.two` positioning (top/left/right instead of right only)
4. ✅ Added `display: block` to `.like-count.one`

### Files Modified
1. `templates/partials/_file_card.html` - Added container div
2. `static/css/file_card.css` - Added container style & fixed positioning

### Result
- ✅ Like count animation works properly
- ✅ Only one number shows at a time
- ✅ No overlapping or stacking issues
- ✅ Smooth transition between states

---

**Ngày fix:** 24/10/2025  
**Issue:** Like count numbers overlapping when liked  
**Solution:** Add container wrapper + fix absolute positioning  
**Status:** ✅ Fixed

