# Testing Strategy

## Backend Testing

```python
# Example test structure
def test_tikz_to_svg_conversion():
    # Test TikZ conversion functionality với lualatex

def test_package_detection():
    # Test automatic package và library detection

def test_user_authentication():
    # Test Google OAuth flow

def test_rate_limiting():
    # Test rate limiting implementation

def test_email_sending():
    # Test Zoho SMTP integration
```

## Frontend Testing

```javascript
// Example test structure
function testCodeMirrorIntegration() {
    // Test TikZ code editor functionality
}

function testFileUpload() {
    // Test file upload functionality
}

function testUserInteraction() {
    // Test like, follow, comment features
}

function testRealTimePolling() {
    // Test real-time updates
}

function testCropperIntegration() {
    // Test avatar cropping functionality
}
```

## Integration Testing

- Test complete user flows từ TikZ input đến SVG output
- Test email sending với Zoho SMTP
- Test file processing pipeline (TikZ → PDF → SVG → PNG/JPEG)
- Test rate limiting cho API và email
- Test real-time features (likes, follows, polling)
- Test responsive design trên multiple devices

## Critical Test Areas

### TikZ Processing Tests
- Test conversion pipeline end-to-end
- Test package auto-detection
- Test manual package specification
- Test package options parsing

### Comments System Tests
- Test LaTeX math rendering
- Test TikZ code block parsing
- Test XSS protection
- Test nested replies

### Email Tests
- Test email sending và templates

### Rate Limiting Tests
- Test API throttling (email, package requests, comments)

### CSS Regression Tests
- Visual testing sau migration

### Accessibility Tests
- Contrast ratio ≥ 6.2:1 (WCAG AAA)
- Keyboard navigation
- Screen reader compatibility

**Coverage:** Mục tiêu ≥ 70% cho critical paths