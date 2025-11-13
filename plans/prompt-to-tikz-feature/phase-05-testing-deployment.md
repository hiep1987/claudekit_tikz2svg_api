# Phase 5: Testing & Deployment

**Duration:** 6-8 hours
**Priority:** Critical (Production Readiness)
**Dependencies:** Phase 1, 2, 3, 4 complete

---

## 🎯 Objectives

Comprehensive testing suite, documentation updates, production deployment, monitoring setup, user communication.

---

## 📋 Tasks Breakdown

### Task 5.1: Unit Testing (120 min)

**Backend Tests:**

```python
# tests/test_tikz_generation_endpoints.py

import pytest
from unittest.mock import patch, Mock
import json

class TestTikZGenerationAPI:
    """Test tikz generation API endpoints"""

    def test_generate_requires_authentication(self, client):
        """Test authentication requirement"""
        response = client.post('/api/tikz/generate', json={
            'prompt': 'vẽ bảng biến thiên'
        })
        assert response.status_code == 401

    def test_generate_validates_empty_prompt(self, client, auth_user):
        """Test empty prompt validation"""
        response = client.post('/api/tikz/generate', json={
            'prompt': ''
        })
        assert response.status_code == 400
        data = response.json
        assert 'error' in data
        assert data['code'] == 'EMPTY_PROMPT'

    def test_generate_validates_long_prompt(self, client, auth_user):
        """Test prompt length validation"""
        long_prompt = 'a' * 501
        response = client.post('/api/tikz/generate', json={
            'prompt': long_prompt
        })
        assert response.status_code == 400
        data = response.json
        assert 'quá dài' in data['error'].lower()

    @patch('app.call_tikz_api')
    def test_generate_success(self, mock_tikz_api, client, auth_user):
        """Test successful generation"""
        mock_tikz_api.return_value = {
            'success': True,
            'tikz_code': '\\begin{tikzpicture}...\\end{tikzpicture}',
            'type': 'variation_table',
            'latex_preamble': ['tikz', 'tkz-tab']
        }

        response = client.post('/api/tikz/generate', json={
            'prompt': 'vẽ bảng biến thiên y = x^2',
            'save_history': True
        })

        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'tikz_code' in data
        assert data['type'] == 'variation_table'
        assert 'tikz' in data['latex_preamble']

    @patch('app.call_tikz_api')
    def test_generate_handles_api_failure(self, mock_tikz_api, client, auth_user):
        """Test handling of tikz-api failures"""
        mock_tikz_api.return_value = {
            'success': False,
            'error': 'Service temporarily unavailable'
        }

        response = client.post('/api/tikz/generate', json={
            'prompt': 'test prompt'
        })

        assert response.status_code == 500
        data = response.json
        assert data['success'] is False
        assert 'error' in data

    @patch('requests.post')
    def test_call_tikz_api_timeout(self, mock_post):
        """Test timeout handling in call_tikz_api"""
        from app import call_tikz_api
        import requests

        mock_post.side_effect = requests.Timeout

        result = call_tikz_api('test prompt')

        assert result['success'] is False
        assert 'Quá thời gian' in result['error']

    @patch('requests.post')
    def test_call_tikz_api_connection_error(self, mock_post):
        """Test connection error handling"""
        from app import call_tikz_api
        import requests

        mock_post.side_effect = requests.ConnectionError

        result = call_tikz_api('test prompt')

        assert result['success'] is False
        assert 'kết nối' in result['error'].lower()

    def test_history_retrieval(self, client, auth_user, db):
        """Test history retrieval endpoint"""
        # Create test history entries
        cursor = db.cursor()
        for i in range(5):
            cursor.execute("""
                INSERT INTO tikz_generations
                (user_id, prompt, generated_code, diagram_type)
                VALUES (%s, %s, %s, %s)
            """, (auth_user.id, f'test prompt {i}', f'code {i}', 'other'))
        db.commit()

        response = client.get('/api/tikz/history?limit=10')

        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert len(data['generations']) == 5

    def test_mark_as_used(self, client, auth_user, db):
        """Test marking generation as used"""
        # Create test generation
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO tikz_generations
            (user_id, prompt, generated_code, diagram_type)
            VALUES (%s, %s, %s, %s)
        """, (auth_user.id, 'test', 'code', 'other'))
        db.commit()
        generation_id = cursor.lastrowid

        response = client.post(f'/api/tikz/history/{generation_id}/use')

        assert response.status_code == 200

        # Verify database updated
        cursor.execute("""
            SELECT used FROM tikz_generations WHERE id = %s
        """, (generation_id,))
        result = cursor.fetchone()
        assert result[0] is True

    def test_delete_history(self, client, auth_user, db):
        """Test deleting history item"""
        # Create test generation
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO tikz_generations
            (user_id, prompt, generated_code, diagram_type)
            VALUES (%s, %s, %s, %s)
        """, (auth_user.id, 'test', 'code', 'other'))
        db.commit()
        generation_id = cursor.lastrowid

        response = client.delete(f'/api/tikz/history/{generation_id}')

        assert response.status_code == 200

        # Verify deletion
        cursor.execute("""
            SELECT COUNT(*) FROM tikz_generations WHERE id = %s
        """, (generation_id,))
        count = cursor.fetchone()[0]
        assert count == 0

    def test_cannot_delete_other_users_history(self, client, auth_user, other_user, db):
        """Test user cannot delete other users' history"""
        # Create generation for other user
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO tikz_generations
            (user_id, prompt, generated_code, diagram_type)
            VALUES (%s, %s, %s, %s)
        """, (other_user.id, 'test', 'code', 'other'))
        db.commit()
        generation_id = cursor.lastrowid

        # Try to delete as auth_user
        response = client.delete(f'/api/tikz/history/{generation_id}')

        assert response.status_code == 404

    def test_rate_limiting(self, client, auth_user):
        """Test rate limiting (10 per 10 minutes)"""
        # Make 10 requests (should succeed)
        for i in range(10):
            response = client.post('/api/tikz/generate', json={
                'prompt': f'test {i}'
            })
            # May fail due to tikz-api, but should not be rate limited
            assert response.status_code != 429

        # 11th request should be rate limited
        response = client.post('/api/tikz/generate', json={
            'prompt': 'test 11'
        })
        assert response.status_code == 429


# Run tests
# pytest tests/test_tikz_generation_endpoints.py -v --cov=app
```

