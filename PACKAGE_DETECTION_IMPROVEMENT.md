# Cải tiến Hệ thống Phát hiện Packages cho TikZ

## Tổng quan

Đã cải tiến hệ thống biên dịch TikZ với cơ chế phát hiện và chèn packages tự động một cách an toàn, giúp tránh lỗi thiếu gói khi biên dịch. Hệ thống hỗ trợ **2 cách** để thêm packages:

1. **Tự động phát hiện** (mặc định)
2. **Chỉ định thủ công** bằng cú pháp `%!<...>`

## Các cải tiến chính

### 1. Hệ thống Allowlist An toàn

#### 📦 Packages được phép (34 packages):
- **Nền tảng**: `fontspec`, `polyglossia`, `xcolor`, `graphicx`, `geometry`, `setspace`
- **Toán học**: `amsmath`, `amssymb`, `amsfonts`, `mathtools`, `physics`, `siunitx`, `cancel`, `cases`
- **TikZ/PGF**: `tikz`, `pgfplots`, `tikz-3dplot`, `tkz-euclide`, `tkz-tab`, `pgf`, `pgfkeys`, `pgfornament`
- **Chuyên biệt**: `circuitikz`, `tikz-timing`, `tikz-cd`, `tikz-network`, `tikzpeople`, `tikzmark`
- **Bổ sung**: `array`, `booktabs`, `multirow`, `colortbl`, `longtable`, `tabularx`

#### 🎨 TikZ Libraries được phép (37 libraries):
- **Cơ bản**: `calc`, `math`, `positioning`, `arrows.meta`, `intersections`, `angles`, `quotes`
- **Trang trí**: `decorations.markings`, `decorations.pathreplacing`, `decorations.text`
- **Hình dạng**: `patterns`, `patterns.meta`, `shadings`, `shapes.geometric`, `shapes.symbols`, `shapes.arrows`
- **Nâng cao**: `hobby`, `spy`, `backgrounds`, `fit`, `matrix`, `chains`, `automata`, `petri`, `mindmap`, `trees`, `graphs`, `shadows`, `fadings`

#### 📊 PGFPlots Libraries được phép (9 libraries):
- `polar`, `statistics`, `dateplot`, `fillbetween`, `colorbrewer`, `groupplots`, `ternary`, `smithchart`, `units`

### 2. Phát hiện Tự động Packages

Hệ thống tự động phát hiện packages cần thiết dựa trên nội dung code TikZ:

#### 📦 Packages được phát hiện:
- **siunitx**: Khi có `\si{`, `\SI{`, `\num{`, `\ang{`, `\unit{`
- **circuitikz**: Khi có `\ohm`, `\volt`, `\ampere`, `\resistor`, `\capacitor`, `\inductor`, `\battery`, `\lamp`
- **tikz-timing**: Khi có `\timing`, `\timingD{`, `\timingL{`, `\timingH{`, `\timingX{`
- **physics**: Khi có `\vec{`, `\abs{`, `\norm{`, `\order{`, `\qty{`, `\mrm{`
- **mathtools**: Khi có `\DeclarePairedDelimiter`, `\DeclareMathOperator`, `\mathclap`, `\mathllap`, `\mathrlap`
- **tikz-cd**: Khi có `\begin{tikzcd}`, `\arrow[`, `\arrow{r}`, `\arrow{d}`
- **tikz-network**: Khi có `\begin{tikzpicture}[network]`, `\Vertex[`, `\Edge[`
- **tikzpeople**: Khi có `\person[`, `\tikzstyle{PersonStyle}`
- **tikzmark**: Khi có `\tikzmark{`, `\tikzmarkin{`, `\tikzmarkend{`
- **pgfornament**: Khi có `\pgfornament{`, `\pgfornament[`, `\pgfornament[`

