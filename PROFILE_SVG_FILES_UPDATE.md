# Cập nhật trang profile_svg_files.html

## Mục tiêu
Khi tách trang `profile.html` thành 3 trang riêng biệt, trang `profile_svg_files.html` cần hiển thị giống như trang profile cũ với header thông tin user và logic tương tự.

## URL mục tiêu
- **URL cũ**: `https://tikz2svg.mathlib.io.vn/profile/5`
- **URL mới**: `https://tikz2svg.mathlib.io.vn/profile/5/svg-files`

## Những thay đổi đã thực hiện

### 1. Cập nhật Route trong `app.py`

**File**: `app.py` - Route `/profile/<int:user_id>/svg-files`

**Thêm logic follow/unfollow**:
```python
# Follow logic
is_followed = False
follower_count = 0

# Luôn tính follower_count bất kể đăng nhập hay không
cursor.execute("SELECT COUNT(*) as count FROM user_follow WHERE followee_id=%s", (user_id,))
follower_count = cursor.fetchone()['count']

# Chỉ kiểm tra is_followed nếu đã đăng nhập và không phải owner
if current_user_id and not is_owner:
    cursor.execute("SELECT 1 FROM user_follow WHERE follower_id=%s AND followee_id=%s", (current_user_id, user_id))
    is_followed = cursor.fetchone() is not None
```

**Thêm các biến mới vào template**:
- `email_verified=True`
- `is_followed=is_followed`
- `follower_count=follower_count`

### 2. Cập nhật Template `profile_svg_files.html`

**Thêm Public Profile Header**:
```html
<!-- Public Profile Header -->
<div class="public-profile-header" style="text-align: center; margin-bottom: 40px; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
    <!-- Avatar -->
    <div style="margin-bottom: 20px;">
        {% if avatar %}
            <img src="{{ url_for('static', filename='avatars/' ~ avatar) }}" alt="Avatar" style="width: 120px; height: 120px; border-radius: 50%; border: 4px solid rgba(255,255,255,0.3); object-fit: cover;">
        {% else %}
            <div style="width: 120px; height: 120px; border-radius: 50%; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 48px; font-weight: bold; border: 4px solid rgba(255,255,255,0.3);">
                {{ user_email[0].upper() if user_email else 'U' }}
            </div>
        {% endif %}
    </div>
    
    <!-- Username -->
    <h2 style="margin-bottom: 10px; font-size: 28px; font-weight: bold;">{{ username or user_email.split('@')[0] }}</h2>
    
    <!-- Follower count -->
    <div style="margin-bottom: 15px; font-size: 16px;">
        👥 {{ follower_count }} followers
    </div>
    
    <!-- Bio -->
    {% if bio %}
        <div style="margin-bottom: 20px; font-style: italic; font-size: 16px; opacity: 0.9;">
            {{ bio }}
        </div>
    {% endif %}
    
    <!-- Email -->
    <div style="margin-bottom: 20px; font-size: 14px; opacity: 0.8;">
        <strong>Email liên hệ:</strong> {{ user_email }}
    </div>
    
    <!-- Follow/Unfollow button -->
    {% if current_user.is_authenticated and not is_owner %}
        <div style="margin-top: 20px;">
            {% if is_followed %}
                <button type="button" class="btn btn-secondary" onclick="unfollowUser({{ user_id }})" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;">
                    👥 Bỏ theo dõi
                </button>
            {% else %}
                <button type="button" class="btn btn-primary" onclick="followUser({{ user_id }})" style="background: #1976d2; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;">
                    👥 Theo dõi
                </button>
            {% endif %}
        </div>
    {% endif %}
</div>
```

### 3. Thêm JavaScript cho Follow/Unfollow

