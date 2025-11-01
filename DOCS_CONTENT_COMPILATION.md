# 📚 TikZ2SVG API Documentation - Nội dung tổng hợp

> **File này tổng hợp tất cả nội dung đã phân tích để chuẩn bị tạo trang docs.html production**

## 📋 Mục lục

1. [🚀 Giới thiệu tổng quan](#1-giới-thiệu-tổng-quan)
2. [📋 Hướng dẫn bắt đầu nhanh](#2-hướng-dẫn-bắt-đầu-nhanh)  
3. [🔧 Chức năng biên dịch chi tiết](#3-chức-năng-biên-dịch-chi-tiết)
   - [3.3 🌏 Unicode & Multi-language Support](#33--unicode--multi-language-support-nâng-cao)
   - [3.4 📦 Manual Package Specification](#34--manual-package-specification-nâng-cao)
   - [3.5 📮 Yêu cầu thêm Package mới](#35--yêu-cầu-thêm-package-mới)
4. [🎨 Quản lý File SVG & Menu Actions](#4-quản-lý-file-svg--menu-actions)
5. [🔄 Chuyển đổi định dạng](#5-chuyển-đổi-định-dạng)
6. [💬 Hệ thống Comments](#6-hệ-thống-comments)
7. [👤 Profile & Tương tác xã hội](#7-profile--tương-tác-xã-hội)
8. [🛡️ Xác thực danh tính & Bảo mật](#8-xác-thực-danh-tính--bảo-mật)
9. [🔍 Tìm kiếm & Từ khóa](#9-tìm-kiếm--từ-khóa)
10. [🛠️ Xử lý lỗi & Troubleshooting](#10-xử-lý-lỗi--troubleshooting)
11. [💡 Tips & Best Practices](#11-tips--best-practices)

---

## 1. 🚀 Giới thiệu tổng quan

### Mô tả ứng dụng
**TikZ2SVG API** là một web application mạnh mẽ cho phép chuyển đổi TikZ LaTeX code thành các file SVG vector graphics chất lượng cao. Ứng dụng cung cấp giao diện thân thiện, hệ thống quản lý file, tương tác xã hội và API mở cho developers.

### Tính năng chính
- ✅ **Biên dịch TikZ real-time** với preview ngay lập tức
- ✅ **Auto-detection packages** thông minh và manual specification nâng cao
- ✅ **Yêu cầu Package mới** gửi đề xuất thêm LaTeX packages vào hệ thống
- ✅ **Unicode đầy đủ** hỗ trợ tiếng Việt, Trung, Nhật, Hàn (CJK) với LuaLaTeX + fontspec
- ✅ **Quản lý file SVG** với like/unlike, follow/unfollow system
- ✅ **Comments System** bình luận với LaTeX & TikZ code sharing
- ✅ **Chuyển đổi đa định dạng** SVG → PNG/JPEG với tùy chọn size, DPI
- ✅ **Hệ thống xác thực** email verification với mã 6 số
- ✅ **Tương tác xã hội** follow users, xem followed posts
- ✅ **Search & tagging** tìm kiếm SVG theo keywords
- ✅ **Email notifications** cho các hoạt động quan trọng
- ✅ **RESTful API** cho integration và automation
- ✅ **Responsive design** hoạt động mượt trên mọi device

### Công nghệ sử dụng
- **Backend**: Python Flask, MySQL, LuaLaTeX, pdf2svg
- **Frontend**: Bootstrap 5, JavaScript ES6+, CodeMirror
- **Email**: Zoho Mail SMTP với rate limiting
- **Security**: OAuth 2.0 (Google), CSRF protection, input validation
- **Performance**: Caching, async processing, image optimization

---

## 2. 📋 Hướng dẫn bắt đầu nhanh

### 2.1 Đăng ký tài khoản
1. **Truy cập trang chủ** tại `/`
2. **Nhấn "Đăng nhập"** → Chọn "Google OAuth"
3. **Authorize ứng dụng** với Google account của bạn
4. **Tự động tạo profile** với thông tin cơ bản từ Google

### 2.2 Chuyển đổi TikZ đầu tiên
1. **Nhập TikZ code** vào code editor (CodeMirror)
   ```latex
   \begin{tikzpicture}
   \draw (0,0) circle (1cm);
   \node at (0,0) {Hello World};
   \end{tikzpicture}
   ```
2. **Nhấn "Biên dịch"** → Hệ thống tự động phát hiện packages
3. **Xem preview SVG** ngay lập tức ở phần kết quả
4. **Tải về hoặc lưu** file SVG vào account

### 2.3 Lưu và quản lý file
1. **Nhấn "Lưu SVG"** sau khi biên dịch thành công
2. **Nhập keywords/tags** để dễ tìm kiếm sau này
3. **Xem file đã lưu** trong section "Các file SVG đã tạo"
4. **Sử dụng menu actions** trên mỗi file card để quản lý

---

## 3. 🔧 Chức năng biên dịch chi tiết

### 3.1 Trình biên dịch TikZ cơ bản
- **Input**: CodeMirror editor với syntax highlighting
- **Auto-detection**: Tự động phát hiện packages, TikZ libraries, PGFPlots libraries cần thiết
- **Compilation**: LuaLaTeX → PDF → svg (pdf2svg)
- **Preview**: Real-time SVG preview với zoom/pan
- **Error handling**: Chi tiết log lỗi LaTeX với line numbers

### 3.2 Auto-detection thông minh
Hệ thống tự động phát hiện các packages sau:

**LaTeX Packages cơ bản:**
- **Nền tảng**: `fontspec`, `polyglossia`, `xcolor`, `graphicx`, `geometry`, `setspace`
- **Toán học**: `amsmath`, `amssymb`, `amsfonts`, `mathtools`, `physics`, `siunitx`, `cancel`, `cases`
- **TikZ/PGF**: `tikz`, `pgfplots`, `tikz-3dplot`, `tkz-euclide`, `tkz-tab`, `pgf`, `pgfkeys`, `pgfornament`
- **Chuyên biệt**: `circuitikz`, `tikz-timing`, `tikz-cd`, `tikz-network`, `tikzpeople`, `tikzmark`
- **Bảng biểu**: `array`, `booktabs`, `multirow`, `colortbl`, `longtable`, `tabularx`

**TikZ Libraries:**
- **Tính toán**: `calc`, `math`, `positioning`, `arrows.meta`, `intersections`
- **Hình học**: `angles`, `quotes`, `shapes.geometric`, `shapes.symbols`, `shapes.arrows`, `shapes.multipart`
- **Trang trí**: `decorations.markings`, `decorations.pathreplacing`, `decorations.text`
- **Hiệu ứng**: `patterns`, `patterns.meta`, `shadings`, `hobby`, `spy`, `backgrounds`, `fadings`, `shadows`
- **Cấu trúc**: `fit`, `matrix`, `chains`, `automata`, `petri`, `mindmap`, `trees`
- **Nâng cao**: `graphs`, `graphdrawing`, `lindenmayersystems`, `external`
- **Dữ liệu**: `datavisualization`, `datavisualization.formats.files`, `datavisualization.formats.files.csv`, `datavisualization.formats.files.json`

**PGFPlots Libraries:**
- **Biểu đồ**: `polar`, `statistics`, `dateplot`, `fillbetween`, `colorbrewer`
- **Layout**: `groupplots`, `ternary`, `smithchart`, `units`

*Lưu ý: Đây là danh sách đầy đủ các packages được phép sử dụng. Hệ thống sẽ tự động phát hiện khi bạn sử dụng các lệnh như `\draw`, `\node`, `\addplot`, etc.*

### 3.3 🌏 Unicode & Multi-language Support (Nâng cao)

**Hệ thống hỗ trợ Unicode đầy đủ:**
- ✅ **Hệ thống hỗ trợ ĐẦY ĐỦ** chữ Trung/Nhật/Hàn (CJK characters)
- ✅ **Người dùng CHỈ CẦN thêm** `\setmainfont{STSong}` để hiển thị chữ CJK
- ✅ **KHÔNG CẦN sửa** `app.py` hay thêm package
- ✅ **LuaLaTeX + fontspec** = Unicode native support HOÀN HẢO

**Ví dụ sử dụng chữ Trung Quốc, Nhật Bản, Hàn Quốc:**

```latex
\setmainfont{STSong}  % Chỉ cần thêm dòng này!

\begin{tikzpicture}
  \node {中文: 富贵};                    % Tiếng Trung
  \node at (0,-1) {日本語: こんにちは};    % Tiếng Nhật
  \node at (0,-2) {한국어: 안녕하세요};    % Tiếng Hàn
\end{tikzpicture}
```

**Fonts CJK có sẵn trên hệ thống:**
- **STSong** (宋体) - ✅ Khuyến nghị cho văn bản thông thường
- **Heiti TC/SC** (黑体) - Chữ đậm, tiêu đề
- **Kaiti TC/SC** (楷书) - Thư pháp, chữ viết tay đẹp

**Lưu ý:**
- ❌ **KHÔNG dùng** `%!<CJKutf8>` (xung đột với LuaLaTeX + fontspec)
- ❌ **KHÔNG dùng** `\begin{CJK*}{UTF8}{gbsn}...\end{CJK*}` (cú pháp cũ)
- ✅ **CHỈ CẦN** `\setmainfont{STSong}` (hoặc font CJK khác)
- ✅ Tiếng Việt hoạt động **HOÀN HẢO** không cần font đặc biệt

**Xem chi tiết:** Tham khảo `USER_GUIDE_CJK_CHARACTERS.md` và `CHINESE_CHARACTERS_ANALYSIS.md`

---

### 3.4 📦 Manual Package Specification (Nâng cao)

**Khi nào cần sử dụng?**
- ✅ Hệ thống không tự động phát hiện package cần thiết  
- ✅ Packages ít phổ biến hoặc mới
- ✅ Cần kiểm soát chính xác packages được load

**Cú pháp**: `%!<commands>`

```latex
%!<\usepackage{pgfornament}>
\begin{tikzpicture}
\pgfornament[width=2cm]{15}
\end{tikzpicture}
```

**Multiple packages:**
```latex
%!<\usepackage{circuitikz},\usetikzlibrary{angles,quotes}>
\begin{tikzpicture}
\draw (0,0) to[R, o-o] (2,0);
\pic [draw, angle radius=5mm] {angle = A--B--C};
\end{tikzpicture}
```

**Packages được hỗ trợ:**
- **Nền tảng**: `fontspec`, `polyglossia`, `xcolor`, `graphicx`, `geometry`, `setspace`
- **Toán học**: `amsmath`, `amssymb`, `amsfonts`, `mathtools`, `physics`, `siunitx`, `cancel`, `cases`  
- **TikZ/PGF**: `tikz`, `pgfplots`, `tikz-3dplot`, `tkz-euclide`, `tkz-tab`, `pgf`, `pgfkeys`, `pgfornament`
- **Chuyên biệt**: `circuitikz`, `tikz-timing`, `tikz-cd`, `tikz-network`, `tikzpeople`, `tikzmark`
- **Bảng biểu**: `array`, `booktabs`, `multirow`, `colortbl`, `longtable`, `tabularx`

**TikZ Libraries được hỗ trợ:**
- `calc`, `math`, `positioning`, `arrows.meta`, `intersections`, `angles`, `quotes`
- `decorations.markings`, `decorations.pathreplacing`, `decorations.text`
- `patterns`, `patterns.meta`, `shadings`, `hobby`, `spy`, `backgrounds`
- `shapes.geometric`, `shapes.symbols`, `shapes.arrows`, `shapes.multipart`
- `fit`, `matrix`, `chains`, `automata`, `petri`, `mindmap`, `trees`
- `graphs`, `graphdrawing`, `lindenmayersystems`, `fadings`, `shadows`, `external`
- `datavisualization`, `datavisualization.formats.files.*`

**PGFPlots Libraries được hỗ trợ:**
- `polar`, `statistics`, `dateplot`, `fillbetween`, `colorbrewer`
- `groupplots`, `ternary`, `smithchart`, `units`

**Quy trình sử dụng:**
1. � **Viết TikZ code** như bình thường
2. 📦 **Thêm dòng `%!<...>`** ở đầu nếu cần package đặc biệt
3. ⚡ **Biên dịch** → Hệ thống tự động xử lý
4. ✅ **Xem kết quả SVG** như thường lệ

---

### 3.5 📮 Yêu cầu thêm Package mới

**Khi nào cần sử dụng?**
- ❓ Package bạn cần chưa có trong danh sách hỗ trợ
- 🆕 Muốn sử dụng package mới hoặc ít phổ biến
- 🤝 Đóng góp mở rộng thư viện cho cộng đồng

**Cách gửi yêu cầu:**

#### Bước 1: Truy cập trang Packages
1. **Vào trang chủ** → Click menu "📦 Packages"
2. **Hoặc truy cập trực tiếp**: `/packages`
3. **Xem danh sách packages** hiện có để đảm bảo package chưa tồn tại

#### Bước 2: Mở form yêu cầu
1. **Cuộn xuống** phần "Yêu cầu Package mới"
2. **Click nút** "🚀 Gửi yêu cầu Package"
3. **Chuyển đến** trang form yêu cầu `/packages/request`

#### Bước 3: Điền thông tin yêu cầu

**📦 Thông tin Package:**
- **Tên Package** (bắt buộc): Nhập tên chính xác như trong LaTeX documentation
  - Ví dụ: `amsmath`, `circuitikz`, `tikz-3dplot`, `siunitx`
  - Có thể là LaTeX package, TikZ library, hoặc PGFPlots library
  - Tối đa 100 ký tự

**💡 Lý do yêu cầu:**
- **Justification** (bắt buộc): Giải thích tại sao package này cần thiết
  - Tính năng nào còn thiếu hiện tại?
  - Package này giúp tạo loại diagram nào?
  - Tối đa 1000 ký tự
  
- **Ví dụ sử dụng** (tùy chọn): Mô tả cụ thể cách sử dụng
  - Ví dụ: "Tôi cần `circuitikz` để vẽ sơ đồ mạch điện tử với transistor, diode..."
  - Tối đa 800 ký tự

**📧 Thông tin liên hệ:**
- **Họ tên** (bắt buộc): Tên của bạn
  - Tự động điền nếu đã đăng nhập
  
- **Email** (bắt buộc): Email để nhận thông báo
  - Tự động điền nếu đã đăng nhập
  
- **Mức độ ưu tiên**: Chọn độ khẩn cấp
  - 🟢 **Thấp**: Có thể chờ đợi
  - 🟡 **Trung bình**: Cần trong vài tuần (mặc định)
  - 🟠 **Cao**: Cần gấp cho dự án
  - 🔴 **Khẩn cấp**: Cần ngay lập tức

#### Bước 4: Gửi yêu cầu
1. **Kiểm tra lại** thông tin đã nhập
2. **Click "🚀 Gửi yêu cầu"**
3. **Nhận thông báo** xác nhận đã gửi thành công

**Giới hạn Rate Limiting:**
- ⏱️ **Tối đa 3 yêu cầu/giờ** để tránh spam
- 📧 **Email thông báo** khi yêu cầu được xử lý

---

#### Quy trình xét duyệt

**Trạng thái yêu cầu:**
1. ⏳ **Pending**: Yêu cầu đang chờ xử lý
2. 🔍 **Under Review**: Admin đang xem xét
3. ✅ **Approved**: Đã phê duyệt, package sẽ được thêm
4. ❌ **Rejected**: Bị từ chối (có lý do kèm theo)

**Sau khi được phê duyệt:**
- **Active Package**: Có sẵn trong template mặc định (không cần `%!<...>`)
- **Manual Package**: Cần thêm `%!<package>` vào TikZ code để sử dụng

**Thời gian xử lý:**
- ⚡ **Yêu cầu khẩn cấp**: 1-2 ngày làm việc
- 🟠 **Ưu tiên cao**: 3-5 ngày làm việc
- 🟡 **Trung bình**: 1-2 tuần
- 🟢 **Thấp**: 2-4 tuần

---

#### Kiểm tra trùng lặp

**Hệ thống tự động kiểm tra:**
- ✅ **Package đã tồn tại**: Chuyển hướng đến trang `/packages` với thông báo
- ⏳ **Yêu cầu đang xử lý**: Thông báo yêu cầu trùng lặp, vui lòng đợi kết quả

**Lưu ý:**
- Kiểm tra kỹ danh sách packages hiện có trước khi gửi yêu cầu
- Mỗi package chỉ cần yêu cầu một lần
- Nếu nhiều người yêu cầu cùng package, admin sẽ ưu tiên xử lý

---

#### Tips để yêu cầu được chấp nhận

✅ **Nên làm:**
- Nhập tên package **chính xác** như trong documentation
- Giải thích **rõ ràng** lý do cần thiết
- Cung cấp **ví dụ cụ thể** về cách sử dụng
- Đặt **mức độ ưu tiên** phù hợp với nhu cầu thực tế
- Kiểm tra package **chưa tồn tại** trong hệ thống

❌ **Không nên:**
- Gửi yêu cầu cho package đã có sẵn
- Viết lý do quá ngắn gọn hoặc không rõ ràng
- Spam nhiều yêu cầu giống nhau
- Đặt mức ưu tiên "Khẩn cấp" khi không thực sự cần
- Nhập sai tên package

---

#### Xem danh sách Packages hiện có

**Truy cập trang `/packages` để xem:**
- 📦 **Active Packages**: Packages có sẵn trong template mặc định
- 🔧 **Manual Packages**: Packages cần khai báo `%!<...>` để sử dụng
- 📊 **Thống kê**: Tổng số packages được hỗ trợ
- 🔍 **Tìm kiếm**: Tìm package theo tên hoặc loại

**Phân loại Packages:**
- **LaTeX Packages**: `\usepackage{...}` - amsmath, geometry, xcolor, etc.
- **TikZ Libraries**: `\usetikzlibrary{...}` - calc, positioning, arrows.meta, etc.
- **PGFPlots Libraries**: `\usepgfplotslibrary{...}` - polar, statistics, fillbetween, etc.

---

## 4. 🎨 Quản lý File SVG & Menu Actions

### 4.1 Giao diện File Card
Mỗi SVG file được hiển thị dưới dạng "thẻ" (card) bao gồm:
- **📷 Ảnh preview**: Hiển thị SVG đã tạo
- **👤 Thông tin tác giả**: Tên người tạo và thời gian
- **❤️ Nút Like**: Thể hiện sự yêu thích
- **⋯ Menu actions**: Các hành động có thể thực hiện
- **💻 Code section**: TikZ code (có thể ẩn/hiện)

### 4.2 Cách sử dụng Menu Actions
**Trên máy tính (Desktop):**
- **Di chuột qua file card** → Menu actions tự động xuất hiện
- **Click vào button** để thực hiện hành động

**Trên điện thoại (Mobile):**
- **Tap 1 lần** vào nút menu (⋯) → Hiện menu actions  
- **Tap 2 lần** vào action button → Thực hiện hành động

### 4.3 Các hành động có thể thực hiện

| Hành động | Mô tả | Cần đăng nhập? | Ghi chú |
|-----------|-------|----------------|---------|
| **📥 Tải ảnh** | Xem chi tiết và tải file SVG về máy | ❌ | Chuyển đến trang xem chi tiết |
| **📘 Facebook** | Copy link để chia sẻ lên Facebook | ❌ | Link sẽ được copy vào clipboard |  
| **🔗 Copy Link** | Copy đường dẫn trực tiếp đến file SVG | ❌ | Xuất hiện thông báo "Đã copy!" |
| **💻 Xem Code** | Hiển thị/ẩn mã TikZ đã sử dụng | ✅ | Chỉ user đã đăng nhập |
| **🗑️ Xóa file** | Xóa file SVG khỏi hệ thống | ✅ | Chỉ chủ sở hữu file |

**Lưu ý:** 
- ✅ = Cần đăng nhập
- ❌ = Không cần đăng nhập
- User chưa đăng nhập sẽ thấy nút bị mờ và có thông báo yêu cầu đăng nhập

### 4.4 Xem và copy mã TikZ

**Xem mã TikZ:**
1. **Đăng nhập** vào tài khoản (bắt buộc)
2. **Click "💻 Xem Code"** trên file card
3. **Mã TikZ xuất hiện** bên dưới với syntax highlighting
4. **Click lại** để ẩn mã

**Copy mã TikZ:**
1. **Mở code section** (như trên)
2. **Click nút "📋 Copy"** góc trên bên phải  
3. **Mã được copy** vào clipboard
4. **Paste** vào editor yêu thích để sử dụng lại

**Lợi ích:**
- 📚 **Học hỏi**: Xem cách người khác viết TikZ code
- 🔄 **Tái sử dụng**: Copy code để làm base cho project mới
- 🎓 **Tham khảo**: Học syntax và techniques mới

### 4.5 Hệ thống Like (Yêu thích)

**Cách sử dụng:**
1. **Đăng nhập** tài khoản (bắt buộc)
2. **Click vào nút ❤️** trên file card
3. **Trái tim chuyển màu đỏ** → Đã like
4. **Click lại để unlike** → Trái tim về màu xám

**Tính năng:**
- 💖 **Thể hiện sở thích**: Like những SVG bạn yêu thích
- 📊 **Thống kê phổ biến**: Xem SVG nào được like nhiều nhất  
- 🔄 **Cập nhật real-time**: Số like thay đổi ngay lập tức
- 👀 **Không cần đăng nhập để xem**: Ai cũng thấy được số like

**Lưu ý:**
- User **chưa đăng nhập** thấy nút like **bị mờ**
- Click vào sẽ **yêu cầu đăng nhập**
- **Không giới hạn** số lượng file có thể like

### 4.5.1 Xem tất cả người đã like (modal danh sách)

Bạn có thể **click vào số lượt like** (bên cạnh nút ❤️) trên mỗi file SVG để xem **danh sách tất cả người đã like** file đó.

- Một **modal** sẽ hiện ra, hiển thị avatar, username và thời gian like của từng người.
- Danh sách này hỗ trợ **phân trang** (20 người/lần), có nút "Xem thêm" để tải thêm.
- Có thể click vào username để truy cập profile của người đó.
- Modal này hoạt động tốt trên cả desktop và mobile.

**Lưu ý:**
- Nếu file chưa có ai like, modal sẽ hiển thị thông báo phù hợp.
- Nếu bạn chưa đăng nhập, vẫn xem được danh sách này (trừ khi file đặt ở chế độ riêng tư).

Tính năng này giúp bạn dễ dàng khám phá cộng đồng, xem ai đã yêu thích các tác phẩm SVG của mình hoặc của người khác.

### 4.6 Thông tin hiển thị trên File Card

**Thông tin tác giả:**
- 👤 **Tên người tạo**: Click để xem profile của họ
- 🕐 **Thời gian tạo**: "2 giờ trước", "3 ngày trước", etc.

**Thông tin file:**
- 🖼️ **Preview SVG**: Hình ảnh xem trước chất lượng cao
- ❤️ **Số lượt like**: Hiển thị độ phổ biến
- 🏷️ **Tags/Keywords**: Từ khóa để tìm kiếm (nếu có)

**Tương tác:**
- **Click vào tên tác giả** → Xem profile và các SVG khác của họ  
- **Click vào preview** → Xem chi tiết file
- **Hover trên thời gian** → Xem thời gian chính xác

---

## 5. 🔄 Chuyển đổi định dạng

### 5.1 Định dạng được hỗ trợ
- **SVG → PNG**: Chuyển đổi raster với tùy chỉnh chiều rộng/cao/DPI
- **SVG → JPEG**: Chuyển đổi chất lượng cao với tùy chọn nén
- **Xử lý hàng loạt**: Chuyển đổi nhiều file cùng lúc  

### 5.2 Cách chuyển đổi định dạng

**Bước 1: Tạo SVG**
1. Biên dịch TikZ code thành công
2. Lưu SVG vào tài khoản (nếu muốn)

**Bước 2: Chuyển đổi**  
1. **Click "📥 Tải ảnh"** trên file card
2. **Chọn định dạng**: PNG hoặc JPEG
3. **Tùy chỉnh kích thước** (optional):
   - Width (chiều rộng)
   - Height (chiều cao)  
   - DPI (độ phân giải, max 2000)
4. **Click "Convert"** để bắt đầu
5. **Tải file** về máy khi hoàn tất

### 5.3 Giới hạn kích thước & Kiểm tra
- **Tối đa pixels**: 60MP tổng cộng (60,000,000 pixels)
- **Tối đa DPI**: 2000 DPI  
- **Kiểm tra**: Hệ thống kiểm tra trước khi chuyển đổi
- **Thông báo lỗi**: Phản hồi rõ ràng khi vượt giới hạn

### 5.4 Quy trình chuyển đổi
**Các bước hệ thống thực hiện:**
1. **Kiểm tra file**: Đảm bảo file tồn tại và định dạng hỗ trợ
2. **Tính toán kích thước**: Kiểm tra không vượt giới hạn 60MP
3. **Chuyển đổi chất lượng cao**: Sử dụng công nghệ rasterization tiên tiến
4. **Tối ưu hóa**: Giảm dung lượng file mà vẫn giữ chất lượng
5. **Hoàn tất**: Cung cấp link tải với thông tin chi tiết file

---

## 6. 💬 Hệ thống Comments

### 6.1 Giới thiệu Comments System

**Comments System** cho phép người dùng trao đổi, thảo luận về TikZ code trực tiếp trên trang xem SVG. Hệ thống hỗ trợ **LaTeX math**, **TikZ code sharing**, và **nested replies** để tạo môi trường học tập và chia sẻ kiến thức phong phú.

**Tính năng chính:**
- ✅ **Bình luận & trả lời** với cấu trúc thread (parent → replies)
- ✅ **LaTeX math support** inline `$x^2$` và display `$$\int f(x) dx$$`
- ✅ **TikZ code blocks** với syntax `\code{...}` và copy button
- ✅ **Real-time preview** MathJax rendering khi gõ
- ✅ **Like/Unlike** comments để đánh giá chất lượng
- ✅ **Edit & Delete** comments của chính mình
- ✅ **Pagination** tự động load thêm comments
- ✅ **Glass morphism UI** đẹp mắt, responsive

---

### 6.2 Cách sử dụng Comments

#### Đăng bình luận mới

**Yêu cầu:** Phải đăng nhập

**Bước thực hiện:**
1. **Truy cập trang SVG** bất kỳ (ví dụ: `/view_svg.html?filename=example.svg`)
2. **Cuộn xuống phần Comments** (ở dưới caption)
3. **Nhập nội dung** vào textarea:
   - Text thông thường
   - LaTeX math: `$x^2 + y^2 = r^2$`
   - TikZ code: `\code{\tikz \draw (0,0) circle (1cm);}`
4. **Xem preview** real-time với MathJax rendering
5. **Click "Gửi bình luận"** để đăng

**Giới hạn:**
- **5000 ký tự** tối đa cho mỗi comment
- **Rate limiting** để tránh spam

---

#### Trả lời comment (Replies)

**Cách trả lời:**
1. **Click nút "Trả lời"** ở comment bất kỳ
2. **Form trả lời xuất hiện** dưới comment đó
3. **Nhập nội dung** với full LaTeX & TikZ support
4. **Xem preview** real-time
5. **Click "Gửi"** hoặc "Hủy"

**Đặc điểm:**
- Replies **lồng vào trong** parent comment
- Hiển thị **avatar** và **username** của người trả lời
- **Badge** verified nếu tài khoản đã xác thực

---

### 6.3 LaTeX Math Support

#### Inline math (trong dòng)

**Syntax:** `$công thức$`

**Ví dụ:**
```
Công thức $E = mc^2$ rất nổi tiếng.
```

**Hiển thị:** Công thức $E = mc^2$ rất nổi tiếng.

---

#### Display math (hiển thị riêng)

**Syntax:** `$$công thức$$`

**Ví dụ:**
```
Tích phân:
$$\int_0^\infty e^{-x} dx = 1$$
```

**Hiển thị:** Tích phân trên một dòng riêng, to hơn, căn giữa

---

### 6.4 TikZ Code Blocks

#### Cú pháp chia sẻ TikZ code

**Syntax:** `\code{...TikZ code...}`

**Ví dụ đơn giản:**
```
Vẽ circle đơn giản:

\code{
\tikz \draw (0,0) circle (1cm);
}
```

**Hiển thị:**
```
┌─────────────────────────────────┐
│ TikZ Code                  📋  │ ← Header với copy button
├─────────────────────────────────┤
│ \tikz \draw (0,0) circle (1cm);│ ← Code formatted
└─────────────────────────────────┘
```

---

#### Ví dụ phức tạp với nested braces

```
\code{
\begin{tikzpicture}
  \draw (-2,0) -- (2,0);
  \filldraw [red] (0,0) circle (4pt);
  \draw (-2,-2) .. controls (0,0) .. (2,-2);
  \draw (-2,2) .. controls (-1,0) and (1,0) .. (2,2);
\end{tikzpicture}
}
```

**Đặc điểm:**
- ✅ **Hỗ trợ nested braces** không giới hạn độ sâu
- ✅ **Copy button** một click copy toàn bộ code
- ✅ **Visual feedback** 📋 → ✅ khi copy thành công
- ✅ **Light professional design** dễ đọc
- ✅ **Syntax preservation** giữ nguyên format

---

#### Copy TikZ Code

**Cách copy:**
1. **Hover vào code block** → Border chuyển màu xanh
2. **Click nút 📋** ở góc phải header
3. **Icon đổi thành ✅** (2 giây) → Code đã copy!
4. **Paste** vào editor để sử dụng

**Lợi ích:**
- Không cần select + copy thủ công
- Code được copy **chính xác 100%**
- Tiết kiệm thời gian, giảm lỗi

---

### 6.5 Like & Unlike Comments

#### Cách like comment

**Bước thực hiện:**
1. **Đọc comment** hữu ích hoặc hay
2. **Click nút 👍** ở footer comment
3. **Button chuyển màu xanh** (liked state)
4. **Số like tăng lên** +1

**Cách unlike:**
- **Click lại nút 👍** đã liked
- Button trở về trạng thái mặc định
- Số like giảm -1

**Đặc điểm:**
- **Optimistic UI**: Cập nhật ngay lập tức
- **API validation**: Xác thực từ server
- **Visual feedback**: Màu xanh đậm khi liked
- **Like count** hiển thị số người like

---

### 6.6 Edit & Delete Comments

#### Edit comment

**Yêu cầu:** Comment của chính mình

**Bước thực hiện:**
1. **Click nút "✏️ Sửa"** ở comment của bạn
2. **Textarea hiện ra** với nội dung cũ
3. **Chỉnh sửa nội dung** (vẫn support LaTeX & TikZ)
4. **Click "Lưu"** hoặc "Hủy"
5. **Label "(đã chỉnh sửa)"** hiển thị sau timestamp

**Lưu ý:**
- Không thể edit comment của người khác
- Edit được **unlimited lần**
- Timestamp không đổi, chỉ thêm edited label

---

#### Delete comment

**Yêu cầu:** Comment của chính mình

**Bước thực hiện:**
1. **Click nút "🗑️ Xóa"** ở comment của bạn
2. **Confirm dialog** xuất hiện
3. **Confirm xóa** → Comment biến mất
4. **Comment count** tự động cập nhật

**Lưu ý:**
- **Xóa vĩnh viễn**, không thể khôi phục
- Xóa parent comment sẽ **xóa tất cả replies**
- Comment count bao gồm cả replies bị xóa

---

### 6.7 Pagination & Loading

#### Auto-load more comments

**Cách hoạt động:**
- Mỗi trang load **20 comments** (top-level)
- **Button "Tải thêm"** xuất hiện nếu còn comments
- Click button → Load 20 comments tiếp theo
- **Smooth scrolling** và loading skeleton

**Navigation:**
- **Trang hiện tại** / **Tổng số trang** hiển thị
- **Nút Previous/Next** để chuyển trang
- **Disable** khi ở trang đầu/cuối

---

### 6.8 UI/UX Features

#### Glass Morphism Design

**Đặc điểm:**
- **Backdrop blur** effect sang trọng
- **Transparent background** với glass texture
- **Subtle shadows** tăng chiều sâu
- **Hover effects** smooth transitions

**Consistency:**
- Match với **image caption section**
- Sử dụng **design system variables**
- **WCAG AAA** contrast ratios

---

#### Mobile Responsive

**Tối ưu cho mobile:**
- **Font size** giảm phù hợp (11px → 14px)
- **Touch-friendly buttons** padding lớn hơn
- **Avatar** hiển thị rõ ràng
- **Code blocks** horizontal scroll smooth

**Breakpoints:**
- **Mobile**: <768px - Compact, vertical layout
- **Tablet**: 768px-992px - Balanced
- **Desktop**: ≥992px - Full features

---

#### Avatar & Verified Badge

**Avatar display:**
- **User đã upload**: Hiển thị ảnh avatar
- **Chưa upload**: Fallback circle với chữ cái đầu
- **Gradient background**: Blue → Purple
- **Rounded 50%**: Hình tròn đẹp mắt

**Verified badge:**
- Icon **✓ xanh** bên cạnh username
- Chỉ hiện nếu **đã xác thực email**
- **Tooltip** "Tài khoản đã xác thực"

---

### 6.9 Real-time Preview

**Khi gõ comment:**
1. **Textarea input** → Trigger preview update (debounced 300ms)
2. **HTML escaping** để tránh XSS
3. **Parse LaTeX** `$...$` và `$$...$$`
4. **Parse TikZ code** `\code{...}`
5. **MathJax rendering** công thức toán
6. **Line breaks** conversion `\n` → `<br>`

**Hiển thị preview:**
- **"Preview (với MathJax):"** title
- Content render **y hệt** như comment đã gửi
- Update **real-time** khi gõ
- **Placeholder** khi chưa nhập gì

---

### 6.10 Comment Count Badge

**Hiển thị:**
```
💬 Bình luận (15)
            ↑
    Total comments + replies
```

**Cách đếm:**
- **Top-level comments** + **All replies** = Total
- Align với **industry standard** (YouTube, Facebook, Reddit)
- **Auto-update** khi thêm/xóa comment

**Lợi ích:**
- User biết **tổng engagement**
- **Social proof** cao hơn
- **Transparent** về activity

---

### 6.11 Security & Validation

#### XSS Protection

**Comments System sử dụng:**
1. **HTML escaping** tất cả user input
2. **Double escaping** cho TikZ code:
   - Escape → Extract code → Re-escape
3. **No eval()** - Code chỉ display, không execute
4. **CSP headers** restrict script sources

**Test XSS:**
```
Input:  \code{<script>alert('XSS')</script>}
Output: &lt;script&gt;...&lt;/script&gt; ✅ Safe!
```

---

#### Input Validation

**Server-side:**
- **Max length**: 5000 characters
- **Required fields**: comment_text, svg_filename
- **Sanitization**: Strip HTML tags (trừ preview)
- **Rate limiting**: Tránh spam

**Client-side:**
- **Character counter**: 0/5000
- **Warning color** khi gần limit (>4500)
- **Disable submit** khi rỗng
- **Trim whitespace** before send

---

### 6.12 FAQ Comments

**Q: Tại sao comment của tôi không hiện?**
**A:** Kiểm tra:
- Đã đăng nhập chưa?
- Content có vượt 5000 ký tự không?
- Có lỗi network không? (Check console)

**Q: Tôi có thể edit comment sau khi gửi không?**
**A:** Có, click nút "✏️ Sửa" ở comment của bạn, edit và "Lưu".

**Q: Comment bị xóa có thể khôi phục không?**
**A:** Không, xóa là vĩnh viễn. Hãy cẩn thận trước khi xóa.

**Q: Làm sao để copy TikZ code từ comment?**
**A:** Click nút 📋 ở góc phải code block, code sẽ được copy vào clipboard.

**Q: Comment có hỗ trợ markdown không?**
**A:** Không, nhưng hỗ trợ LaTeX math ($...$) và TikZ code (\code{...}).

**Q: Tôi có thể reply reply không?**
**A:** Hiện tại chỉ support 1 cấp (parent → replies). Reply to reply sẽ cùng cấp với reply đầu tiên.

---

## 7. 👤 Profile & Tương tác xã hội

### 7.1 Quản lý Profile
- **Tải ảnh đại diện**: Hỗ trợ nhiều định dạng (PNG, JPG, GIF)
- **Chỉnh sửa tiểu sử**: Soạn thảo rich text với hỗ trợ markdown
- **Trang cài đặt**: `/profile/{user_id}/settings`
- **Profile công khai**: `/profile/{user_id}` có thể xem bởi người khác

### 7.2 Follow/Unfollow System

#### Yêu cầu để Follow
- **✅ Tài khoản đã xác thực**: Cần xác thực email trước khi follow người khác
- **🚫 Không thể tự follow**: Không thể follow chính mình
- **👥 Theo dõi lẫn nhau**: Có thể follow và được follow lại

### 7.3 Xem bài đăng từ người đã Follow
**Cách sử dụng:**
1. **Đăng nhập** và **xác thực tài khoản** (bắt buộc)
2. **Follow các user** mà bạn quan tâm
3. **Xem feed** các SVG mới từ những người bạn follow
4. **Sắp xếp theo thời gian** (mới nhất hiển thị trước)
5. **Tự động tải thêm** khi cuộn xuống dưới

### 7.4 Tương tác xã hội
**Các hoạt động có thể thực hiện:**
- **❤️ Like/Unlike**: Thể hiện sở thích với SVG của người khác
- **👀 Xem profile**: Click vào tên tác giả để xem profile và các SVG khác
- **👥 Follow từ profile**: Follow người dùng ngay từ trang profile của họ
- **📋 Theo dõi hoạt động**: Xem timeline các SVG mới từ người bạn follow

---

## 8. 🛡️ Xác thực danh tính & Bảo mật

### 7.1 Tại sao cần xác thực?
- **🔒 Bảo mật cao hơn**: Xác nhận email thật
- **👥 Unlock features**: Follow/Unfollow yêu cầu verified account
- **✅ Uy tín**: Badge "Đã xác thực" tăng trust
- **🚀 Priority access**: Features mới ưu tiên cho verified users

### 8.2 Quy trình xác thực 5 bước

#### Bước 1: Kiểm tra trạng thái
- Vào **Profile Settings** → Xem verification status
- **⚠️ Chưa xác thực**: Hiện nút "Xác thực tài khoản"  
- **✅ Đã xác thực**: Hiện verification badge

#### Bước 2: Bắt đầu xác thực
- Nhấn **"Xác thực tài khoản"** → `/profile/verification`
- Đọc **Terms & Conditions** về usage policy
- Nhấn **"Tôi đồng ý"** để continue

#### Bước 3: Nhận email xác thực  
- Hệ thống gửi **6-digit code** đến registered email
- Check **Inbox và Spam folder**
- Mã có hiệu lực **24 giờ**

#### Bước 4: Nhập mã xác thực
- Enter chính xác **6 digits** từ email
- **Max 5 attempts** (security limit)
- Nhấn **"Xác thực"** để complete

#### Bước 5: Verification thành công
- Status chuyển thành **"✅ Đã xác thực"**
- **Badge icon** xuất hiện trên profile  
- **Unlock Follow/Unfollow** functionality

### 7.3 Tính năng bảo mật
- **Giới hạn thử**: Tối đa 5 lần nhập mã xác thực
- **Hết hạn mã**: Mã xác thực có hiệu lực 24 giờ
- **Tự động dọn dẹp**: Mã hết hạn được xóa tự động
- **Mã hóa dữ liệu**: Thông tin xác thực được bảo vệ
- **Theo dõi hoạt động**: Ghi lại các lần xác thực để bảo mật

### 7.4 Lợi ích khi xác thực
**🔓 Tính năng mở khóa:**
- 👥 Follow/Unfollow người dùng khác
- 📋 Xem bài đăng từ người đã follow  
- 🔔 Thông báo email cho các hoạt động
- ⭐ Hỗ trợ ưu tiên

**🛡️ Bảo mật nâng cao:**
- Khôi phục tài khoản qua email đã xác thực
- Thông báo bảo mật cho hoạt động bất thường  
- Xác thực hai yếu tố (sắp ra mắt)

---

## 9. 🔍 Tìm kiếm & Từ khóa

### 8.1 Tính năng tìm kiếm mới (2024)
**Enhanced Search Bar với hai chế độ:**

🔹 **Tìm theo từ khóa** (mặc định)
- **Placeholder**: "Tìm theo từ khóa..."
- **Auto-suggestions**: Hiển thị gợi ý từ keywords database
- **Tìm kiếm**: SVG files có keywords matching
- **Real-time**: Suggestions xuất hiện khi gõ

🔹 **Tìm theo tên tài khoản**
- **Placeholder**: "Tìm theo tên tài khoản..."
- **No suggestions**: Tìm kiếm trực tiếp, không có dropdown
- **Tìm kiếm**: SVG files của username matching
- **Fuzzy search**: Hỗ trợ tìm kiếm gần đúng

### 8.2 Cách sử dụng Search Bar
**Bước 1: Chọn loại tìm kiếm**
1. **Click button "Từ khóa"** (active mặc định) - màu xanh
2. **Hoặc click "Tên tài khoản"** để chuyển mode

**Bước 2: Nhập và tìm kiếm**
- **Mode từ khóa**: Gõ từ khóa → chọn từ suggestions → Enter
- **Mode tên tài khoản**: Gõ username → Enter (không có suggestions)

**Bước 3: Xem kết quả**
- **Hiển thị loại tìm kiếm**: "Từ khóa: 'abc'" hoặc "Tên tài khoản: 'user123'"
- **Grid layout**: Tất cả SVG files matching
- **File cards**: Preview, likes, creator info

### 8.3 Backend API
**Endpoints:**
```
GET /search?q={query}&type=keywords    # Tìm theo keywords
GET /search?q={query}&type=username    # Tìm theo username
GET /api/keywords/search?q={query}     # API suggestions
```

**Database queries:**
- **Keywords**: Join `svg_image` → `svg_image_keyword` → `keyword`
- **Username**: Join `svg_image` → `user` on `username LIKE %query%`

### 8.4 Hệ thống từ khóa
**Gắn thẻ cho SVG:**
- **Khi lưu SVG**: Nhập keywords để dễ tìm kiếm sau
- **Gợi ý tự động**: Hệ thống gợi ý từ keywords có sẵn
- **Không phân biệt hoa thường**: "Circle" và "circle" được coi như nhau

### 8.5 UI/UX Design
**Glass Morphism Design:**
- **Custom buttons**: Thay thế radio buttons để tránh conflicts
- **Active state**: Button được chọn có background xanh
- **Hover effects**: Smooth transitions
- **Responsive**: Mobile-friendly button sizing

**Technical Implementation:**
- **CSS Foundation System**: Sử dụng design variables
- **JavaScript**: Custom button state management
- **No radio button conflicts**: Stable behavior across browsers

---

## 10. 🛠️ Xử lý lỗi & Troubleshooting

### 9.1 Lỗi biên dịch LaTeX

#### Thiếu Packages
```
Error: ! LaTeX Error: File `pgfornament.sty' not found.
```
**Solutions:**
- Use manual package specification: `%!<\usepackage{pgfornament}>`
- Check package name spelling
- Verify package is in allowlist

#### Lỗi cú pháp
```
Error: ! Missing $ inserted.
```
**Solutions:**
- Check TikZ code syntax
- Ensure proper math mode delimiters
- Validate bracket matching

#### Vấn đề bộ nhớ/Timeout  
```
Error: Compilation timeout after 30 seconds
```
**Solutions:**
- Simplify complex diagrams
- Reduce number of plot points
- Optimize loops và calculations

### 9.2 Vấn đề Upload/Lưu file

#### Giới hạn dung lượng file
- **SVG files**: Max 10MB
- **Converted images**: Max 60MP (60M pixels)
- **DPI limit**: Max 2000 DPI

#### Vấn đề mạng
```
Error: Failed to save file - network timeout
```  
**Solutions:**
- Check internet connection
- Try again after short delay
- Clear browser cache

#### Lỗi phân quyền
```  
Error: Access denied - insufficient permissions
```
**Solutions:**
- Ensure logged in
- Check file ownership
- Verify account verification status

### 9.3 Vấn đề xác thực

#### Vấn đề Google OAuth
- **Redirect URI mismatch**: Check OAuth settings
- **Scope permissions**: Ensure email scope approved
- **Session timeout**: Re-login after extended inactivity

#### Vấn đề xác thực
- **Email not received**: Check spam folder, wait 2-3 minutes
- **Code expired**: Request new verification code
- **Max attempts**: Wait 24 hours for reset

### 9.4 Tương thích trình duyệt
- **Modern browsers**: Chrome 80+, Firefox 75+, Safari 13+
- **JavaScript required**: Enable JavaScript for full functionality  
- **Cookies required**: Enable cookies for authentication
- **Local storage**: Required for user preferences

### 9.5 Vấn đề hiệu suất
- **Slow loading**: Check network connection, try refresh
- **Memory usage**: Close unused tabs, restart browser
- **Mobile performance**: Use Chrome/Safari for best experience

---

## 11. 💡 Tips & Best Practices

### 10.1 TikZ Code Examples Library

#### Basic Shapes
```latex
% Circle with label
\begin{tikzpicture}
\draw (0,0) circle (1cm);
\node at (0,0) {Center};
\end{tikzpicture}

% Rectangle with rounded corners
\begin{tikzpicture}
\draw[rounded corners=5pt] (0,0) rectangle (3,2);
\end{tikzpicture}
```

#### Mathematical Diagrams
```latex
% Function plot
\begin{tikzpicture}
\begin{axis}[domain=-2:2]
\addplot {x^2};
\end{axis}
\end{tikzpicture}

% Geometric construction
%!<\usetikzlibrary{angles,quotes}>
\begin{tikzpicture}
\coordinate (A) at (0,0);
\coordinate (B) at (3,0);  
\coordinate (C) at (1,2);
\draw (A) -- (B) -- (C) -- cycle;
\pic [draw, angle radius=8mm, "$\alpha$"] {angle = B--A--C};
\end{tikzpicture}
```

#### Circuit Diagrams
```latex  
%!<\usepackage{circuitikz}>
\begin{tikzpicture}
\draw (0,0) to[R=1<\ohm>] (2,0)
      to[L=1<\henry>] (4,0)
      to[C=1<\farad>] (6,0);
\end{tikzpicture}
```

### 10.2 Sử dụng trên nhiều thiết bị

#### Trải nghiệm trên Desktop
- **Hover hiệu ứng**: Di chuột để xem menu actions
- **Transitions mượt**: Chuyển động tự nhiên khi tương tác
- **Visual feedback**: Phản hồi trực quan khi click nút
- **Loading states**: Hiện placeholder khi đang tải

#### Trải nghiệm trên Mobile
- **2-tap logic**: Tap để hiện menu, tap lần 2 để thực hiện
- **Touch-friendly**: Nút to đủ cho ngón tay
- **Responsive**: Tự động điều chỉnh theo màn hình
- **Smooth scroll**: Cuộn mượt mà trên touch screen

---

## 11. ❓ Câu hỏi thường gặp (FAQ)

### Q: Tôi có thể sử dụng miễn phí không?
**A:** Có, TikZ2SVG hoàn toàn miễn phí cho tất cả tính năng cơ bản. Bạn chỉ cần đăng nhập bằng Google để sử dụng đầy đủ tính năng.

### Q: File SVG có bị xóa tự động không?
**A:** Không, file SVG của bạn được lưu trữ vĩnh viễn sau khi tạo. Chỉ có chủ sở hữu mới có thể xóa file của mình.

### Q: Tôi có thể tạo bao nhiêu file SVG mỗi ngày?
**A:** Hiện tại giới hạn 10 file SVG mới mỗi ngày cho mỗi tài khoản để đảm bảo chất lượng dịch vụ.

### Q: Tại sao tôi không thể follow người khác?
**A:** Để follow người khác, bạn cần xác thực tài khoản qua email. Vào Profile Settings → Xác thực tài khoản để mở khóa tính năng này.

### Q: File TikZ của tôi không biên dịch được, phải làm sao?
**A:** Kiểm tra:
- Cú pháp TikZ có đúng không
- Có thiếu packages không (sử dụng `%!<\usepackage{...}>` nếu cần)
- Xem log lỗi chi tiết để khắc phục

### Q: Tôi có thể sử dụng TikZ code của người khác không?
**A:** Có, nhưng chỉ nên sử dụng để học hỏi và tham khảo. Hãy tôn trọng tác giả và không copy hoàn toàn mà không ghi nguồn.

### Q: Làm sao để file SVG của tôi được nhiều người thấy?
**A:**
- Sử dụng keywords/tags phù hợp khi lưu file
- Tạo nội dung chất lượng và hữu ích
- Tương tác với cộng đồng bằng cách like và follow người khác

### Q: Tôi quên mật khẩu thì sao?
**A:** TikZ2SVG sử dụng Google OAuth, bạn chỉ cần đăng nhập bằng tài khoản Google của mình. Không cần nhớ mật khẩu riêng.

### Q: Làm sao để hiển thị chữ Trung Quốc, Nhật Bản, Hàn Quốc trong TikZ?
**A:** Hệ thống hỗ trợ ĐẦY ĐỦ Unicode với LuaLaTeX + fontspec. Bạn chỉ cần thêm dòng `\setmainfont{STSong}` vào đầu code TikZ:
```latex
\setmainfont{STSong}
\begin{tikzpicture}
  \node {中文: 富贵};  % Tiếng Trung hiển thị HOÀN HẢO
\end{tikzpicture}
```
**Lưu ý:** KHÔNG dùng `%!<CJKutf8>` vì không tương thích với LuaLaTeX. Xem chi tiết tại section "3.3 Unicode & Multi-language Support".

### Q: Tại sao chữ Trung/Nhật/Hàn hiện thành hộp vuông `��`?
**A:** Bạn chưa chọn font hỗ trợ CJK. Thêm `\setmainfont{STSong}` (hoặc font CJK khác) vào đầu code TikZ. Font mặc định (Latin Modern) không có ký tự CJK.

### Q: Làm sao để yêu cầu thêm package mới vào hệ thống?
**A:** Truy cập trang `/packages` → Cuộn xuống phần "Yêu cầu Package mới" → Click "Gửi yêu cầu Package" → Điền form với thông tin package cần thiết. Bạn cần cung cấp tên package, lý do yêu cầu, và thông tin liên hệ. Hệ thống giới hạn 3 yêu cầu/giờ.

### Q: Mất bao lâu để yêu cầu package được xử lý?
**A:** Tùy vào mức độ ưu tiên:
- **Khẩn cấp**: 1-2 ngày làm việc
- **Cao**: 3-5 ngày làm việc  
- **Trung bình**: 1-2 tuần
- **Thấp**: 2-4 tuần

Bạn sẽ nhận email thông báo khi yêu cầu được xử lý.

### Q: Package tôi yêu cầu có chắc chắn được thêm vào không?
**A:** Không chắc chắn. Admin sẽ xem xét dựa trên:
- Tính hợp lệ và an toàn của package
- Mức độ cần thiết cho cộng đồng
- Khả năng tương thích với hệ thống
- Số lượng người yêu cầu

Nếu bị từ chối, bạn sẽ nhận được email giải thích lý do.

---

## 12. 🎥 Hướng dẫn trực quan

### Video tutorials (sắp ra mắt):
- **"Tạo SVG đầu tiên trong 3 phút"** - Hướng dẫn từ A-Z cho người mới
- **"Sử dụng advanced TikZ features"** - Packages, libraries và tricks nâng cao
- **"Mobile tips & tricks"** - Tối ưu trải nghiệm trên điện thoại
- **"Quản lý profile và tương tác xã hội"** - Follow, like và xây dựng cộng đồng

### Screenshots quan trọng:
📸 **Giao diện chính** - Overview toàn bộ layout với annotations
📸 **Menu actions comparison** - Desktop hover vs Mobile 2-tap
📸 **Verification process** - Step-by-step với email screenshots
📸 **Search functionality** - Keywords vs Username modes
📸 **File conversion** - SVG to PNG/JPEG options

### Interactive demos:
🎮 **TikZ Playground** - Thử nghiệm code mẫu ngay trên browser
🎮 **Package Explorer** - Khám phá packages được hỗ trợ với examples
🎮 **Mobile Simulator** - Test giao diện mobile trên desktop

---

## 13. 👥 Quy tắc cộng đồng

### Nội dung được khuyến khích:
- ✅ **Chia sẻ TikZ code hữu ích** - Giúp cộng đồng học hỏi
- ✅ **Tạo tutorials và examples** - Hướng dẫn các techniques mới
- ✅ **Giúp đỡ người dùng mới** - Trả lời câu hỏi, chia sẻ kinh nghiệm
- ✅ **Feedback xây dựng** - Góp ý cải thiện tính năng
- ✅ **Nội dung giáo dục** - Mathematical diagrams, scientific illustrations

### Nội dung không được phép:
- ❌ **Spam hoặc nội dung không phù hợp** - Quảng cáo, nội dung nhạy cảm
- ❌ **Vi phạm bản quyền** - Copy code/design của người khác không ghi nguồn
- ❌ **Tài khoản fake** - Giả mạo danh tính, tạo nhiều tài khoản
- ❌ **Harassment** - Quấy rối, bình luận tiêu cực về người khác
- ❌ **Malicious code** - TikZ code có thể gây hại hệ thống

### Báo cáo vi phạm:
📧 **Email**: admin@tikz2svg.com
📝 **Thông tin cần cung cấp**: Link file, mô tả vi phạm, screenshots (nếu có)
⏱️ **Thời gian xử lý**: 24-48 giờ cho các báo cáo hợp lệ

---

## 14. 🆕 Tính năng mới & Cập nhật

### Tháng 11/2024 - Package Management System:
- ✨ **Package Request System**: Gửi yêu cầu thêm LaTeX packages mới vào hệ thống
- ✨ **Package Listing Page**: Xem danh sách đầy đủ packages được hỗ trợ (Active & Manual)
- ✨ **Request Status Tracking**: Theo dõi trạng thái yêu cầu (Pending, Under Review, Approved, Rejected)
- 🔧 **Rate Limiting**: Giới hạn 3 yêu cầu/giờ để tránh spam
- 🔧 **Email Notifications**: Thông báo khi yêu cầu được xử lý

### Tháng 10/2024 - Major Update:
- ✨ **Likes Modal Enhancement**: Xem danh sách đầy đủ người đã like với pagination
- ✨ **Real-time Like Updates**: Like count và preview text cập nhật ngay lập tức
- ✨ **Enhanced Search Bar**: Tìm kiếm theo keywords và username với auto-suggestions
- 🔧 **Mobile UX Improvements**: Tối ưu 2-tap logic và touch responsiveness
- 🔧 **Timezone Fix**: Hiển thị thời gian chính xác theo múi giờ Việt Nam

### Tháng 9/2024:
- ✨ **Profile Verification System**: Xác thực tài khoản qua email với 6-digit code
- ✨ **Follow/Unfollow Feature**: Theo dõi người dùng và xem bài đăng từ người đã follow
- 🔧 **CSS Foundation Migration**: Cải thiện performance và consistency
- 🔧 **Glass Morphism UI**: Giao diện hiện đại với hiệu ứng transparency

### Tháng 8/2024:
- ✨ **Advanced Package Detection**: Tự động phát hiện 50+ LaTeX packages
- ✨ **Manual Package Specification**: Syntax `%!<\usepackage{...}>` cho packages đặc biệt
- ✨ **File Conversion System**: SVG → PNG/JPEG với tùy chỉnh DPI và kích thước
- 🔧 **Rate Limiting**: Bảo vệ server khỏi spam và abuse

### Sắp ra mắt (Q4 2024):
- 🔔 **Push Notifications**: Thông báo real-time cho likes, follows và comments
- 📱 **Progressive Web App (PWA)**: Cài đặt như app native trên mobile
- 🤝 **Collaboration Features**: Chia sẻ và co-work trên TikZ projects
- 📊 **Analytics Dashboard**: Thống kê views, likes và engagement cho creators
- 🎨 **Theme Customization**: Dark mode và custom color schemes
- 💬 **Comment System**: Bình luận và thảo luận trên từng SVG file

### Roadmap 2025:
- 🔗 **API v2**: RESTful API công khai cho third-party integrations
- 🏆 **Gamification**: Badges, achievements và leaderboards
- 📚 **Learning Hub**: Interactive TikZ tutorials và challenges
- 🌐 **Internationalization**: Hỗ trợ đa ngôn ngữ (English, Japanese, Korean)

---

## 15. 🌐 Tương thích trình duyệt

### Được hỗ trợ đầy đủ tính năng:
- ✅ **Chrome 80+** (recommended) - Hiệu suất tốt nhất, tất cả tính năng hoạt động
- ✅ **Firefox 75+** - Hỗ trợ tốt, một số animation có thể chậm hơn
- ✅ **Safari 13+** - Tương thích tốt trên macOS và iOS
- ✅ **Edge 80+** - Chromium-based, hiệu suất tương đương Chrome

### Hỗ trợ hạn chế:
- ⚠️ **Chrome/Firefox cũ hơn** - Một số tính năng CSS modern có thể không hoạt động
- ⚠️ **Safari 12 và cũ hơn** - Glass morphism effects có thể không hiển thị
- ⚠️ **Mobile browsers cũ** - Touch events có thể không responsive

### Không được hỗ trợ:
- ❌ **Internet Explorer** (tất cả versions) - Không tương thích với ES6+ và modern CSS
- ❌ **Opera Mini** - JavaScript bị hạn chế, không thể biên dịch TikZ
- ❌ **UC Browser** - WebView engine cũ, performance kém

### Yêu cầu Browser Settings:
- 🍪 **Cookies enabled** - Bắt buộc cho authentication và user preferences
- 📜 **JavaScript enabled** - Cần thiết cho tất cả interactive features
- 💾 **Local Storage** - Lưu trữ temporary data và user settings
- 🔒 **HTTPS support** - Required cho Google OAuth và secure features

### Performance Tips:
- 🚀 **Chrome recommended**: Tốc độ biên dịch nhanh nhất
- 🧹 **Clear cache định kỳ**: Tránh conflicts khi có updates
- 🔄 **Update browser**: Luôn dùng version mới nhất để có trải nghiệm tốt nhất
- 📱 **Mobile**: Safari (iOS) và Chrome (Android) cho performance tối ưu

---

**🎯 Tài liệu này bao gồm tất cả hướng dẫn sử dụng TikZ2SVG web application để giúp người dùng tận dụng tối đa các tính năng có sẵn và hiểu rõ cách thức hoạt động của hệ thống.**