**Frontend Tests:**

```javascript
// tests/js/prompt-to-tikz.test.js

describe('Prompt-to-TikZ Module', () => {
    let mockFetch;

    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <textarea id="tikz-prompt-input" maxlength="500"></textarea>
            <span id="char-current">0</span>
            <div id="prompt-char-count"></div>
            <button id="generate-tikz-btn"></button>
            <div id="generation-loading" hidden></div>
            <div id="generation-error" hidden>
                <p id="generation-error-message"></p>
            </div>
            <div id="generated-code-container" hidden></div>
            <div id="generated-code-editor"></div>
        `;

        // Mock fetch
        mockFetch = jest.spyOn(global, 'fetch');

        // Mock window.appState
        window.appState = { loggedIn: true };

        // Initialize module
        window.PromptToTikZ.init();
    });

    afterEach(() => {
        mockFetch.mockRestore();
    });

    test('character counter updates correctly', () => {
        const textarea = document.getElementById('tikz-prompt-input');
        const counter = document.getElementById('char-current');

        textarea.value = 'Test prompt';
        textarea.dispatchEvent(new Event('input'));

        expect(counter.textContent).toBe('11');
    });

    test('shows warning near character limit', () => {
        const textarea = document.getElementById('tikz-prompt-input');
        const container = document.getElementById('prompt-char-count');

        textarea.value = 'a'.repeat(460); // 92% of 500
        textarea.dispatchEvent(new Event('input'));

        expect(container.classList.contains('warning')).toBe(true);
    });

    test('shows error at character limit', () => {
        const textarea = document.getElementById('tikz-prompt-input');
        const container = document.getElementById('prompt-char-count');

        textarea.value = 'a'.repeat(500);
        textarea.dispatchEvent(new Event('input'));

        expect(container.classList.contains('error')).toBe(true);
    });

    test('validates empty prompt', async () => {
        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = '';

        await window.PromptToTikZ.generateFromPrompt();

        const errorContainer = document.getElementById('generation-error');
        expect(errorContainer.hidden).toBe(false);
    });

    test('validates long prompt', async () => {
        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = 'a'.repeat(501);

        await window.PromptToTikZ.generateFromPrompt();

        const errorContainer = document.getElementById('generation-error');
        expect(errorContainer.hidden).toBe(false);
    });

    test('calls API with correct payload', async () => {
        mockFetch.mockResolvedValue({
            ok: true,
            json: async () => ({
                success: true,
                tikz_code: '\\begin{tikzpicture}...',
                type: 'variation_table',
                latex_preamble: ['tikz']
            })
        });

        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = 'vẽ bảng biến thiên';

        await window.PromptToTikZ.generateFromPrompt();

        expect(mockFetch).toHaveBeenCalledWith('/api/tikz/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: 'vẽ bảng biến thiên',
                save_history: true
            })
        });
    });

    test('displays generated code on success', async () => {
        mockFetch.mockResolvedValue({
            ok: true,
            json: async () => ({
                success: true,
                tikz_code: '\\begin{tikzpicture}...\\end{tikzpicture}',
                type: 'variation_table',
                latex_preamble: ['tikz', 'tkz-tab']
            })
        });

        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = 'test prompt';

        await window.PromptToTikZ.generateFromPrompt();

        const container = document.getElementById('generated-code-container');
        expect(container.hidden).toBe(false);
    });

    test('shows error on API failure', async () => {
        mockFetch.mockResolvedValue({
            ok: false,
            json: async () => ({
                success: false,
                error: 'Service unavailable',
                code: 'GENERATION_FAILED'
            })
        });

        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = 'test prompt';

        await window.PromptToTikZ.generateFromPrompt();

        const errorContainer = document.getElementById('generation-error');
        expect(errorContainer.hidden).toBe(false);
    });

    test('handles network errors', async () => {
        mockFetch.mockRejectedValue(new TypeError('Failed to fetch'));

        const textarea = document.getElementById('tikz-prompt-input');
        textarea.value = 'test prompt';

        await window.PromptToTikZ.generateFromPrompt();

        const errorContainer = document.getElementById('generation-error');
        expect(errorContainer.hidden).toBe(false);
    });

    test('clipboard copy works', async () => {
        navigator.clipboard = {
            writeText: jest.fn().mockResolvedValue()
        };

        window.PromptToTikZ.currentGeneration = {
            tikzCode: '\\begin{tikzpicture}...'
        };

        await window.PromptToTikZ.copyToClipboard();

        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('\\begin{tikzpicture}...');
    });
});

