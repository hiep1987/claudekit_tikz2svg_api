# Hệ thống Quản lý Packages TikZ2SVG

## 📋 Tổng quan

Hệ thống TikZ2SVG đã được cải tiến với khả năng quản lý LaTeX packages thông minh, hỗ trợ **2 cách** để thêm packages:

1. **🔄 Tự động phát hiện** (mặc định)
2. **✏️ Chỉ định thủ công** bằng cú pháp `%!<...>`

## 🎯 Tính năng chính

### ✅ Tự động phát hiện Packages
- Hệ thống tự động quét code TikZ và phát hiện packages cần thiết
- Hỗ trợ 34 packages, 37 TikZ libraries, 9 PGFPlots libraries
- An toàn với hệ thống allowlist

### ✅ Chỉ định thủ công
- Cú pháp `%!<...>` để chỉ định packages thủ công
- Hỗ trợ packages, TikZ libraries, PGFPlots libraries
- Kết hợp linh hoạt với hệ thống tự động

### ✅ Bảo mật
- Hệ thống allowlist nghiêm ngặt
- Chỉ cho phép packages đã được kiểm tra
- Loại bỏ packages không hợp lệ

### ✅ Hiệu suất
- Chỉ load packages cần thiết
- Loại bỏ trùng lặp tự động
- Template LaTeX tối ưu

## 🚀 Cách sử dụng

### Phương pháp 1: Tự động phát hiện (Khuyến nghị)

Chỉ cần gõ code TikZ bình thường, hệ thống sẽ tự động phát hiện:

```latex
\begin{tikzpicture}
\pgfornament[width=2cm]{1}
\pgfornament[width=2cm,color=red]{2}
\end{tikzpicture}
```

→ Hệ thống tự động thêm `\usepackage{pgfornament}`

### Phương pháp 2: Chỉ định thủ công

Sử dụng cú pháp `%!<...>` khi cần thiết:

```latex
%!<\usepackage{pgfornament}>
\begin{tikzpicture}
\path [rotate=210,postaction={decoration={text along path,text format delimiters={|}{|}, text={|\Huge| 
					LABORATORY OF MATHEMATICS AND ITS APPLICATIONS {\pgfornament[scale=.4,ydelta=-9pt]{15}} UNIVERSITY OF MEDEA{\pgfornament[scale=.4,ydelta=-9pt]{15}}},
				text align=fit to path,reverse path}, decorate}] 
		circle[radius=7.2cm] ;
\end{tikzpicture}
```

## 📚 Danh sách Packages hỗ trợ

### 📦 Packages (34 packages)
- **Nền tảng**: `fontspec`, `polyglossia`, `xcolor`, `graphicx`, `geometry`, `setspace`
- **Toán học**: `amsmath`, `amssymb`, `amsfonts`, `mathtools`, `physics`, `siunitx`, `cancel`, `cases`
- **TikZ/PGF**: `tikz`, `pgfplots`, `tikz-3dplot`, `tkz-euclide`, `tkz-tab`, `pgf`, `pgfkeys`, `pgfornament`
- **Chuyên biệt**: `circuitikz`, `tikz-timing`, `tikz-cd`, `tikz-network`, `tikzpeople`, `tikzmark`
- **Bổ sung**: `array`, `booktabs`, `multirow`, `colortbl`, `longtable`, `tabularx`

### 🎨 TikZ Libraries (37 libraries)
- **Cơ bản**: `calc`, `math`, `positioning`, `arrows.meta`, `intersections`, `angles`, `quotes`
- **Trang trí**: `decorations.markings`, `decorations.pathreplacing`, `decorations.text`
- **Hình dạng**: `patterns`, `patterns.meta`, `shadings`, `shapes.geometric`, `shapes.symbols`, `shapes.arrows`
- **Nâng cao**: `hobby`, `spy`, `backgrounds`, `fit`, `matrix`, `chains`, `automata`, `petri`, `mindmap`, `trees`, `graphs`, `shadows`, `fadings`

### 📊 PGFPlots Libraries (9 libraries)
- `polar`, `statistics`, `dateplot`, `fillbetween`, `colorbrewer`, `groupplots`, `ternary`, `smithchart`, `units`

## 🔧 Ví dụ thực tế

### Ví dụ 1: Sử dụng pgfornament
```latex
%!<\usepackage{pgfornament}>
\begin{tikzpicture}
\pgfornament[width=2cm]{1}
\pgfornament[width=2cm,color=red]{2}
\pgfornament[width=2cm,color=blue]{3}
\end{tikzpicture}
```

### Ví dụ 2: Sử dụng circuitikz
```latex
%!<\usepackage{circuitikz}>
\begin{tikzpicture}
\draw (0,0) to[R, o-o] (2,0);
\draw (2,0) to[L, o-o] (4,0);
\draw (4,0) to[C, o-o] (6,0);
\end{tikzpicture}
```

