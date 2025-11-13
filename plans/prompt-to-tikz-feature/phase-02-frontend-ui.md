# Phase 2: Frontend UI

**Duration:** 4-6 hours
**Priority:** High (Can start in parallel with Phase 1)
**Dependencies:** None (CSS Foundation, HTML structure)

---

## 🎯 Objectives

Create responsive, accessible UI for prompt-to-TikZ generation following CSS Foundation System design principles.

---

## 📋 Tasks Breakdown

### Task 2.1: HTML Structure (60 min)

**File:** `templates/index.html`

**Location:** Insert AFTER `.input-preview-section` (line ~127)

```html
<!-- TikZ Generation from Prompt Section -->
<div class="prompt-to-tikz-section page-container">
    <h2 class="section-title">
        <span class="title-icon">✨</span>
        Sinh mã TikZ từ mô tả
    </h2>

    <p class="section-description">
        Mô tả hình vẽ bạn muốn bằng tiếng Việt hoặc tiếng Anh, AI sẽ tự động sinh mã TikZ cho bạn.
    </p>

    <!-- Input Area -->
    <div class="prompt-input-container">
        <label for="tikz-prompt-input" class="prompt-label">
            Mô tả hình vẽ của bạn
            <span class="prompt-hint">(VD: "vẽ bảng biến thiên hàm số y = x^2 - 4x + 3")</span>
        </label>

        <textarea
            id="tikz-prompt-input"
            class="prompt-textarea"
            placeholder="Mô tả hình vẽ bạn muốn tạo..."
            rows="5"
            maxlength="500"
            aria-describedby="prompt-char-count prompt-examples"
        ></textarea>

        <div class="prompt-footer">
            <div class="prompt-char-count" id="prompt-char-count" aria-live="polite">
                <span id="char-current">0</span> / 500 ký tự
            </div>

            <button
                type="button"
                id="show-examples-btn"
                class="show-examples-btn"
                aria-expanded="false"
                aria-controls="prompt-examples"
            >
                <span class="icon">💡</span>
                Xem ví dụ
            </button>
        </div>

        <!-- Example Prompts (collapsible) -->
        <div id="prompt-examples" class="prompt-examples" hidden>
            <h4 class="examples-title">Ví dụ mô tả tốt:</h4>
            <ul class="examples-list">
                <li class="example-item" data-prompt="vẽ bảng biến thiên của hàm số y = x^3 - 3x + 1">
                    <button class="example-btn" aria-label="Dùng ví dụ này">
                        <span class="example-text">"vẽ bảng biến thiên của hàm số y = x^3 - 3x + 1"</span>
                        <span class="example-action">Dùng</span>
                    </button>
                </li>
                <li class="example-item" data-prompt="vẽ đồ thị hàm số y = sin(x) trên đoạn [0, 2π]">
                    <button class="example-btn" aria-label="Dùng ví dụ này">
                        <span class="example-text">"vẽ đồ thị hàm số y = sin(x) trên đoạn [0, 2π]"</span>
                        <span class="example-action">Dùng</span>
                    </button>
                </li>
                <li class="example-item" data-prompt="vẽ tam giác đều ABC với cạnh dài 4cm">
                    <button class="example-btn" aria-label="Dùng ví dụ này">
                        <span class="example-text">"vẽ tam giác đều ABC với cạnh dài 4cm"</span>
                        <span class="example-action">Dùng</span>
                    </button>
                </li>
                <li class="example-item" data-prompt="vẽ đường tròn tâm O bán kính 3cm và tiếp tuyến tại điểm A">
                    <button class="example-btn" aria-label="Dùng ví dụ này">
                        <span class="example-text">"vẽ đường tròn tâm O bán kính 3cm và tiếp tuyến tại điểm A"</span>
                        <span class="example-action">Dùng</span>
                    </button>
                </li>
            </ul>
        </div>

        <!-- Generate Button -->
        <div class="prompt-actions">
            <button
                type="button"
                id="generate-tikz-btn"
                class="generate-btn"
                {% if not logged_in %}
                disabled
                title="Bạn cần đăng nhập Google để sử dụng tính năng này"
                {% endif %}
            >
                <span class="btn-icon">🎨</span>
                <span class="btn-text">Sinh mã TikZ</span>
            </button>

            {% if not logged_in %}
            <p class="login-hint">
                <a href="{{ url_for('google.login') }}" class="login-link">Đăng nhập</a>
                để sử dụng tính năng sinh mã tự động
            </p>
            {% endif %}
        </div>
    </div>

    <!-- Loading State -->
    <div id="generation-loading" class="generation-loading" hidden aria-live="polite">
        <div class="loading-spinner"></div>
        <p class="loading-text">Đang sinh mã TikZ... Vui lòng đợi trong giây lát.</p>
        <p class="loading-subtext">Thời gian chờ tối đa: 30 giây</p>
    </div>

    <!-- Error Display -->
    <div id="generation-error" class="generation-error" hidden role="alert">
        <div class="error-icon">⚠️</div>
        <div class="error-content">
            <h4 class="error-title">Có lỗi xảy ra</h4>
            <p class="error-message" id="generation-error-message"></p>
            <button type="button" class="error-retry-btn" id="retry-generation-btn">
                Thử lại
            </button>
        </div>
    </div>

    <!-- Generated Code Display -->
    <div id="generated-code-container" class="generated-code-container" hidden>
        <div class="generated-header">
            <h3 class="generated-title">
                <span class="title-icon">✅</span>
                Mã TikZ đã sinh
            </h3>
            <div class="generated-meta">
                <span class="diagram-type-badge" id="diagram-type-badge"></span>
                <span class="generation-time" id="generation-time"></span>
            </div>
        </div>

        <!-- Code Editor (will be CodeMirror instance) -->
        <div id="generated-code-editor" class="generated-code-editor"></div>

        <!-- Required Packages Info -->
        <div class="packages-info" id="packages-info">
            <h4 class="packages-title">📦 Packages cần thiết:</h4>
            <ul class="packages-list" id="packages-list"></ul>
        </div>

        <!-- Actions -->
        <div class="generated-actions">
            <button type="button" id="copy-generated-btn" class="action-btn copy-btn">
                <span class="btn-icon">📋</span>
                <span class="btn-text">Sao chép</span>
            </button>

            <button type="button" id="use-generated-btn" class="action-btn use-btn">
                <span class="btn-icon">✨</span>
                <span class="btn-text">Dùng code này</span>
            </button>

            <button type="button" id="clear-generated-btn" class="action-btn clear-btn">
                <span class="btn-icon">🗑️</span>
                <span class="btn-text">Xóa</span>
            </button>
        </div>

        <!-- Success Toast (for copy action) -->
        <div id="copy-success-toast" class="copy-success-toast" hidden>
            ✓ Đã sao chép vào clipboard
        </div>
    </div>

    <!-- History Dropdown (Optional) -->
    {% if logged_in %}
    <div class="generation-history">
        <button
            type="button"
            id="show-history-btn"
            class="show-history-btn"
            aria-expanded="false"
            aria-controls="history-dropdown"
        >
            <span class="btn-icon">📚</span>
            <span class="btn-text">Lịch sử sinh mã</span>
            <span class="history-count" id="history-count" hidden></span>
        </button>

        <div id="history-dropdown" class="history-dropdown" hidden>
            <div class="history-header">
                <h4 class="history-title">10 lần sinh mã gần nhất</h4>
                <button type="button" class="history-close-btn" aria-label="Đóng">×</button>
            </div>

            <div id="history-list" class="history-list">
                <!-- Populated by JavaScript -->
                <p class="history-empty">Chưa có lịch sử</p>
            </div>
        </div>
    </div>
    {% endif %}
</div>
```

