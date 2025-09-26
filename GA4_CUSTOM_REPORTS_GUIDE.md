
# 📊 Google Analytics 4 - Hướng dẫn thiết lập lại custom reports cho tikz2svg.com

## 🎯 Measurement ID: G-DH7Q258GXF

## Hiện trạng
- Website hiện chỉ gửi pageview mặc định của GA4 (không còn event custom từ code).
- Các event TikZ render, copy, download, export, search... sẽ được thiết lập lại qua Google Tag Manager (GTM).

## Quy trình thiết lập lại event tracking qua GTM
1. Truy cập Google Tag Manager, tạo Container cho website.
2. Thêm Tag GA4 Configuration với Measurement ID: G-DH7Q258GXF.
3. Thiết lập các Trigger cho các event mong muốn (render, copy, download, export, search...)
4. Tạo Tag GA4 Event cho từng loại event, đặt tên và tham số phù hợp.
5. Kiểm tra lại bằng Debug mode của GTM và Google Analytics DebugView.

## Hướng dẫn tạo custom reports trên GA4
1. Vào Analytics → Explore → Blank report
2. Thêm dimensions: Event name, các custom parameter bạn đã thiết lập qua GTM
3. Thêm metrics: Event count, Users, v.v.
4. Tạo các báo cáo cho từng event (render, download, copy, search...)

## Lưu ý
- Sau khi xóa code gửi event, mọi tracking sẽ do GTM quản lý.
- Nếu cần tracking nâng cao, hãy thiết lập thêm các biến và trigger trong GTM.

## Kiểm tra kết quả
- Kiểm tra Network (filter collect) để xác nhận event gửi về GA4.
- Kiểm tra Realtime và Engagement → Events trong GA4 để xem dữ liệu.

## Tài liệu tham khảo
- [Google Tag Manager Documentation](https://support.google.com/tagmanager/)
- [GA4 Custom Events](https://support.google.com/analytics/answer/9267735)