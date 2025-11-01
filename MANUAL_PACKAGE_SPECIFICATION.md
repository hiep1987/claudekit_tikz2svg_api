# Hướng dẫn sử dụng tính năng chỉ định Packages thủ công

## 📋 Tổng quan

Hệ thống TikZ2SVG hỗ trợ **2 cách** để thêm LaTeX packages và libraries:

1. **Tự động phát hiện** (mặc định)
2. **Chỉ định thủ công** bằng cú pháp `%!<...>`

## 🎯 Khi nào sử dụng chỉ định thủ công?

Sử dụng cú pháp `%!<...>` khi:

- ✅ Hệ thống không tự động phát hiện được package cần thiết
- ✅ Bạn muốn đảm bảo package được load trước khi biên dịch
- ✅ Sử dụng packages ít phổ biến hoặc mới
- ✅ Cần kiểm soát chính xác packages được sử dụng

## 📝 Cú pháp cơ bản

### Cấu trúc chung:
```latex
%!<command1,command2,command3>
\begin{tikzpicture}
% ... code TikZ của bạn ...
\end{tikzpicture}
```

### Các loại command hỗ trợ:

| Loại | Cú pháp | Ví dụ |
|------|---------|-------|
| Package | `\usepackage{package_name}` | `\usepackage{pgfornament}` |
| TikZ Library | `\usetikzlibrary{library_name}` | `\usetikzlibrary{angles}` |
| PGFPlots Library | `\usepgfplotslibrary{library_name}` | `\usepgfplotslibrary{statistics}` |

## 🔧 Ví dụ sử dụng

### Ví dụ 1: Chỉ định package đơn lẻ

```latex
%!<\usepackage{pgfornament}>
\begin{tikzpicture}
\path [rotate=210,postaction={decoration={text along path,text format delimiters={|}{|}, text={|\Huge| 
					LABORATORY OF MATHEMATICS AND ITS APPLICATIONS {\pgfornament[scale=.4,ydelta=-9pt]{15}} UNIVERSITY OF MEDEA{\pgfornament[scale=.4,ydelta=-9pt]{15}}},
				text align=fit to path,reverse path}, decorate}] 
		circle[radius=7.2cm] ;
\end{tikzpicture}
```

**Kết quả:** Hệ thống sẽ tự động thêm `\usepackage{pgfornament}` vào template.

### Ví dụ 2: Chỉ định nhiều packages và libraries

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

**Kết quả:** Hệ thống sẽ thêm:
- `\usetikzlibrary{angles}`
- `\usetikzlibrary{quotes}`
- `\usetikzlibrary{positioning}`
- `\usepackage{tikz}`

### Ví dụ 3: Kết hợp tự động và thủ công

```latex
%!<\usepackage{pgfornament}>
\begin{tikzpicture}
\pgfornament[width=2cm]{1}
\pgfornament[width=2cm,color=red]{2}
\pgfornament[width=2cm,color=blue]{3}
\end{tikzpicture}
```

**Kết quả:** 
- Tự động phát hiện: `pgfornament` (từ `\pgfornament{...}`)
- Thủ công: `pgfornament` (từ `%!<...>`)
- Hệ thống sẽ loại bỏ trùng lặp và chỉ thêm một lần

## 📚 Danh sách packages được hỗ trợ

### Packages cơ bản:
- `fontspec`, `polyglossia`, `xcolor`, `graphicx`, `geometry`, `setspace`
- `amsmath`, `amssymb`, `amsfonts`, `mathtools`, `physics`, `siunitx`, `cancel`, `cases`
- `tikz`, `pgfplots`, `tikz-3dplot`, `tkz-euclide`, `tkz-tab`, `pgf`, `pgfkeys`, `pgfornament`
- `circuitikz`, `tikz-timing`, `tikz-cd`, `tikz-network`, `tikzpeople`, `tikzmark`
- `array`, `booktabs`, `multirow`, `colortbl`, `longtable`, `tabularx`

### TikZ Libraries:
- `calc`, `math`, `positioning`, `arrows.meta`, `intersections`, `angles`, `quotes`
- `decorations.markings`, `decorations.pathreplacing`, `decorations.text`
- `patterns`, `patterns.meta`, `shadings`, `hobby`, `spy`, `backgrounds`
- `shapes.geometric`, `shapes.symbols`, `shapes.arrows`, `shapes.multipart`
- `fit`, `matrix`, `chains`, `automata`, `petri`, `mindmap`, `trees`
- `graphs`, `graphdrawing`, `lindenmayersystems`, `fadings`, `shadows`
- `external`, `datavisualization`, `datavisualization.formats.files`
- `datavisualization.formats.files.csv`, `datavisualization.formats.files.json`

