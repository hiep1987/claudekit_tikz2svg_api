# Phase 1: Backend Infrastructure

**Duration:** 4-6 hours
**Priority:** High (Foundation for all other phases)
**Dependencies:** None

---

## 🎯 Objectives

Build robust backend API endpoint integrating tikz-api service with authentication, rate limiting, error handling.

---

## 📋 Tasks Breakdown

### Task 1.1: Environment Configuration (30 min)

**File:** `.env`

Add tikz-api configuration:
```bash
# TikZ Generation API Configuration
TIKZ_API_URL=http://localhost:8000
TIKZ_API_TIMEOUT=30
TIKZ_API_MAX_PROMPT_LENGTH=500
TIKZ_GENERATION_RATE_LIMIT=10  # per 10 minutes
```

**Validation:**
- [ ] Variables loaded correctly
- [ ] Default values if not set

---

### Task 1.2: Database Schema (Optional - 45 min)

**Decision Point:** Enable history feature?

If YES, create table:

```sql
CREATE TABLE IF NOT EXISTS tikz_generations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    prompt TEXT NOT NULL,
    generated_code TEXT NOT NULL,
    diagram_type VARCHAR(50) DEFAULT 'other',
    latex_packages JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_created (user_id, created_at DESC),
    INDEX idx_user_used (user_id, used, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Migration approach:**
```python
# In app.py initialization section
def init_tikz_generations_table():
    """Create tikz_generations table if not exists"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tikz_generations (
                -- schema above
            )
        """)
        conn.commit()
        print("✓ tikz_generations table ready")
    except mysql.connector.Error as err:
        print(f"✗ Error creating tikz_generations: {err}")
    finally:
        cursor.close()
        conn.close()

# Call during app initialization
init_tikz_generations_table()
```

**Validation:**
- [ ] Table created successfully
- [ ] Foreign key constraints work
- [ ] Indexes created

---

### Task 1.3: Rate Limiting Configuration (30 min)

**File:** `app.py`

Add new rate limit rule:

```python
# After existing RATE_LIMITS definition
RATE_LIMITS = {
    'api_likes_preview': "500 per minute",
    'api_like_counts': "500 per minute",
    'api_general': "1000 per minute",
    'api_write': "50 per minute",
    'tikz_generation': "10 per 10 minutes",  # NEW
}
```

**Why 10/10min?**
- tikz-api has 10 req/min limit
- Allows buffer for other API operations
- Prevents abuse while allowing exploration
- Matches tikz-api service capacity

**Validation:**
- [ ] Rate limit enforced correctly
- [ ] Reset after 10 minutes
- [ ] User-friendly error message

---

### Task 1.4: TikZ-API Client Function (60 min)

**File:** `app.py`

Create reusable client function:

```python
import requests
from typing import Dict, Optional