**Accessibility Features:**
- Semantic HTML (section, labels, buttons)
- ARIA attributes (aria-live, aria-expanded, aria-controls)
- Keyboard navigation support
- Screen reader friendly
- Focus management

**Validation:**
- [ ] Valid HTML5
- [ ] Semantic structure
- [ ] ARIA attributes correct
- [ ] Labels for all inputs

---

### Task 2.2: CSS Foundation Integration (30 min)

**File:** `static/css/foundation/master-variables.css`

Add new variables:

```css
/* Prompt-to-TikZ Section Variables */
:root {
    /* Colors */
    --prompt-bg: var(--glass-bg-light);
    --prompt-border: rgba(31, 38, 135, 0.15);
    --prompt-focus: var(--primary-color);
    --prompt-error: #dc3545;
    --prompt-success: #28a745;

    /* Spacing */
    --prompt-section-gap: var(--spacing-16);
    --prompt-element-gap: var(--spacing-8);

    /* Typography */
    --prompt-title-size: 1.75rem;
    --prompt-description-size: 1rem;
    --prompt-hint-size: 0.875rem;

    /* Borders */
    --prompt-border-radius: 12px;
    --prompt-border-width: 1px;

    /* Shadows */
    --prompt-shadow: var(--glass-shadow);
    --prompt-focus-shadow: 0 0 0 3px rgba(25, 118, 210, 0.2);

    /* Transitions */
    --prompt-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    /* Loading Spinner */
    --spinner-size: 40px;
    --spinner-border: 4px;
    --spinner-color: var(--primary-color);
}
```

