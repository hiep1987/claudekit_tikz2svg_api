# Khắc phục vấn đề "Layout was forced before the page was fully loaded"

## Vấn đề

Cảnh báo "Layout was forced before the page was fully loaded" xảy ra do **race condition** giữa việc tải CSS và thực thi JavaScript. Điều này xảy ra khi:

1. JavaScript cố gắng truy cập thông tin layout (kích thước, vị trí) của các phần tử
2. CSS chưa được tải và áp dụng hoàn toàn
3. Trình duyệt buộc phải tính toán layout ngay lập tức (forced layout)

## Nguyên nhân chính

- **CodeMirror initialization**: Thư viện CodeMirror cần đo kích thước của textarea để hiển thị đúng
- **Timing issues**: JavaScript chạy trước khi CSS được tải xong
- **Network conditions**: Mạng chậm làm CSS tải lâu hơn JavaScript

## Giải pháp đã áp dụng

### 1. Helper Function `isCSSReady()`

```javascript
function isCSSReady() {
    const stylesheets = Array.from(document.styleSheets);
    const externalStylesheets = stylesheets.filter(sheet => {
        try {
            return sheet.href && sheet.href.startsWith('http');
        } catch (e) {
            return false;
        }
    });
    
    if (externalStylesheets.length === 0) {
        return true;
    }
    
    return externalStylesheets.every(sheet => {
        try {
            return sheet.cssRules && sheet.cssRules.length > 0;
        } catch (e) {
            return true;
        }
    });
}
```

### 2. Safe Layout Operation Wrapper

```javascript
function safeLayoutOperation(operation) {
    if (!isCSSReady()) {
        setTimeout(() => safeLayoutOperation(operation), 50);
        return;
    }
    
    if (document.readyState !== 'complete' && document.readyState !== 'interactive') {
        setTimeout(() => safeLayoutOperation(operation), 50);
        return;
    }
    
    try {
        operation();
    } catch (error) {
        console.error('Layout operation failed:', error);
    }
}
```

### 3. Cải thiện CodeMirror Initialization

- Kiểm tra CSS readiness trước khi khởi tạo
- Thêm retry mechanism nếu CSS chưa sẵn sàng
- Sử dụng safe wrapper cho tất cả layout operations

### 4. Cải thiện Event Timing

- Sử dụng `window.addEventListener('load', ...)` thay vì `DOMContentLoaded`
- Thêm delay nhỏ để đảm bảo CSS đã được áp dụng
- Kiểm tra document.readyState trước khi thực hiện layout operations

## Files đã được cập nhật

### `static/js/index.js`
- Thêm `isCSSReady()` helper function
- Thêm `safeLayoutOperation()` wrapper
- Cải thiện `ensureCodeMirror()` và `initCodeMirrorAndBindings()`
- Sử dụng safe wrapper cho highlight.js initialization

### `static/js/file_card.js`
- Thêm `isCSSReady()` helper function
- Cải thiện CodeMirror initialization trong `toggleTikzCode()`
- Thêm retry mechanism cho CodeMirror

## Kết quả mong đợi

1. **Loại bỏ forced layout warnings**: Không còn cảnh báo "Layout was forced"
2. **Cải thiện performance**: Tránh layout thrashing và reflow không cần thiết
3. **Tăng độ ổn định**: CodeMirror khởi tạo đúng cách mọi lúc
4. **Better UX**: Không còn hiện tượng "nháy" (FOUC) khi tải trang

## Testing

Sử dụng file `test_layout_optimization.html` để kiểm tra:
- CSS loading status
- CodeMirror initialization timing
- Console logs cho debugging

## Lưu ý

- Các thay đổi này tương thích ngược và không ảnh hưởng đến functionality hiện tại
- Performance có thể được cải thiện thêm bằng cách preload critical CSS
- Monitor console logs để đảm bảo không có lỗi mới xuất hiện
