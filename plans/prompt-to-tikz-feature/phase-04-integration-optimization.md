# Phase 4: Integration & Optimization

**Duration:** 4-6 hours
**Priority:** Medium (Enhancement)
**Dependencies:** Phase 1, 2, 3 complete

---

## 🎯 Objectives

Optimize performance, add caching, enhance error messages, implement advanced history features, polish UX.

---

## 📋 Tasks Breakdown

### Task 4.1: Performance Optimization (90 min)

**Debounce Character Counter:**

```javascript
// In prompt-to-tikz.js

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Apply to character counter
const debouncedCharCount = debounce(updateCharCount, 100);
elements.promptTextarea?.addEventListener('input', debouncedCharCount);
```

**Lazy Load History:**

```javascript
// Only load history when user clicks history button
let historyLoaded = false;

async function toggleHistory() {
    if (!historyLoaded) {
        showHistoryLoading();
        await loadHistory();
        historyLoaded = true;
        hideHistoryLoading();
    }

    state.historyVisible = !state.historyVisible;
    elements.historyDropdown.hidden = !state.historyVisible;
    elements.showHistoryBtn.setAttribute('aria-expanded', state.historyVisible);
}

function showHistoryLoading() {
    elements.historyList.innerHTML = '<div class="history-loading"><span class="spinner"></span>Đang tải...</div>';
}

function hideHistoryLoading() {
    // History list will be populated by updateHistoryUI()
}
```

**Optimize CodeMirror Refresh:**

```javascript
// Debounce CodeMirror refresh to reduce reflows
const debouncedRefresh = debounce(() => {
    if (state.generatedCodeEditor && state.generatedCodeEditor.refresh) {
        state.generatedCodeEditor.refresh();
    }
}, 150);

// Call after DOM updates
function displayGeneratedCode(generation) {
    // ... existing code ...

    // Show container first
    elements.generatedContainer.hidden = false;

    // Defer CodeMirror refresh
    requestAnimationFrame(() => {
        debouncedRefresh();
    });
}
```

**Reduce DOM Queries:**

```javascript
// Cache frequently accessed elements
const cache = {
    mainEditor: null,
    mainTextarea: null
};

function getMainEditor() {
    if (!cache.mainEditor) {
        cache.mainEditor = window.tikzCodeMirror;
        cache.mainTextarea = document.getElementById('code');
    }
    return cache.mainEditor || cache.mainTextarea;
}

function useGeneratedCode() {
    const editor = getMainEditor();
    // ... use cached editor ...
}
```

**Validation:**
- [ ] Character counter responsive
- [ ] History loads only when needed
- [ ] CodeMirror refresh smooth
- [ ] No unnecessary DOM queries
- [ ] Performance metrics improved (DevTools)

---

### Task 4.2: Caching Strategy (60 min)

**Client-side Cache for Prompts:**

```javascript
// Simple in-memory cache with LRU eviction
class PromptCache {
    constructor(maxSize = 20) {
        this.cache = new Map();
        this.maxSize = maxSize;
    }

    get(prompt) {
        const key = this.hashPrompt(prompt);
        if (this.cache.has(key)) {
            // Move to end (most recently used)
            const value = this.cache.get(key);
            this.cache.delete(key);
            this.cache.set(key, value);
            return value;
        }
        return null;
    }

    set(prompt, result) {
        const key = this.hashPrompt(prompt);

        // Remove oldest if at capacity
        if (this.cache.size >= this.maxSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }

        this.cache.set(key, {
            ...result,
            cached: true,
            cachedAt: new Date().toISOString()
        });
    }

    hashPrompt(prompt) {
        // Simple hash function (for demo; use better hash in production)
        return prompt.trim().toLowerCase();
    }

    clear() {
        this.cache.clear();
    }
}

// Initialize cache
const promptCache = new PromptCache(20);

// Modify handleGenerate to check cache
async function handleGenerate() {
    const prompt = elements.promptTextarea.value.trim();

    if (!prompt) {
        showError('Vui lòng nhập mô tả hình vẽ.');
        return;
    }

    // Check cache first
    const cached = promptCache.get(prompt);
    if (cached) {
        console.log('Using cached result for prompt:', prompt);
        handleGenerationSuccess({
            ...cached,
            generation_id: null // Don't save duplicate
        });
        return;
    }

    // ... proceed with API call ...

    // On success, cache result
    if (response.ok && data.success) {
        promptCache.set(prompt, data);
        handleGenerationSuccess(data);
    }
}
```

