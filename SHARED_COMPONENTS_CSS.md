## Shared Components CSS Consolidation

### Purpose
Create a single source of truth for cross-page, reusable styles to reduce duplication and ease maintenance.

### New File
- `static/css/shared_components.css`

### What moved here
- Monospace font preservation for code contexts:
  - `body .CodeMirror, body .CodeMirror *`
  - `body pre, body code, body .code, body .tikz-code, body textarea[name="code"]`
- Code block styles:
  - `.code-block`, `.code-block pre`, `.code-block code`
- Copy button styles:
  - `.copy-btn`, `.copy-btn:hover`
- CodeMirror minor enhancements (gutters/placeholder)
- Shared primary button styles (unified):
  - `.btn-primary, .btn-action, .compile-save-row-btn, .export-btn, .Btn`
  - Includes hover styles

### Files updated to remove duplication
- `static/css/index.css`
  - Removed local primary button styles; now rely on shared `.btn-primary` group (and existing class names)
- Other pages previously using `!important` for fonts updated to rely on higher-specificity selectors:
  - `static/css/navigation.css`
  - `static/css/view_svg.css`
  - `static/css/search_results.css`
  - `static/css/profile_settings.css`

### Rationale
- Eliminates CSS duplication across pages/components
- Ensures consistent look and feel for buttons and code blocks
- Removes `!important` in favor of higher-specificity selectors for maintainability

### How to use
- Prefer `.btn-primary` for primary call-to-action buttons
- Continue using existing page-specific class names (`.btn-action`, `.compile-save-row-btn`, `.export-btn`, `.Btn`) — styles are unified via shared rules
- For code sections, wrap content in `.code-block` and use `.copy-btn` for copy actions

### Follow-ups (optional)
- Replace page-specific button classes in templates with `.btn-primary` for semantic consistency
- Audit remaining component CSS files to move any duplicated, cross-page styles into `shared_components.css`
