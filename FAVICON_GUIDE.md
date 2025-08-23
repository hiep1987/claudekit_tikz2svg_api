# Hướng dẫn Favicon cho TikZ to SVG

## Tổng quan
Website TikZ to SVG đã được cấu hình với đầy đủ favicon cho tất cả các thiết bị và trình duyệt. Favicon được tạo từ file `static/logo.svg` để đảm bảo chất lượng cao nhất.

## File nguồn
- **File gốc**: `static/logo.svg` (50KB)
- **Định dạng**: SVG (Vector Graphics)
- **Ưu điểm**: Không mất chất lượng khi resize, sắc nét ở mọi kích thước

## Các file favicon đã tạo

### 1. Favicon cơ bản
- `favicon.ico` (479 bytes) - Cho trình duyệt cũ, bao gồm 16x16, 32x32, 48x48px
- `favicon-16x16.png` (474 bytes) - Tab trình duyệt, bookmarks
- `favicon-32x32.png` (1,019 bytes) - Windows taskbar, desktop shortcuts
- `favicon-48x48.png` (1,538 bytes) - Windows Explorer

### 2. Apple Touch Icon
- `apple-touch-icon.png` (6,432 bytes) - iOS Safari, màn hình chính iPhone/iPad

### 3. Android Chrome
- `android-chrome-192x192.png` (6,864 bytes) - Android home screen
- `android-chrome-512x512.png` (20,929 bytes) - PWA, app stores

## Kích thước chuẩn theo thiết bị

| Thiết bị/Trình duyệt | Kích thước | File |
|---------------------|------------|------|
| Tab trình duyệt | 16x16px | favicon-16x16.png |
| Windows taskbar | 32x32px | favicon-32x32.png |
| Windows Explorer | 48x48px | favicon-48x48.png |
| iOS Safari | 180x180px | apple-touch-icon.png |
| Android Chrome | 192x192px | android-chrome-192x192.png |
| PWA/App Store | 512x512px | android-chrome-512x512.png |
| Trình duyệt cũ | 16x16, 32x32, 48x48px | favicon.ico |

## Cách thêm favicon vào HTML

```html
<!-- Favicon -->
<link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">
<link rel="icon" type="image/png" sizes="16x16" href="{{ url_for('static', filename='favicon-16x16.png') }}">
<link rel="icon" type="image/png" sizes="32x32" href="{{ url_for('static', filename='favicon-32x32.png') }}">
<link rel="icon" type="image/png" sizes="48x48" href="{{ url_for('static', filename='favicon-48x48.png') }}">
<link rel="apple-touch-icon" sizes="180x180" href="{{ url_for('static', filename='apple-touch-icon.png') }}">
<link rel="icon" type="image/png" sizes="192x192" href="{{ url_for('static', filename='android-chrome-192x192.png') }}">
<link rel="icon" type="image/png" sizes="512x512" href="{{ url_for('static', filename='android-chrome-512x512.png') }}">
<link rel="shortcut icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">
```

## Script tạo favicon

### Tạo từ file SVG (Khuyến nghị)
```bash
python create_favicons_from_svg.py
```

### Tạo từ file PNG (Cũ)
```bash
python create_favicons.py
python create_favicon_ico.py
```

## Yêu cầu thư viện
```bash
pip install Pillow cairosvg
```

## Lưu ý quan trọng

1. **Chất lượng SVG**: File SVG đảm bảo favicon sắc nét ở mọi kích thước
2. **Thứ tự ưu tiên**: Trình duyệt sẽ chọn favicon phù hợp nhất với kích thước cần thiết
3. **Tương thích**: favicon.ico đảm bảo tương thích với tất cả trình duyệt cũ
4. **Mobile**: apple-touch-icon và android-chrome icons tối ưu cho thiết bị di động
5. **PWA**: 512x512px icon cần thiết cho Progressive Web Apps

## Kiểm tra favicon

1. Mở website trong trình duyệt
2. Kiểm tra tab có hiển thị icon không
3. Thêm vào bookmarks để kiểm tra
4. Trên mobile, thêm vào màn hình chính
5. Sử dụng công cụ kiểm tra favicon online

## Cập nhật favicon

Để thay đổi favicon:
1. **Thay thế file SVG**: Cập nhật `static/logo.svg`
2. **Chạy script**: `python create_favicons_from_svg.py`
3. **Xóa cache**: Xóa cache trình duyệt để thấy thay đổi

## So sánh chất lượng

| Nguồn | Ưu điểm | Nhược điểm |
|-------|---------|------------|
| SVG | Không mất chất lượng, sắc nét | Cần thư viện cairosvg |
| PNG | Đơn giản, phổ biến | Có thể mất chất lượng khi resize |
| ICO | Tương thích tốt | Chỉ hỗ trợ kích thước cố định |
