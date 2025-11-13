# Phase 3: JavaScript Functionality

**Duration:** 6-8 hours
**Priority:** High
**Dependencies:** Phase 1 (API endpoints), Phase 2 (UI structure)

---

## 🎯 Objectives

Implement JavaScript logic for AJAX requests, CodeMirror integration, clipboard operations, state management, and error handling.

---

## 📋 Tasks Breakdown

### Task 3.1: Module Structure (30 min)

**File:** `static/js/prompt-to-tikz.js`

Create modular, maintainable JavaScript:

```javascript
/**
 * Prompt-to-TikZ Generation Module
 *
 * Handles AI-powered TikZ code generation from natural language prompts.
 *
 * Features:
 * - AJAX generation requests
 * - CodeMirror integration
 * - Clipboard operations
 * - History management
 * - Error handling
 *
 * Dependencies:
 * - CodeMirror (loaded in base template)
 * - Clipboard API (native)
 *
 * @version 1.0.0
 */

(function() {
    'use strict';

    // ==============================================
    // MODULE STATE
    // ==============================================

    const state = {
        isGenerating: false,
        currentGeneration: null,
        generatedCodeEditor: null,
        history: [],
        historyVisible: false
    };

    // ==============================================
    // DOM ELEMENTS
    // ==============================================

    const elements = {
        promptTextarea: document.getElementById('tikz-prompt-input'),
        charCount: document.getElementById('char-current'),
        charCountContainer: document.getElementById('prompt-char-count'),
        showExamplesBtn: document.getElementById('show-examples-btn'),
        promptExamples: document.getElementById('prompt-examples'),
        exampleButtons: document.querySelectorAll('.example-btn'),
        generateBtn: document.getElementById('generate-tikz-btn'),
        loadingContainer: document.getElementById('generation-loading'),
        errorContainer: document.getElementById('generation-error'),
        errorMessage: document.getElementById('generation-error-message'),
        retryBtn: document.getElementById('retry-generation-btn'),
        generatedContainer: document.getElementById('generated-code-container'),
        generatedEditor: document.getElementById('generated-code-editor'),
        diagramTypeBadge: document.getElementById('diagram-type-badge'),
        generationTime: document.getElementById('generation-time'),
        packagesList: document.getElementById('packages-list'),
        copyBtn: document.getElementById('copy-generated-btn'),
        useBtn: document.getElementById('use-generated-btn'),
        clearBtn: document.getElementById('clear-generated-btn'),
        copyToast: document.getElementById('copy-success-toast'),
        showHistoryBtn: document.getElementById('show-history-btn'),
        historyDropdown: document.getElementById('history-dropdown'),
        historyList: document.getElementById('history-list'),
        historyCount: document.getElementById('history-count')
    };

    // ==============================================
    // INITIALIZATION
    // ==============================================

    function init() {
        // Check if user is logged in
        if (!window.appState || !window.appState.loggedIn) {
            console.log('User not logged in, skipping prompt-to-tikz initialization');
            return;
        }

        setupEventListeners();
        initializeCodeMirror();
        loadHistory();

        console.log('Prompt-to-TikZ module initialized');
    }

    // ==============================================
    // EVENT LISTENERS
    // ==============================================

    function setupEventListeners() {
        // Character counter
        elements.promptTextarea?.addEventListener('input', updateCharCount);

        // Show/hide examples
        elements.showExamplesBtn?.addEventListener('click', toggleExamples);

        // Example buttons
        elements.exampleButtons?.forEach(btn => {
            btn.addEventListener('click', useExample);
        });

        // Generate button
        elements.generateBtn?.addEventListener('click', handleGenerate);

        // Retry button
        elements.retryBtn?.addEventListener('click', handleGenerate);

        // Action buttons
        elements.copyBtn?.addEventListener('click', copyToClipboard);
        elements.useBtn?.addEventListener('click', useGeneratedCode);
        elements.clearBtn?.addEventListener('click', clearGenerated);

        // History button
        elements.showHistoryBtn?.addEventListener('click', toggleHistory);

        // Close history dropdown when clicking outside
        document.addEventListener('click', handleOutsideClick);

        // Keyboard shortcuts
        document.addEventListener('keydown', handleKeyboardShortcuts);
    }

    // ==============================================
    // CHARACTER COUNTER
    // ==============================================

    function updateCharCount() {
        const current = elements.promptTextarea.value.length;
        const max = parseInt(elements.promptTextarea.getAttribute('maxlength')) || 500;

        elements.charCount.textContent = current;

        // Update styling based on proximity to limit
        elements.charCountContainer.classList.remove('warning', 'error');

        if (current >= max) {
            elements.charCountContainer.classList.add('error');
        } else if (current >= max * 0.9) {
            elements.charCountContainer.classList.add('warning');
        }
    }

    // ==============================================
    // EXAMPLES
    // ==============================================

    function toggleExamples() {
        const isExpanded = elements.showExamplesBtn.getAttribute('aria-expanded') === 'true';

        elements.showExamplesBtn.setAttribute('aria-expanded', !isExpanded);
        elements.promptExamples.hidden = isExpanded;
    }

    function useExample(event) {
        const prompt = event.currentTarget.closest('.example-item').dataset.prompt;

        if (prompt) {
            elements.promptTextarea.value = prompt;
            updateCharCount();

            // Focus textarea
            elements.promptTextarea.focus();

            // Scroll to textarea
            elements.promptTextarea.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Optional: Auto-hide examples
            elements.promptExamples.hidden = true;
            elements.showExamplesBtn.setAttribute('aria-expanded', 'false');
        }
    }

    // ==============================================
    // GENERATION
    // ==============================================

    async function handleGenerate() {
        // Validation
        const prompt = elements.promptTextarea.value.trim();

        if (!prompt) {
            showError('Vui lòng nhập mô tả hình vẽ.');
            elements.promptTextarea.focus();
            return;
        }

        const maxLength = parseInt(elements.promptTextarea.getAttribute('maxlength')) || 500;
        if (prompt.length > maxLength) {
            showError(`Mô tả quá dài (tối đa ${maxLength} ký tự).`);
            return;
        }

        // Clear previous results
        hideError();
        hideGenerated();

        // Show loading
        showLoading();

        // Update state
        state.isGenerating = true;
        elements.generateBtn.disabled = true;

        try {
            const response = await fetch('/api/tikz/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    save_history: true
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                handleGenerationSuccess(data);
            } else {
                handleGenerationError(data);
            }

        } catch (error) {
            console.error('Generation error:', error);
            showError('Có lỗi xảy ra khi kết nối đến server. Vui lòng thử lại.');
        } finally {
            hideLoading();
            state.isGenerating = false;
            elements.generateBtn.disabled = false;
        }
    }

    function handleGenerationSuccess(data) {
        // Store generation
        state.currentGeneration = {
            prompt: elements.promptTextarea.value.trim(),
            tikzCode: data.tikz_code,
            type: data.type,
            packages: data.latex_preamble,
            generationId: data.generation_id,
            timestamp: new Date().toISOString()
        };

        // Display generated code
        displayGeneratedCode(state.currentGeneration);

        // Reload history if generation was saved
        if (data.generation_id) {
            loadHistory();
        }

        // Scroll to result
        elements.generatedContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function handleGenerationError(data) {
        let errorMessage = 'Có lỗi xảy ra. Vui lòng thử lại.';

        if (data.error) {
            errorMessage = data.error;
        }

        // Handle specific error codes
        switch (data.code) {
            case 'EMPTY_PROMPT':
                errorMessage = 'Vui lòng nhập mô tả hình vẽ.';
                elements.promptTextarea.focus();
                break;
            case 'PROMPT_TOO_LONG':
                errorMessage = data.error;
                break;
            case 'GENERATION_FAILED':
                errorMessage = 'Không thể sinh mã TikZ. ' + data.error;
                break;
            case 'INTERNAL_ERROR':
                errorMessage = 'Lỗi hệ thống. Vui lòng thử lại sau.';
                break;
        }

        showError(errorMessage);
    }

    // ==============================================
    // UI STATE MANAGEMENT
    // ==============================================

    function showLoading() {
        elements.loadingContainer.hidden = false;
        elements.loadingContainer.setAttribute('aria-busy', 'true');
    }

    function hideLoading() {
        elements.loadingContainer.hidden = true;
        elements.loadingContainer.setAttribute('aria-busy', 'false');
    }

    function showError(message) {
        elements.errorMessage.textContent = message;
        elements.errorContainer.hidden = false;

        // Scroll to error
        elements.errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideError() {
        elements.errorContainer.hidden = true;
    }

    function hideGenerated() {
        elements.generatedContainer.hidden = true;
    }

    // ==============================================
    // CODE DISPLAY
    // ==============================================

    function initializeCodeMirror() {
        if (!elements.generatedEditor || !window.CodeMirror) {
            console.warn('CodeMirror not available');
            return;
        }

        state.generatedCodeEditor = CodeMirror(elements.generatedEditor, {
            mode: 'stex', // LaTeX mode
            lineNumbers: true,
            readOnly: true,
            theme: 'default',
            lineWrapping: true,
            viewportMargin: Infinity
        });
    }

    function displayGeneratedCode(generation) {
        // Update CodeMirror
        if (state.generatedCodeEditor) {
            state.generatedCodeEditor.setValue(generation.tikzCode);
            state.generatedCodeEditor.refresh();
        } else {
            // Fallback if CodeMirror not available
            elements.generatedEditor.textContent = generation.tikzCode;
        }

        // Update diagram type badge
        const typeNames = {
            'variation_table': 'Bảng biến thiên',
            'function_graph': 'Đồ thị hàm số',
            'geometry': 'Hình học',
            'diagram': 'Sơ đồ',
            'other': 'Khác'
        };
        elements.diagramTypeBadge.textContent = typeNames[generation.type] || 'Khác';

        // Update timestamp
        const timestamp = new Date(generation.timestamp);
        elements.generationTime.textContent = `Sinh lúc ${timestamp.toLocaleTimeString('vi-VN')}`;

        // Update packages list
        displayPackages(generation.packages);

        // Show container
        elements.generatedContainer.hidden = false;
    }

    function displayPackages(packages) {
        elements.packagesList.innerHTML = '';

        if (!packages || packages.length === 0) {
            elements.packagesList.innerHTML = '<li class="package-item">Không yêu cầu package đặc biệt</li>';
            return;
        }

        packages.forEach(pkg => {
            const li = document.createElement('li');
            li.className = 'package-item';
            li.textContent = `\\usepackage{${pkg}}`;
            elements.packagesList.appendChild(li);
        });
    }

    // ==============================================
    // CLIPBOARD
    // ==============================================

    async function copyToClipboard() {
        if (!state.currentGeneration) return;

        try {
            await navigator.clipboard.writeText(state.currentGeneration.tikzCode);
            showCopyToast();
        } catch (error) {
            console.error('Failed to copy:', error);

            // Fallback: Select text
            if (state.generatedCodeEditor) {
                state.generatedCodeEditor.execCommand('selectAll');
            }

            alert('Không thể tự động sao chép. Vui lòng dùng Ctrl+C/Cmd+C để sao chép.');
        }
    }

    function showCopyToast() {
        elements.copyToast.hidden = false;

        setTimeout(() => {
            elements.copyToast.hidden = true;
        }, 3000);
    }

    // ==============================================
    // USE GENERATED CODE
    // ==============================================

    function useGeneratedCode() {
        if (!state.currentGeneration) return;

        // Get main TikZ editor (CodeMirror instance from index.js)
        const mainEditor = window.tikzCodeMirror || document.getElementById('code');

        if (window.tikzCodeMirror) {
            // CodeMirror instance
            window.tikzCodeMirror.setValue(state.currentGeneration.tikzCode);
            window.tikzCodeMirror.refresh();
        } else if (mainEditor) {
            // Fallback to textarea
            mainEditor.value = state.currentGeneration.tikzCode;
        }

        // Mark as used in backend (if saved)
        if (state.currentGeneration.generationId) {
            markAsUsed(state.currentGeneration.generationId);
        }

        // Scroll to main editor
        if (mainEditor) {
            mainEditor.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        // Show feedback
        showCopyToast();
    }

    async function markAsUsed(generationId) {
        try {
            await fetch(`/api/tikz/history/${generationId}/use`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        } catch (error) {
            console.error('Failed to mark as used:', error);
            // Non-critical, don't show error to user
        }
    }

    // ==============================================
    // CLEAR GENERATED
    // ==============================================

    function clearGenerated() {
        // Confirmation
        if (!confirm('Xóa mã đã sinh? Bạn có thể xem lại trong lịch sử.')) {
            return;
        }

        // Clear state
        state.currentGeneration = null;

        // Clear editor
        if (state.generatedCodeEditor) {
            state.generatedCodeEditor.setValue('');
        }

        // Hide container
        hideGenerated();

        // Focus prompt textarea
        elements.promptTextarea.focus();
    }

    // ==============================================
    // HISTORY MANAGEMENT
    // ==============================================

    async function loadHistory() {
        if (!elements.showHistoryBtn) return; // History feature disabled

        try {
            const response = await fetch('/api/tikz/history?limit=10');
            const data = await response.json();

            if (response.ok && data.success) {
                state.history = data.generations;
                updateHistoryUI();
            }
        } catch (error) {
            console.error('Failed to load history:', error);
            // Non-critical, don't show error to user
        }
    }

    function updateHistoryUI() {
        if (!elements.historyList) return;

        // Update count badge
        if (state.history.length > 0) {
            elements.historyCount.textContent = state.history.length;
            elements.historyCount.hidden = false;
        } else {
            elements.historyCount.hidden = true;
        }

        // Clear list
        elements.historyList.innerHTML = '';

        // Show empty state
        if (state.history.length === 0) {
            elements.historyList.innerHTML = '<p class="history-empty">Chưa có lịch sử</p>';
            return;
        }

        // Populate list
        state.history.forEach(gen => {
            const item = createHistoryItem(gen);
            elements.historyList.appendChild(item);
        });
    }

    function createHistoryItem(generation) {
        const item = document.createElement('div');
        item.className = 'history-item';

        const timestamp = new Date(generation.created_at);
        const timeStr = timestamp.toLocaleString('vi-VN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        item.innerHTML = `
            <div class="history-item-header">
                <span class="history-item-time">${timeStr}</span>
                <span class="history-item-type">${generation.type}</span>
            </div>
            <p class="history-item-prompt">${escapeHtml(generation.prompt)}</p>
            <button type="button" class="history-item-use-btn" data-id="${generation.id}">
                Dùng lại
            </button>
        `;

        // Add click handler
        const useBtn = item.querySelector('.history-item-use-btn');
        useBtn.addEventListener('click', () => useHistoryItem(generation));

        return item;
    }

    function useHistoryItem(generation) {
        // Populate prompt textarea
        elements.promptTextarea.value = generation.prompt;
        updateCharCount();

        // Display code directly
        state.currentGeneration = {
            prompt: generation.prompt,
            tikzCode: generation.tikz_code,
            type: generation.type,
            packages: JSON.parse(generation.latex_packages || '[]'),
            generationId: generation.id,
            timestamp: generation.created_at
        };

        displayGeneratedCode(state.currentGeneration);

        // Close history
        elements.historyDropdown.hidden = true;
        state.historyVisible = false;

        // Scroll to generated code
        elements.generatedContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function toggleHistory() {
        state.historyVisible = !state.historyVisible;
        elements.historyDropdown.hidden = !state.historyVisible;
        elements.showHistoryBtn.setAttribute('aria-expanded', state.historyVisible);
    }

    // ==============================================
    // KEYBOARD SHORTCUTS
    // ==============================================

    function handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + Enter: Generate
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            if (document.activeElement === elements.promptTextarea) {
                event.preventDefault();
                handleGenerate();
            }
        }

        // Escape: Close history/examples
        if (event.key === 'Escape') {
            if (state.historyVisible) {
                elements.historyDropdown.hidden = true;
                state.historyVisible = false;
            }
            if (!elements.promptExamples.hidden) {
                elements.promptExamples.hidden = true;
                elements.showExamplesBtn.setAttribute('aria-expanded', 'false');
            }
        }
    }

    // ==============================================
    // UTILITY FUNCTIONS
    // ==============================================

    function handleOutsideClick(event) {
        // Close history dropdown if clicking outside
        if (state.historyVisible &&
            elements.historyDropdown &&
            !elements.historyDropdown.contains(event.target) &&
            event.target !== elements.showHistoryBtn) {
            elements.historyDropdown.hidden = true;
            state.historyVisible = false;
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ==============================================
    // EXPORT MODULE
    // ==============================================

    window.PromptToTikZ = {
        init,
        generateFromPrompt: handleGenerate,
        useGeneratedCode,
        clearGenerated,
        loadHistory
    };

    // Auto-initialize when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
```