// Run tests:
// npm test -- prompt-to-tikz.test.js
```

**Validation:**
- [ ] All backend tests passing
- [ ] All frontend tests passing
- [ ] Test coverage ≥70%
- [ ] No flaky tests

---

### Task 5.2: Integration Testing (90 min)

**End-to-End Test:**

```javascript
// tests/e2e/tikz-generation-flow.test.js

const puppeteer = require('puppeteer');

describe('Prompt-to-TikZ E2E', () => {
    let browser, page;

    beforeAll(async () => {
        browser = await puppeteer.launch({ headless: true });
    });

    afterAll(async () => {
        await browser.close();
    });

    beforeEach(async () => {
        page = await browser.newPage();
        await page.goto('http://localhost:5000');

        // Login (mock or real)
        await loginUser(page);
    });

    test('complete generation workflow', async () => {
        // 1. Navigate to prompt section
        await page.waitForSelector('#tikz-prompt-input');

        // 2. Enter prompt
        await page.type('#tikz-prompt-input', 'vẽ bảng biến thiên y = x^2 - 4x + 3');

        // 3. Verify character counter
        const charCount = await page.$eval('#char-current', el => el.textContent);
        expect(parseInt(charCount)).toBeGreaterThan(0);

        // 4. Click generate
        await page.click('#generate-tikz-btn');

        // 5. Wait for loading
        await page.waitForSelector('#generation-loading:not([hidden])');

        // 6. Wait for result (max 35s)
        await page.waitForSelector('#generated-code-container:not([hidden])', {
            timeout: 35000
        });

        // 7. Verify code displayed
        const codeVisible = await page.$eval(
            '#generated-code-container',
            el => !el.hidden
        );
        expect(codeVisible).toBe(true);

        // 8. Click "Use code"
        await page.click('#use-generated-btn');

        // 9. Verify main editor populated
        await page.waitForFunction(() => {
            const editor = document.getElementById('code');
            return editor && editor.value.includes('tikzpicture');
        });

        const mainEditorValue = await page.$eval('#code', el => el.value);
        expect(mainEditorValue).toContain('tikzpicture');
    });

    test('error handling workflow', async () => {
        // Test empty prompt
        await page.waitForSelector('#generate-tikz-btn');
        await page.click('#generate-tikz-btn');

        await page.waitForSelector('#generation-error:not([hidden])');
        const errorVisible = await page.$eval('#generation-error', el => !el.hidden);
        expect(errorVisible).toBe(true);
    });

    test('history workflow', async () => {
        // Generate code
        await page.type('#tikz-prompt-input', 'test prompt');
        await page.click('#generate-tikz-btn');
        await page.waitForSelector('#generated-code-container:not([hidden])', {
            timeout: 35000
        });

        // Open history
        await page.click('#show-history-btn');
        await page.waitForSelector('#history-dropdown:not([hidden])');

        // Verify history item exists
        const historyItems = await page.$$('.history-item');
        expect(historyItems.length).toBeGreaterThan(0);
    });
});

async function loginUser(page) {
    // Mock login or use real OAuth flow
    await page.evaluate(() => {
        window.appState = {
            loggedIn: true,
            userEmail: 'test@example.com',
            username: 'testuser'
        };
    });
}

// Run tests:
// npm run test:e2e
```

**Load Testing:**

```python
# tests/load/test_tikz_generation_load.py

