# CSS Foundation System Guide

## Architecture Overview

Dự án sử dụng CSS Foundation System để đảm bảo consistency và maintainability.

### Load Order (Critical)
```html
1. master-variables.css  <!-- MUST BE FIRST -->
2. global-base.css      <!-- Base styles -->
3. component.css        <!-- Individual components -->
```

### Design System Variables
```css
/* Colors */
--primary-color: #1976d2;
--text-on-glass: #2d3436;
--text-header-glass: #1e3a8a;

/* Glass Morphism */
--glass-bg-light: rgba(255, 255, 255, 0.95);
--glass-bg-strong: rgba(248, 249, 250, 0.92);
--glass-blur-medium: blur(12px);
--glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);

/* Spacing (8px base) */
--spacing-4: 0.5rem;    /* 8px */
--spacing-8: 1rem;      /* 16px */
--spacing-16: 2rem;     /* 32px */
```

## Migration Rules

1. **Backup First:** `cp file.css file.css.backup_migration`
2. **Remove Conflicts:** Delete duplicate html/body/:root rules
3. **Add Scoping:** Prefix all selectors với `.tikz-app`
4. **Replace Values:** Hardcoded → `var(--variable-name)`
5. **Test Thoroughly:** Visual regression + accessibility

## Migration Status (6/10 Complete)

- ✅ `index.css` - Main page (latest)
- ✅ `profile_svg_files.css` - Profile pages
- ✅ `profile_settings.css` - Settings & modals
- ✅ `profile_verification.css` - Verification system
- ✅ `profile_followed_posts.css` - User interactions
- ⏳ `file_card.css` - Next priority
- ⏳ `navigation.css` - Global navigation

## Quality Standards

- **Accessibility:** Contrast ratio ≥ 4.5:1 (achieved ≥ 6.2:1)
- **Performance:** No CSS redundancy, optimized loading
- **Maintainability:** Single source of truth for design tokens
- **Cross-browser:** webkit-backdrop-filter + backdrop-filter

## CSS Architecture Requirements

### Variables First
- Luôn sử dụng `var(--variable-name)` thay vì hardcoded values
- Check master-variables.css trước khi tạo new values

### Scoping
- Tất cả selectors phải có `.tikz-app` prefix
- Tránh duplicate html/body/:root rules

### Glass Morphism
- Sử dụng foundation glass variables cho UI transparency
- Apply consistent blur and shadow effects

### Responsive Design
- Foundation breakpoint variables cho consistency
- Mobile-first approach

### Accessibility
- WCAG AAA compliance (contrast ≥ 6.2:1)
- Test contrast ratios before finalizing

### Migration Verification Commands
```bash
# Check conflicts
grep -rn ":root\|html.*{\|body.*{" static/css/

# Verify scoping
grep -rn "^[^\.tikz-app]" static/css/

# Test accessibility (use browser tools)
# Manual visual regression testing required
```