# CSS Override Prevention Guide

## Tổng quan
Hướng dẫn này mô tả quy trình cải tiến CSS để tránh bị override trong dự án tikz2svg_api. Phương pháp được sử dụng là **CSS Scoping** với container wrapper.

## Vấn đề gặp phải
- CSS classes bị Bootstrap và external libraries override
- Conflicts giữa các component CSS files
- Specificity wars giữa các selectors
- Media queries overlap gây ra responsive issues

## Phương pháp giải quyết: CSS Scoping với Container

### Phase 1: Thêm Wrapper Container

#### 1. Cập nhật HTML Template
```html
<!-- Trước -->
<body>
    {% include 'partials/_navbar.html' %}
    <div class="page-container">
        <!-- content -->
    </div>
    {% include 'partials/_login_modal.html' %}
</body>

<!-- Sau -->
<body>
    <div class="tikz-app">
        {% include 'partials/_navbar.html' %}
        <div class="page-container">
            <!-- content -->
        </div>
        {% include 'partials/_login_modal.html' %}
    </div>
</body>
```

**⚠️ Lưu ý quan trọng:**
- Navbar và modals phải được đưa VÀO TRONG `.tikz-app` container
- Nếu để ngoài sẽ bị mất functionality do CSS scoping

#### 2. Automated CSS Scoping với Python Script

```python
import os
import re

def scope_css_file(file_path, scope_class='.tikz-app'):
    """
    Tự động thêm scope class vào tất cả CSS selectors
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original file
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    lines = content.split('\n')
    processed_lines = []
    
    for line in lines:
        # Skip comments, empty lines, keyframes, media queries
        if (line.strip().startswith('/*') or 
            line.strip().startswith('*') or 
            line.strip() == '' or
            '@keyframes' in line or
            '@media' in line or
            line.strip().startswith('@')):
            processed_lines.append(line)
            continue
        
        # Process CSS selectors
        if '{' in line and not line.strip().startswith('/*'):
            # Extract selector part
            parts = line.split('{')
            selector_part = parts[0].strip()
            rest = '{'.join(parts[1:])
            
            # Skip if already scoped or is root element
            if (scope_class.replace('.', '') in selector_part or
                selector_part.startswith('html') or
                selector_part.startswith('body') or
                selector_part.startswith('*')):
                processed_lines.append(line)
                continue
            
            # Add scope to selector
            if selector_part:
                # Handle multiple selectors separated by comma
                selectors = [s.strip() for s in selector_part.split(',')]
                scoped_selectors = []
                
                for sel in selectors:
                    if sel.startswith('#') or sel.startswith('.') or sel.startswith('['):
                        scoped_sel = f"{scope_class} {sel}"
                    else:
                        scoped_sel = f"{scope_class} {sel}"
                    scoped_selectors.append(scoped_sel)
                
                new_selector = ', '.join(scoped_selectors)
                new_line = f"{new_selector} {{{rest}"
                processed_lines.append(new_line)
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    # Write processed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(processed_lines))
    
    print(f"✅ Scoped: {file_path}")

# Apply to all CSS files
css_files = [
    'static/css/index.css',
    'static/css/navigation.css', 
    'static/css/file_card.css',
    'static/css/login_modal.css'
]

for css_file in css_files:
    if os.path.exists(css_file):
        scope_css_file(css_file)
```

#### 3. Manual Fixes cần thiết sau automation

```css
/* Fix unscoped selectors in navigation.css */
/* Trước */
nav .menu-item { list-style: none; }
input[type="text"] { border: 1px solid #ccc; }

/* Sau */
.tikz-app nav .menu-item { list-style: none; }
.tikz-app input[type="text"] { border: 1px solid #ccc; }

/* Fix unscoped selectors in file_card.css */
/* Trước */
input[id^="heart-"] { display: none; }

/* Sau */
.tikz-app input[id^="heart-"] { display: none; }
```

## Quy trình rà soát CSS sau khi scope

### 1. Tìm và fix duplicate selectors

```bash
# Tìm duplicate selectors
grep -n "\.tikz-app \.page-container" static/css/index.css

# Example output:
# 18:.tikz-app .page-container {
# 514:.tikz-app .input-preview-section.page-container.container {
```