**Validation:**
- [ ] Module loads without errors
- [ ] No global scope pollution
- [ ] Event listeners attached correctly
- [ ] CodeMirror integration works

---

### Task 3.2: Template Integration (15 min)

**File:** `templates/index.html`

Add script tag:

```html
{% block extra_js %}
<!-- Existing scripts -->
<script src="{{ url_for('static', filename='js/navigation.js', v='1.0') }}"></script>
<script src="{{ url_for('static', filename='js/file_card.js', v='1.3') }}"></script>
<script src="{{ url_for('static', filename='js/index.js', v='1.0') }}"></script>

<!-- Prompt-to-TikZ module -->
<script src="{{ url_for('static', filename='js/prompt-to-tikz.js', v='1.0') }}"></script>
{% endblock %}
```

**Validation:**
- [ ] Script loads after dependencies
- [ ] No 404 errors
- [ ] Module initializes correctly

---

### Task 3.3: History CSS Styles (30 min)

**File:** `static/css/prompt-to-tikz.css`

Add history item styles:

```css
/* ============================================
   HISTORY ITEMS (populated by JS)
   ============================================ */

.tikz-app .history-item {
    padding: var(--spacing-8);
    margin-bottom: var(--spacing-4);
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(31, 38, 135, 0.1);
    border-radius: 8px;
    transition: var(--prompt-transition);
}

.tikz-app .history-item:hover {
    background: rgba(255, 255, 255, 0.9);
    border-color: var(--primary-color);
}

.tikz-app .history-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-4);
}

.tikz-app .history-item-time {
    font-size: 0.875rem;
    color: rgba(45, 52, 54, 0.7);
}

.tikz-app .history-item-type {
    padding: var(--spacing-1) var(--spacing-4);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: white;
    background: var(--primary-color);
    border-radius: 8px;
}

.tikz-app .history-item-prompt {
    font-size: 0.9375rem;
    color: var(--text-on-glass);
    margin: 0 0 var(--spacing-6) 0;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.tikz-app .history-item-use-btn {
    width: 100%;
    padding: var(--spacing-4) var(--spacing-8);
    font-size: 0.9375rem;
    font-weight: 500;
    color: white;
    background: var(--primary-color);
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: var(--prompt-transition);
}

.tikz-app .history-item-use-btn:hover {
    background: #1565c0;
}
```

