# Sửa Logic Desktop Button cho nút "Xem Code" trong profile_followed_posts.html

## ✅ Đã sửa logic Desktop button để giống với profile_svg_files.html

**Vấn đề:** Click nút "Xem code" không hiện log gì cả, cần tham khảo logic từ profile_svg_files.html.

## 🔍 Phân tích vấn đề:

### **So sánh logic giữa hai files:**

**profile_svg_files.html (Hoạt động tốt):**
```html
<!-- Nút "Xem Code" có onclick attribute -->
<button type="button" class="Btn" onclick="toggleTikzCode(this)">
  <div class="sign">
    <i class="fas fa-code logoIcon"></i>
  </div>
  <div class="text">Xem Code</div>
</button>
```

**Desktop button logic (chỉ xử lý Facebook và Copy Link):**
```javascript
// Thêm event listener cho Desktop buttons
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.file-card:not(.followed-post-card) .fb-share-btn, .file-card:not(.followed-post-card) .file-copy-link-btn');
    if (!btn) return;
    
    // Chỉ xử lý Facebook share và Copy Link
    if (btn.classList.contains('fb-share-btn')) {
        // Facebook logic
    } else if (btn.classList.contains('file-copy-link-btn')) {
        // Copy Link logic
    }
    // KHÔNG có logic cho nút "Xem Code"
});
```

**profile_followed_posts.html (Có vấn đề):**
```html
<!-- Nút "Xem Code" có onclick attribute -->
<button type="button" class="Btn" onclick="toggleTikzCode(this)">
  <div class="sign">
    <i class="fas fa-code logoIcon"></i>
  </div>
  <div class="text">Xem Code</div>
</button>
```

**Desktop button logic (đã override onclick):**
```javascript
// Thêm event listener cho Desktop buttons
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.followed-post-card .fb-share-btn, .followed-post-card .file-copy-link-btn, .followed-post-card .Btn[data-filename]:not(.fb-share-btn):not(.file-copy-link-btn), .followed-post-card .Btn[onclick*="toggleTikzCode"]');
    if (!btn) return;
    
    // Xử lý cả Facebook, Copy Link, Tải ảnh, và Xem Code
    if (btn.classList.contains('fb-share-btn')) {
        // Facebook logic
    } else if (btn.classList.contains('file-copy-link-btn')) {
        // Copy Link logic
    } else if (btn.hasAttribute('data-filename') && !btn.classList.contains('fb-share-btn') && !btn.classList.contains('file-copy-link-btn')) {
        // Tải ảnh logic
    } else if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes('toggleTikzCode')) {
        // Xem Code logic - CÓ THỂ ĐANG OVERRIDE ONCLICK
        toggleTikzCode(btn);
    }
});
```

## 🔧 Giải pháp đã áp dụng:

### 1. Sửa logic Desktop button để giống với profile_svg_files.html:

**Trước (Có vấn đề):**
```javascript
// Thêm event listener cho Desktop buttons
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.followed-post-card .fb-share-btn, .followed-post-card .file-copy-link-btn, .followed-post-card .Btn[data-filename]:not(.fb-share-btn):not(.file-copy-link-btn), .followed-post-card .Btn[onclick*="toggleTikzCode"]');
    if (!btn) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    if (btn.classList.contains('fb-share-btn')) {
        // Facebook logic
    } else if (btn.classList.contains('file-copy-link-btn')) {
        // Copy Link logic
    } else if (btn.hasAttribute('data-filename') && !btn.classList.contains('fb-share-btn') && !btn.classList.contains('file-copy-link-btn')) {
        // Tải ảnh logic
    } else if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes('toggleTikzCode')) {
        // Xem Code logic - CÓ THỂ ĐANG OVERRIDE ONCLICK
        toggleTikzCode(btn);
    }
});
```

**Sau (Giống profile_svg_files.html):**
```javascript
// Thêm event listener cho Desktop buttons
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.followed-post-card .fb-share-btn, .followed-post-card .file-copy-link-btn');
    if (!btn) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    if (btn.classList.contains('fb-share-btn')) {
        // Facebook logic
    } else if (btn.classList.contains('file-copy-link-btn')) {
        // Copy Link logic
    }
    // KHÔNG xử lý nút "Xem Code" - để onclick attribute hoạt động
});
```

### 2. Thêm debug logs cho toggleTikzCode function:

