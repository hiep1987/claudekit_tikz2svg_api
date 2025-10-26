# CSS Conflicts Analysis - Comments System

## 🔍 Phát hiện vấn đề

User báo: "Phát triển trang templates/view_svg.html nhưng ảnh hưởng đến CSS của trang index"

## 📋 Checklist kiểm tra

### 1. File CSS đã tạo
- [x] `static/css/comments.css` - 700+ lines
- Được include trong: `templates/view_svg.html` ONLY
- Có prefix: `.tikz-app` cho tất cả selectors

### 2. Kiểm tra conflicts tiềm ẩn

**Class names có thể conflict:**
- `.comment-btn` → ✅ Có prefix `.tikz-app`
- `.comment-textarea` → ✅ Có prefix `.tikz-app`
- `.pagination-btn` → ✅ Có prefix `.tikz-app`
- `.loading` → ⚠️ Generic name nhưng có prefix

**CSS Variables:**
- Không định nghĩa CSS variables mới
- Chỉ sử dụng existing variables từ base.css

**Media Queries:**
- ✅ Tất cả đều có prefix `.tikz-app`
- ⚠️ Nhưng có thể ảnh hưởng nếu index.html cũng có `.tikz-app`

### 3. Kiểm tra template inclusion

**view_svg.html:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/view_svg.css', v='2.0') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/comments.css', v='1.0') }}">
```

**index.html cần kiểm tra:**
- Có include comments.css không? → KHÔNG NÊN
- Có class `.tikz-app` không? → CẦN KIỂM TRA

## 🐛 Nguyên nhân có thể

### Scenario 1: Comments CSS được load globally
❌ `base.html` có include `comments.css` → Ảnh hưởng tất cả pages

### Scenario 2: Index page có class `.tikz-app`
⚠️ Nếu index.html có `.tikz-app` wrapper → CSS sẽ apply

### Scenario 3: CSS variables conflict
⚠️ Comments CSS có thể override CSS variables

### Scenario 4: Selector specificity issues
⚠️ `.tikz-app .btn` có thể override `.index-page .btn`

## 🔧 Kế hoạch Fix

### Bước 1: Kiểm tra file inclusion
```bash
grep -r "comments.css" templates/
```

### Bước 2: Kiểm tra base.html
- Xem có include comments.css globally không
- Xem có CSS variables mới không

### Bước 3: Kiểm tra index.html
- Xem có class `.tikz-app` không
- Xem có class names trùng với comments không

### Bước 4: Tăng specificity
Nếu cần, thay đổi prefix từ `.tikz-app` → `.tikz-app.view-svg-page`

### Bước 5: Isolate CSS
Nếu cần, wrap toàn bộ trong:
```css
.view-svg-page .comments-section { ... }
```

## 📝 Action Items

1. [ ] Grep tất cả file templates
2. [ ] Kiểm tra base.html
3. [ ] Kiểm tra index.html structure
4. [ ] Xác định class conflicts
5. [ ] Fix CSS scoping
6. [ ] Test lại cả 2 pages
7. [ ] Commit fix

## 🎯 Giải pháp đề xuất

### Option 1: Thêm page-specific class
```css
/* Old */
.tikz-app .comments-section { }

/* New */
.tikz-app.view-svg-page .comments-section { }
```

### Option 2: Sử dụng :has() selector (modern browsers)
```css
body:has(.view-svg-container) .comments-section { }
```

### Option 3: Nested scoping
```css
.view-svg-container ~ .comments-section { }
```

### Option 4: Data attribute
```html
<body data-page="view-svg">
```
```css
[data-page="view-svg"] .comments-section { }
```

## ✅ Best Practice đề xuất

**Sử dụng page-specific class:**
1. Thêm class vào body trong view_svg.html
2. Update CSS với class mới
3. Đảm bảo không ảnh hưởng pages khác