from locust import HttpUser, task, between
import random

class TikZGenerationUser(HttpUser):
    wait_time = between(5, 15)

    def on_start(self):
        """Login before starting"""
        # Mock login or use real OAuth
        self.client.get('/login')

    @task(3)
    def generate_tikz(self):
        """Generate TikZ code"""
        prompts = [
            'vẽ bảng biến thiên y = x^2',
            'vẽ đồ thị hàm số y = sin(x)',
            'vẽ tam giác đều ABC',
            'vẽ đường tròn tâm O'
        ]

        prompt = random.choice(prompts)

        with self.client.post('/api/tikz/generate',
                              json={'prompt': prompt, 'save_history': True},
                              catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    response.success()
                else:
                    response.failure(f"Generation failed: {data.get('error')}")
            elif response.status_code == 429:
                response.success()  # Rate limit expected
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def get_history(self):
        """Get generation history"""
        self.client.get('/api/tikz/history?limit=10')

# Run load test:
# locust -f tests/load/test_tikz_generation_load.py --host=http://localhost:5000
```

**Validation:**
- [ ] E2E tests passing
- [ ] Load tests handle 10 concurrent users
- [ ] Rate limiting works under load
- [ ] No crashes or memory leaks

---

### Task 5.3: User Acceptance Testing (60 min)

**UAT Checklist:**

```markdown
# User Acceptance Test Plan

## Test Scenario 1: First-time User
**Objective:** New user generates TikZ for the first time

Steps:
1. [ ] Login with Google
2. [ ] Navigate to prompt section
3. [ ] Read description and examples
4. [ ] Click "Xem ví dụ"
5. [ ] Select an example
6. [ ] Click "Sinh mã TikZ"
7. [ ] Wait for generation (observe loading state)
8. [ ] Review generated code
9. [ ] Click "Dùng code này"
10. [ ] Verify code in main editor
11. [ ] Click "Biên dịch" to compile TikZ
12. [ ] Verify SVG output

**Success Criteria:**
- Process clear and intuitive
- Loading state informative
- Generated code valid
- Integration with main editor smooth

## Test Scenario 2: Power User
**Objective:** Experienced user uses advanced features

Steps:
1. [ ] Enter custom Vietnamese prompt
2. [ ] Generate code
3. [ ] Copy to clipboard
4. [ ] Open history
5. [ ] Search history
6. [ ] Sort history
7. [ ] Reuse old generation
8. [ ] Delete old generation
9. [ ] Generate 10 times rapidly (test rate limit)
10. [ ] Handle rate limit error gracefully

**Success Criteria:**
- History features functional
- Rate limit clear and fair
- No data loss
- Performance acceptable

## Test Scenario 3: Error Handling
**Objective:** Test error scenarios

Steps:
1. [ ] Submit empty prompt
2. [ ] Submit 501-character prompt
3. [ ] Generate with tikz-api offline
4. [ ] Generate with slow network
5. [ ] Handle timeout (>30s prompt)
6. [ ] Retry after error

**Success Criteria:**
- Error messages clear (Vietnamese)
- Suggestions helpful
- Retry works
- No crashes

## Test Scenario 4: Mobile Experience
**Objective:** Test on mobile devices

Steps:
1. [ ] Access on iPhone Safari
2. [ ] Access on Android Chrome
3. [ ] Enter prompt (touch keyboard)
4. [ ] Generate code
5. [ ] Scroll through generated code
6. [ ] Copy to clipboard
7. [ ] Use code in main editor
8. [ ] Open history (touch interaction)

**Success Criteria:**
- Touch targets ≥44px
- Keyboard doesn't obscure UI
- Scrolling smooth
- No layout issues
```

**UAT Execution:**

Recruit 3-5 test users:
- 1-2 beginners (never used TikZ)
- 2-3 experienced users (familiar with LaTeX)
- 1 mobile-only user

Collect feedback:
- System Usability Scale (SUS) score
- Time to first successful generation
- Error frequency
- Satisfaction rating (1-5)

**Validation:**
- [ ] UAT completed with ≥3 users
- [ ] SUS score ≥70 (good)
- [ ] All critical bugs fixed
- [ ] Feedback incorporated

---

### Task 5.4: Documentation Updates (90 min)

**Update `DOCS_CONTENT_COMPILATION.md`:**

```markdown
## Sinh mã TikZ từ mô tả (AI-powered)

### Giới thiệu
Tính năng mới nhất của TikZ2SVG cho phép bạn sinh mã TikZ tự động từ mô tả bằng tiếng Việt hoặc tiếng Anh, được hỗ trợ bởi AI Google Gemini.

### Cách sử dụng

#### Bước 1: Mô tả hình vẽ
Nhập mô tả chi tiết về hình vẽ bạn muốn tạo vào ô văn bản. Mô tả càng rõ ràng, kết quả càng chính xác.

**Ví dụ mô tả tốt:**
- "vẽ bảng biến thiên của hàm số y = x^3 - 3x + 1"
- "vẽ đồ thị hàm số y = sin(x) trên đoạn [0, 2π]"
- "vẽ tam giác đều ABC với cạnh dài 4cm và đường cao từ A"
- "vẽ đường tròn tâm O bán kính 3cm và tiếp tuyến tại điểm A"

**Tips để mô tả tốt:**
- Nêu rõ loại hình vẽ (bảng biến thiên, đồ thị, hình học...)
- Cung cấp thông số cụ thể (kích thước, tọa độ, phạm vi...)
- Mô tả các yếu tố quan trọng (tiếp tuyến, đường cao, điểm đặc biệt...)
- Giữ mô tả dưới 500 ký tự
- Sử dụng thuật ngữ toán học chính xác

#### Bước 2: Sinh mã TikZ
1. Nhấn nút **"Sinh mã TikZ"**
2. Đợi AI xử lý (thường <5 giây, tối đa 30 giây)
3. Quan sát thanh loading để biết quá trình đang diễn ra

#### Bước 3: Xem và sử dụng code
Sau khi sinh thành công, bạn sẽ thấy:
- Mã TikZ được highlight cú pháp
- Loại biểu đồ (bảng biến thiên, đồ thị, hình học...)
- Danh sách packages LaTeX cần thiết
- Thời gian sinh

**Các thao tác:**
- **Sao chép:** Copy mã vào clipboard
- **Dùng code này:** Đưa mã vào editor chính để biên dịch
- **Xóa:** Xóa kết quả và thử lại

#### Bước 4: Biên dịch
Sau khi nhấn "Dùng code này", mã TikZ sẽ tự động xuất hiện trong editor chính. Nhấn **"Biên dịch"** như bình thường để tạo SVG.

### Lịch sử sinh mã

Hệ thống lưu 10 lần sinh mã gần nhất của bạn. Bạn có thể:
- Xem lại các mã đã sinh
- Tìm kiếm theo mô tả
- Sắp xếp theo thời gian hoặc trạng thái
- Dùng lại mã cũ
- Xóa lịch sử không cần thiết

**Cách truy cập lịch sử:**
1. Nhấn nút **"Lịch sử sinh mã"** (hiện số lượng)
2. Chọn mục muốn xem
3. Nhấn **"Dùng lại"** để load mã vào editor

### Giới hạn sử dụng

Để đảm bảo chất lượng dịch vụ cho mọi người:
- **10 lần sinh mã mỗi 10 phút**
- Tối đa 500 ký tự cho mỗi mô tả
- Thời gian chờ tối đa 30 giây

Nếu vượt giới hạn, hệ thống sẽ thông báo và bạn cần chờ vài phút.

### Xử lý lỗi

**Lỗi thường gặp:**

1. **"Quá thời gian chờ"**
   - Mô tả quá phức tạp
   - Thử rút gọn hoặc tách thành nhiều hình nhỏ hơn

2. **"Không thể sinh mã TikZ"**
   - Mô tả không rõ ràng hoặc thiếu thông tin
   - Tham khảo ví dụ và thử lại với mô tả chi tiết hơn

3. **"Đã vượt giới hạn"**
   - Bạn đã sinh 10 lần trong 10 phút
   - Chờ vài phút và thử lại
   - Hoặc dùng lại mã cũ trong lịch sử

4. **"Không thể kết nối"**
   - Kiểm tra kết nối internet
   - Tải lại trang và thử lại
   - Liên hệ admin nếu vấn đề tiếp diễn

### Ví dụ thực tế

#### Ví dụ 1: Bảng biến thiên
**Mô tả:**
```
vẽ bảng biến thiên của hàm số y = x^3 - 3x + 1 trên R
```

**Code sinh ra:**
```latex
\begin{tikzpicture}[scale=0.8]
  \tkzTabInit[lgt=2]{$x$ /1, $y'$ /1, $y$ /2}
             {$-\infty$, $-1$, $1$, $+\infty$}
  \tkzTabLine{, +, 0, -, 0, +, }
  \tkzTabVar{-/$-\infty$, +/$3$, -/$-1$, +/$+\infty$}
\end{tikzpicture}
```

**Packages:** `tkz-tab`, `tikz`

#### Ví dụ 2: Đồ thị hàm số
**Mô tả:**
```
vẽ đồ thị hàm số y = sin(x) trên đoạn [0, 2π] với trục tọa độ
```

**Code sinh ra:**
```latex
\begin{tikzpicture}
  \begin{axis}[
    axis lines = middle,
    xlabel = $x$,
    ylabel = $y$,
    domain = 0:2*pi,
    samples = 100,
  ]
  \addplot[blue, thick] {sin(deg(x))};
  \end{axis}
\end{tikzpicture}
```

**Packages:** `pgfplots`, `tikz`

#### Ví dụ 3: Hình học
**Mô tả:**
```
vẽ tam giác đều ABC với cạnh dài 4cm và đường cao từ đỉnh A
```

**Code sinh ra:**
```latex
\begin{tikzpicture}[scale=0.8]
  \coordinate (B) at (0,0);
  \coordinate (C) at (4,0);
  \coordinate (A) at (2,3.464);

  \draw[thick] (A) -- (B) -- (C) -- cycle;
  \draw[dashed] (A) -- (2,0);

  \node[below left] at (B) {B};
  \node[below right] at (C) {C};
  \node[above] at (A) {A};
\end{tikzpicture}
```

**Packages:** `tikz`

### Câu hỏi thường gặp

**Q: Tôi có thể dùng tiếng Anh không?**
A: Có, hệ thống hỗ trợ cả tiếng Việt và tiếng Anh.

**Q: Mã sinh ra có chính xác 100% không?**
A: AI cố gắng sinh mã chính xác nhất, nhưng bạn nên kiểm tra và chỉnh sửa nếu cần.

**Q: Tôi có thể chỉnh sửa mã sau khi sinh không?**
A: Có, nhấn "Dùng code này" để đưa vào editor chính, sau đó chỉnh sửa tùy ý.

**Q: Lịch sử sinh mã lưu bao lâu?**
A: Lưu vĩnh viễn cho đến khi bạn xóa hoặc đạt giới hạn 10 mục (xóa cũ nhất).

**Q: Tôi quên mật khẩu có mất lịch sử không?**
A: Không, lịch sử gắn với tài khoản Google của bạn.

### Lời khuyên sử dụng hiệu quả

1. **Bắt đầu đơn giản:** Thử với mô tả đơn giản trước, sau đó tăng độ phức tạp.

2. **Học từ ví dụ:** Xem các ví dụ có sẵn để biết cách mô tả hiệu quả.

3. **Sử dụng lịch sử:** Lưu các mã tốt vào lịch sử để tái sử dụng.

4. **Kết hợp AI và manual:** Dùng AI sinh khung code, sau đó tinh chỉnh bằng tay.

5. **Chia nhỏ bài toán:** Nếu hình phức tạp, chia thành nhiều phần nhỏ.

6. **Kiểm tra packages:** Đảm bảo bạn hiểu các packages được sinh ra.

### Báo lỗi và góp ý

Nếu bạn gặp vấn đề hoặc có ý tưởng cải thiện:
- Liên hệ: [your-email]
- Báo lỗi qua form feedback
- Đóng góp trên GitHub: [repository-link]

---

**Cập nhật:** 13/11/2025
**Phiên bản:** 1.0
```

**Update `CLAUDE.md`:**

```markdown
### 8. TikZ Generation from Prompts (NEW)
- **AI-powered Generation:** Google Gemini 2.5 Flash integration
- **Vietnamese/English Support:** Natural language prompts
- **Diagram Types:** Variation tables, function graphs, geometry, general diagrams
- **Package Detection:** Automatic LaTeX package identification
- **History Management:** Save last 10 generations
- **Rate Limiting:** 10 requests/10 minutes
- **Caching:** Client-side cache for duplicate prompts
```

**Create User Guide:**

```markdown
# USER_GUIDE_AI_TIKZ_GENERATION.md

[Full user guide content similar to above but more detailed]
```

**Validation:**
- [ ] All documentation updated
- [ ] User guide created
- [ ] Screenshots added (if applicable)
- [ ] Links work
- [ ] Grammar/spelling checked

---

### Task 5.5: Production Deployment (90 min)

**Pre-deployment Checklist:**

```markdown
# Pre-deployment Checklist

## Code Quality
- [ ] All tests passing (unit, integration, E2E)
- [ ] Test coverage ≥70%
- [ ] No console errors
- [ ] No console.log() in production code
- [ ] Linting passed (pylint, eslint)
- [ ] Type checking passed (if applicable)

## Security
- [ ] Environment variables configured
- [ ] API keys secured (.env, not committed)
- [ ] Rate limiting tested
- [ ] SQL injection tests passed
- [ ] XSS protection verified
- [ ] CSRF tokens working
- [ ] HTTPS configured

## Performance
- [ ] Bundle size acceptable (<50KB gzipped)
- [ ] Lighthouse score ≥90
- [ ] Page load time <3s
- [ ] API response time <5s
- [ ] Database queries optimized
- [ ] Indexes created

## Database
- [ ] Migration scripts ready
- [ ] Backup before deployment
- [ ] Rollback plan documented
- [ ] Test data cleaned
- [ ] Indexes verified

## Dependencies
- [ ] tikz-api service running
- [ ] tikz-api accessible (network/firewall)
- [ ] Redis configured (if using)
- [ ] MySQL version compatible

## Monitoring
- [ ] Logging configured
- [ ] Error tracking setup (Sentry/similar)
- [ ] Performance monitoring ready
- [ ] Alerting rules defined

## Documentation
- [ ] README updated
- [ ] DOCS_CONTENT_COMPILATION updated
- [ ] CLAUDE.md updated
- [ ] User guide created
- [ ] API documentation updated

## Communication
- [ ] Announcement prepared
- [ ] User notifications scheduled
- [ ] Support team briefed
- [ ] Rollback plan communicated
```

**Deployment Steps:**

```bash
# 1. Backup database
mysqldump -u user -p tikz2svg > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Pull latest code
git pull origin main

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python migrate_tikz_generations.py

# 5. Collect static files (if needed)
python collect_static.py

# 6. Test tikz-api connection
curl http://localhost:8000/health

# 7. Restart services
sudo systemctl restart tikz2svg
sudo systemctl restart tikz-api  # if on same server

# 8. Verify deployment
curl -I https://yourdomain.com
curl https://yourdomain.com/api/tikz/generate -X POST -H "Content-Type: application/json" -d '{"prompt": "test"}'

# 9. Monitor logs
tail -f /var/log/tikz2svg/error.log
tail -f /var/log/tikz2svg/access.log

# 10. Check metrics
# - Response times
# - Error rates
# - Memory usage
# - Database connections
```

**Rollback Plan:**

```bash
# If deployment fails:

# 1. Restore database
mysql -u user -p tikz2svg < backup_TIMESTAMP.sql

# 2. Revert code
git revert HEAD
# or
git checkout PREVIOUS_COMMIT_HASH

# 3. Restart services
sudo systemctl restart tikz2svg

# 4. Verify rollback
curl https://yourdomain.com

# 5. Notify users
# - Post announcement
# - Send emails
# - Update status page
```

**Validation:**
- [ ] Deployment successful
- [ ] All endpoints responding
- [ ] No errors in logs
- [ ] Monitoring active
- [ ] Users notified

---

### Task 5.6: Post-Deployment Monitoring (60 min)

**Monitoring Dashboard:**

```python
# monitoring/dashboard.py

import logging
from datetime import datetime, timedelta
from collections import defaultdict

class TikZGenerationMonitor:
    """Monitor TikZ generation feature metrics"""

    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'rate_limits': 0,
            'average_response_time': 0,
            'peak_concurrent_users': 0,
            'errors': defaultdict(int)
        }

    def log_request(self, success, response_time, error=None):
        """Log generation request"""
        self.metrics['total_requests'] += 1

        if success:
            self.metrics['successful_generations'] += 1
        else:
            self.metrics['failed_generations'] += 1

        if error:
            self.metrics['errors'][error] += 1

        # Update average response time
        total = self.metrics['total_requests']
        avg = self.metrics['average_response_time']
        self.metrics['average_response_time'] = (
            (avg * (total - 1) + response_time) / total
        )

    def log_rate_limit(self):
        """Log rate limit hit"""
        self.metrics['rate_limits'] += 1

    def get_metrics(self):
        """Get current metrics"""
        success_rate = (
            self.metrics['successful_generations'] /
            self.metrics['total_requests'] * 100
            if self.metrics['total_requests'] > 0 else 0
        )

        return {
            **self.metrics,
            'success_rate': f"{success_rate:.1f}%"
        }

    def get_health_status(self):
        """Determine health status"""
        metrics = self.get_metrics()
        success_rate = float(metrics['success_rate'].rstrip('%'))

        if success_rate >= 95:
            return 'healthy'
        elif success_rate >= 80:
            return 'degraded'
        else:
            return 'unhealthy'