**LocalStorage Persistence (Optional):**

```javascript
// Persist cache across sessions
function saveCacheToLocalStorage() {
    try {
        const cacheData = Array.from(promptCache.cache.entries());
        localStorage.setItem('tikz_prompt_cache', JSON.stringify(cacheData));
    } catch (error) {
        console.warn('Failed to save cache to localStorage:', error);
    }
}

function loadCacheFromLocalStorage() {
    try {
        const cacheData = localStorage.getItem('tikz_prompt_cache');
        if (cacheData) {
            const entries = JSON.parse(cacheData);
            promptCache.cache = new Map(entries);
        }
    } catch (error) {
        console.warn('Failed to load cache from localStorage:', error);
    }
}

// Call on init and before unload
function init() {
    // ... existing init code ...
    loadCacheFromLocalStorage();

    window.addEventListener('beforeunload', saveCacheToLocalStorage);
}
```

**Cache Indicator in UI:**

```html
<!-- Add to generated-code-container in index.html -->
<div class="cache-indicator" id="cache-indicator" hidden>
    <span class="cache-icon">⚡</span>
    Kết quả từ bộ nhớ cache
</div>
```

```css
/* Add to prompt-to-tikz.css */
.tikz-app .cache-indicator {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-2);
    padding: var(--spacing-2) var(--spacing-6);
    font-size: 0.75rem;
    font-weight: 600;
    color: #ff9800;
    background: rgba(255, 152, 0, 0.1);
    border-radius: 12px;
}

.tikz-app .cache-icon {
    font-size: 1rem;
}
```

```javascript
// Show cache indicator when using cached result
function handleGenerationSuccess(data) {
    // ... existing code ...

    // Show cache indicator if from cache
    const cacheIndicator = document.getElementById('cache-indicator');
    if (cacheIndicator) {
        cacheIndicator.hidden = !data.cached;
    }

    // ... rest of function ...
}
```

**Validation:**
- [ ] Cache stores results correctly
- [ ] Cache retrieves on duplicate prompts
- [ ] LRU eviction works
- [ ] LocalStorage persistence works
- [ ] Cache indicator shows correctly

---

### Task 4.3: Enhanced Error Messages (45 min)

**Contextual Error Messages:**