**Validation:**
- [ ] History items styled correctly
- [ ] Hover states work
- [ ] Text truncation works

---

### Task 3.4: Error Handling & Edge Cases (60 min)

Implement robust error handling:

**Network Errors:**
```javascript
// In handleGenerate() catch block
catch (error) {
    console.error('Generation error:', error);

    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        showError('Không thể kết nối đến server. Kiểm tra kết nối mạng và thử lại.');
    } else if (error.name === 'AbortError') {
        showError('Yêu cầu bị hủy. Vui lòng thử lại.');
    } else {
        showError('Có lỗi xảy ra. Vui lòng thử lại sau.');
    }
}
```

**Rate Limit Handling:**
```javascript
// In handleGenerate()
if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    const message = retryAfter
        ? `Đã vượt giới hạn. Vui lòng thử lại sau ${retryAfter} giây.`
        : 'Đã vượt giới hạn. Vui lòng chờ vài phút.';
    showError(message);
    return;
}
```

**Timeout Handling:**
```javascript
// Add timeout to fetch
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 35000); // 35s (server timeout 30s + buffer)

try {
    const response = await fetch('/api/tikz/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, save_history: true }),
        signal: controller.signal
    });

    clearTimeout(timeoutId);
    // ... rest of handling
} catch (error) {
    clearTimeout(timeoutId);
    // ... error handling
}
```