#### 🎨 TikZ Libraries được phát hiện:
- **decorations**: Khi có `\draw[decorate`, `\draw[decoration`, `\decorate`, `\decoration{`
- **patterns**: Khi có `\draw[pattern`, `\pattern`, `\fill[pattern`
- **shadings**: Khi có `\draw[shade`, `\shade`, `\shadedraw`, `\shading`
- **hobby**: Khi có `\draw[hobby`, `\hobby`, `\curve{`
- **spy**: Khi có `\spy`
- **backgrounds**: Khi có `\begin{scope}[on background layer]`, `\begin{background}`
- **intersections**: Khi có `\path[name intersections`, `\coordinate[name intersections`
- **angles**: Khi có `\pic[angle`, `\angle`, `\draw pic[angle`
- **quotes**: Khi có `\draw[quotes`, `\quotes`, `\draw[quotes=`
- **positioning**: Khi có `\node[above`, `\node[below`, `\node[left`, `\node[right`
- **arrows.meta**: Khi có `\draw[-{`, `\draw[->{`, `\draw[<->{`, `\draw[arrows=`
- **shapes.geometric**: Khi có `\draw[regular polygon`, `\draw[star`, `\draw[diamond`
- **shapes.symbols**: Khi có `\draw[signal`, `\draw[tape`, `\draw[magnifying glass`
- **shapes.arrows**: Khi có `\draw[arrow box`, `\draw[strike out`, `\draw[rounded rectangle`
- **fit**: Khi có `\node[fit=`, `\fit{`, `\draw[fit=`
- **matrix**: Khi có `\matrix[`, `\matrix of`, `\matrix (`, `\matrix{`
- **chains**: Khi có `\begin{scope}[start chain`, `\chainin`, `\onchain`
- **automata**: Khi có `\begin{tikzpicture}[automaton`, `\node[state`
- **petri**: Khi có `\begin{tikzpicture}[petri`, `\place[`, `\transition[`, `\arc[`
- **mindmap**: Khi có `\begin{tikzpicture}[mindmap`, `\concept[`, `\concept color=`
- **trees**: Khi có `\begin{tikzpicture}[tree`, `\node[level`, `\child[`, `\child {`
- **graphs**: Khi có `\begin{tikzpicture}[graph`, `\graph[`, `\graph {`, `\graph (`
- **shadows**: Khi có `\draw[shadow`, `\shadow`, `\shadow{`, `\draw[drop shadow`
- **fadings**: Khi có `\begin{tikzfadingfrompicture`, `\tikzfading`, `\path[fading=`

#### 📊 PGFPlots Libraries được phát hiện:
- **fillbetween**: Khi có `\addplot[fill between`, `\addplot[fillbetween`, `\fillbetween`
- **statistics**: Khi có `\addplot[statistics`, `\addplot[hist`, `\addplot[boxplot`, `\addplot[error bars`
- **dateplot**: Khi có `\addplot[date coordinates`, `\addplot[dateplot`, `\dateplot`
- **colorbrewer**: Khi có `\addplot[colorbrewer`, `\colormap[colorbrewer`, `\pgfplotsset{colormap name=`
- **groupplots**: Khi có `\begin{groupplot}`, `\nextgroupplot`, `\groupplot[`
- **ternary**: Khi có `\begin{ternaryaxis}`, `\ternaryaxis[`, `\addplot3[ternary`
- **smithchart**: Khi có `\begin{smithchart}`, `\smithchart[`, `\addplot[smithchart`
- **units**: Khi có `\begin{axis}[x unit=`, `\begin{axis}[y unit=`, `\addplot[unit=`

### 3. Template LaTeX Cải tiến

```latex
\documentclass[12pt,tikz,border=10pt]{standalone}

% Unicode & ngôn ngữ
\usepackage{fontspec}
\usepackage{polyglossia}
\setdefaultlanguage{vietnamese}

% Toán & đồ hoạ
\usepackage{amsmath,amssymb,amsfonts}
\usepackage[dvipsnames,svgnames,x11names]{xcolor}
\usepackage{graphicx}

% Hệ sinh thái TikZ/PGF
\usepackage{tikz}
\usepackage{tikz-3dplot}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{tkz-euclide}
\usepackage{tkz-tab}

% Thư viện TikZ mặc định
\usetikzlibrary{calc,math,positioning,arrows.meta,intersections,angles,quotes,
                decorations.markings,decorations.pathreplacing,decorations.text,
                patterns,patterns.meta,shadings,hobby,spy,backgrounds}

% Thư viện pgfplots mặc định
\usepgfplotslibrary{polar}

% ==== EXTRA AUTO-INJECT START ====
% (Sẽ được chèn thêm ở đây)
% ==== EXTRA AUTO-INJECT END ====

\begin{document}
{tikz_code}
\end{document}
```

### 4. API Endpoints Mới

#### `/compile_with_packages` (POST)
- Cho phép biên dịch với packages tùy chỉnh
- Parameters: `tikz_code`, `extra_packages`, `extra_tikz_libs`, `extra_pgfplots_libs`
- Trả về JSON với kết quả biên dịch

#### `/api/available_packages` (GET)
- Trả về danh sách tất cả packages và libraries được phép
- Hữu ích cho frontend để hiển thị options

### 5. Logic Biên dịch Cải tiến

```python
# Tự động phát hiện packages cần thiết từ TikZ code
extra_packages, extra_tikz_libs, extra_pgfplots_libs = detect_required_packages(tikz_code)

# Tạo nguồn LaTeX với packages được phát hiện tự động
try:
    latex_source = generate_latex_source(
        tikz_code=tikz_code,
        extra_packages=extra_packages,
        extra_tikz_libs=extra_tikz_libs,
        extra_pgfplots_libs=extra_pgfplots_libs
    )
except ValueError as e:
    # Nếu có package không được phép, chỉ sử dụng template cơ bản
    print(f"[WARN] Package không được phép: {e}", flush=True)
    latex_source = TEX_TEMPLATE.replace("{tikz_code}", tikz_code)
```