**Thêm các hàm JavaScript**:
```javascript
// Follow/Unfollow functions
function followUser(userId) {
    fetch(`/follow/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button to unfollow
            const followBtn = event.target;
            followBtn.textContent = '👥 Bỏ theo dõi';
            followBtn.className = 'btn btn-secondary';
            followBtn.onclick = () => unfollowUser(userId);
            
            // Update follower count
            const followerCountElement = document.querySelector('.public-profile-header div[style*="👥"]');
            if (followerCountElement) {
                const currentCount = parseInt(followerCountElement.textContent.match(/\d+/)[0]);
                followerCountElement.textContent = `👥 ${currentCount + 1} followers`;
            }
            
            console.log('✅ Successfully followed user');
        } else {
            alert(data.error || 'Lỗi khi theo dõi user!');
        }
    })
    .catch(error => {
        console.error('Follow error:', error);
        alert('Lỗi khi theo dõi user!');
    });
}

function unfollowUser(userId) {
    fetch(`/unfollow/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button to follow
            const unfollowBtn = event.target;
            unfollowBtn.textContent = '👥 Theo dõi';
            unfollowBtn.className = 'btn btn-primary';
            unfollowBtn.onclick = () => followUser(userId);
            
            // Update follower count
            const followerCountElement = document.querySelector('.public-profile-header div[style*="👥"]');
            if (followerCountElement) {
                const currentCount = parseInt(followerCountElement.textContent.match(/\d+/)[0]);
                followerCountElement.textContent = `👥 ${Math.max(0, currentCount - 1)} followers`;
            }
            
            console.log('✅ Successfully unfollowed user');
        } else {
            alert(data.error || 'Lỗi khi bỏ theo dõi user!');
        }
    })
    .catch(error => {
        console.error('Unfollow error:', error);
        alert('Lỗi khi bỏ theo dõi user!');
    });
}
```

## Tính năng đã có

### 1. Header thông tin user
- ✅ Avatar (hoặc placeholder với chữ cái đầu email)
- ✅ Username
- ✅ Số lượng followers
- ✅ Bio/giới thiệu
- ✅ Email liên hệ
- ✅ Nút Follow/Unfollow (cho user đã đăng nhập)

### 2. Navigation
- ✅ Nút "🏠 Về trang chủ"
- ✅ Nút "👤 Hồ sơ" 
- ✅ Nút "⚙️ Cài đặt"
- ✅ Nút "📰 Bài đăng"
- ✅ Nút "🌙 Dark Mode"
- ✅ Thông tin user đang đăng nhập
- ✅ Nút "Đăng xuất"

### 3. Danh sách SVG files
- ✅ Hiển thị tất cả SVG files của user
- ✅ Thông tin: tên file, thời gian tạo, kích thước
- ✅ Nút like/unlike (cho user đã đăng nhập)
- ✅ Hiển thị số like (cho user chưa đăng nhập)
- ✅ Các nút tương tác: Tải ảnh, Facebook, Copy Link, Xem Code
- ✅ Nút xóa (chỉ cho owner)

### 4. Tính năng tương tác
- ✅ Follow/Unfollow user
- ✅ Like/Unlike SVG files
- ✅ Copy code TikZ
- ✅ Chia sẻ Facebook
- ✅ Copy link trực tiếp
- ✅ Xóa file (cho owner)

## Kết quả

Khi truy cập `https://tikz2svg.mathlib.io.vn/profile/5/svg-files` với tài khoản id=1, trang sẽ hiển thị:

1. **Header thông tin user id=5**:
   - Avatar của Quávui🐱
   - Tên: Quávui🐱
   - 2 followers
   - Bio: "Tôi thích Tikz và Latex"
   - Email: hiep.data.tk@gmail.com
   - Nút Follow/Unfollow (tùy thuộc vào trạng thái hiện tại)

2. **Danh sách SVG files**:
   - 5 files SVG với đầy đủ thông tin
   - Các nút tương tác cho từng file
   - Hiển thị số like và trạng thái like

3. **Navigation đầy đủ**:
   - Các nút điều hướng giữa các trang profile
   - Thông tin user đang đăng nhập (id=1)
   - Dark mode toggle

Trang này giờ đây có đầy đủ tính năng như trang profile cũ nhưng tập trung vào việc hiển thị SVG files. 