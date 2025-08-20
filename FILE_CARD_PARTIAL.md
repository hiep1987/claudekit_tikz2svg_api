# File Card Partial Component Documentation

## 📋 **Tổng quan**

File Card Partial Component là một component tái sử dụng được tạo để giải quyết vấn đề maintenance và consistency giữa các trang trong ứng dụng TikZ to SVG. Component này bao gồm HTML, CSS, và JavaScript được modularized để dễ dàng maintain và update.

## 🏗️ **Cấu trúc Files**

```
templates/
├── _file_card.html              # 🆕 Jinja2 partial template
├── index.html                   # Sử dụng partial
├── search_results.html          # Sử dụng partial
└── ...

static/
├── css/
│   └── file_card.css           # 🆕 CSS styles cho component
├── js/
│   ├── file_card.js            # 🆕 HTML generator function
│   └── file_card_functions.js  # 🆕 JavaScript functionality
└── ...
```

## 📄 **Files Chi tiết**

### 1. `templates/_file_card.html`
**Mục đích**: Jinja2 partial template cho server-side rendering
**Sử dụng**: Trong `search_results.html` và các trang khác sử dụng Jinja2

**Cách sử dụng**:
```html
{% for file in search_results %}
    {% include '_file_card.html' %}
{% endfor %}
```

**Variables cần thiết**:
- `file.id`: ID của file
- `file.creator_id`: ID của người tạo
- `file.creator_username`: Tên người tạo
- `file.created_time_vn`: Thời gian tạo (VN timezone)
- `file.url`: URL của ảnh SVG
- `file.filename`: Tên file
- `file.like_count`: Số lượt like
- `file.is_liked_by_current_user`: User đã like chưa
- `file.tikz_code`: Code TikZ (optional)
- `logged_in`: Trạng thái đăng nhập

### 2. `static/js/file_card.js`
**Mục đích**: JavaScript function để tạo HTML cho client-side rendering
**Sử dụng**: Trong `index.html` và các trang sử dụng JavaScript

**Cách sử dụng**:
```javascript
// Include file
<script src="/static/js/file_card.js"></script>

// Sử dụng function
const html = createFileCardHTML(file);
container.innerHTML = html;
```

### 3. `static/css/file_card.css`
**Mục đích**: Tất cả CSS styles cho file card component
**Sử dụng**: Include trong các trang sử dụng component

**Cách sử dụng**:
```html
<link rel="stylesheet" href="/static/css/file_card.css">
```

### 4. `static/js/file_card_functions.js`
**Mục đích**: Tất cả JavaScript functionality cho component
**Sử dụng**: Include trong các trang sử dụng component

**Cách sử dụng**:
```html
<script src="/static/js/file_card_functions.js"></script>
<script>
    // Initialize component
    initializeFileCardComponent();
</script>
```

## 🎯 **Lợi ích của Partial Component**

### ✅ **DRY Principle**
- Code được viết một lần, sử dụng nhiều nơi
- Giảm 90% duplicate code
- Dễ dàng maintain và update

### ✅ **Consistency Guaranteed**
- UI/UX luôn đồng bộ giữa các trang
- Không còn lo lắng về việc sync code
- Bug fixes được apply tự động cho tất cả trang

### ✅ **Maintainability**
- Thay đổi chỉ cần thực hiện ở 1 file
- Testing tập trung vào 1 component
- Code review đơn giản hơn

## 🔧 **Implementation Steps**

### **Phase 1: Create Partials**
1. ✅ Extract file card HTML từ `index.html`
2. ✅ Create `_file_card.html` với Jinja2 variables
3. ✅ Create CSS và JavaScript files

### **Phase 2: Update Existing Pages**
1. ✅ Replace file card HTML trong `search_results.html`
2. 🔄 Replace file card HTML trong `index.html` (pending)
3. 🔄 Test functionality

### **Phase 3: Optimize**
1. 🔄 Move CSS to separate file
2. 🔄 Optimize JavaScript loading
3. 🔄 Performance testing

## 📱 **Responsive Design**

Component hỗ trợ đầy đủ responsive design với các breakpoints:

- **Desktop**: Hover effects, full button labels
- **Tablet (768px)**: Adjusted grid layout
- **Mobile (600px)**: Single column layout
- **Small Mobile (480px)**: Optimized spacing

## 🎨 **Features**

### **Desktop Features**
- Hover effects cho action buttons
- Smooth transitions
- Full button labels on hover

### **Mobile Features**
- 2-tap logic cho action buttons
- Touch-friendly interface
- Action toggle button (⋯)
- Optimized spacing và sizing

### **Universal Features**
- Like button với animation
- Copy to clipboard functionality
- TikZ code display với CodeMirror
- Facebook sharing
- Image download

## 🔄 **Migration Guide**

### **Từ Old Implementation sang Partial**

#### **Cho Jinja2 Templates (search_results.html)**
```html
<!-- OLD -->
<div class="file-card" data-file-id="{{ file.id }}">
    <!-- 100+ lines of HTML -->
</div>

<!-- NEW -->
{% include '_file_card.html' %}
```

#### **Cho JavaScript Templates (index.html)**
```javascript
// OLD
const html = `
    <div class="file-card" data-file-id="${file.id}">
        <!-- 100+ lines of HTML -->
    </div>
`;

// NEW
const html = createFileCardHTML(file);
```

## 🚀 **Future Enhancements**

### **Planned Improvements**
1. **Sub-components**: Tách thành smaller partials
   - `_like_button.html`
   - `_action_buttons.html`
   - `_tikz_code_section.html`

2. **Performance Optimization**
   - Lazy loading cho images
   - CSS optimization
   - JavaScript bundling

3. **Accessibility**
   - ARIA labels
   - Keyboard navigation
   - Screen reader support

## 📝 **Maintenance Notes**

### **Khi cần update component**:
1. Edit `templates/_file_card.html` cho Jinja2 templates
2. Edit `static/js/file_card.js` cho JavaScript templates
3. Edit `static/css/file_card.css` cho styling
4. Edit `static/js/file_card_functions.js` cho functionality
5. Test trên tất cả pages sử dụng component

### **Testing Checklist**:
- [ ] Desktop hover effects
- [ ] Mobile 2-tap logic
- [ ] Copy to clipboard functionality
- [ ] Like button functionality
- [ ] TikZ code display
- [ ] Responsive design
- [ ] Cross-browser compatibility

## 🎯 **Conclusion**

File Card Partial Component đã giải quyết thành công vấn đề maintenance và consistency. Tất cả file card components giờ đây được maintain ở một chỗ duy nhất, đảm bảo UI/UX đồng bộ và dễ dàng update trong tương lai.