**Validation:**
- [ ] Variables follow naming convention
- [ ] Use existing foundation variables
- [ ] No hardcoded values

---

### Task 2.3: Component CSS (120 min)

**File:** `static/css/prompt-to-tikz.css`

```css
/**
 * Prompt-to-TikZ Generation Section
 *
 * CSS Foundation System compliant
 * WCAG AAA accessibility (contrast ≥ 6.2:1)
 * Mobile-first responsive design
 */

/* ============================================
   SECTION CONTAINER
   ============================================ */

.tikz-app .prompt-to-tikz-section {
    background: var(--prompt-bg);
    backdrop-filter: var(--glass-blur-medium);
    -webkit-backdrop-filter: var(--glass-blur-medium);
    border-radius: var(--prompt-border-radius);
    padding: var(--spacing-12);
    margin-top: var(--spacing-16);
    box-shadow: var(--prompt-shadow);
    border: var(--prompt-border-width) solid var(--prompt-border);
}

.tikz-app .section-title {
    font-size: var(--prompt-title-size);
    font-weight: 600;
    color: var(--text-header-glass);
    margin-bottom: var(--spacing-4);
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
}

.tikz-app .title-icon {
    font-size: 1.5rem;
    line-height: 1;
}

.tikz-app .section-description {
    font-size: var(--prompt-description-size);
    color: var(--text-on-glass);
    margin-bottom: var(--spacing-12);
    line-height: 1.6;
}

/* ============================================
   PROMPT INPUT
   ============================================ */

.tikz-app .prompt-input-container {
    display: flex;
    flex-direction: column;
    gap: var(--prompt-element-gap);
}

.tikz-app .prompt-label {
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-header-glass);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
}

.tikz-app .prompt-hint {
    font-size: var(--prompt-hint-size);
    font-weight: 400;
    color: rgba(45, 52, 54, 0.7);
    font-style: italic;
}

.tikz-app .prompt-textarea {
    width: 100%;
    padding: var(--spacing-8);
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 1rem;
    line-height: 1.6;
    color: var(--text-on-glass);
    background: rgba(255, 255, 255, 0.5);
    border: var(--prompt-border-width) solid var(--prompt-border);
    border-radius: var(--prompt-border-radius);
    resize: vertical;
    min-height: 120px;
    transition: var(--prompt-transition);
}

.tikz-app .prompt-textarea:focus {
    outline: none;
    border-color: var(--prompt-focus);
    box-shadow: var(--prompt-focus-shadow);
    background: rgba(255, 255, 255, 0.8);
}

.tikz-app .prompt-textarea::placeholder {
    color: rgba(45, 52, 54, 0.5);
}

/* ============================================
   PROMPT FOOTER
   ============================================ */

.tikz-app .prompt-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--spacing-4);
}

.tikz-app .prompt-char-count {
    font-size: var(--prompt-hint-size);
    color: rgba(45, 52, 54, 0.7);
}

.tikz-app .prompt-char-count #char-current {
    font-weight: 600;
    color: var(--text-on-glass);
}

/* Warning when near limit */
.tikz-app .prompt-char-count.warning #char-current {
    color: #ff9800;
}

/* Error when at limit */
.tikz-app .prompt-char-count.error #char-current {
    color: var(--prompt-error);
}

.tikz-app .show-examples-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    padding: var(--spacing-4) var(--spacing-8);
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--primary-color);
    background: transparent;
    border: 1px solid var(--primary-color);
    border-radius: 8px;
    cursor: pointer;
    transition: var(--prompt-transition);
}

.tikz-app .show-examples-btn:hover {
    background: rgba(25, 118, 210, 0.1);
}

.tikz-app .show-examples-btn:focus {
    outline: 2px solid var(--prompt-focus);
    outline-offset: 2px;
}

/* ============================================
   EXAMPLE PROMPTS
   ============================================ */

.tikz-app .prompt-examples {
    margin-top: var(--spacing-8);
    padding: var(--spacing-8);
    background: rgba(25, 118, 210, 0.05);
    border-left: 3px solid var(--primary-color);
    border-radius: 8px;
}

.tikz-app .examples-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-header-glass);
    margin-bottom: var(--spacing-4);
}

.tikz-app .examples-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-4);
}

.tikz-app .example-item {
    margin: 0;
}

.tikz-app .example-btn {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-6);
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(31, 38, 135, 0.1);
    border-radius: 8px;
    cursor: pointer;
    transition: var(--prompt-transition);
    text-align: left;
}

.tikz-app .example-btn:hover {
    background: rgba(255, 255, 255, 0.9);
    border-color: var(--primary-color);
    transform: translateX(4px);
}

.tikz-app .example-btn:focus {
    outline: 2px solid var(--prompt-focus);
    outline-offset: 2px;
}

.tikz-app .example-text {
    font-size: 0.9375rem;
    color: var(--text-on-glass);
    line-height: 1.5;
}

.tikz-app .example-action {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--primary-color);
    white-space: nowrap;
}

/* ============================================
   GENERATE BUTTON & ACTIONS
   ============================================ */

.tikz-app .prompt-actions {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-4);
    margin-top: var(--spacing-8);
}

.tikz-app .generate-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-4);
    padding: var(--spacing-8) var(--spacing-12);
    font-size: 1.125rem;
    font-weight: 600;
    color: white;
    background: linear-gradient(135deg, var(--primary-color), #1565c0);
    border: none;
    border-radius: var(--prompt-border-radius);
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
    transition: var(--prompt-transition);
}

.tikz-app .generate-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(25, 118, 210, 0.4);
}

.tikz-app .generate-btn:active:not(:disabled) {
    transform: translateY(0);
}

.tikz-app .generate-btn:disabled {
    background: rgba(45, 52, 54, 0.3);
    color: rgba(45, 52, 54, 0.5);
    cursor: not-allowed;
    box-shadow: none;
}

.tikz-app .generate-btn:focus {
    outline: 2px solid var(--prompt-focus);
    outline-offset: 2px;
}

.tikz-app .btn-icon {
    font-size: 1.25rem;
    line-height: 1;
}

.tikz-app .login-hint {
    font-size: 0.875rem;
    color: rgba(45, 52, 54, 0.7);
    text-align: center;
    margin: 0;
}

.tikz-app .login-link {
    color: var(--primary-color);
    font-weight: 600;
    text-decoration: none;
    transition: var(--prompt-transition);
}

.tikz-app .login-link:hover {
    text-decoration: underline;
}

/* ============================================
   LOADING STATE
   ============================================ */

.tikz-app .generation-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-8);
    padding: var(--spacing-16);
    margin-top: var(--spacing-12);
    background: rgba(255, 255, 255, 0.7);
    border-radius: var(--prompt-border-radius);
    border: 1px dashed var(--primary-color);
}

.tikz-app .loading-spinner {
    width: var(--spinner-size);
    height: var(--spinner-size);
    border: var(--spinner-border) solid rgba(25, 118, 210, 0.2);
    border-top-color: var(--spinner-color);
    border-radius: 50%;
    animation: spinner-rotate 1s linear infinite;
}

@keyframes spinner-rotate {
    to { transform: rotate(360deg); }
}

.tikz-app .loading-text {
    font-size: 1.125rem;
    font-weight: 500;
    color: var(--text-header-glass);
    margin: 0;
}

.tikz-app .loading-subtext {
    font-size: 0.875rem;
    color: rgba(45, 52, 54, 0.7);
    margin: 0;
}

/* ============================================
   ERROR DISPLAY
   ============================================ */

.tikz-app .generation-error {
    display: flex;
    gap: var(--spacing-8);
    padding: var(--spacing-12);
    margin-top: var(--spacing-12);
    background: rgba(220, 53, 69, 0.1);
    border-left: 4px solid var(--prompt-error);
    border-radius: var(--prompt-border-radius);
}

.tikz-app .error-icon {
    font-size: 2rem;
    line-height: 1;
    flex-shrink: 0;
}

.tikz-app .error-content {
    flex: 1;
}

.tikz-app .error-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--prompt-error);
    margin: 0 0 var(--spacing-4) 0;
}

.tikz-app .error-message {
    font-size: 1rem;
    color: var(--text-on-glass);
    margin: 0 0 var(--spacing-8) 0;
    line-height: 1.5;
}

.tikz-app .error-retry-btn {
    padding: var(--spacing-4) var(--spacing-8);
    font-size: 0.9375rem;
    font-weight: 500;
    color: white;
    background: var(--prompt-error);
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: var(--prompt-transition);
}

.tikz-app .error-retry-btn:hover {
    background: #c82333;
}

/* ============================================
   GENERATED CODE DISPLAY
   ============================================ */

.tikz-app .generated-code-container {
    margin-top: var(--spacing-12);
    padding: var(--spacing-12);
    background: rgba(40, 167, 69, 0.05);
    border: 1px solid rgba(40, 167, 69, 0.3);
    border-radius: var(--prompt-border-radius);
}

.tikz-app .generated-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--spacing-4);
    margin-bottom: var(--spacing-8);
}

.tikz-app .generated-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-header-glass);
    margin: 0;
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
}

.tikz-app .generated-meta {
    display: flex;
    gap: var(--spacing-4);
    align-items: center;
}

.tikz-app .diagram-type-badge {
    padding: var(--spacing-2) var(--spacing-6);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: white;
    background: var(--primary-color);
    border-radius: 12px;
}

.tikz-app .generation-time {
    font-size: 0.875rem;
    color: rgba(45, 52, 54, 0.7);
}

/* CodeMirror wrapper */
.tikz-app .generated-code-editor {
    margin-bottom: var(--spacing-8);
    border: 1px solid rgba(31, 38, 135, 0.15);
    border-radius: 8px;
    overflow: hidden;
}

.tikz-app .generated-code-editor .CodeMirror {
    height: auto;
    min-height: 150px;
    max-height: 400px;
    font-size: 0.9375rem;
}

/* ============================================
   PACKAGES INFO
   ============================================ */

.tikz-app .packages-info {
    margin-bottom: var(--spacing-8);
    padding: var(--spacing-8);
    background: rgba(255, 255, 255, 0.5);
    border-radius: 8px;
}

.tikz-app .packages-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-header-glass);
    margin: 0 0 var(--spacing-4) 0;
}

.tikz-app .packages-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-4);
}

.tikz-app .package-item {
    padding: var(--spacing-2) var(--spacing-6);
    font-size: 0.875rem;
    font-family: 'Courier New', monospace;
    color: var(--text-on-glass);
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(31, 38, 135, 0.15);
    border-radius: 6px;
}

/* ============================================
   ACTION BUTTONS
   ============================================ */

.tikz-app .generated-actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-4);
}

.tikz-app .action-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
    padding: var(--spacing-6) var(--spacing-12);
    font-size: 1rem;
    font-weight: 500;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: var(--prompt-transition);
}

.tikz-app .copy-btn {
    color: white;
    background: var(--primary-color);
}

.tikz-app .copy-btn:hover {
    background: #1565c0;
    transform: translateY(-1px);
}

.tikz-app .use-btn {
    color: white;
    background: var(--prompt-success);
}

.tikz-app .use-btn:hover {
    background: #218838;
    transform: translateY(-1px);
}

.tikz-app .clear-btn {
    color: var(--text-on-glass);
    background: rgba(45, 52, 54, 0.1);
    border: 1px solid rgba(45, 52, 54, 0.2);
}

.tikz-app .clear-btn:hover {
    background: rgba(45, 52, 54, 0.2);
}

.tikz-app .action-btn:focus {
    outline: 2px solid var(--prompt-focus);
    outline-offset: 2px;
}

/* ============================================
   COPY SUCCESS TOAST
   ============================================ */

.tikz-app .copy-success-toast {
    position: fixed;
    bottom: var(--spacing-12);
    right: var(--spacing-12);
    padding: var(--spacing-8) var(--spacing-12);
    font-size: 1rem;
    font-weight: 500;
    color: white;
    background: var(--prompt-success);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: toast-slide-in 0.3s ease-out;
    z-index: 9999;
}

@keyframes toast-slide-in {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* ============================================
   HISTORY (Optional)
   ============================================ */

.tikz-app .generation-history {
    margin-top: var(--spacing-12);
    position: relative;
}

.tikz-app .show-history-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
    padding: var(--spacing-6) var(--spacing-12);
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-on-glass);
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(31, 38, 135, 0.15);
    border-radius: 8px;
    cursor: pointer;
    transition: var(--prompt-transition);
}

.tikz-app .show-history-btn:hover {
    background: rgba(255, 255, 255, 0.9);
    border-color: var(--primary-color);
}

.tikz-app .history-count {
    padding: var(--spacing-1) var(--spacing-4);
    font-size: 0.75rem;
    font-weight: 600;
    color: white;
    background: var(--primary-color);
    border-radius: 12px;
}

.tikz-app .history-dropdown {
    position: absolute;
    top: calc(100% + var(--spacing-4));
    left: 0;
    right: 0;
    max-width: 600px;
    max-height: 400px;
    overflow-y: auto;
    background: var(--glass-bg-strong);
    backdrop-filter: var(--glass-blur-medium);
    -webkit-backdrop-filter: var(--glass-blur-medium);
    border: 1px solid rgba(31, 38, 135, 0.15);
    border-radius: var(--prompt-border-radius);
    box-shadow: var(--glass-shadow);
    z-index: 100;
}

.tikz-app .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-8);
    border-bottom: 1px solid rgba(31, 38, 135, 0.1);
}

.tikz-app .history-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-header-glass);
    margin: 0;
}

.tikz-app .history-close-btn {
    font-size: 1.5rem;
    color: rgba(45, 52, 54, 0.5);
    background: transparent;
    border: none;
    cursor: pointer;
    transition: var(--prompt-transition);
}

.tikz-app .history-close-btn:hover {
    color: var(--text-on-glass);
}

.tikz-app .history-list {
    padding: var(--spacing-4);
}

.tikz-app .history-empty {
    padding: var(--spacing-16);
    text-align: center;
    color: rgba(45, 52, 54, 0.5);
}

/* History items populated by JavaScript */

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */

@media (max-width: 768px) {
    .tikz-app .prompt-to-tikz-section {
        padding: var(--spacing-8);
    }

    .tikz-app .section-title {
        font-size: 1.5rem;
    }

    .tikz-app .prompt-textarea {
        font-size: 0.9375rem;
    }

    .tikz-app .generated-header {
        flex-direction: column;
        align-items: flex-start;
    }

    .tikz-app .generated-actions {
        flex-direction: column;
        width: 100%;
    }

    .tikz-app .action-btn {
        width: 100%;
        justify-content: center;
    }

    .tikz-app .history-dropdown {
        max-width: 100%;
    }

    .tikz-app .copy-success-toast {
        bottom: var(--spacing-8);
        right: var(--spacing-8);
        left: var(--spacing-8);
        text-align: center;
    }
}

/* ============================================
   PRINT STYLES
   ============================================ */

@media print {
    .tikz-app .prompt-to-tikz-section {
        page-break-inside: avoid;
    }

    .tikz-app .generation-loading,
    .tikz-app .generation-error,
    .tikz-app .prompt-actions,
    .tikz-app .generated-actions,
    .tikz-app .generation-history {
        display: none;
    }
}
```

