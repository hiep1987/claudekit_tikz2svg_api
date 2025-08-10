# Hướng dẫn tính năng Avatar Upload

## ✅ Đã hoàn thành việc thêm tính năng Avatar Upload

Tính năng upload và crop avatar đã được thêm vào trang `profile_settings.html` và route `/profile/<int:user_id>/settings`.

## 🔧 Cách hoạt động

### 1. Frontend (profile_settings.html)

#### Input File
```html
<input type="file" id="avatar-input" name="avatar" accept="image/*" onchange="openCropperModal(this)">
```

#### Cropper Modal
- Sử dụng **Cropper.js** để crop ảnh thành hình tròn
- Modal hiển thị khi user chọn file
- Có thể zoom, move, crop ảnh
- Tạo canvas hình tròn từ ảnh đã crop

#### JavaScript Functions
- `openCropperModal(input)`: Mở modal cropper
- `closeCropperModal()`: Đóng modal
- `crop-avatar-btn`: Lưu ảnh đã crop

### 2. Backend (app.py - route profile_settings)

#### Xử lý POST Request
```python
if request.method == 'POST':
    avatar_file = request.files.get('avatar')
    avatar_cropped_data = request.form.get('avatar_cropped')
```

#### Hai cách upload:

**A. Upload file trực tiếp:**
```python
if avatar_file and avatar_file.filename != '':
    # Xóa avatar cũ
    # Lưu file mới với secure_filename
    # Update database
```

**B. Upload base64 (từ cropper):**
```python
elif avatar_cropped_data and avatar_cropped_data.startswith('data:image'):
    # Parse base64 data
    # Tạo tên file random với uuid
    # Decode và lưu file
    # Update database
```

## 📁 Cấu trúc file

### Thư mục lưu trữ
- **Path:** `static/avatars/`
- **Format:** `avatar_{uuid}.{ext}`
- **Ví dụ:** `avatar_a1b2c3d4e5f6.png`

### Database
- **Table:** `user`
- **Column:** `avatar` (VARCHAR)
- **Lưu:** Tên file (không bao gồm path)

## 🔒 Bảo mật

### File Upload Security
- Sử dụng `secure_filename()` để sanitize tên file
- Kiểm tra file type: `image/jpeg`, `image/jpg`, `image/png`, `image/gif`
- Giới hạn kích thước: 5MB
- Tạo tên file random với UUID để tránh conflict

### Access Control
- Chỉ owner mới có thể upload avatar
- Route có kiểm tra `is_owner`
- Redirect về trang profile nếu không phải owner

## 🧪 Test Cases

### Test Case 1: Upload file trực tiếp
1. Truy cập `/profile/1/settings` (với user ID = 1)
2. Click "📷 Chọn ảnh đại diện"
3. Chọn file ảnh
4. Submit form
5. Kiểm tra file được lưu trong `static/avatars/`
6. Kiểm tra database được update

### Test Case 2: Upload với cropper
1. Truy cập `/profile/1/settings` (với user ID = 1)
2. Click "📷 Chọn ảnh đại diện"
3. Chọn file ảnh
4. Crop ảnh trong modal
5. Click "Cắt & Lưu"
6. Submit form
7. Kiểm tra file hình tròn được lưu

### Test Case 3: Xóa avatar cũ
1. Upload avatar mới
2. Kiểm tra avatar cũ bị xóa khỏi filesystem
3. Kiểm tra database chỉ lưu tên file mới

### Test Case 4: Access Control
1. Truy cập `/profile/1/settings` với user khác
2. Kiểm tra bị redirect về `/profile/1`

## 🐛 Error Handling

### Frontend Errors
- File quá lớn (>5MB): Hiển thị alert
- File type không hợp lệ: Hiển thị alert
- Cropper error: Log error và hiển thị thông báo

### Backend Errors
- File save error: Log warning và tiếp tục
- Database error: Log error và rollback
- Avatar cũ không xóa được: Log warning và tiếp tục

## 📝 Log Messages

### Success
```
"Đã cập nhật hồ sơ!"
```

### Errors
```
"[WARN] Không thể xóa avatar cũ: {error}"
"[WARN] Error saving cropped avatar: {error}"
"Có lỗi khi lưu ảnh đại diện đã cắt."
```

## 🚀 Lợi ích

1. **User Experience:** Giao diện thân thiện với cropper
2. **Security:** Bảo mật file upload
3. **Performance:** Tự động xóa file cũ
4. **Flexibility:** Hỗ trợ cả upload trực tiếp và crop
5. **Maintainability:** Code sạch và có tổ chức

## 🔄 Workflow

1. User chọn file ảnh
2. Frontend validate file (size, type)
3. Mở cropper modal (nếu cần)
4. User crop và lưu
5. Submit form với base64 data
6. Backend xử lý và lưu file
7. Xóa avatar cũ
8. Update database
9. Redirect và hiển thị thông báo thành công 