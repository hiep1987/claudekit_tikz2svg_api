# Hướng dẫn cài đặt Human MCP thành công

> **Dựa trên trải nghiệm thành công ngày 17/10/2025**
>
> Trước đây đã thất bại nhiều lần, lần này đã thành công!

---

## 🔍 Bối cảnh

- **Ngày cài đặt thành công:** 17/10/2025
- **Claude Code version:** Latest
- **Hàm test thành công:** `gemini_gen_image`
- **Kết quả:** Tạo ảnh mountain landscape thành công (1.4MB, 1024x1024px)

---

## 📋 Điều kiện tiên quyết

### 1. Môi trường đã verified
- **OS:** macOS (Darwin 24.5.0)
- **Node.js:** Đã cài đặt (để chạy MCP server)
- **Claude Code:** Đã đăng nhập và hoạt động
- **Network:** Internet ổn định (cho Gemini API calls)

### 2. API Keys cần thiết
- **Google AI Studio API Key:** Cho Gemini image generation
  - Lấy từ: https://aistudio.google.com/app/apikey
  - Cần enable Gemini API

---

## 🛠️ Quy trình cài đặt thành công

### Bước 1: Cài đặt MCP server

```bash
# Clone hoặc download Human MCP server
git clone https://github.com/anthropics/mcp-servers.git
# Hoặc download trực tiếp nếu có file release

# Di chuyển đến thư mục project
cd mcp-servers/human-mcp

# Install dependencies
npm install
```

### Bước 2: Cấu hình API Keys

**Quan trọng:** Sử dụng environment variables thay vì hardcode!

```bash
# Tạo file .env trong thư mục human-mcp
touch .env

# Thêm API key vào .env
echo "GOOGLE_AI_API_KEY=your_actual_api_key_here" >> .env
```

### Bước 3: Cấu hình Claude Code

**File cấu hình:** `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "human-mcp": {
      "command": "node",
      "args": ["/path/to/mcp-servers/human-mcp/dist/index.js"],
      "env": {
        "GOOGLE_AI_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

**Lưu ý quan trọng:**
- Đảm bảo path đến `dist/index.js` là chính xác
- Environment variable phải khớp với file .env
- Restart Claude Code sau khi sửa config

### Bước 4: Build và chạy MCP server

```bash
# Build project (nếu cần)
npm run build

# Test server manually (optional)
node dist/index.js
```

### Bước 5: Verify trong Claude Code

1. **Restart Claude Code** hoàn toàn
2. **Check MCP connection:**
   ```
   /mcp list
   ```
3. **Verify tools available:**
   - `gemini_gen_image`
   - `gemini_gen_video`
   - `gemini_edit_image`
   - Các tools khác...

---

## ✅ Test thành công

### Command test đã chạy:
```javascript
// Trong Claude Code
gemini_gen_image({
  prompt: "A serene mountain landscape with a lake reflecting snow-capped peaks at sunset",
  model: "gemini-2.5-flash-image-preview",
  output_format: "base64",
  style: "photorealistic",
  aspect_ratio: "16:9"
})
```

### Kết quả:
- ✅ **Thời gian xử lý:** ~11 giây
- ✅ **Kích thước ảnh:** 1024x1024 pixels
- ✅ **File size:** 1.4 MB
- ✅ **Format:** PNG base64
- ✅ **File saved:** gemini-image-2025-10-17T15-09-26-587Z-9e4ec41a.png

---

## 🔧 Các vấn đã khắc phục

### 1. Path errors
- **Vấn đề:** Không tìm thấy file `dist/index.js`
- **Giải pháp:** Build project với `npm run build`

### 2. API key issues
- **Vấn đề:** API key không hoạt động
- **Giải pháp:**
  - Verify API key từ Google AI Studio
  - Đảm bảo enable Gemini API
  - Check environment variable loading

### 3. Connection issues
- **Vấn đề:** Claude Code không connect được MCP server
- **Giải pháp:**
  - Restart Claude Code hoàn toàn
  - Check path trong config file
  - Verify npm install thành công

---

## 📚 Tools có sẵn

### Image Generation
- `gemini_gen_image` - Tạo ảnh từ text
- `gemini_edit_image` - Edit ảnh với AI
- `gemini_inpaint_image` - Inpainting
- `gemini_outpaint_image` - Expand ảnh
- `gemini_style_transfer_image` - Transfer style
- `gemini_compose_images` - Combine nhiều ảnh

### Video Generation
- `gemini_gen_video` - Tạo video từ text
- `gemini_image_to_video` - Tạo video từ ảnh

### Image Processing (Jimp)
- `jimp_crop_image` - Cắt ảnh
- `jimp_resize_image` - Resize ảnh
- `jimp_rotate_image` - Xoay ảnh
- `jimp_mask_image` - Apply mask

### Background Removal
- `rmbg_remove_background` - Xóa background với AI

### Vision & Screenshot
- `eyes_analyze` - Phân tích ảnh/video
- `eyes_compare` - So sánh ảnh
- `eyes_read_document` - Đọc văn bản từ tài liệu
- `playwright_screenshot_*` - Chụp screenshot webpage

### Speech Generation
- `mouth_speak` - Text to speech
- `mouth_narrate` - Narration cho content dài
- `mouth_explain` - Giải thích code bằng giọng nói
- `mouth_customize` - Test different voices

### Brain & Reasoning
- `sequentialthinking` - Advanced reasoning
- `brain_analyze_simple` - Pattern analysis
- `brain_patterns_info` - Pattern information
- `brain_reflect_enhanced` - AI reflection

---

## 🎯 Best Practices

### 1. API Management
- Luôn sử dụng environment variables
- Không bao giờ commit API keys
- Rotate keys định kỳ cho security

### 2. Error Handling
- Monitor rate limits của Gemini API
- Handle timeout cho large media files
- Log errors để debug

### 3. Performance
- Use appropriate model sizes:
  - `gemini-2.5-flash-image-preview` cho speed
  - `gemini-2.5-pro-preview-tts` cho quality
- Optimize prompts cho better results

### 4. File Management
- Auto-save generated files với timestamps
- Cleanup temporary files
- Monitor disk space usage

---

## 🔄 Maintenance

### Regular checks
1. **API key validity:** Check monthly
2. **MCP server updates:** Update khi có new version
3. **Disk space:** Monitor generated files
4. **Usage limits:** Track Gemini API usage

### Troubleshooting
```bash
# Check MCP server status
ps aux | grep "node.*human-mcp"

# Check Claude Code logs
tail -f ~/.config/claude/claude.log

# Test API connection manually
curl -H "Content-Type: application/json" \
     -d '{"prompt":"test"}' \
     https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent?key=YOUR_KEY
```

---

## 📞 Support

Nếu gặp issues:
1. **Check logs:** Claude Code và MCP server
2. **Verify environment:** API keys, paths, permissions
3. **Consult docs:** Human MCP repository
4. **Test simple:** Start với basic prompts

---

## 🎉 Kết luận

Quy trình trên đã được verify thành công trên macOS. Key factors for success:

1. **Correct API key configuration**
2. **Proper MCP server setup**
3. **Accurate path configuration**
4. **Complete Claude Code restart**

Chúc bạn sử dụng Human MCP hiệu quả! 🚀