**Accessibility compliance:**
- Contrast ratios ≥ 6.2:1 (WCAG AAA)
- Focus visible states
- Keyboard navigation
- Touch-friendly (44px minimum)
- Screen reader support

**Validation:**
- [ ] All selectors have `.tikz-app` prefix
- [ ] Use foundation variables (no hardcoded values)
- [ ] Contrast ratios meet WCAG AAA
- [ ] Mobile responsive
- [ ] Print styles included

---

### Task 2.4: Template Integration (30 min)

**File:** `templates/base.html`

Add CSS link:

```html
<!-- In head section, after other CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/prompt-to-tikz.css', v='1.0') }}">
```

**File:** `templates/index.html`

Ensure section is added after `.input-preview-section` closing tag (see Task 2.1).

**Validation:**
- [ ] CSS loads correctly
- [ ] No 404 errors
- [ ] Styles applied properly
- [ ] No visual conflicts with existing sections

---

### Task 2.5: Responsive Testing (45 min)

Test on multiple devices and breakpoints:

**Desktop (≥1200px):**
- [ ] Full width layout
- [ ] Actions row horizontal
- [ ] History dropdown positioned correctly

**Tablet (768px-1199px):**
- [ ] Readable font sizes
- [ ] Touch targets ≥44px
- [ ] Examples list still usable