# Initialize global monitor
monitor = TikZGenerationMonitor()

# Use in endpoints
@app.route('/api/tikz/generate', methods=['POST'])
@login_required
def api_tikz_generate():
    start_time = time.time()
    success = False
    error = None

    try:
        # ... generation logic ...
        success = True
    except Exception as e:
        error = type(e).__name__
        raise
    finally:
        response_time = time.time() - start_time
        monitor.log_request(success, response_time, error)

    # ... return response ...

# Health endpoint
@app.route('/api/tikz/health', methods=['GET'])
def api_tikz_health():
    """Health check for TikZ generation feature"""
    metrics = monitor.get_metrics()
    health = monitor.get_health_status()

    return jsonify({
        'status': health,
        'metrics': metrics,
        'timestamp': datetime.utcnow().isoformat()
    })
```

**Alerting Rules:**

```yaml
# monitoring/alerts.yml

alerts:
  - name: high_error_rate
    condition: error_rate > 10%
    action: send_email
    recipients: [admin@example.com]

  - name: slow_response_time
    condition: avg_response_time > 10s
    action: send_slack
    channel: #alerts

  - name: rate_limit_spike
    condition: rate_limits > 50/hour
    action: log_warning

  - name: tikz_api_down
    condition: tikz_api_health == unhealthy
    action: send_pagerduty
    severity: critical
