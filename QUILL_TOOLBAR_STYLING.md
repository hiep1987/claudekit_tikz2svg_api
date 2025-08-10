# Cập nhật Styling cho Quill Editor Toolbar

## Mục tiêu
Cập nhật trang `profile_settings.html` để phần toolbar của Quill editor có màu nền giống với `.public-profile-header` và cập nhật màu sắc của color picker cho phù hợp.

## Thay đổi đã thực hiện

### 1. Toolbar Background
**Thay đổi màu nền toolbar:**
```css
.ql-toolbar.ql-snow {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
  border: 1px solid #1565c0 !important;
  border-radius: 8px 8px 0 0 !important;
  color: white !important;
}
```

### 2. Icon Colors
**Cập nhật màu cho các icon:**
```css
.ql-toolbar.ql-snow .ql-stroke {
  stroke: white !important;
}

.ql-toolbar.ql-snow .ql-fill {
  fill: white !important;
}
```

### 3. Button Styling
**Cập nhật màu cho các button:**
```css
.ql-toolbar.ql-snow button {
  color: white !important;
}

.ql-toolbar.ql-snow button:hover {
  color: #e3f2fd !important;
}

.ql-toolbar.ql-snow button.ql-active {
  color: #e3f2fd !important;
}
```

### 4. Color Picker Styling
**Cập nhật color picker để phù hợp với màu nền:**

#### Picker Label:
```css
.ql-toolbar.ql-snow .ql-picker-label {
  color: white !important;
  border: 1px solid rgba(255,255,255,0.3) !important;
}

.ql-toolbar.ql-snow .ql-picker-label:hover {
  border-color: white !important;
}
```

#### Picker Options (Dropdown):
```css
.ql-toolbar.ql-snow .ql-picker-options {
  background: white !important;
  border: 1px solid #1565c0 !important;
  border-radius: 6px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
```

#### Picker Items:
```css
.ql-toolbar.ql-snow .ql-picker-item {
  color: #333 !important;
}

.ql-toolbar.ql-snow .ql-picker-item:hover {
  background: #f0f0f0 !important;
}

.ql-toolbar.ql-snow .ql-picker-item.ql-selected {
  background: #1976d2 !important;
  color: white !important;
}
```

## Kết quả

### 1. Toolbar Appearance
- ✅ **Màu nền**: Gradient xanh dương giống `.public-profile-header`
- ✅ **Border**: Màu xanh đậm phù hợp
- ✅ **Border radius**: Bo tròn góc trên
- ✅ **Text color**: Trắng cho dễ đọc

### 2. Icon và Button
- ✅ **Icons**: Màu trắng (stroke và fill)
- ✅ **Buttons**: Màu trắng với hover effect
- ✅ **Active state**: Màu xanh nhạt khi được chọn

### 3. Color Picker
- ✅ **Label**: Màu trắng với border trong suốt
- ✅ **Dropdown**: Nền trắng với border xanh
- ✅ **Items**: Màu đen với hover effect
- ✅ **Selected item**: Nền xanh với text trắng

## Màu sắc sử dụng
- **Primary**: `#1976d2` (xanh dương)
- **Secondary**: `#1565c0` (xanh đậm)
- **Hover**: `#e3f2fd` (xanh nhạt)
- **Text**: `white` (trắng)
- **Background**: `white` (trắng cho dropdown)

## File đã sửa
- **File**: `tikz2svg_api/templates/profile_settings.html`
- **Vị trí**: Thêm CSS vào phần `<style>` trong `<head>`

## Test
Khi truy cập trang settings, Quill editor toolbar sẽ có:
- Màu nền xanh dương gradient giống header
- Icons và buttons màu trắng
- Color picker với styling phù hợp
- Hover effects mượt mà

## Lưu ý
- Sử dụng `!important` để override CSS mặc định của Quill
- Màu sắc đồng nhất với theme chung của ứng dụng
- Responsive design được duy trì 