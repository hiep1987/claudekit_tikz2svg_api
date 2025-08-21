# TIKZ2SVG DEV PROXY FIX

## Vấn đề
Script `tikz2svg-dev-proxy` sử dụng `rsync -avz --delete` để sync thư mục `static/` từ local lên VPS, gây ra việc xóa các file development local như `static/js/file_card.js` và `static/css/file_card.css`.

## Giải pháp
Đã fix script `tikz2svg-dev-proxy` để:
1. Backup các file development trước khi sync
2. Loại bỏ flag `--delete` từ rsync
3. Restore các file development sau khi sync

## Cách sử dụng
- Lệnh `tikz2svg-dev-proxy` giờ đây chạy script đã được fix
- File gốc được backup tại `/usr/local/bin/tikz2svg-dev-proxy.backup`

## Kiểm tra script
```bash
# Kiểm tra script hiện tại (đã fix)
cat /usr/local/bin/tikz2svg-dev-proxy

# So sánh với backup (script gốc)
cat /usr/local/bin/tikz2svg-dev-proxy.backup
```

---

# PROD STATIC FILES FIX

## Vấn đề
File CSS/JS tồn tại trong `/var/www/tikz2svg_api/current/static/css/file_card.css` nhưng PROD đang serve từ `/var/www/tikz2svg_api/shared/static/` (không có thư mục css/js).

**Cấu trúc hiện tại:**
```
Current (có file):
/var/www/tikz2svg_api/current/static/
├── css/
│   └── file_card.css ✅
└── js/
    └── file_card.js ✅

Shared (thiếu file):
/var/www/tikz2svg_api/shared/static/
├── *.svg files ✅
├── *.png files ✅
├── css/ ❌ (không có)
└── js/ ❌ (không có)
```

**Nguyên nhân:**
- Flask config: `app.config['UPLOAD_FOLDER'] = STATIC_ROOT` (shared/static)
- Static files: CSS/JS được tạo trong current/static nhưng không được copy sang shared
- URL mapping: Browser request `/static/css/file_card.css` nhưng file không có trong shared

## Giải pháp: Symlink (Khuyến nghị)

### Lệnh thực hiện trên PROD:
```bash
# Tạo symlink từ shared đến current (chỉ làm 1 lần)
ln -sf /var/www/tikz2svg_api/current/static/css /var/www/tikz2svg_api/shared/static/css
ln -sf /var/www/tikz2svg_api/current/static/js /var/www/tikz2svg_api/shared/static/js

# Kiểm tra symlink đã tạo
ls -la /var/www/tikz2svg_api/shared/static/
```

### Workflow với Symlink:
1. **Phát triển** trên MacBook → thay đổi CSS/JS
2. **Commit & Push** → lên GitHub
3. **Deploy** → deploy.sh clone code mới về current
4. **Symlink tự động** → shared trỏ đến file mới trong current
5. **Không cần làm gì thêm** → CSS/JS tự động cập nhật

### Ưu điểm của Symlink:
✅ **Tự động cập nhật** khi deploy  
✅ **Chỉ làm 1 lần**  
✅ **Luôn đồng bộ** với current  
✅ **Tiết kiệm dung lượng** (không duplicate files)  
✅ **Workflow tự động**  

### So sánh với Copy files:
❌ **Copy files**: Phải copy thủ công mỗi lần thay đổi, có thể quên, duplicate files, không đồng bộ  
✅ **Symlink**: Tự động, chỉ làm 1 lần, luôn đồng bộ, tiết kiệm dung lượng  

## Kiểm tra sau khi fix:
1. **URL test**: `https://tikz2svg.mathlib.io.vn/static/css/file_card.css`
2. **Browser dev tools**: Network tab xem có 404 không
3. **Functionality**: Test nút "Xem Code" có hoạt động không