```javascript
function getContextualErrorMessage(data, prompt) {
    const baseError = data.error || 'Có lỗi xảy ra';

    // Add helpful suggestions based on error
    const suggestions = [];

    switch (data.code) {
        case 'PROMPT_TOO_LONG':
            suggestions.push('Thử rút gọn mô tả hoặc tách thành nhiều hình vẽ nhỏ hơn.');
            break;

        case 'GENERATION_FAILED':
            suggestions.push('Thử mô tả chi tiết hơn hoặc đơn giản hơn.');
            suggestions.push('Xem ví dụ bên dưới để biết cách mô tả tốt.');
            break;

        case 'EMPTY_PROMPT':
            suggestions.push('Nhấn "Xem ví dụ" để tham khảo các mô tả mẫu.');
            break;

        default:
            if (baseError.includes('timeout') || baseError.includes('thời gian')) {
                suggestions.push('Thử với mô tả đơn giản hơn để giảm thời gian xử lý.');
            } else if (baseError.includes('kết nối') || baseError.includes('network')) {
                suggestions.push('Kiểm tra kết nối internet của bạn.');
                suggestions.push('Thử tải lại trang và thử lại.');
            } else if (baseError.includes('giới hạn') || baseError.includes('limit')) {
                suggestions.push('Bạn đã vượt giới hạn 10 lần sinh mã mỗi 10 phút.');
                suggestions.push('Vui lòng chờ vài phút rồi thử lại.');
            }
    }

    return { message: baseError, suggestions };
}

function showError(messageOrData) {
    let message, suggestions = [];

    if (typeof messageOrData === 'string') {
        message = messageOrData;
    } else {
        const result = getContextualErrorMessage(messageOrData, elements.promptTextarea.value);
        message = result.message;
        suggestions = result.suggestions;
    }

    // Update error message
    elements.errorMessage.innerHTML = `
        <p>${message}</p>
        ${suggestions.length > 0 ? `
            <ul class="error-suggestions">
                ${suggestions.map(s => `<li>${s}</li>`).join('')}
            </ul>
        ` : ''}
    `;

    elements.errorContainer.hidden = false;
    elements.errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
```

**CSS for Suggestions:**

```css
/* Add to prompt-to-tikz.css */
.tikz-app .error-suggestions {
    list-style: disc;
    padding-left: var(--spacing-12);
    margin: var(--spacing-4) 0 0 0;
    color: var(--text-on-glass);
}

.tikz-app .error-suggestions li {
    margin-bottom: var(--spacing-2);
    line-height: 1.5;
}
```

**Validation:**
- [ ] Contextual messages show correctly
- [ ] Suggestions helpful
- [ ] Error messages clear (Vietnamese)
- [ ] Links work (if any)

---

### Task 4.4: Advanced History Features (90 min)

**Search/Filter History:**

```html
<!-- Add to history dropdown -->
<div class="history-header">
    <h4 class="history-title">Lịch sử sinh mã</h4>
    <input
        type="search"
        id="history-search"
        class="history-search"
        placeholder="Tìm kiếm..."
        aria-label="Tìm kiếm lịch sử"
    />
    <button type="button" class="history-close-btn" aria-label="Đóng">×</button>
</div>
```

```javascript
// Filter history by search query
function filterHistory(query) {
    const filtered = state.history.filter(gen =>
        gen.prompt.toLowerCase().includes(query.toLowerCase()) ||
        gen.type.toLowerCase().includes(query.toLowerCase())
    );

    updateHistoryList(filtered);
}

// Setup search listener
elements.historySearch?.addEventListener('input', debounce((e) => {
    filterHistory(e.target.value);
}, 300));
```

**Sort History:**

```html
<!-- Add sort dropdown -->
<select id="history-sort" class="history-sort" aria-label="Sắp xếp">
    <option value="recent">Mới nhất</option>
    <option value="oldest">Cũ nhất</option>
    <option value="used">Đã dùng</option>
    <option value="unused">Chưa dùng</option>
</select>
```

```javascript
function sortHistory(sortBy) {
    let sorted = [...state.history];

    switch (sortBy) {
        case 'recent':
            sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            break;
        case 'oldest':
            sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            break;
        case 'used':
            sorted = sorted.filter(gen => gen.used);
            break;
        case 'unused':
            sorted = sorted.filter(gen => !gen.used);
            break;
    }

    updateHistoryList(sorted);
}

elements.historySort?.addEventListener('change', (e) => {
    sortHistory(e.target.value);
});
```

**Delete History Item:**

