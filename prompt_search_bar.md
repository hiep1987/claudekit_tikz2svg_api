**Prompt phát triển Search Bar:**

1. Phân tích yêu cầu:
   - Giữ chức năng tìm kiếm theo từ khóa hiện có.
   - Bổ sung tùy chọn tìm kiếm theo tên tài khoản.

2. Thiết kế UI/UX:
   - Thêm radio button cho phép chọn kiểu tìm kiếm: "Từ khóa" hoặc "Tên tài khoản".
   - Khi người dùng chọn radio button, Search Bar sẽ thay đổi logic tìm kiếm tương ứng.
   - Đảm bảo giao diện trực quan, dễ sử dụng.

3. Cập nhật logic backend:
   - Nếu chọn "Từ khóa": sử dụng logic tìm kiếm hiện tại.
   - Nếu chọn "Tên tài khoản": truy vấn dữ liệu từ bảng `user`, trường `username` trong CSDL.
     - Ví dụ truy vấn:
       ```sql
       SELECT * FROM user WHERE username LIKE '%<tên_tài_khoản>%';
       ```

4. Kiểm thử:
   - Đảm bảo cả hai chế độ tìm kiếm hoạt động chính xác.
   - Kiểm tra trường hợp không tìm thấy kết quả, hiển thị thông báo phù hợp.

5. Triển khai & tài liệu hóa:
   - Cập nhật tài liệu hướng dẫn sử dụng Search Bar.
   - Đảm bảo tính năng mới được kiểm thử trên các trình duyệt phổ biến.