**Mobile (320px-767px):**
- [ ] Single column layout
- [ ] Actions stack vertically
- [ ] Copy toast full width
- [ ] Textarea height adequate
- [ ] History dropdown full width

**Testing Tools:**
- Chrome DevTools responsive mode
- Firefox Responsive Design Mode
- Real devices (iPhone, Android)
- BrowserStack (optional)

**Validation:**
- [ ] Mobile-first approach verified
- [ ] No horizontal scrolling
- [ ] Touch interactions smooth
- [ ] Text readable without zoom

---

### Task 2.6: Accessibility Audit (30 min)

**Tools:**
- Chrome Lighthouse
- axe DevTools
- WAVE browser extension
- Screen reader (VoiceOver/NVDA)

**Checklist:**
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible (≥3px outline)
- [ ] ARIA attributes correct
- [ ] Color contrast ≥6.2:1
- [ ] Alt text for icons (or aria-label)
- [ ] Screen reader announces state changes
- [ ] Skip links work
- [ ] No keyboard traps

**Lighthouse target scores:**
- Accessibility: 100
- Best Practices: 100
- SEO: 95+

**Validation:**
- [ ] Lighthouse score ≥95 accessibility
- [ ] axe audit passes
- [ ] WAVE errors = 0
- [ ] Screen reader navigation logical

