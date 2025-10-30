# 🚀 HƯỚNG DẪN CÀI ĐẶT CJKutf8 LÊN SERVER

## ✅ TÌNH TRẠNG HIỆN TẠI

- ✅ **Local test:** Chạy thành công `/Users/hieplequoc/Downloads/testttt.tex`
- ✅ **Code TikZ:** Hoàn hảo, không cần sửa
- ✅ **Database:** CJKutf8 đã có (id=93) trong `supported_packages`
- ❌ **Production server:** Chưa cài đặt CJKutf8 package và fonts

---

## 🎯 CẦN CÀI ĐẶT TRÊN SERVER

### **1. CJKutf8 Package (TeX Live)**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install texlive-lang-chinese

# Hoặc cài đầy đủ (khuyến nghị nếu có dung lượng)
sudo apt-get install texlive-full
```

### **2. Chinese Fonts**

```bash
# Arphic fonts (GB Song - gbsn)
sudo apt-get install fonts-arphic-gbsn00lp
sudo apt-get install fonts-arphic-gkai00mp
sudo apt-get install fonts-arphic-bsmi00lp
sudo apt-get install fonts-arphic-bkai00mp

# Hoặc Noto CJK fonts (toàn diện hơn)
sudo apt-get install fonts-noto-cjk
sudo apt-get install fonts-noto-cjk-extra
```

### **3. Update font cache**

```bash
sudo fc-cache -f -v
```

---

## 🔍 KIỂM TRA SAU KHI CÀI

### **Kiểm tra CJKutf8 package:**

```bash
kpsewhich CJKutf8.sty
# Kết quả mong đợi: /usr/share/texlive/.../CJKutf8.sty
```

### **Kiểm tra Chinese fonts:**

```bash
fc-list :lang=zh | grep -i song
# Kết quả mong đợi: danh sách fonts tiếng Trung
```

### **Test compile:**

```bash
cd /tmp
cat > test_cjk.tex << 'EOF'
\documentclass[12pt,border=10pt]{standalone}
\usepackage{CJKutf8}
\begin{document}
\begin{CJK*}{UTF8}{gbsn}
富贵
\end{CJK*}
\end{document}
EOF

pdflatex test_cjk.tex
# Nếu thành công → tạo file test_cjk.pdf
```

---

## 📝 CODE TIKZ CỦA BẠN

Đảm bảo code có `%!<CJKutf8>` ở đầu:

```latex
%!<CJKutf8>

\definecolor{falured}{rgb}{0.5, 0.09, 0.09}
\begin{tikzpicture}[line join=round, line cap=round,scale=1,transform shape]
    \node[falured,scale=.7,inner sep=0,align=left,
    font=\fontfamily{qag}\selectfont] at (3,-4.5) 
    {Code by Lương Như Quỳnh};
    
    \begin{CJK*}{UTF8}{gbsn}
        \node[black,scale=2,inner sep=0,align=left,font=\fontfamily{qag}\selectfont] at (-3,4.5) {富};
        \node[black,scale=2,inner sep=0,align=left,font=\fontfamily{qag}\selectfont] at (-3,3.5) {贵};
    \end{CJK*}
\end{tikzpicture}
```

---

## 🔧 DEPLOY LÊN VPS/PRODUCTION

### **Bước 1: SSH vào server**

```bash
ssh user@your-server-ip
```

### **Bước 2: Chạy script cài đặt**

```bash
# Tạo script
cat > install_cjk.sh << 'EOF'
#!/bin/bash
echo "🚀 Installing CJK support for tikz2svg..."

# Update package list
sudo apt-get update

# Install CJK packages
echo "📦 Installing texlive-lang-chinese..."
sudo apt-get install -y texlive-lang-chinese

# Install Chinese fonts
echo "🔤 Installing Chinese fonts..."
sudo apt-get install -y fonts-arphic-gbsn00lp
sudo apt-get install -y fonts-arphic-gkai00mp
sudo apt-get install -y fonts-noto-cjk

# Update font cache
echo "🔄 Updating font cache..."
sudo fc-cache -f -v

# Verify installation
echo ""
echo "✅ Installation complete!"
echo ""
echo "🔍 Verification:"
echo "CJKutf8.sty: $(kpsewhich CJKutf8.sty)"
echo "Chinese fonts: $(fc-list :lang=zh | wc -l) fonts found"

echo ""
echo "🎉 CJK support ready for tikz2svg!"
EOF

# Chạy script
chmod +x install_cjk.sh
./install_cjk.sh
```

### **Bước 3: Restart tikz2svg service**

```bash
# Nếu dùng systemd
sudo systemctl restart tikz2svg

# Nếu dùng Docker
docker-compose restart

# Nếu chạy manual
pkill -f "python.*app.py"
cd /path/to/tikz2svg_api
python3 app.py
```

---

## 🧪 TEST TRÊN PRODUCTION

### **1. Test qua web interface:**

1. Truy cập: `https://your-tikz2svg-domain.com`
2. Paste code TikZ (có `%!<CJKutf8>`)
3. Click compile
4. Kiểm tra kết quả

### **2. Test qua API:**

```bash
curl -X POST https://your-tikz2svg-domain.com/convert \
  -H "Content-Type: application/json" \
  -d '{
    "tikz_code": "%!<CJKutf8>\n\n\\begin{tikzpicture}\n\\begin{CJK*}{UTF8}{gbsn}\n\\node at (0,0) {富贵};\n\\end{CJK*}\n\\end{tikzpicture}"
  }'
```

---

## 📊 DUNG LƯỢNG CẦN THIẾT

| Package | Kích thước | Ghi chú |
|---------|-----------|---------|
| `texlive-lang-chinese` | ~100MB | CJK packages |
| `fonts-arphic-*` | ~50MB | Chinese fonts |
| `fonts-noto-cjk` | ~200MB | Full CJK support (optional) |
| **Tổng tối thiểu** | **~150MB** | Không bao gồm Noto |

---

## ⚠️ LƯU Ý

1. **Quyền sudo:** Cần quyền root để cài đặt
2. **Dung lượng:** Đảm bảo server còn ~200MB trống
3. **Thời gian:** Cài đặt mất ~5-10 phút
4. **Restart:** Cần restart service sau khi cài

---

## 🎯 CHECKLIST

- [ ] SSH vào server
- [ ] Chạy `sudo apt-get install texlive-lang-chinese`
- [ ] Chạy `sudo apt-get install fonts-arphic-gbsn00lp`
- [ ] Chạy `sudo fc-cache -f -v`
- [ ] Verify: `kpsewhich CJKutf8.sty`
- [ ] Verify: `fc-list :lang=zh`
- [ ] Restart tikz2svg service
- [ ] Test compile code CJK
- [ ] ✅ Success!

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề:

1. **Kiểm tra logs:** `/var/log/tikz2svg/error.log`
2. **Kiểm tra permissions:** TeX Live có quyền đọc fonts?
3. **Thử compile manual:** `pdflatex test_cjk.tex`
4. **Liên hệ admin:** quochiep0504@gmail.com

---

## 🎉 KẾT QUẢ MONG ĐỢI

Sau khi cài đặt xong, code TikZ với `%!<CJKutf8>` sẽ:
- ✅ Compile thành công trên production
- ✅ Hiển thị chữ Trung (富贵) chính xác
- ✅ Giống hệt kết quả trên local

**Code của bạn đã hoàn hảo - chỉ cần setup server! 🚀**