### Ví dụ 3: Sử dụng physics package
```latex
%!<\usepackage{physics}>
\begin{tikzpicture}
\node at (0,0) {$\vec{F} = m\vec{a}$};
\node at (2,0) {$\abs{x} = \norm{\vec{v}}$};
\end{tikzpicture}
```

### Ví dụ 3b: Sử dụng circuitikz với package options (⭐ MỚI)

**Hỗ trợ package options**: Sử dụng `[siunitx]` để có thể dùng cú pháp `1<\ohm>`, `1<\henry>`, `1<\farad>` trong circuitikz:

```latex
%!<\usepackage[siunitx]{circuitikz}>
\begin{tikzpicture}
\draw (0,0) to[R=1<\ohm>] (2,0)
          to[L=1<\henry>] (4,0)
          to[C=1<\farad>] (6,0);
\end{tikzpicture}
```

### Ví dụ 4: Kết hợp nhiều packages
```latex
%!<\usetikzlibrary{angles,quotes},\usetikzlibrary{positioning},\usepackage{tikz}>
\begin{tikzpicture}[scale=3]
\coordinate (A) at (1,0);
\coordinate (B) at (0,0);
\coordinate (C) at (30:1cm);
\draw (A) -- (B) -- (C)
pic [draw=green!50!black, fill=green!20, angle radius=9mm,
"$\alpha$"] {angle = A--B--C};
\end{tikzpicture}
```

## ⚠️ Lưu ý quan trọng

### Cú pháp chính xác:
- ✅ `%!<\usepackage{package_name}>`
- ✅ `%!<\usepackage[options]{package_name}>` (hỗ trợ package options)
- ❌ `%!< \usepackage{package_name} >` (không có khoảng trắng thừa)
- ❌ `%!<usepackage{package_name}>` (thiếu dấu `\`)

### Bảo mật:
- Packages không trong allowlist sẽ bị bỏ qua
- Hệ thống sẽ sử dụng template cơ bản nếu có lỗi
- Các dòng `%!<...>` sẽ bị loại bỏ khỏi output cuối cùng

## 🔍 Cách hoạt động

1. **Phân tích code TikZ**
   - Tìm các dòng `%!<...>` (chỉ định thủ công)
   - Quét toàn bộ code để phát hiện commands (tự động)

2. **Trích xuất packages**
   - Phân tích nội dung trong `%!<...>`
   - Phát hiện commands cần thiết

3. **Kết hợp và loại bỏ trùng lặp**
   - Gộp packages thủ công + tự động
   - Loại bỏ packages trùng lặp

4. **Tạo template LaTeX**
   - Thêm packages vào phần `EXTRA AUTO-INJECT`
   - Loại bỏ các dòng `%!<...>` khỏi TikZ code

5. **Biên dịch**
   - Tạo file `.tex` hoàn chỉnh
   - Biên dịch bằng `lualatex`
   - Chuyển đổi PDF → SVG

## 🚀 Lợi ích

1. **Linh hoạt**: Hỗ trợ cả tự động và thủ công
2. **An toàn**: Hệ thống allowlist nghiêm ngặt
3. **Dễ sử dụng**: Cú pháp đơn giản, rõ ràng
4. **Hiệu suất**: Chỉ load packages cần thiết
5. **Tương thích**: Hoạt động với code TikZ hiện tại
6. **Sạch sẽ**: Cú pháp không xuất hiện trong output

## 📖 Tài liệu chi tiết

- **Hướng dẫn chi tiết**: [MANUAL_PACKAGE_SPECIFICATION.md](MANUAL_PACKAGE_SPECIFICATION.md)
- **Cải tiến hệ thống**: [PACKAGE_DETECTION_IMPROVEMENT.md](PACKAGE_DETECTION_IMPROVEMENT.md)

## 🔧 Troubleshooting

### Lỗi thường gặp:

1. **Package không được thêm vào**:
   - Kiểm tra tên package có đúng không
   - Kiểm tra package có trong danh sách cho phép không

2. **Cú pháp không được nhận diện**:
   - Đảm bảo dòng bắt đầu chính xác bằng `%!<`
   - Kiểm tra không có khoảng trắng thừa

3. **Lỗi biên dịch**:
   - Kiểm tra package có được cài đặt trên hệ thống không
   - Xem log lỗi để biết chi tiết

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra cú pháp theo hướng dẫn
2. Xem log lỗi chi tiết
3. Thử với package khác để xác định vấn đề
4. Liên hệ hỗ trợ nếu cần thiết

---

**Lưu ý**: Luôn ưu tiên sử dụng hệ thống tự động phát hiện trước khi dùng chỉ định thủ công. Tính năng chỉ định thủ công được thiết kế để bổ sung, không thay thế hệ thống tự động.