**Fix:** Merge các properties của duplicate selectors:

```css
/* Trước - Duplicate selectors */
.tikz-app .page-container {
    box-sizing: border-box;
    width: 100%;
}

.tikz-app .page-container {
    max-width: 1200px;
    margin: 0 auto;
}

/* Sau - Merged */
.tikz-app .page-container {
    box-sizing: border-box;
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
}
```

### 2. Kiểm tra ID conflicts

```bash
# Extract HTML IDs
grep -o 'id="[^"]*"' templates/index.html | sort | uniq > /tmp/html_ids.txt

# Extract CSS IDs  
grep -o '#[a-zA-Z][a-zA-Z0-9_-]*' static/css/index.css | sort | uniq > /tmp/css_ids.txt

# Compare for mismatches
diff /tmp/html_ids.txt /tmp/css_ids.txt
```

### 3. Rà soát Media Queries

Kiểm tra các breakpoints để tránh overlap:

```css
/* Potential conflict */
@media (max-width: 1000px) { /* styles */ }
@media (min-width: 1000px) { /* styles */ }  /* Same breakpoint! */

/* Better approach */
@media (max-width: 999px) { /* styles */ }
@media (min-width: 1000px) { /* styles */ }
```

Verify tất cả selectors trong media queries đều có scope:

```css
/* Đúng */
@media (max-width: 768px) {
    .tikz-app .input-preview-section {
        padding: 20px 0;
    }
}

/* Sai - thiếu scope */
@media (max-width: 768px) {
    .input-preview-section {  /* Missing .tikz-app */
        padding: 20px 0;
    }
}
```

## Kết quả đạt được

### ✅ Lợi ích
- **Tránh CSS conflicts:** Bootstrap và external libraries không override
- **Component isolation:** Mỗi component CSS được bảo vệ
- **Maintainable:** Dễ debug và maintain
- **Scalable:** Có thể thêm components mới mà không lo conflicts

### ⚠️ Trade-offs
- **CSS file size:** Tăng ~10-15% do thêm scope prefixes
- **Specificity:** Tăng specificity, cần chú ý khi override
- **Migration effort:** Cần update HTML structure

## Testing Checklist

Sau khi implement, test các functionality:

- [ ] **Navbar functionality** - Menu clicks, dropdowns
- [ ] **Form submissions** - AJAX forms, validation
- [ ] **Modals** - Login modal, keyword modal  
- [ ] **CodeMirror editor** - Syntax highlighting, shortcuts
- [ ] **Export functionality** - PNG/JPEG downloads
- [ ] **Search features** - Autocomplete, suggestions
- [ ] **File cards** - Like buttons, actions, hover effects
- [ ] **Responsive design** - Mobile/tablet/desktop layouts
- [ ] **Real-time features** - Live preview, polling updates

## Lệnh hữu ích

```bash
# Backup CSS files trước khi modify
find static/css -name "*.css" -exec cp {} {}.backup \;

# Restore từ backup nếu cần
find static/css -name "*.backup" -exec bash -c 'mv "$1" "${1%.backup}"' _ {} \;

# Count total selectors
grep -c '{' static/css/*.css

# Find unscoped selectors (potential issues)
grep -n '^[^.#@/].*{' static/css/index.css
```

## Alternative Approaches (không được sử dụng)

### BEM Methodology
```css
/* Sẽ require major refactor */
.tikz-form__input--primary { }
.tikz-card__header--highlighted { }
```

### CSS Modules
```css
/* Require build tools setup */
.container :local(.header) { }
```

### CSS-in-JS
```javascript
// Require framework changes
const styles = styled.div`
  .header { color: blue; }
`;
```

**Lý do chọn CSS Scoping:** Minimal changes, backward compatible, không require build tools.

## Kết luận

CSS Scoping với container wrapper là solution hiệu quả nhất cho việc tránh override issues trong project này. Phương pháp này:

1. **Đơn giản implement** - Chỉ cần thêm wrapper và scope CSS
2. **Backward compatible** - Không break existing functionality  
3. **Performance good** - Minimal overhead
4. **Maintainable** - Dễ understand và maintain

Việc automation với Python script giúp reduce manual work và ensure consistency across CSS files.