**CodeMirror Fallback:**
```javascript
function initializeCodeMirror() {
    if (!window.CodeMirror) {
        console.warn('CodeMirror not available, using textarea fallback');

        // Create plain textarea fallback
        const textarea = document.createElement('textarea');
        textarea.className = 'generated-code-textarea';
        textarea.readOnly = true;
        textarea.rows = 10;
        elements.generatedEditor.appendChild(textarea);

        state.generatedCodeEditor = {
            setValue: (value) => { textarea.value = value; },
            getValue: () => textarea.value,
            refresh: () => {},
            execCommand: (cmd) => {
                if (cmd === 'selectAll') textarea.select();
            }
        };

        return;
    }

    // Normal CodeMirror initialization
    state.generatedCodeEditor = CodeMirror(elements.generatedEditor, {
        mode: 'stex',
        lineNumbers: true,
        readOnly: true,
        theme: 'default',
        lineWrapping: true
    });
}
```

**Validation:**
- [ ] Network errors handled
- [ ] Rate limits displayed clearly
- [ ] Timeout shows user-friendly message
- [ ] CodeMirror fallback works
- [ ] No unhandled promise rejections

---

### Task 3.5: Integration with Main Editor (30 min)

Ensure seamless integration:

**File:** `static/js/index.js`