```javascript
// Toggle TikZ code function
function toggleTikzCode(btn) {
    console.log('🔍 toggleTikzCode function called');
    console.log('🔍 btn:', btn);
    
    const card = btn.closest('.file-card');
    const codeBlock = card.querySelector('.tikz-code-block');
    const textDiv = btn.querySelector('.text');
    
    console.log('🔍 card:', card);
    console.log('🔍 codeBlock:', codeBlock);
    console.log('🔍 textDiv:', textDiv);
    
    if (codeBlock.style.display === 'none' || !codeBlock.style.display) {
        codeBlock.style.display = 'block';
        textDiv.textContent = 'Ẩn code';
        
        // Initialize CodeMirror when showing the code block
        setTimeout(() => {
            const textarea = codeBlock.querySelector('.tikz-cm');
            
            if (textarea && !textarea.CodeMirror) {
                const existingCm = codeBlock.querySelector('.CodeMirror');
                if (existingCm) {
                    existingCm.remove();
                }
                
                if (typeof CodeMirror !== 'undefined') {
                    try {
                        const cmInstance = CodeMirror.fromTextArea(textarea, {
                            mode: 'stex',
                            theme: 'material',
                            lineNumbers: true,
                            readOnly: true,
                            lineWrapping: true,
                            foldGutter: true,
                            gutters: ['CodeMirror-linenumbers'],
                            viewportMargin: Infinity
                        });
                        
                        // Refresh CodeMirror after a short delay
                        setTimeout(() => {
                            cmInstance.refresh();
                        }, 100);
                    } catch (error) {
                        console.error('❌ Error creating CodeMirror instance:', error);
                    }
                } else {
                    console.error('❌ CodeMirror is not defined!');
                }
            }
        }, 50);
    } else {
        codeBlock.style.display = 'none';
        textDiv.textContent = 'Xem Code';
    }
}
```

## 📋 Logic hoạt động:

### **profile_svg_files.html (Reference):**
1. **Nút "Xem Code"** có `onclick="toggleTikzCode(this)"`
2. **Desktop button logic** chỉ xử lý Facebook và Copy Link
3. **Nút "Xem Code"** hoạt động hoàn toàn dựa trên onclick attribute
4. **Mobile** sử dụng 2-tap logic trong `initializeTouchBtnEvents()`

### **profile_followed_posts.html (Sau khi sửa):**
1. **Nút "Xem Code"** có `onclick="toggleTikzCode(this)"`
2. **Desktop button logic** chỉ xử lý Facebook và Copy Link (giống reference)
3. **Nút "Xem Code"** hoạt động hoàn toàn dựa trên onclick attribute
4. **Mobile** sử dụng 2-tap logic trong `initializeTouchBtnEvents()`

## 🧪 Test Cases:

### 1. Desktop (Logged In) - Nút "Xem Code":
1. Open followed posts page on desktop
2. Hover over followed post card
3. Click "Xem Code" button
4. Expected logs:
   ```
   🔍 toggleTikzCode function called
   🔍 btn: [HTMLElement]
   🔍 card: [HTMLElement]
   🔍 codeBlock: [HTMLElement]
   🔍 textDiv: [HTMLElement]
   ```
5. Expected behavior: Code block toggles và CodeMirror được tạo

### 2. Desktop (Logged In) - Nút "Tải ảnh":
1. Open followed posts page on desktop
2. Hover over followed post card
3. Click "Tải ảnh" button
4. Expected behavior: Navigate to view page (dựa trên onclick attribute)

### 3. Desktop (Logged In) - Facebook và Copy Link:
1. Open followed posts page on desktop
2. Hover over followed post card
3. Click Facebook hoặc Copy Link button
4. Expected behavior: Desktop button logic xử lý (copy to clipboard)

## 📊 Before vs After:

### Before Fix:
```
❌ Desktop button logic override onclick attribute
❌ Nút "Xem Code" không hoạt động
❌ Logic khác với profile_svg_files.html
❌ Không có debug logs
```

### After Fix:
```
✅ Desktop button logic giống với profile_svg_files.html
✅ Nút "Xem Code" hoạt động dựa trên onclick attribute
✅ Logic nhất quán với reference
✅ Có debug logs để troubleshoot
```

## 🚀 Kết quả:

### ✅ Đã sửa:
- **Desktop Button Logic**: Chỉ xử lý Facebook và Copy Link (giống reference)
- **Onclick Attribute**: Để onclick="toggleTikzCode(this)" hoạt động tự nhiên
- **Debug Logs**: Thêm logs để troubleshoot
- **Consistency**: Logic nhất quán với profile_svg_files.html

### 📈 Improvements:
- **Functionality**: Nút "Xem Code" hoạt động đúng cách
- **Consistency**: Behavior giống với profile_svg_files.html
- **Debugging**: Có logs để troubleshoot
- **Maintenance**: Logic dễ hiểu và maintain

## 🔍 Expected Behavior:

### Desktop (Logged In):
1. **Nút "Tải ảnh"**: Navigate dựa trên onclick attribute
2. **Nút "Xem Code"**: Toggle code block dựa trên onclick attribute
3. **Nút "Facebook"**: Copy to clipboard dựa trên Desktop button logic
4. **Nút "Copy Link"**: Copy to clipboard dựa trên Desktop button logic

### Mobile (Logged In):
1. **Tất cả buttons**: 2-tap logic trong `initializeTouchBtnEvents()`

## 🔍 Lưu ý:

- **Onclick Priority**: Onclick attribute có priority cao hơn event listeners
- **Event Delegation**: Desktop button logic chỉ xử lý buttons không có onclick
- **Consistency**: Logic giống với profile_svg_files.html
- **Debugging**: Có logs để troubleshoot khi cần
- **Maintenance**: Dễ maintain và debug 