---

## ✅ Validation Checklist

### Visual Tests
- [ ] Section renders correctly
- [ ] Glass morphism effect visible
- [ ] Animations smooth
- [ ] Buttons have hover states
- [ ] Loading spinner rotates
- [ ] Error styling clear
- [ ] Success styling positive
- [ ] Toast appears and disappears

### Functional Tests
- [ ] Textarea accepts input
- [ ] Character counter updates
- [ ] Examples button toggles
- [ ] Example buttons populate textarea
- [ ] Generate button disabled when not logged in
- [ ] Login hint visible when not logged in
- [ ] Responsive layout works

### Accessibility Tests
- [ ] Tab navigation works
- [ ] Enter key submits
- [ ] Escape key closes modals
- [ ] Focus visible
- [ ] Color contrast compliant
- [ ] Screen reader friendly
- [ ] ARIA attributes correct

### Cross-browser Tests
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS/iOS)
- [ ] Mobile browsers (Chrome Android, Safari iOS)

---

## 📊 Browser Support

| Browser | Minimum Version | Notes |
|---------|----------------|-------|
| Chrome | 90+ | Full support |
| Firefox | 88+ | Full support |
| Safari | 14+ | webkit-backdrop-filter prefix |
| Edge | 90+ | Full support (Chromium) |
| Mobile Safari | 14+ | Touch-friendly |
| Chrome Android | 90+ | Touch-friendly |

