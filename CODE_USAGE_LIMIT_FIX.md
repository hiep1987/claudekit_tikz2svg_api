# Code Usage Limit Fix - Implementation Summary

## 🎯 **Problem Fixed**

**Issue:** Mã xác thực bị generate mới sau mỗi lần submit thay vì cho phép dùng 1 mã trong 5 lần.

**Expected Behavior:** 1 mã xác thực có thể được dùng 5 lần trong vòng 10 phút.

## 🔧 **Changes Made**

### **1. Database Schema Addition**
- **File:** `add_usage_count_field.sql`
- **Purpose:** Thêm field `profile_verification_usage_count` để track số lần sử dụng mã

```sql
ALTER TABLE `user` 
ADD COLUMN `profile_verification_usage_count` INT DEFAULT 0 COMMENT 'Số lần mã xác thực đã được sử dụng thành công (max 5 lần)';
```

### **2. Code Generation Logic Fix**
- **File:** `app.py` (lines 2253-2321)
- **Change:** Thay vì luôn tạo mã mới, giờ kiểm tra và tái sử dụng mã hiện tại nếu:
  - Mã chưa hết hạn (< 10 phút)
  - Mã chưa hết lượt sử dụng (< 5 lần)

```python
# Kiểm tra có thể tái sử dụng mã hiện tại không
if (existing_verification and 
    existing_verification['profile_verification_code'] and
    existing_verification['profile_verification_expires_at'] and
    datetime.now() < existing_verification['profile_verification_expires_at'] and
    (existing_verification.get('profile_verification_usage_count', 0) or 0) < 5):
    
    # Tái sử dụng mã hiện tại
    verification_code = existing_verification['profile_verification_code']
    expires_at = existing_verification['profile_verification_expires_at']
    usage_count = existing_verification.get('profile_verification_usage_count', 0) or 0
    print(f"🔄 DEBUG: Reusing existing code {verification_code}, usage: {usage_count}/5", flush=True)
else:
    # Tạo mã xác thực mới
    verification_code = generate_verification_code(6)
    expires_at = datetime.now() + timedelta(minutes=10)  # 10 phút thay vì 24 giờ
    usage_count = 0
    print(f"🆕 DEBUG: Generated new code {verification_code}", flush=True)
```

### **3. Code Cleanup Logic Fix**
- **File:** `app.py` (lines 3814-3875)
- **Change:** Thay vì xóa mã sau mỗi lần sử dụng, giờ tăng usage count và chỉ xóa khi:
  - Đã dùng hết 5 lần
  - Hoặc hết hạn 10 phút

```python
# Tăng usage count thay vì xóa mã (chỉ khi có field usage_count)
if 'profile_verification_usage_count' in result:
    new_usage_count = usage_count + 1
    
    if new_usage_count >= 5:
        # Đã hết lượt sử dụng - xóa thông tin xác thực
        flash("✅ Xác thực thành công! Hồ sơ đã được cập nhật. Mã xác thực đã hết lượt sử dụng.", "success")
    else:
        # Còn lượt sử dụng - chỉ tăng usage count
        remaining_uses = 5 - new_usage_count
        flash(f"✅ Xác thực thành công! Hồ sơ đã được cập nhật. Mã còn {remaining_uses} lượt sử dụng.", "success")
```

### **4. Backward Compatibility**
- **Fallback Logic:** Code hoạt động bình thường ngay cả khi chưa có field `profile_verification_usage_count` trong database
- **Error Handling:** Try-catch blocks để gracefully degrade về logic cũ nếu field chưa tồn tại

## 🧪 **Testing Instructions**

### **Step 1: Apply Database Changes**
```bash
# Run this SQL command on your database
source venv/bin/activate
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < add_usage_count_field.sql
```

### **Step 2: Test Code Reuse Logic**
1. **Lần 1:** Thay đổi bio → Nhận mã `XXXXXX`
2. **Lần 2:** Thay đổi tên hiển thị → Kiểm tra DB: mã phải **GIỮ NGUYÊN** `XXXXXX`
3. **Lần 3-5:** Tiếp tục thay đổi → Mã vẫn phải là `XXXXXX`
4. **Lần 6:** Thay đổi gì đó → Mã phải **TẠO MỚI**

### **Step 3: Test Time Expiry**
1. Thay đổi profile → Nhận mã
2. Đợi 10 phút
3. Thay đổi lại → Phải tạo mã mới

### **Step 4: Test Usage Count**
1. Dùng mã thành công 5 lần
2. Lần 6 → Phải yêu cầu mã mới

## 🔍 **Debug Information**

Look for these debug messages in the console:
- `🔄 DEBUG: Reusing existing code XXXXXX, usage: X/5` - Mã được tái sử dụng
- `🆕 DEBUG: Generated new code XXXXXX` - Mã mới được tạo
- `⚠️ DEBUG: Field profile_verification_usage_count chưa tồn tại` - Fallback mode

## 📊 **Expected Results**

**Before Fix:**
```
21:45 - Bio change → Code: 259973
21:46 - Name change → Code: 323540 (❌ NEW CODE)
```

**After Fix:**
```
21:45 - Bio change → Code: 259973
21:46 - Name change → Code: 259973 (✅ SAME CODE)
21:47 - Avatar change → Code: 259973 (✅ SAME CODE)
...up to 5 times...
21:50 - 6th change → Code: 456789 (✅ NEW CODE after 5 uses)
```

## 🎉 **Success Criteria**
- ✅ 1 mã có thể dùng tối đa 5 lần
- ✅ Mã hết hiệu lực sau 10 phút  
- ✅ Backward compatible với database cũ
- ✅ Debug logging cho troubleshooting
- ✅ User feedback về số lượt còn lại