```

**Validation:**
- [ ] Metrics collected correctly
- [ ] Dashboard accessible
- [ ] Alerts firing correctly
- [ ] Logs readable
- [ ] Performance within targets

---

### Task 5.7: User Communication (30 min)

**Announcement Post:**

```markdown
# 🎉 Tính năng mới: Sinh mã TikZ từ mô tả (AI-powered)

Chúng tôi vui mừng giới thiệu tính năng mới nhất của TikZ2SVG: **Sinh mã TikZ tự động từ mô tả tiếng Việt/tiếng Anh** được hỗ trợ bởi AI Google Gemini!

## ✨ Điểm nổi bật

- 🤖 **AI thông minh:** Hiểu mô tả tiếng Việt/tiếng Anh tự nhiên
- 📊 **Đa dạng loại hình:** Bảng biến thiên, đồ thị, hình học...
- 📦 **Tự động packages:** Nhận diện packages LaTeX cần thiết
- 📚 **Lịch sử:** Lưu 10 lần sinh gần nhất
- ⚡ **Nhanh chóng:** Kết quả trong <5 giây

## 🚀 Cách sử dụng

1. Mô tả hình vẽ bạn muốn (VD: "vẽ bảng biến thiên y = x^2")
2. Nhấn "Sinh mã TikZ"
3. Xem code được sinh tự động
4. Nhấn "Dùng code này" để biên dịch