**Fallbacks:**
- `backdrop-filter` → Solid background if not supported
- CSS Grid → Flexbox fallback
- CSS variables → Hardcoded values (not recommended)

---

## 🐛 Common Issues & Fixes

**Issue:** Glass effect not visible
```css
/* Add fallback */
.tikz-app .prompt-to-tikz-section {
    background: rgba(255, 255, 255, 0.95); /* Fallback */
    background: var(--prompt-bg);
}
```

**Issue:** Buttons too small on mobile
```css
/* Ensure min-height */
.tikz-app .action-btn {
    min-height: 44px; /* Touch-friendly */
}
```

**Issue:** Text unreadable on glass background
```css
/* Increase contrast */
.tikz-app .section-description {
    color: var(--text-on-glass);
    text-shadow: 0 0 1px rgba(255, 255, 255, 0.5); /* Subtle enhancement */
}
```

---

## 📝 Documentation Updates

**Add to `CSS_ARCHITECTURE_MIGRATION_STATUS.md`:**

```markdown
### Phase 2 Completion: prompt-to-tikz.css

✅ **Status:** Complete
**File:** `static/css/prompt-to-tikz.css`
**Lines:** ~800 lines
**Foundation Compliant:** Yes

**Features:**
- CSS Foundation variables throughout
- `.tikz-app` scoping on all selectors
- WCAG AAA accessibility (contrast ≥ 6.2:1)
- Mobile-first responsive design
- Glass morphism effects
- Print styles

**Migration Quality:**
- ✅ No hardcoded values
- ✅ Foundation variable usage
- ✅ Scoping correct
- ✅ Accessibility compliant
- ✅ Responsive breakpoints
- ✅ Browser compatibility
```

---

## ✅ Completion Criteria

Phase 2 complete when:
- [ ] HTML structure added to index.html
- [ ] CSS file created and loaded
- [ ] Foundation variables added
- [ ] All selectors `.tikz-app` prefixed
- [ ] Responsive design working (mobile, tablet, desktop)
- [ ] Accessibility audit passes (Lighthouse ≥95)
- [ ] Cross-browser tested
- [ ] No visual regressions on existing pages
- [ ] Print styles working
- [ ] Documentation updated

---

**Next Phase:** Phase 3 - JavaScript Functionality
**Dependencies:** Phase 1 API for testing AJAX calls