## Kết quả Test

✅ **7/7 test cases chính đã pass**
- Basic TikZ: ✅
- Circuit with siunitx: ✅
- Physics notation: ✅
- Commutative diagram: ✅
- Decorations and patterns: ✅
- PGFPlots with statistics: ✅
- Complex example: ✅

## Lợi ích

1. **Tự động hóa**: Không cần user nhớ import packages
2. **An toàn**: Chỉ cho phép packages đã được kiểm tra
3. **Linh hoạt**: Có thể mở rộng allowlist dễ dàng
4. **Hiệu suất**: Chỉ load packages cần thiết
5. **Tương thích**: Hoạt động với code TikZ hiện tại

## Hướng dẫn Mở rộng

### Thêm Package mới:
1. Thêm vào `SAFE_PACKAGES`
2. Thêm logic phát hiện trong `detect_required_packages()`
3. Test với code TikZ tương ứng

### Thêm TikZ Library mới:
1. Thêm vào `SAFE_TIKZ_LIBS`
2. Thêm logic phát hiện trong `detect_required_packages()`
3. Test với code TikZ tương ứng

### Thêm PGFPlots Library mới:
1. Thêm vào `SAFE_PGFPLOTS_LIBS`
2. Thêm logic phát hiện trong `detect_required_packages()`
3. Test với code TikZ tương ứng

## 🆕 Tính năng mới: Chỉ định Packages thủ công

### Tổng quan
Hệ thống hỗ trợ chỉ định packages thủ công bằng cú pháp `%!<...>` để bổ sung cho hệ thống tự động phát hiện.

### Cú pháp sử dụng

#### Cấu trúc cơ bản:
```latex
%!<command1,command2,command3>
\begin{tikzpicture}
% ... code TikZ của bạn ...
\end{tikzpicture}
```

#### Các loại command hỗ trợ:
- **Package**: `\usepackage{package_name}`
- **TikZ Library**: `\usetikzlibrary{library_name}`
- **PGFPlots Library**: `\usepgfplotslibrary{library_name}`

### Ví dụ sử dụng

#### Ví dụ 1: Chỉ định package đơn lẻ
```latex
%!<\usepackage{pgfornament}>
\begin{tikzpicture}
\path [rotate=210,postaction={decoration={text along path,text format delimiters={|}{|}, text={|\Huge| 
					LABORATORY OF MATHEMATICS AND ITS APPLICATIONS {\pgfornament[scale=.4,ydelta=-9pt]{15}} UNIVERSITY OF MEDEA{\pgfornament[scale=.4,ydelta=-9pt]{15}}},
				text align=fit to path,reverse path}, decorate}] 
		circle[radius=7.2cm] ;
\end{tikzpicture}
```

#### Ví dụ 2: Chỉ định nhiều packages và libraries
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

### Cách hoạt động

1. **Phân tích code TikZ**: Tìm các dòng bắt đầu bằng `%!<`
2. **Trích xuất commands**: Phân tích nội dung trong `<>`
3. **Kết hợp với tự động**: Gộp packages thủ công + tự động phát hiện
4. **Loại bỏ trùng lặp**: Chỉ thêm mỗi package một lần
5. **Tạo template**: Thêm packages vào phần `EXTRA AUTO-INJECT`
6. **Loại bỏ cú pháp**: Các dòng `%!<...>` bị loại bỏ khỏi TikZ code cuối cùng

### Lợi ích

1. **Linh hoạt**: Chỉ định packages mà hệ thống không tự phát hiện
2. **An toàn**: Vẫn áp dụng allowlist để đảm bảo bảo mật
3. **Dễ sử dụng**: Cú pháp đơn giản, rõ ràng
4. **Tương thích**: Hoạt động song song với hệ thống tự động
5. **Sạch sẽ**: Cú pháp không xuất hiện trong output cuối cùng

### Lưu ý quan trọng

- ✅ Cú pháp chính xác: `%!<\usepackage{package_name}>`
- ❌ Không có khoảng trắng thừa: `%!< \usepackage{package_name} >`
- ❌ Không thiếu dấu `\`: `%!<usepackage{package_name}>`
- Packages không trong allowlist sẽ bị bỏ qua
- Các dòng `%!<...>` sẽ bị loại bỏ khỏi TikZ code cuối cùng

### Xem thêm
Chi tiết hướng dẫn sử dụng: [MANUAL_PACKAGE_SPECIFICATION.md](MANUAL_PACKAGE_SPECIFICATION.md)