Expose CodeMirror instance globally:

```javascript
// In index.js, after CodeMirror initialization
window.tikzCodeMirror = editor; // Make accessible to prompt-to-tikz.js
```

**File:** `static/js/prompt-to-tikz.js`

Use main editor:

```javascript
function useGeneratedCode() {
    if (!state.currentGeneration) return;

    // Get main editor
    const mainEditor = window.tikzCodeMirror;

    if (mainEditor && mainEditor.setValue) {
        // CodeMirror instance available
        mainEditor.setValue(state.currentGeneration.tikzCode);
        mainEditor.refresh();

        // Trigger any compilation if auto-compile enabled
        if (window.tikzApp && window.tikzApp.compile) {
            window.tikzApp.compile();
        }
    } else {
        // Fallback to textarea
        const textarea = document.getElementById('code');
        if (textarea) {
            textarea.value = state.currentGeneration.tikzCode;

            // Trigger input event for any listeners
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    // ... rest of function
}
```

**Validation:**
- [ ] Generated code populates main editor
- [ ] CodeMirror refreshes correctly
- [ ] Textarea fallback works
- [ ] Scroll animation smooth

---

### Task 3.6: Testing (120 min)

Comprehensive testing suite:

**Unit Tests (Jest/Mocha):**

```javascript
// tests/js/test-prompt-to-tikz.js

describe('Prompt-to-TikZ Module', () => {
    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <textarea id="tikz-prompt-input" maxlength="500"></textarea>
            <span id="char-current">0</span>
            <!-- ... other elements -->
        `;

        // Mock fetch
        global.fetch = jest.fn();

        // Initialize module
        window.PromptToTikZ.init();
    });

    test('Character counter updates on input', () => {
        const textarea = document.getElementById('tikz-prompt-input');
        const counter = document.getElementById('char-current');

        textarea.value = 'Test prompt';
        textarea.dispatchEvent(new Event('input'));

        expect(counter.textContent).toBe('11');
    });

    test('Example button populates textarea', () => {
        const exampleBtn = document.querySelector('.example-btn');
        const textarea = document.getElementById('tikz-prompt-input');

        exampleBtn.click();

        expect(textarea.value).toBe(exampleBtn.dataset.prompt);
    });

    test('Generate button calls API', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({
                success: true,
                tikz_code: '\\begin{tikzpicture}...',
                type: 'variation_table',
                latex_preamble: ['tikz']
            })
        });

        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = 'Test prompt';

        await window.PromptToTikZ.generateFromPrompt();

        expect(global.fetch).toHaveBeenCalledWith('/api/tikz/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: 'Test prompt',
                save_history: true
            })
        });
    });

    test('Error shown on empty prompt', async () => {
        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = '';

        await window.PromptToTikZ.generateFromPrompt();

        const errorContainer = document.getElementById('generation-error');
        expect(errorContainer.hidden).toBe(false);
    });

    test('Clipboard copy works', async () => {
        navigator.clipboard = {
            writeText: jest.fn().mockResolvedValue()
        };

        // Set current generation
        window.PromptToTikZ.currentGeneration = {
            tikzCode: '\\begin{tikzpicture}...'
        };

        await window.PromptToTikZ.copyToClipboard();

        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('\\begin{tikzpicture}...');
    });
});
```

**Integration Tests:**

```javascript
// tests/integration/test-prompt-to-tikz-flow.js

