# Google Tag Manager Setup Note

**Ngày thực hiện:** 27/09/2025

## Nội dung

Đã thêm mã Google Tag Manager vào website:

- Đoạn script GTM được thêm vào phần `<head>` ở vị trí cao nhất:

```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-N6J4LQJ4');</script>
<!-- End Google Tag Manager -->
```

- Đoạn noscript GTM được thêm ngay sau thẻ mở `<body>`:

```html
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-N6J4LQJ4"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
```

## Ý nghĩa
- Cho phép quản lý tracking, event, conversion... qua Google Tag Manager thay vì code tay.
- Dễ dàng chỉnh sửa, thêm mới các event mà không cần deploy lại code.

## Lưu ý
- Đảm bảo mã GTM luôn nằm ở vị trí cao nhất trong `<head>` và ngay sau thẻ `<body>`.
- Kiểm tra hoạt động của GTM bằng Tag Assistant hoặc DebugView của Google Analytics.