```javascript
// Add delete button to history items
function createHistoryItem(generation) {
    const item = document.createElement('div');
    item.className = 'history-item';

    item.innerHTML = `
        <div class="history-item-header">
            <span class="history-item-time">${timeStr}</span>
            <div class="history-item-actions">
                <span class="history-item-type">${generation.type}</span>
                <button
                    type="button"
                    class="history-item-delete-btn"
                    data-id="${generation.id}"
                    aria-label="Xóa"
                    title="Xóa khỏi lịch sử"
                >
                    🗑️
                </button>
            </div>
        </div>
        <p class="history-item-prompt">${escapeHtml(generation.prompt)}</p>
        <button type="button" class="history-item-use-btn" data-id="${generation.id}">
            Dùng lại
        </button>
    `;

    // Use button handler
    item.querySelector('.history-item-use-btn').addEventListener('click', () => useHistoryItem(generation));

    // Delete button handler
    item.querySelector('.history-item-delete-btn').addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm('Xóa lịch sử này?')) {
            await deleteHistoryItem(generation.id);
        }
    });

    return item;
}

async function deleteHistoryItem(generationId) {
    try {
        const response = await fetch(`/api/tikz/history/${generationId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // Remove from local state
            state.history = state.history.filter(gen => gen.id !== generationId);
            updateHistoryUI();
        } else {
            alert('Không thể xóa. Vui lòng thử lại.');
        }
    } catch (error) {
        console.error('Failed to delete history:', error);
        alert('Có lỗi xảy ra khi xóa.');
    }
}
```

**Backend Delete Endpoint:**

```python
# Add to app.py