def call_tikz_api(prompt: str, timeout: int = 30) -> Dict:
    """
    Call tikz-api service to generate TikZ code from prompt.

    Args:
        prompt: Vietnamese/English math description
        timeout: Request timeout in seconds (default: 30)

    Returns:
        dict: {
            'success': bool,
            'tikz_code': str,
            'type': str,
            'latex_preamble': list,
            'error': str (if failed)
        }

    Raises:
        requests.RequestException: Network/timeout errors
    """
    api_url = os.environ.get('TIKZ_API_URL', 'http://localhost:8000')
    endpoint = f"{api_url}/api/v1/generate"

    try:
        response = requests.post(
            endpoint,
            json={'prompt': prompt},
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()

        data = response.json()

        # Validate response structure
        if data.get('status') == 'success':
            return {
                'success': True,
                'tikz_code': data.get('tikz_code', ''),
                'type': data.get('type', 'other'),
                'latex_preamble': data.get('latex_preamble', [])
            }
        else:
            return {
                'success': False,
                'error': data.get('error', {}).get('message', 'Unknown error')
            }

    except requests.Timeout:
        return {
            'success': False,
            'error': 'Quá thời gian chờ (30 giây). Vui lòng thử lại với mô tả ngắn hơn.'
        }
    except requests.ConnectionError:
        return {
            'success': False,
            'error': 'Không thể kết nối đến dịch vụ sinh mã TikZ. Vui lòng thử lại sau.'
        }
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            return {
                'success': False,
                'error': 'Đã vượt giới hạn số lần tạo mã. Vui lòng chờ vài phút.'
            }
        elif e.response.status_code == 400:
            return {
                'success': False,
                'error': 'Mô tả không hợp lệ. Vui lòng mô tả rõ ràng hơn về hình vẽ bạn muốn.'
            }
        else:
            return {
                'success': False,
                'error': f'Lỗi từ dịch vụ (HTTP {e.response.status_code})'
            }
    except Exception as e:
        logging.error(f"Unexpected error calling tikz-api: {str(e)}")
        return {
            'success': False,
            'error': 'Có lỗi xảy ra. Vui lòng thử lại sau.'
        }
```

**Error handling covers:**
- Timeout (30s)
- Connection errors
- HTTP errors (400, 429, 500)
- Invalid response format
- Unexpected exceptions

**Validation:**
- [ ] Successful generation returns correct structure
- [ ] Timeout handled gracefully
- [ ] Error messages user-friendly (Vietnamese)
- [ ] Logs errors for debugging

---

### Task 1.5: API Endpoint Implementation (90 min)

**File:** `app.py`

Create `/api/tikz/generate` endpoint:

```python
@app.route('/api/tikz/generate', methods=['POST'])
@login_required
@limiter.limit(RATE_LIMITS['tikz_generation'])
def api_tikz_generate():
    """
    Generate TikZ code from Vietnamese/English prompt using tikz-api service.

    Request Body:
        {
            "prompt": "vẽ bảng biến thiên hàm số y = x^3 - 3x + 1",
            "save_history": true  // optional, default: false
        }

    Response:
        Success (200):
        {
            "success": true,
            "tikz_code": "\\begin{tikzpicture}...",
            "type": "variation_table",
            "latex_preamble": ["amsmath", "tikz", "tkz-tab"],
            "generation_id": 123  // if save_history=true
        }

        Error (400/429/500):
        {
            "success": false,
            "error": "Mô tả không hợp lệ...",
            "code": "INVALID_PROMPT"
        }

    Rate Limit: 10 requests per 10 minutes per user
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Thiếu dữ liệu yêu cầu',
                'code': 'MISSING_DATA'
            }), 400

        prompt = data.get('prompt', '').strip()
        save_history = data.get('save_history', False)

        # Validation
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Vui lòng nhập mô tả hình vẽ',
                'code': 'EMPTY_PROMPT'
            }), 400

        max_length = int(os.environ.get('TIKZ_API_MAX_PROMPT_LENGTH', 500))
        if len(prompt) > max_length:
            return jsonify({
                'success': False,
                'error': f'Mô tả quá dài (tối đa {max_length} ký tự)',
                'code': 'PROMPT_TOO_LONG'
            }), 400

        # Call tikz-api service
        result = call_tikz_api(prompt)

        if not result['success']:
            return jsonify({
                'success': False,
                'error': result['error'],
                'code': 'GENERATION_FAILED'
            }), 500

        # Optional: Save to history
        generation_id = None
        if save_history:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO tikz_generations
                    (user_id, prompt, generated_code, diagram_type, latex_packages)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    current_user.id,
                    prompt,
                    result['tikz_code'],
                    result['type'],
                    json.dumps(result['latex_preamble'])
                ))
                conn.commit()
                generation_id = cursor.lastrowid
            except mysql.connector.Error as err:
                logging.error(f"Error saving generation history: {err}")
                # Continue even if history save fails
            finally:
                cursor.close()
                conn.close()

        # Success response
        response_data = {
            'success': True,
            'tikz_code': result['tikz_code'],
            'type': result['type'],
            'latex_preamble': result['latex_preamble']
        }

        if generation_id:
            response_data['generation_id'] = generation_id

        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"Error in api_tikz_generate: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Có lỗi xảy ra. Vui lòng thử lại sau.',
            'code': 'INTERNAL_ERROR'
        }), 500
```

**Security measures:**
- `@login_required` - Only authenticated users
- Rate limiting - 10 requests/10 minutes
- Input validation - Length, non-empty
- XSS protection - JSON response (no HTML)
- SQL injection - Parameterized queries

**Validation:**
- [ ] Returns 401 if not logged in
- [ ] Returns 429 if rate limit exceeded
- [ ] Returns 400 for invalid input
- [ ] Returns 200 with valid TikZ code
- [ ] Saves history if requested
- [ ] Handles tikz-api errors gracefully

---

### Task 1.6: History Retrieval Endpoint (Optional - 45 min)

**File:** `app.py`

If history enabled, create endpoint to fetch user's generations:

```python
@app.route('/api/tikz/history', methods=['GET'])
@login_required
@limiter.limit(RATE_LIMITS['api_general'])
def api_tikz_history():
    """
    Get user's recent TikZ generations (last 10).

    Query Params:
        limit: int (default: 10, max: 50)

    Response:
        {
            "success": true,
            "generations": [
                {
                    "id": 123,
                    "prompt": "vẽ bảng biến thiên...",
                    "tikz_code": "\\begin{tikzpicture}...",
                    "type": "variation_table",
                    "created_at": "2025-11-13T10:30:00Z",
                    "used": false
                },
                ...
            ],
            "total": 25
        }
    """
    try:
        limit = min(int(request.args.get('limit', 10)), 50)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get recent generations
        cursor.execute("""
            SELECT id, prompt, generated_code as tikz_code,
                   diagram_type as type, created_at, used
            FROM tikz_generations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (current_user.id, limit))

        generations = cursor.fetchall()

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM tikz_generations
            WHERE user_id = %s
        """, (current_user.id,))

        total = cursor.fetchone()['total']

        cursor.close()
        conn.close()

        # Format timestamps
        for gen in generations:
            if gen['created_at']:
                gen['created_at'] = gen['created_at'].isoformat()

        return jsonify({
            'success': True,
            'generations': generations,
            'total': total
        }), 200

    except Exception as e:
        logging.error(f"Error fetching generation history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Không thể tải lịch sử',
            'code': 'HISTORY_FETCH_FAILED'
        }), 500
```

**Validation:**
- [ ] Returns last 10 generations
- [ ] Respects limit parameter
- [ ] Returns total count
- [ ] Formats timestamps correctly

---

### Task 1.7: Mark Generation as Used (Optional - 30 min)

**File:** `app.py`

Track which generations user actually used:

```python
@app.route('/api/tikz/history/<int:generation_id>/use', methods=['POST'])
@login_required
@limiter.limit(RATE_LIMITS['api_write'])
def api_tikz_mark_used(generation_id):
    """
    Mark a generation as used (user clicked "Use code").

    Response:
        {
            "success": true
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify ownership and update
        cursor.execute("""
            UPDATE tikz_generations
            SET used = TRUE
            WHERE id = %s AND user_id = %s
        """, (generation_id, current_user.id))

        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy generation'
            }), 404

        cursor.close()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        logging.error(f"Error marking generation as used: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Có lỗi xảy ra'
        }), 500
