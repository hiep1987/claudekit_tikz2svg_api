# CSS Conflicts Analysis Prompt for Claude

## 🎯 Mục tiêu
Tìm và loại bỏ CSS conflicts phức tạp để không cần sử dụng `!important` trong file_card component.

## 📋 Context
Hiện tại file_card component cần `!important` để hoạt động do CSS conflicts từ nhiều file khác. Cần phân tích và refactor để loại bỏ `!important`.

## 🔍 Vấn đề hiện tại

### 1. CSS Rules cần `!important`:
```css
/* Action Toggle Button */
.is-touch .tikz-app .action-toggle-btn {
  display: block !important;
  background: rgba(0, 255, 0, 0.8) !important;
  border: 2px solid green !important;
}

/* Action Container */
.tikz-app .file-card.active .file-action-container {
  display: block !important;
  opacity: 1 !important;
  pointer-events: auto !important;
  transform: translateX(0) !important;
  z-index: 999 !important;
}
```

### 2. Các file CSS có thể gây conflicts:
- `static/css/file_card.css`
- `static/css/profile_svg_files.css`
- `static/css/index.css`
- `static/css/profile_followed_posts.css`
- `static/css/foundation/global-base.css`

## 🛠️ Nhiệm vụ cho Claude

### Bước 1: Phân tích CSS Conflicts
```bash
# Tìm tất cả CSS rules liên quan đến:
grep -r "\.file-action-container" static/css/
grep -r "\.action-toggle-btn" static/css/
grep -r "\.file-card" static/css/
```

### Bước 2: Xác định CSS Specificity
Với mỗi CSS rule tìm được, tính toán specificity:
- Inline styles: 1,0,0,0
- IDs: 0,1,0,0
- Classes, attributes, pseudo-classes: 0,0,1,0
- Elements, pseudo-elements: 0,0,0,1

### Bước 3: Tìm CSS Loading Order
Kiểm tra thứ tự load CSS trong templates:
- `base.html`
- `index.html`
- `profile_svg_files.html`
- Các template khác

### Bước 4: Phân tích Media Queries Conflicts
Tìm các media queries có thể gây conflicts:
```css
@media (hover: none), (pointer: coarse) { ... }
@media (hover: hover) and (pointer: fine) { ... }
@media (width <= 768px) { ... }
```

## 🎯 Kết quả mong đợi

### 1. Báo cáo CSS Conflicts
- Danh sách tất cả CSS rules conflict
- Specificity của từng rule
- Thứ tự CSS loading
- Media queries conflicts

### 2. Giải pháp đề xuất
- Refactor CSS để tăng specificity tự nhiên
- Tối ưu CSS loading order
- Consolidate duplicate CSS rules
- Sử dụng CSS custom properties thay vì !important

### 3. Code refactored
- CSS không cần !important
- Specificity cao hơn tự nhiên
- Performance tốt hơn
- Dễ maintain

## 📝 Prompt Template

```
Tôi cần bạn phân tích CSS conflicts phức tạp trong project này để loại bỏ !important.

CONTEXT:
- File card component cần !important để hoạt động
- Có CSS conflicts từ nhiều file: file_card.css, profile_svg_files.css, index.css, profile_followed_posts.css
- Cần tìm và fix conflicts để không cần !important

NHIỆM VỤ:
1. Tìm tất cả CSS rules liên quan đến .file-action-container và .action-toggle-btn
2. Tính toán CSS specificity của từng rule
3. Xác định CSS loading order trong templates
4. Phân tích media queries conflicts
5. Đề xuất giải pháp refactor CSS
6. Implement code refactored không cần !important

KẾT QUẢ MONG ĐỢI:
- Báo cáo chi tiết CSS conflicts
- CSS refactored với specificity cao tự nhiên
- Không cần !important
- Performance và maintainability tốt hơn

Hãy bắt đầu phân tích từ việc tìm tất cả CSS rules liên quan.
```

## 🔧 Tools cần sử dụng

### 1. Grep Search
```bash
# Tìm CSS rules
grep -r "\.file-action-container" static/css/
grep -r "\.action-toggle-btn" static/css/
grep -r "\.file-card" static/css/

# Tìm media queries
grep -r "@media" static/css/

# Tìm !important
grep -r "!important" static/css/
```

### 2. CSS Specificity Calculator
```javascript
// Function để tính specificity
function calculateSpecificity(selector) {
  // Implementation
}
```

### 3. CSS Loading Order Analysis
```bash
# Tìm CSS links trong templates
grep -r "\.css" templates/
grep -r "stylesheet" templates/
```

## 📊 Expected Output Format

### 1. CSS Conflicts Report
```
FILE: static/css/file_card.css
RULE: .tikz-app .file-action-container
SPECIFICITY: 0,0,2,0
CONFLICTS WITH: profile_svg_files.css line 123

FILE: static/css/profile_svg_files.css  
RULE: .file-action-container
SPECIFICITY: 0,0,1,0
CONFLICTS WITH: file_card.css line 74
```

### 2. Refactored CSS
```css
/* Thay vì !important, sử dụng specificity cao hơn */
.tikz-app .file-card.active .file-action-container.file-action-container {
  display: block;
  opacity: 1;
  pointer-events: auto;
  transform: translateX(0);
  z-index: 999;
}
```

## 🚀 Success Criteria

- [ ] Không còn !important trong file_card.css
- [ ] CSS specificity cao hơn tự nhiên
- [ ] File card component hoạt động tốt
- [ ] Performance không bị ảnh hưởng
- [ ] Code dễ maintain và debug

---

**Sử dụng prompt này để yêu cầu Claude phân tích và fix CSS conflicts!**
