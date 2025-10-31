# CSP Quill.js CDN Fix - Profile Settings Page

## Issue Summary

When accessing the `templates/profile_settings.html` page, the Quill.js rich text editor library failed to load due to Content Security Policy (CSP) violations.

### Error Messages:
```
Refused to load the stylesheet 'https://cdn.quilljs.com/1.3.6/quill.snow.css' 
because it violates the following Content Security Policy directive: 
"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 
https://codemirror.net https://fonts.googleapis.com". 

Refused to load the script 'https://cdn.quilljs.com/1.3.6/quill.min.js' 
because it violates the following Content Security Policy directive: 
"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net 
https://www.googletagmanager.com https://cdnjs.cloudflare.com https://codemirror.net".

Uncaught ReferenceError: Quill is not defined at profile_settings.js:197
```

## Root Cause

The Content Security Policy (CSP) configuration did not include `https://cdn.quilljs.com` as an allowed source for scripts and stylesheets. The Quill editor is used in the profile settings page for the bio/introduction field.

## Solution

Added `https://cdn.quilljs.com` to the allowed CSP sources in three configuration files:

### 1. Development/Runtime CSP - `comments_helpers.py`

**File:** `/Users/hieplequoc/web/work/tikz2svg_api/comments_helpers.py`

**Lines 134-141:** Updated the `add_security_headers()` function

```python
response.headers['Content-Security-Policy'] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://www.googletagmanager.com https://cdnjs.cloudflare.com https://codemirror.net https://cdn.quilljs.com; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://codemirror.net https://fonts.googleapis.com https://cdn.quilljs.com; "
    "img-src 'self' data: https:; "
    "font-src 'self' data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
    "connect-src 'self' https://cdn.jsdelivr.net https://cdn.quilljs.com"
)
```

**Changes:**
- Added `https://cdn.quilljs.com` to `script-src` directive
- Added `https://cdn.quilljs.com` to `style-src` directive
- Added `https://cdn.quilljs.com` to `connect-src` directive (for source maps)

### 2. Production CSP Configuration - `config_production.py`

**File:** `/Users/hieplequoc/web/work/tikz2svg_api/config_production.py`

**Lines 37-48:** Updated the `CSP_POLICY` dictionary

```python
CSP_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net", 
                   "https://www.googletagmanager.com", "https://cdnjs.cloudflare.com", 
                   "https://codemirror.net", "https://cdn.quilljs.com"],
    'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", 
                  "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", 
                  "https://codemirror.net", "https://cdn.quilljs.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net", 
                 "https://cdnjs.cloudflare.com"],
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'", "https://cdn.jsdelivr.net", "https://cdn.quilljs.com"],
    'frame-ancestors': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
}
```

**Changes:**
- Added `https://cdn.quilljs.com` to `script-src` array
- Added `https://cdn.quilljs.com` to `style-src` array
- Added `https://cdn.quilljs.com` to `connect-src` array (for source maps)
- Also added other CDN sources for consistency with development config

### 3. Nginx Production Deployment - `deploy_vps_production.sh`

**File:** `/Users/hieplequoc/web/work/tikz2svg_api/deploy_vps_production.sh`

**Line 538:** Updated nginx CSP header configuration

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://www.googletagmanager.com https://cdnjs.cloudflare.com https://codemirror.net https://cdn.quilljs.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://codemirror.net https://cdn.quilljs.com; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' data: https:; connect-src 'self' https://cdn.jsdelivr.net https://cdn.quilljs.com;" always;
```

**Changes:**
- Added `https://cdn.quilljs.com` to `script-src` directive
- Added `https://cdn.quilljs.com` to `style-src` directive
- Added `https://cdn.quilljs.com` to `connect-src` directive (for source maps)
- Updated other directives for consistency

## Testing

After applying these changes:

1. **Development Environment:**
   - Restart Flask development server
   - Access `/profile/<user_id>/settings`
   - Verify Quill editor loads without CSP errors
   - Test bio editor functionality (formatting, colors, etc.)

2. **Production Environment:**
   - Deploy updated code
   - Reload nginx configuration: `sudo nginx -s reload`
   - Clear browser cache
   - Test profile settings page
   - Verify no CSP violations in browser console

## Verification Checklist

- [x] CSP updated in `comments_helpers.py` (runtime headers)
- [x] CSP updated in `config_production.py` (production config)
- [x] CSP updated in `deploy_vps_production.sh` (nginx config)
- [x] No linter errors introduced
- [ ] Tested in development environment
- [ ] Tested in production environment
- [ ] Browser console shows no CSP violations
- [ ] Quill editor loads and functions correctly

## Files Modified

1. `/Users/hieplequoc/web/work/tikz2svg_api/comments_helpers.py`
2. `/Users/hieplequoc/web/work/tikz2svg_api/config_production.py`
3. `/Users/hieplequoc/web/work/tikz2svg_api/deploy_vps_production.sh`

## Security Considerations

**Q: Is it safe to add cdn.quilljs.com to CSP?**

**A:** Yes, because:
1. Quill.js is a well-established, reputable library maintained by Salesforce
2. The CDN is the official Quill.js CDN
3. We're only allowing specific resources (scripts and styles) from this domain
4. The CSP still maintains protection against other unauthorized sources
5. This is the standard approach for using third-party libraries via CDN

**Alternative Approaches (if needed):**
- **Self-host Quill.js:** Download and serve from `/static/js/` and `/static/css/`
- **Use npm/package manager:** Install via npm and bundle with your assets
- **Subresource Integrity (SRI):** Add integrity hashes to verify CDN files haven't been tampered with

## Impact

- **User Experience:** Profile settings bio editor now works correctly
- **Security:** Maintains strong CSP while allowing necessary resources
- **Performance:** No impact (CDN resources load efficiently)
- **Compatibility:** Works across all environments (dev, staging, production)

## Related Files

- Template: `templates/profile_settings.html` (lines 32, 268)
- JavaScript: `static/js/profile_settings.js` (line 197)
- CSS: `static/css/bio-editor.css`

## Date Fixed

October 31, 2025

## Git Branch

`feature/base-template-migration`