```

---

## ✅ Validation Checklist

### Functional Tests
- [ ] Generate TikZ from Vietnamese prompt
- [ ] Generate TikZ from English prompt
- [ ] Handle timeout (>30s)
- [ ] Handle invalid prompt (empty, too long)
- [ ] Rate limiting triggers after 10 requests
- [ ] Rate limit resets after 10 minutes
- [ ] Authentication required (401 if not logged in)
- [ ] History saved correctly (if enabled)
- [ ] History retrieval works
- [ ] Mark as used works

### Error Handling Tests
- [ ] tikz-api service offline → user-friendly error
- [ ] tikz-api timeout → clear timeout message
- [ ] Invalid prompt → helpful validation message
- [ ] Database error → graceful degradation (no history)
- [ ] Network error → clear connectivity message

### Security Tests
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection (JSON responses)
- [ ] Rate limiting works per user
- [ ] Cannot access other users' history
- [ ] Cannot mark other users' generations as used

---

## 📊 Testing Strategy

### Unit Tests (pytest)

```python
# tests/test_tikz_generation.py

def test_call_tikz_api_success(mocker):
    """Test successful tikz-api call"""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'status': 'success',
        'tikz_code': '\\begin{tikzpicture}...',
        'type': 'variation_table',
        'latex_preamble': ['tikz', 'tkz-tab']
    }
    mock_response.raise_for_status = mocker.Mock()

    mocker.patch('requests.post', return_value=mock_response)

    result = call_tikz_api('vẽ bảng biến thiên')

    assert result['success'] == True
    assert 'tikz_code' in result
    assert result['type'] == 'variation_table'

def test_call_tikz_api_timeout(mocker):
    """Test timeout handling"""
    mocker.patch('requests.post', side_effect=requests.Timeout)

    result = call_tikz_api('test prompt')

    assert result['success'] == False
    assert 'Quá thời gian' in result['error']

def test_api_tikz_generate_requires_auth(client):
    """Test authentication requirement"""
    response = client.post('/api/tikz/generate', json={'prompt': 'test'})
    assert response.status_code == 401

def test_api_tikz_generate_rate_limit(client, auth_user):
    """Test rate limiting"""
    # Make 10 requests (should succeed)
    for i in range(10):
        response = client.post('/api/tikz/generate',
                              json={'prompt': f'test {i}'})
        assert response.status_code == 200

    # 11th request should fail
    response = client.post('/api/tikz/generate', json={'prompt': 'test 11'})
    assert response.status_code == 429