describe('Prompt-to-TikZ Full Flow', () => {
    it('completes full generation workflow', async () => {
        // 1. User enters prompt
        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = 'vẽ bảng biến thiên y = x^2';

        // 2. Clicks generate
        const generateBtn = document.getElementById('generate-tikz-btn');
        generateBtn.click();

        // 3. Wait for loading
        await waitForElement('#generation-loading:not([hidden])');

        // 4. Wait for result
        await waitForElement('#generated-code-container:not([hidden])');

        // 5. Verify code displayed
        const codeEditor = document.getElementById('generated-code-editor');
        expect(codeEditor).toBeTruthy();

        // 6. Click "Use code"
        const useBtn = document.getElementById('use-generated-btn');
        useBtn.click();

        // 7. Verify main editor populated
        const mainEditor = document.getElementById('code');
        expect(mainEditor.value).toContain('tikzpicture');
    });
});
```

**Manual Testing Checklist:**
- [ ] Generate from Vietnamese prompt
- [ ] Generate from English prompt
- [ ] Handle empty prompt
- [ ] Handle too long prompt (>500 chars)
- [ ] Show loading spinner during generation
- [ ] Display generated code with syntax highlighting
- [ ] Copy to clipboard works
- [ ] Use code button populates main editor
- [ ] Clear button works
- [ ] Example buttons work
- [ ] Character counter updates
- [ ] History loads on page load
- [ ] History items clickable
- [ ] Rate limit error shows (after 10 requests)
- [ ] Network error handled
- [ ] Keyboard shortcuts work (Ctrl+Enter, Escape)
- [ ] Mobile touch interactions smooth
- [ ] Screen reader announces state changes

**Validation:**
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing checklist complete
- [ ] No console errors
- [ ] No memory leaks (check DevTools)

---

## ✅ Completion Criteria

Phase 3 complete when:
- [ ] JavaScript module functional
- [ ] AJAX requests to API working
- [ ] CodeMirror integration working
- [ ] Clipboard operations functional
- [ ] History management working
- [ ] Error handling comprehensive
- [ ] Keyboard shortcuts working
- [ ] All tests passing
- [ ] No console errors
- [ ] Memory usage acceptable
- [ ] Performance acceptable (<100ms interactions)

---

**Next Phase:** Phase 4 - Integration & Optimization
**Focus:** Performance, caching, enhanced features