### PGFPlots Libraries:
- `polar`, `statistics`, `dateplot`, `fillbetween`, `colorbrewer`
- `groupplots`, `ternary`, `smithchart`, `units`

## ⚠️ Lưu ý quan trọng

### 1. Cú pháp chính xác:
- ✅ `%!<\usepackage{package_name}>`
- ✅ `%!<\usepackage[options]{package_name}>` (với package options)
- ❌ `%!< \usepackage{package_name} >` (không có khoảng trắng thừa)
- ❌ `%!<usepackage{package_name}>` (thiếu dấu `\`)

### 2. Tên package hợp lệ:
- ✅ Chỉ chứa chữ cái, số, dấu gạch ngang, dấu chấm, dấu gạch dưới
- ❌ Không chứa ký tự đặc biệt khác

### 3. Packages không được phép:
- Nếu package không có trong danh sách cho phép, hệ thống sẽ bỏ qua
- Chỉ sử dụng template cơ bản để tránh lỗi bảo mật

### 4. Loại bỏ cú pháp:
- Các dòng `%!<...>` sẽ bị loại bỏ khỏi TikZ code cuối cùng
- Chỉ được sử dụng để chỉ định packages, không ảnh hưởng đến output

## 🔍 Cách hoạt động

### Quy trình xử lý:

1. **Phân tích code TikZ**:
   - Tìm các dòng bắt đầu bằng `%!<`
   - Trích xuất commands từ nội dung trong `<>`

2. **Phát hiện tự động**:
   - Quét code TikZ để tìm commands cần thiết
   - Phát hiện packages, tikz libraries, pgfplots libraries

3. **Kết hợp và loại bỏ trùng lặp**:
   - Gộp packages thủ công + tự động
   - Loại bỏ các package trùng lặp

4. **Tạo template LaTeX**:
   - Thêm packages vào phần `EXTRA AUTO-INJECT`
   - Loại bỏ các dòng `%!<...>` khỏi TikZ code

5. **Biên dịch**:
   - Tạo file `.tex` hoàn chỉnh
   - Biên dịch bằng `lualatex`
   - Chuyển đổi PDF → SVG

## 🎨 Ví dụ thực tế

### Ví dụ 4: Sử dụng circuitikz (cơ bản)

```latex
%!<\usepackage{circuitikz}>
\begin{tikzpicture}
\draw (0,0) to[R, o-o] (2,0);
\draw (2,0) to[L, o-o] (4,0);
\draw (4,0) to[C, o-o] (6,0);
\end{tikzpicture}
```

### Ví dụ 4b: Sử dụng circuitikz với options (siunitx)

**⚠️ Mới:** Hệ thống hỗ trợ package options!

```latex
%!<\usepackage[siunitx]{circuitikz}>
\begin{tikzpicture}
\draw (0,0) to[R=1<\ohm>] (2,0)
          to[L=1<\henry>] (4,0)
          to[C=1<\farad>] (6,0);
\end{tikzpicture}
```

**Kết quả:** Hệ thống sẽ tự động thêm `\usepackage[siunitx]{circuitikz}` vào template, cho phép sử dụng cú pháp `1<\ohm>`, `1<\henry>`, `1<\farad>` trong circuitikz.

### Ví dụ 5: Sử dụng physics package

```latex
%!<\usepackage{physics}>
\begin{tikzpicture}
\node at (0,0) {$\vec{F} = m\vec{a}$};
\node at (2,0) {$\abs{x} = \norm{\vec{v}}$};
\end{tikzpicture}
```

### Ví dụ 6: Sử dụng siunitx

```latex
%!<\usepackage{siunitx}>
\begin{tikzpicture}
\node at (0,0) {$\SI{100}{\meter\per\second}$};
\node at (2,0) {$\ang{45}$};
\end{tikzpicture}
```

## 🚀 Lợi ích

1. **Linh hoạt**: Chỉ định packages mà hệ thống không tự phát hiện
2. **An toàn**: Vẫn áp dụng allowlist để đảm bảo bảo mật
3. **Dễ sử dụng**: Cú pháp đơn giản, rõ ràng
4. **Tương thích**: Hoạt động song song với hệ thống tự động
5. **Sạch sẽ**: Cú pháp không xuất hiện trong output cuối cùng

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

Nếu gặp vấn đề, hãy:
1. Kiểm tra cú pháp theo hướng dẫn trên
2. Xem log lỗi chi tiết
3. Thử với package khác để xác định vấn đề
4. Liên hệ hỗ trợ nếu cần thiết

---

**Lưu ý**: Tính năng này được thiết kế để bổ sung cho hệ thống tự động phát hiện, không thay thế hoàn toàn. Luôn ưu tiên sử dụng hệ thống tự động trước khi dùng chỉ định thủ công.