## 📖 Tài liệu

Xem hướng dẫn chi tiết tại: [/docs#sinh-ma-tikz](/docs#sinh-ma-tikz)

## 💡 Thử ngay!

Đăng nhập và trải nghiệm tính năng mới tại [trang chủ](/).

---

Có câu hỏi? Liên hệ: [your-email]
```

**Email to Users:**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Tính năng mới: AI sinh mã TikZ</title>
</head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1>🎉 Tính năng mới đã có trên TikZ2SVG!</h1>

    <p>Xin chào,</p>

    <p>Chúng tôi vui mừng thông báo tính năng mới: <strong>Sinh mã TikZ tự động từ mô tả</strong>, được hỗ trợ bởi AI Google Gemini.</p>

    <h2>✨ Bạn có thể làm gì?</h2>
    <ul>
        <li>Mô tả hình vẽ bằng tiếng Việt hoặc tiếng Anh</li>
        <li>AI sinh mã TikZ tự động trong vài giây</li>
        <li>Sử dụng ngay code được sinh để tạo SVG</li>
        <li>Lưu lịch sử để tái sử dụng sau</li>
    </ul>

    <h2>🚀 Thử ngay!</h2>
    <p>
        <a href="https://yourdomain.com/" style="display: inline-block; padding: 12px 24px; background: #1976d2; color: white; text-decoration: none; border-radius: 8px;">
            Trải nghiệm ngay
        </a>
    </p>

    <h2>📖 Hướng dẫn</h2>
    <p>Xem hướng dẫn chi tiết tại <a href="https://yourdomain.com/docs">trang tài liệu</a>.</p>

    <p>Chúc bạn có trải nghiệm tuyệt vời!</p>

    <p>
        Trân trọng,<br>
        TikZ2SVG Team
    </p>
</body>
</html>
```

**Validation:**
- [ ] Announcement posted
- [ ] Email sent to users
- [ ] Social media updated (if applicable)
- [ ] Documentation links work

---

## ✅ Completion Criteria

Phase 5 complete when:
- [ ] All unit tests passing (≥70% coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Load tests completed
- [ ] UAT completed with ≥3 users
- [ ] All documentation updated
- [ ] Production deployment successful
- [ ] Monitoring active
- [ ] Alerting configured
- [ ] Users notified
- [ ] No critical bugs
- [ ] Performance targets met

---

## 🎉 Project Complete!

After Phase 5, the prompt-to-TikZ generation feature is:
- ✅ Fully tested
- ✅ Documented
- ✅ Deployed to production
- ✅ Monitored
- ✅ Communicated to users

**Next steps:**
- Monitor metrics for 1 week
- Collect user feedback
- Iterate based on feedback
- Plan Phase 2 features (if needed)

---

**Congratulations on completing the implementation!** 🚀
