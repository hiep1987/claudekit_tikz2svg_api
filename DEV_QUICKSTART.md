# Hướng Dẫn Quy Trình Làm Việc

Tài liệu này giải thích quy trình phát triển và triển khai dự án `tikz2svg_api`.

## Quy Trình Phát Triển

- Thực hiện các thay đổi trong môi trường DEV.
- Kiểm tra kỹ lưỡng.
- Commit và đẩy các thay đổi lên GitHub.

## Triển Khai lên Production

Trước khi triển khai mã lên máy chủ production, hãy đảm bảo rằng tất cả các thay đổi của bạn đã được commit và đẩy từ môi trường DEV lên kho lưu trữ GitHub. Ví dụ:

```bash
git add <file>
git commit -m "Nội dung commit của bạn"
git push origin main
```

Điều này đảm bảo rằng máy chủ production sẽ kéo mã mới nhất khi triển khai.

Để triển khai mã mới nhất lên máy chủ production, chạy lệnh sau trên VPS:

```bash
sudo bash /var/www/tikz2svg_api/deploy.sh git@github.com:hiep1987/tikz2svg_api.git main
```

Script này sẽ kéo mã mới nhất từ kho lưu trữ và khởi động lại máy chủ production.

## Tính năng mới: Xác thực danh tính và Theo dõi

- Tài khoản cần "✔ Đã xác thực" để sử dụng tính năng Theo dõi người dùng khác.
- Người dùng chưa xác thực sẽ thấy nút Theo dõi bị vô hiệu hóa kèm nhắc chuyển tới trang xác thực.
- Luồng xác thực: `profile_settings` → nút "Xác thực tài khoản" → `profile_verification` → đồng ý điều khoản → nhận mã email → nhập mã 6 số → thành công.
- Badge xác thực hiển thị trên avatar (navbar) và trong `profile_settings.html`.

## Khôi Phục file/thư mục từ PROD về DEV

Nếu môi trường PROD đã được commit và đẩy lên GitHub, bạn có thể khôi phục một file hoặc thư mục từ PROD về DEV bằng lệnh sau:

```bash
git checkout origin/main -- path/to/your/file_or_folder
```

Ví dụ, để khôi phục một file:

```bash
git checkout origin/main -- src/main.py
```

Hoặc để khôi phục một thư mục:

```bash
git checkout origin/main -- src/utils/
```

**Nếu PROD đã commit & push lên GitHub, bạn chỉ cần trong DEV làm:**

```bash
cd ~/dev/tikz2svg_api
git fetch origin main
git checkout origin/main -- path/to/your/file.py
```

- `git fetch origin main` → lấy code mới nhất từ GitHub (PROD).
- `git checkout origin/main -- path/to/your/file.py` → lấy lại đúng file từ PROD mà không ảnh hưởng file khác.

Xong rồi bạn có thể chỉnh tiếp hoặc commit vào DEV:
```bash
git add path/to/your/file.py
git commit -m "Rollback file <filename> từ PROD"
```

**Lưu ý:** Lệnh này sẽ ghi đè phiên bản hiện tại trong DEV. Nếu bạn muốn phục hồi toàn bộ dự án để khớp chính xác với PROD, bạn có thể sử dụng:

```bash
git reset --hard origin/main
```

Tuy nhiên, hãy lưu ý rằng lệnh này sẽ xóa tất cả các thay đổi chưa được commit trong môi trường DEV của bạn.


## Xóa file (kể cả file có dấu cách trong tên)

Khi xóa file bằng git, nếu tên file chứa dấu cách, cần dùng dấu nháy hoặc escape dấu cách để tránh lỗi.

Ví dụ:

```bash
cd ~/dev/tikz2svg_api         # Vào thư mục dự án trên Mac
git fetch origin main         # Cập nhật code mới nhất từ GitHub (PROD)
git checkout main             # Đảm bảo đang ở branch main
git rm templates/profile.html    # Xóa file bình thường
git rm "udo systemctl restart tikz2svg_apiq"    # Xóa file có dấu cách (cách 1: dùng dấu nháy)
git rm udo\ systemctl\ restart\ tikz2svg_apiq   # Xóa file có dấu cách (cách 2: escape dấu cách)
git commit -m "Xóa file profile.html khỏi PROD"
git push origin main          # Đẩy thay đổi lên GitHub
```
##Ví dụ
Bạn nên chạy lại đúng với đường dẫn thực tế:
```bash
git add templates/index.html templates/profile_svg_files.html templates/profile_followed_posts.html templates/view_svg.html
git commit -m "Nav bar trên mobile"
git push origin main
```
Hoặc nhanh hơn (nếu bạn muốn add mọi thay đổi trong repo, không chỉ 3 file đó):
```bash
git add .
git commit -m "Cập nhật vị trí nút like"
git push origin main
```
##Chạy stagewise, mở thư mục trên Mac
```bash
rm -f ./stagewise.json
BROWSER=open npx stagewise@latesthay 
```

## Fix PROD Static Files (CSS/JS)

### Vấn đề thường gặp
Khi thêm file CSS/JS mới (như `file_card.css`, `file_card.js`), PROD có thể báo lỗi 404 vì:
- File tồn tại trong `/var/www/tikz2svg_api/current/static/css/`
- Nhưng PROD serve từ `/var/www/tikz2svg_api/shared/static/` (không có thư mục css/js)

### Giải pháp: Symlink (Khuyến nghị)

**Chạy lệnh sau trên PROD (chỉ làm 1 lần):**
```bash
# Tạo symlink từ shared đến current
ln -sf /var/www/tikz2svg_api/current/static/css /var/www/tikz2svg_api/shared/static/css
ln -sf /var/www/tikz2svg_api/current/static/js /var/www/tikz2svg_api/shared/static/js

# Kiểm tra symlink đã tạo
ls -la /var/www/tikz2svg_api/shared/static/
```

### Workflow tự động
1. **DEV**: Thay đổi CSS/JS → Commit & Push
2. **Deploy**: `deploy.sh` clone code mới về current
3. **Symlink tự động**: shared trỏ đến file mới trong current
4. **PROD**: CSS/JS tự động cập nhật

### Kiểm tra sau khi fix
- **URL test**: `https://tikz2svg.com/static/css/file_card.css`
- **Browser dev tools**: Network tab xem có 404 không
- **Functionality**: Test nút "Xem Code" có hoạt động không

### Lưu ý
- Symlink chỉ cần tạo 1 lần
- Tự động cập nhật khi deploy
- Không cần copy thủ công mỗi lần thay đổi