def test_api_tikz_generate_validation(client, auth_user):
    """Test input validation"""
    # Empty prompt
    response = client.post('/api/tikz/generate', json={'prompt': ''})
    assert response.status_code == 400
    assert 'Vui lòng nhập' in response.json['error']

    # Too long prompt
    long_prompt = 'a' * 501
    response = client.post('/api/tikz/generate', json={'prompt': long_prompt})
    assert response.status_code == 400
    assert 'quá dài' in response.json['error']
```

### Integration Tests

```python
# tests/integration/test_tikz_generation_flow.py

def test_full_generation_flow(client, auth_user, tikz_api_mock):
    """Test complete generation workflow"""
    # 1. Generate TikZ
    response = client.post('/api/tikz/generate', json={
        'prompt': 'vẽ bảng biến thiên y = x^2',
        'save_history': True
    })

    assert response.status_code == 200
    data = response.json
    assert data['success'] == True
    assert 'tikz_code' in data
    generation_id = data.get('generation_id')

    # 2. Fetch history
    response = client.get('/api/tikz/history')
    assert response.status_code == 200
    assert len(response.json['generations']) > 0

    # 3. Mark as used
    if generation_id:
        response = client.post(f'/api/tikz/history/{generation_id}/use')
        assert response.status_code == 200
```

---

## 🐛 Debugging Tips

### Common Issues

**Issue:** tikz-api connection refused
```bash
# Check tikz-api is running
curl http://localhost:8000/health

# Start tikz-api if not running
cd /Users/hieplequoc/Projects/tikz-api
python main.py
```

**Issue:** Rate limiting not working
```python
# Check limiter configuration
print(f"Limiter enabled: {limiter.enabled}")
print(f"Storage: {limiter._storage_uri}")

# Clear Redis cache (if using Redis)
redis-cli FLUSHDB
```

**Issue:** Database errors on history save
```sql
-- Check table exists
SHOW TABLES LIKE 'tikz_generations';

-- Check foreign key
SHOW CREATE TABLE tikz_generations;

-- Test insert
INSERT INTO tikz_generations (user_id, prompt, generated_code, diagram_type)
VALUES (1, 'test', 'test code', 'other');
```

---

## 📈 Performance Optimization

### Connection Pooling
```python
# Use existing connection pool
# app.py already handles this via get_db_connection()
```

### Timeout Tuning
```python
# Adjust timeout based on tikz-api performance
TIKZ_API_TIMEOUT = 30  # Start with 30s
# Monitor actual response times and adjust
```

### Caching (Future Enhancement)
```python
# Redis cache for frequently generated prompts
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

def call_tikz_api_cached(prompt):
    cache_key = f"tikz:prompt:{hashlib.md5(prompt.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    result = call_tikz_api(prompt)
    if result['success']:
        cache.setex(cache_key, 3600, json.dumps(result))  # 1 hour TTL
    return result
```

---

## 📝 Documentation Updates

### Add to `DOCS_CONTENT_COMPILATION.md`

```markdown
## Sinh mã TikZ từ mô tả

### Giới thiệu
Sử dụng AI để tự động sinh mã TikZ từ mô tả tiếng Việt hoặc tiếng Anh.

### Cách sử dụng
1. Mô tả hình vẽ bạn muốn (VD: "vẽ bảng biến thiên hàm số y = x^3 - 3x + 1")
2. Nhấn "Sinh mã TikZ"
3. Xem mã được sinh tự động
4. Nhấn "Dùng code này" để đưa vào editor chính
5. Biên dịch như bình thường

### Ví dụ mô tả tốt
- "vẽ bảng biến thiên của hàm số y = x^2 - 4x + 3"
- "vẽ đồ thị hàm số y = sin(x) trên đoạn [0, 2π]"
- "vẽ tam giác đều với cạnh dài 3cm"
- "vẽ sơ đồ khối cho hàm số bậc hai"

### Giới hạn
- 10 lần sinh mã mỗi 10 phút
- Tối đa 500 ký tự mô tả
- Thời gian chờ tối đa 30 giây
```

---

## ✅ Completion Criteria

Phase 1 complete when:
- [ ] `/api/tikz/generate` endpoint functional
- [ ] Authentication middleware enforced
- [ ] Rate limiting (10/10min) working
- [ ] tikz-api integration successful
- [ ] Error handling comprehensive
- [ ] Database table created (if history enabled)
- [ ] History endpoints working (if enabled)
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Documentation updated

---

**Next Phase:** Phase 2 - Frontend UI
**Dependencies for Phase 3:** Need Phase 1 API working to test AJAX calls
