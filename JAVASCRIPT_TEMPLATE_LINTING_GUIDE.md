# JavaScript Template Linting Guide

## Tổng quan

Do stylelint được thiết kế để kiểm tra CSS, việc kiểm tra JavaScript trong HTML templates cần một approach khác. Chúng ta đã tạo một hệ thống hoàn chỉnh để lint JavaScript trong các template HTML.

## Công cụ đã thiết lập

### 1. ESLint Configuration (eslint.config.js)
- ✅ Cấu hình ESLint 9.x format mới
- ✅ Hỗ trợ browser globals (window, document, console)
- ✅ Rules phù hợp cho template JavaScript

### 2. Template JavaScript Linter (lint-template-js.js)
- ✅ Tự động extract JavaScript từ HTML templates
- ✅ Xử lý Jinja2 template syntax
- ✅ Lint từng block JavaScript riêng biệt
- ✅ Báo cáo chi tiết với line numbers

### 3. NPM Scripts
Đã thêm các script mới vào `package.json`:

```json
{
  "lint:js": "npx eslint static/js/**/*.js",
  "lint:js:fix": "npx eslint static/js/**/*.js --fix",
  "lint:template-js": "node lint-template-js.js templates/base.html",
  "lint:all": "npm run lint:css && npm run lint:js && npm run lint:template-js"
}
```

## Cách sử dụng

### Kiểm tra JavaScript trong templates/base.html
```bash
npm run lint:template-js
```

### Kiểm tra tất cả JavaScript files
```bash
npm run lint:js
```

### Kiểm tra tất cả (CSS + JavaScript + Template JavaScript)
```bash
npm run lint:all
```

### Kiểm tra template khác
```bash
node lint-template-js.js path/to/template.html
```

## Kết quả kiểm tra templates/base.html

✅ **3 JavaScript blocks được tìm thấy và đều PASS linting:**

1. **Block 1 (lines 139-156)**: Google Tag Manager code
2. **Block 2 (lines 161-173)**: Environment detection & user ID setup
3. **Block 3 (lines 261-278)**: MathJax configuration

## Tính năng của Template Linter

### JavaScript Extraction
- Tự động tìm và extract tất cả `<script>` tags
- Loại bỏ external scripts (có `src` attribute)
- Báo cáo line numbers chính xác

### Jinja2 Template Handling
- Xử lý `{% %}` control blocks
- Thay thế `{{ }}` variables với `null`
- Xử lý if/else statements phức tạp
- Clean up whitespace và formatting

### ESLint Integration
- Tạo temporary files để lint
- Sử dụng modern ESLint configuration
- Tự động cleanup temporary files
- Detailed error reporting

## Best Practices

### 1. Template JavaScript
```javascript
// ✅ Good: Simple, clean JavaScript
window.currentUserId = null; // Will be set by template

// ❌ Avoid: Complex template logic in JavaScript
window.data = {% if complex_condition %}{{ complex_data }}{% endif %};
```

### 2. CSP-Safe Patterns
```javascript
// ✅ Good: Use data attributes
const userId = document.body.dataset.userId;

// ❌ Avoid: Inline template variables
window.userId = {{ user.id }};
```

### 3. External Files
```html
<!-- ✅ Good: Extract complex JavaScript -->
<script src="{{ url_for('static', filename='js/myfile.js') }}"></script>

<!-- ❌ Avoid: Large inline scripts -->
<script>
  // 100+ lines of JavaScript code
</script>
```

## Troubleshooting

### ESLint Errors
- Kiểm tra `eslint.config.js` configuration
- Đảm bảo globals được định nghĩa đúng
- Check temporary files nếu cần debug

### Template Syntax Issues
- Script có thể cần update regex patterns
- Test với template syntax phức tạp
- Consider extracting to separate files

### Performance
- Template linting chạy nhanh (<1 second)
- Temporary files được tự động cleanup
- Safe để chạy trong CI/CD pipeline

## Monitoring & Updates

### Regular Checks
```bash
# Chạy hàng ngày hoặc trước commit
npm run lint:all
```

### CI Integration
Thêm vào GitHub Actions hoặc CI pipeline:
```yaml
- name: Lint JavaScript
  run: npm run lint:all
```

### Template Updates
Khi thêm JavaScript mới vào templates:
1. Chạy `npm run lint:template-js`
2. Fix any issues reported
3. Consider extracting to separate files nếu quá phức tạp

## Files Created

- `eslint.config.js` - Modern ESLint configuration
- `lint-template-js.js` - Comprehensive template linter
- `JAVASCRIPT_TEMPLATE_LINTING_GUIDE.md` - This guide
- Updated `package.json` - New lint scripts

## Summary

✅ **Successfully implemented JavaScript linting for HTML templates**
- Không thể dùng stylelint trực tiếp cho JavaScript
- Tạo workflow hoàn chỉnh với ESLint
- All templates/base.html JavaScript blocks pass linting
- Easy-to-use npm scripts
- Comprehensive documentation

Giờ bạn có thể kiểm tra JavaScript trong templates một cách tự động và chuyên nghiệp!
