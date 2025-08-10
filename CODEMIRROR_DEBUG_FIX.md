# Debug và Sửa lỗi CodeMirror trong profile_followed_posts.html

## ✅ Đã thêm debug logging và error handling cho CodeMirror

**Vấn đề:** Trang followed-post-card trên desktop khi đăng nhập, khi click nút xem code có log: `🔍 Tạo CodeMirror instance mới` nhưng không thấy class="CodeMirror cm-s-material CodeMirror-wrap".

## 🔍 Phân tích vấn đề:

### **Các vấn đề có thể xảy ra:**
1. **CodeMirror libraries chưa được load** - Scripts chưa load xong
2. **CSS syntax errors** - Lỗi CSS có thể ảnh hưởng đến việc tạo CodeMirror
3. **Timing issues** - CodeMirror được gọi trước khi libraries load xong
4. **Error trong CodeMirror creation** - Exception khi tạo instance
5. **DOM manipulation issues** - Element không được tạo đúng cách

## 🔧 Giải pháp đã áp dụng:

### 1. Sửa lỗi CSS syntax:

**Lỗi phát hiện:**
```css
.Btn.individual-active .text,
.Btn.ready-to-execute .text {
  opacity: 1 !important;
  width: auto !important;
  max-width: 85px !important;
  color: #ffffff !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}
  opacity: 1;  /* ❌ CSS properties bị lạc chỗ */
  width: auto;
  max-width: 85px;
}
```

**Đã sửa:**
```css
.Btn.individual-active .text,
.Btn.ready-to-execute .text {
  opacity: 1 !important;
  width: auto !important;
  max-width: 85px !important;
  color: #ffffff !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}
```

### 2. Thêm CodeMirror availability check:

**Trước:**
```javascript
// ==== Initialize CodeMirror ====
initializeCodeMirror();
```

**Sau:**
```javascript
// ==== Initialize CodeMirror ====
// Kiểm tra xem CodeMirror đã được load chưa
if (typeof CodeMirror !== 'undefined') {
    console.log('✅ CodeMirror is available');
    initializeCodeMirror();
} else {
    console.log('⏳ CodeMirror not loaded yet, waiting...');
    // Thử lại sau 1 giây
    setTimeout(() => {
        if (typeof CodeMirror !== 'undefined') {
            console.log('✅ CodeMirror is now available');
            initializeCodeMirror();
        } else {
            console.error('❌ CodeMirror failed to load');
        }
    }, 1000);
}
```

### 3. Thêm comprehensive debug logging:

**Trong function toggleTikzCode:**
```javascript
function toggleTikzCode(btn) {
    const card = btn.closest('.file-card');
    const codeBlock = card.querySelector('.tikz-code-block');
    const textDiv = btn.querySelector('.text');
    
    console.log('🔍 toggleTikzCode called');
    console.log('🔍 card:', card);
    console.log('🔍 codeBlock:', codeBlock);
    console.log('🔍 textDiv:', textDiv);
    
    if (codeBlock.style.display === 'none' || !codeBlock.style.display) {
        codeBlock.style.display = 'block';
        textDiv.textContent = 'Ẩn code';
        
        console.log('🔍 Code block is now visible');
        
        // Initialize CodeMirror when showing the code block
        setTimeout(() => {
            const textarea = codeBlock.querySelector('.tikz-cm');
            console.log('🔍 textarea found:', textarea);
            console.log('🔍 textarea.CodeMirror:', textarea ? textarea.CodeMirror : 'N/A');
            
            if (textarea && !textarea.CodeMirror) {
                console.log('🔍 Tạo CodeMirror instance mới');
                const existingCm = codeBlock.querySelector('.CodeMirror');
                console.log('🔍 existingCm:', existingCm);
                if (existingCm) {
                    existingCm.remove();
                    console.log('🔍 Removed existing CodeMirror');
                }
                
                if (typeof CodeMirror !== 'undefined') {
                    console.log('🔍 CodeMirror is available, creating instance...');
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
                        
                        console.log('🔍 CodeMirror instance created:', cmInstance);
                        
                        // Refresh CodeMirror after a short delay
                        setTimeout(() => {
                            cmInstance.refresh();
                            console.log('🔍 CodeMirror instance refreshed');
                            
                            // Kiểm tra xem CodeMirror element đã được tạo chưa
                            const cmElement = codeBlock.querySelector('.CodeMirror');
                            console.log('🔍 CodeMirror element in DOM:', cmElement);
                            if (cmElement) {
                                console.log('🔍 CodeMirror classes:', cmElement.className);
                            }
                        }, 100);
                    } catch (error) {
                        console.error('❌ Error creating CodeMirror instance:', error);
                    }
                } else {
                    console.error('❌ CodeMirror is not defined!');
                }
            } else {
                console.log('🔍 CodeMirror instance already exists or textarea not found');
            }
        }, 50);
    } else {
        codeBlock.style.display = 'none';
        textDiv.textContent = 'Xem Code';
    }
}
```

### 4. Thêm error handling cho CodeMirror creation:

**Trong function initializeCodeMirror:**
```javascript
if (typeof CodeMirror !== 'undefined') {
    console.log('🔍 CodeMirror is available, creating instance...');
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
        
        console.log('🔍 CodeMirror instance created:', cmInstance);
        
        // Refresh CodeMirror after a short delay
        setTimeout(() => {
            cmInstance.refresh();
            console.log('🔍 CodeMirror instance created and refreshed');
        }, 100);
    } catch (error) {
        console.error('❌ Error creating CodeMirror instance:', error);
    }
} else {
    console.error('❌ CodeMirror is not defined!');
}
```

## 📋 Debug Information:

### Expected Logs khi click nút "Xem Code":

**1. Initial call:**
```
🔍 toggleTikzCode called
🔍 card: [HTMLElement]
🔍 codeBlock: [HTMLElement]
🔍 textDiv: [HTMLElement]
🔍 Code block is now visible
```

**2. CodeMirror creation:**
```
🔍 textarea found: [HTMLTextAreaElement]
🔍 textarea.CodeMirror: undefined
🔍 Tạo CodeMirror instance mới
🔍 existingCm: null
🔍 CodeMirror is available, creating instance...
🔍 CodeMirror instance created: [CodeMirror instance]
🔍 CodeMirror instance refreshed
🔍 CodeMirror element in DOM: [HTMLElement]
🔍 CodeMirror classes: CodeMirror cm-s-material CodeMirror-wrap
```

### Error Logs có thể xuất hiện:

**1. CodeMirror not loaded:**
```
❌ CodeMirror is not defined!
```

**2. Creation error:**
```
❌ Error creating CodeMirror instance: [Error details]
```

**3. Timing issue:**
```
⏳ CodeMirror not loaded yet, waiting...
✅ CodeMirror is now available
```

## 🧪 Test Cases:

### 1. Desktop (Logged In) - Normal Flow:
1. Open followed posts page on desktop
2. Hover over followed post card
3. Click "Xem Code" button
4. Expected logs:
   - `🔍 toggleTikzCode called`
   - `🔍 Code block is now visible`
   - `🔍 Tạo CodeMirror instance mới`
   - `🔍 CodeMirror is available, creating instance...`
   - `🔍 CodeMirror instance created`
   - `🔍 CodeMirror element in DOM`
   - `🔍 CodeMirror classes: CodeMirror cm-s-material CodeMirror-wrap`

### 2. Desktop (Logged In) - CodeMirror not loaded:
1. Open followed posts page on desktop
2. Click "Xem Code" button before CodeMirror loads
3. Expected logs:
   - `❌ CodeMirror is not defined!`
   - `⏳ CodeMirror not loaded yet, waiting...`
   - `✅ CodeMirror is now available`

### 3. Desktop (Logged In) - Creation error:
1. Open followed posts page on desktop
2. Click "Xem Code" button
3. Expected logs:
   - `❌ Error creating CodeMirror instance: [Error details]`

## 🔍 Troubleshooting Steps:

### 1. Kiểm tra CodeMirror libraries:
```javascript
console.log('CodeMirror:', typeof CodeMirror);
console.log('CodeMirror.fromTextArea:', typeof CodeMirror?.fromTextArea);
```

### 2. Kiểm tra textarea element:
```javascript
const textarea = codeBlock.querySelector('.tikz-cm');
console.log('textarea:', textarea);
console.log('textarea.value:', textarea?.value);
```

### 3. Kiểm tra CodeMirror element sau khi tạo:
```javascript
const cmElement = codeBlock.querySelector('.CodeMirror');
console.log('cmElement:', cmElement);
console.log('cmElement.className:', cmElement?.className);
```

### 4. Kiểm tra CSS classes:
```javascript
const cmElement = codeBlock.querySelector('.CodeMirror');
if (cmElement) {
    console.log('Has cm-s-material:', cmElement.classList.contains('cm-s-material'));
    console.log('Has CodeMirror-wrap:', cmElement.classList.contains('CodeMirror-wrap'));
}
```

## 📊 Before vs After:

### Before Debug:
```
❌ CSS syntax errors
❌ No CodeMirror availability check
❌ No error handling
❌ Limited debug information
❌ Timing issues not handled
```

### After Debug:
```
✅ CSS syntax fixed
✅ CodeMirror availability check added
✅ Comprehensive error handling
✅ Detailed debug logging
✅ Timing issues handled
✅ DOM element verification
```

## 🚀 Kết quả:

### ✅ Đã thêm:
- **CSS Fix**: Sửa lỗi CSS syntax
- **Availability Check**: Kiểm tra CodeMirror đã load chưa
- **Error Handling**: Try-catch cho CodeMirror creation
- **Debug Logging**: Comprehensive logging cho troubleshooting
- **DOM Verification**: Kiểm tra element đã được tạo chưa
- **Timing Handling**: Retry mechanism cho loading issues

### 📈 Improvements:
- **Reliability**: CodeMirror creation more reliable
- **Debugging**: Easy to troubleshoot issues
- **Error Recovery**: Better error handling
- **User Experience**: More stable code display
- **Maintenance**: Easier to maintain và debug

## 🔍 Lưu ý:

- **Console Logs**: Kiểm tra console để xem debug information
- **Timing**: CodeMirror có thể cần thời gian để load
- **CSS Classes**: Expected classes: `CodeMirror cm-s-material CodeMirror-wrap`
- **Error Handling**: Errors sẽ được logged với details
- **Retry Logic**: Automatic retry nếu CodeMirror chưa load 