@app.route('/api/tikz/history/<int:generation_id>', methods=['DELETE'])
@login_required
@limiter.limit(RATE_LIMITS['api_write'])
def api_tikz_delete_history(generation_id):
    """Delete a generation from history."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify ownership and delete
        cursor.execute("""
            DELETE FROM tikz_generations
            WHERE id = %s AND user_id = %s
        """, (generation_id, current_user.id))

        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy'
            }), 404

        cursor.close()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        logging.error(f"Error deleting generation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Có lỗi xảy ra'
        }), 500
```

**Validation:**
- [ ] Search filters history correctly
- [ ] Sort options work
- [ ] Delete removes item from UI and database
- [ ] Cannot delete other users' history

---

### Task 4.5: Progressive Enhancement (45 min)

**Loading States with Skeletons:**

```html
<!-- Skeleton loading for history -->
<div class="history-skeleton" id="history-skeleton">
    <div class="skeleton-item"></div>
    <div class="skeleton-item"></div>
    <div class="skeleton-item"></div>
</div>
```

```css
/* Add to prompt-to-tikz.css */
.tikz-app .history-skeleton {
    padding: var(--spacing-8);
}

.tikz-app .skeleton-item {
    height: 80px;
    margin-bottom: var(--spacing-4);
    background: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.5) 25%,
        rgba(255, 255, 255, 0.7) 50%,
        rgba(255, 255, 255, 0.5) 75%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: 8px;
}

@keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
```

**Optimistic UI Updates:**

```javascript
// Update UI immediately, then sync with server
async function markAsUsed(generationId) {
    // Optimistic update
    const historyItem = state.history.find(gen => gen.id === generationId);
    if (historyItem) {
        historyItem.used = true;
        updateHistoryUI();
    }

    // Sync with server
    try {
        await fetch(`/api/tikz/history/${generationId}/use`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (error) {
        console.error('Failed to mark as used:', error);
        // Rollback on error
        if (historyItem) {
            historyItem.used = false;
            updateHistoryUI();
        }
    }
}
```

**Keyboard Navigation Enhancement:**

```javascript
// Arrow key navigation in history list
function setupHistoryKeyboardNav() {
    elements.historyList?.addEventListener('keydown', (e) => {
        const items = Array.from(elements.historyList.querySelectorAll('.history-item-use-btn'));
        const currentIndex = items.indexOf(document.activeElement);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = Math.min(currentIndex + 1, items.length - 1);
            items[nextIndex]?.focus();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = Math.max(currentIndex - 1, 0);
            items[prevIndex]?.focus();
        }
    });
}
```

**Validation:**
- [ ] Skeleton loading shows during fetch
- [ ] Optimistic UI updates immediate
- [ ] Rollback works on error
- [ ] Keyboard navigation smooth

---

### Task 4.6: Analytics & Monitoring (30 min)

**Track Usage Metrics:**

```javascript
// Simple analytics tracking
const analytics = {
    generationsCount: 0,
    successRate: 0,
    averageResponseTime: 0,
    errors: []
};

async function handleGenerate() {
    const startTime = performance.now();

    try {
        // ... generation logic ...

        if (response.ok) {
            analytics.generationsCount++;
            analytics.successRate = calculateSuccessRate();
            const responseTime = performance.now() - startTime;
            analytics.averageResponseTime = updateAverageResponseTime(responseTime);

            // Log to console in development
            console.log('Generation metrics:', {
                responseTime: `${responseTime.toFixed(0)}ms`,
                successRate: `${(analytics.successRate * 100).toFixed(1)}%`,
                averageTime: `${analytics.averageResponseTime.toFixed(0)}ms`
            });
        }
    } catch (error) {
        analytics.errors.push({
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
}

function calculateSuccessRate() {
    const totalAttempts = analytics.generationsCount + analytics.errors.length;
    return totalAttempts > 0 ? analytics.generationsCount / totalAttempts : 0;
}

function updateAverageResponseTime(newTime) {
    const count = analytics.generationsCount;
    return ((analytics.averageResponseTime * (count - 1)) + newTime) / count;
}

// Expose metrics for debugging
window.PromptToTikZ.getMetrics = () => analytics;
```

**Error Logging to Backend:**

```javascript
async function logErrorToBackend(error, context) {
    try {
        await fetch('/api/log/error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                error: error.message || String(error),
                stack: error.stack,
                context,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent
            })
        });
    } catch (logError) {
        console.error('Failed to log error:', logError);
    }
}

// Use in error handlers
catch (error) {
    console.error('Generation error:', error);
    logErrorToBackend(error, { action: 'generate_tikz', prompt });
    showError('...');
}
```

**Validation:**
- [ ] Metrics tracked correctly
- [ ] Console logs in development only
- [ ] Error logging works
- [ ] No performance impact

---

## ✅ Validation Checklist

### Performance Tests
- [ ] Character counter responsive (<50ms)
- [ ] History loads <500ms
- [ ] Cache hit <100ms
- [ ] CodeMirror refresh smooth
- [ ] No memory leaks (check DevTools)
- [ ] Bundle size acceptable (<50KB gzipped)

### Feature Tests
- [ ] Cache stores and retrieves correctly
- [ ] History search/filter works
- [ ] History sort works
- [ ] History delete works
- [ ] Error messages contextual
- [ ] Skeleton loading smooth
- [ ] Optimistic UI updates work
- [ ] Keyboard navigation enhanced
- [ ] Analytics tracking accurate

### Integration Tests
- [ ] Works with existing index.js
- [ ] No conflicts with other scripts
- [ ] Main editor sync works
- [ ] Navigation doesn't break
- [ ] File card interactions unaffected

---

## 📊 Performance Metrics

Target metrics after optimization:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Initial load | N/A | - | <2s |
| Generate (cache hit) | N/A | - | <100ms |
| Generate (API call) | N/A | - | <5s |
| History load | N/A | - | <500ms |
| Character counter | N/A | - | <50ms |
| Memory usage | N/A | - | <10MB |

Measure using Chrome DevTools Performance tab.

---

## ✅ Completion Criteria

Phase 4 complete when:
- [ ] Performance optimizations applied
- [ ] Caching implemented and working
- [ ] Enhanced error messages clear
- [ ] History features complete (search, sort, delete)
- [ ] Progressive enhancement features working
- [ ] Analytics tracking functional
- [ ] Performance metrics meet targets
- [ ] No regressions from optimizations
- [ ] Code maintainable and documented

---

**Next Phase:** Phase 5 - Testing & Deployment
**Focus:** Comprehensive testing, documentation, production deployment
