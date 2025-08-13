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
git rm templates/test.html    # Xóa file bình thường
git rm "udo systemctl restart tikz2svg_apiq"    # Xóa file có dấu cách (cách 1: dùng dấu nháy)
git rm udo\ systemctl\ restart\ tikz2svg_apiq   # Xóa file có dấu cách (cách 2: escape dấu cách)
git commit -m "Xóa file templates/test.html khỏi PROD"
git push origin main          # Đẩy thay đổi lên GitHub
```