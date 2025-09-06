# MIGRATION ANALYSIS - BASE TEMPLATE

## 📋 Template Dependencies Matrix

| Template | Highlight.js | CodeMirror | File Card | Navigation | Login Modal | Special CSS | Special JS | Body Attrs |
|----------|-------------|------------|-----------|------------|-------------|-------------|------------|------------|
| **index.html** | ✅ | ✅ | ✅ | ✅ | ✅ | index.css | index.js, file_card.js, navigation.js | ❌ |
| **search_results.html** | ✅ | ✅ | ✅ | ✅ | ✅ | search_results.css | search_results.js, file_card.js | ❌ |
| **profile_settings.html** | ❌ | ❌ | ❌ | ✅ | ❌ | profile_settings.css, bio-editor.css | profile_settings.js | ❌ |
| **profile_svg_files.html** | ❌ | ❌ | ✅ | ✅ | ✅ | profile_svg_files.css | profile_svg_files.js, file_card.js | ❌ |
| **profile_followed_posts.html** | ❌ | ❌ | ✅ | ✅ | ✅ | profile_followed_posts.css | profile_followed_posts.js, file_card.js | ❌ |
| **profile_verification.html** | ✅ | ✅ | ❌ | ✅ | ✅ | profile_verification.css | profile_verification.js | ❌ |
| **view_svg.html** | ✅ | ✅ | ❌ | ✅ | ✅ | view_svg.css | view_svg.js | ✅ Special |

## 🎯 Migration Complexity Levels

### 🟢 **LEVEL 1: SIMPLE** (Ít dependencies, dễ migrate)
- **search_results.html** - Standard structure, ít customization
- **profile_verification.html** - Straightforward layout

### 🟡 **LEVEL 2: MEDIUM** (Dependencies trung bình)
- **profile_followed_posts.html** - File card + custom JS
- **profile_svg_files.html** - File card + custom JS  
- **profile_settings.html** - Special editors (Quill, Cropper)

### 🔴 **LEVEL 3: COMPLEX** (Nhiều dependencies, logic phức tạp)
- **index.html** - Trang chủ với nhiều features
- **view_svg.html** - Body attributes đặc biệt + complex logic

## 📝 Migration Order (Đơn giản → Phức tạp)

1. **search_results.html** ⭐ (Test base template)
2. **profile_verification.html** ⭐ (Validate approach)
3. **profile_followed_posts.html** 🔄 (Test file card integration)
4. **profile_svg_files.html** 🔄 (Similar to #3)
5. **profile_settings.html** 🔧 (Test special libraries)
6. **index.html** 🏠 (Main page - careful testing)
7. **view_svg.html** ⚠️ (Special body attributes)

## 🛠️ Special Considerations

### view_svg.html
- Body attributes: `data-is-logged-in`, `data-set-next-url`
- Cần block riêng trong base template

### profile_settings.html  
- Cropper.js, Quill Editor
- Bio-editor CSS riêng

### index.html
- App state JSON script
- Multiple JS files coordination
- Search functionality

## 🔍 Validation Points

- [ ] CSS loading order maintained
- [ ] JavaScript execution order preserved  
- [ ] Login state consistency
- [ ] Responsive design intact
- [ ] SEO meta tags correct
- [ ] Favicon loading properly
