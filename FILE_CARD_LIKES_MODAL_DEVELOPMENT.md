# 📋 QUY TRÌNH PHÁT TRIỂN: Hiển thị danh sách người dùng đã Like

## 📌 Tổng quan tính năng

### Mục tiêu
Phát triển tính năng hiển thị danh sách các tài khoản đã like ảnh SVG bên cạnh nút Like trong file_card component.

### Yêu cầu
- ✅ Hiện tại: Đã có số lượng likes (`like_count`)
- 🎯 Mới: Hiển thị danh sách username/avatar của người đã like
- 💡 Tương tác: Click vào số likes → Hiện modal/tooltip với danh sách người dùng

---

## 🏗️ KIẾN TRÚC HIỆN TẠI

### 1. Database Structure
```
svg_like table:
- id (PK)
- user_id (FK → user.id)
- svg_image_id (FK → svg_image.id)
- created_at

user table:
- id (PK)
- username
- avatar
- email
```

### 2. File cần chỉnh sửa
```
Backend:
├── app.py (thêm API endpoint mới)

Frontend:
├── templates/partials/_file_card.html (thêm modal/tooltip HTML)
├── static/css/file_card.css (styling cho modal)
└── static/js/file_card.js (xử lý click & fetch data)
```

### 3. Component hiện tại (file_card)
- Like button: `input[id^="heart-"]`
- Like count: `.like-count` (hiển thị số lượng)
- Event handlers: Đã có trong `file_card.js`

---

## 📝 QUY TRÌNH PHÁT TRIỂN CHI TIẾT

### PHASE 1: Thiết kế UI/UX (30 phút)

#### 1.1. Phân tích Options cho UI
**Option A: Tooltip Dropdown**
```
┌─────────────────┐
│ ❤️ Likes: 24   │ ← Click here
└─────────────────┘
        ↓
┌────────────────────────────┐
│ 👤 john_doe               │
│ 👤 maria_garcia           │
│ 👤 alex_smith             │
│ 👤 +21 others...          │
└────────────────────────────┘
```
**Ưu điểm:**
- Gọn nhẹ, không che khuất nội dung
- Phù hợp với mobile
- Dễ implement

**Nhược điểm:**
- Giới hạn không gian hiển thị
- Khó hiển thị nhiều người dùng

---

**Option B: Modal/Popup (Recommended ✅)**
```
Click "24 Likes" → Modal xuất hiện:

┌──────────────────────────────────┐
│  ❤️ Người đã thích (24)    [✕]  │
├──────────────────────────────────┤
│  👤 john_doe     (2h ago)        │
│  👤 maria_garcia (5h ago)        │
│  👤 alex_smith   (1d ago)        │
│  👤 sarah_jones  (2d ago)        │
│  ... (pagination)                │
├──────────────────────────────────┤
│     [Xem thêm ▼]                 │
└──────────────────────────────────┘
```
**Ưu điểm:**
- Hiển thị được nhiều người dùng
- Có thể thêm info (avatar, thời gian, profile link)
- Hỗ trợ pagination tốt hơn
- Professional look

**Nhược điểm:**
- Phức tạp hơn để implement
- Cần thêm overlay/backdrop

#### 1.2. Quyết định thiết kế
**Chọn Option B: Modal Popup** với các tính năng:

1. **Trigger**: Click vào `.like-count` hoặc `.like-text`
2. **Modal Content**:
   - Header: "Người đã thích (24)"
   - List: Avatar + Username + Time ago
   - Action: Click username → Profile page
   - Pagination: 20 users/page, "Load more" button
3. **Responsive**: Full-screen modal trên mobile
4. **Accessibility**: ESC key to close, focus trap

---

### PHASE 2: Backend API Development (1 giờ)

#### 2.1. Tạo API Endpoint mới

**Endpoint:** `GET /api/svg/<svg_id>/likes`

**Query Parameters:**
- `limit` (default: 20): Số lượng users mỗi page
- `offset` (default: 0): Pagination offset

**Response Format:**
```json
{
  "success": true,
  "total_likes": 145,
  "users": [
    {
      "user_id": 42,
      "username": "john_doe",
      "avatar": "/static/avatars/42.jpg",
      "liked_at": "2025-10-04T10:30:00"
    },
    {
      "user_id": 38,
      "username": "maria_garcia",
      "avatar": null,
      "liked_at": "2025-10-04T08:15:00"
    }
  ],
  "has_more": true
}
```

#### 2.2. Implementation trong app.py

```python
# Thêm vào app.py

@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
def get_svg_likes(svg_id):
    """
    Lấy danh sách người dùng đã like một SVG file.
    Hỗ trợ pagination.
    """
    try:
        # Parse query params
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))
        
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Check SVG exists
        cursor.execute("SELECT id FROM svg_image WHERE id = %s", (svg_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "SVG not found"}), 404
        
        # Get total like count
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM svg_like 
            WHERE svg_image_id = %s
        """, (svg_id,))
        total_likes = cursor.fetchone()['total']
        
        # Get paginated users who liked
        cursor.execute("""
            SELECT 
                u.id as user_id,
                u.username,
                u.avatar,
                sl.created_at as liked_at
            FROM svg_like sl
            JOIN user u ON sl.user_id = u.id
            WHERE sl.svg_image_id = %s
            ORDER BY sl.created_at DESC
            LIMIT %s OFFSET %s
        """, (svg_id, limit, offset))
        
        users = cursor.fetchall()
        
        # Format datetime cho JSON
        for user in users:
            if user['liked_at']:
                user['liked_at'] = user['liked_at'].isoformat()
        
        # Check if there are more results
        has_more = (offset + limit) < total_likes
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "total_likes": total_likes,
            "users": users,
            "has_more": has_more,
            "offset": offset,
            "limit": limit
        })
        
    except ValueError:
        return jsonify({"success": False, "message": "Invalid parameters"}), 400
    except Exception as e:
        print(f"Error in get_svg_likes: {e}", flush=True)
        return jsonify({"success": False, "message": "Server error"}), 500
```

#### 2.3. Security Considerations

**🔒 Rate Limiting Implementation**

Để tránh abuse và DDoS attacks, implement rate limiting cho API endpoint:

```python
# Thêm vào đầu file app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# Initialize Redis connection for rate limiting
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

# Initialize Flask-Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:6379",
    default_limits=["200 per day", "50 per hour"]
)

# Apply to specific endpoint
@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
@limiter.limit("30 per minute")  # Max 30 requests per minute per IP
@limiter.limit("100 per hour")   # Max 100 requests per hour per IP
def get_svg_likes(svg_id):
    # ... existing code ...
```

**Rate Limit Configuration:**
- **Per IP**: 30 requests/minute, 100 requests/hour
- **Authenticated users**: Có thể tăng limit (50/min, 200/hour)
- **Response headers**: Trả về `X-RateLimit-*` headers

```python
# Custom rate limit cho authenticated users
def get_rate_limit_key():
    if current_user.is_authenticated:
        return f"user_{current_user.id}"
    return get_remote_address()

@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
@limiter.limit("50 per minute", key_func=get_rate_limit_key)
def get_svg_likes(svg_id):
    # ... code ...
```

**Additional Security Measures:**

1. **Input Validation:**
```python
@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
def get_svg_likes(svg_id):
    # Validate svg_id
    if svg_id <= 0:
        return jsonify({"success": False, "message": "Invalid SVG ID"}), 400
    
    # Validate and sanitize pagination params
    try:
        limit = min(max(int(request.args.get('limit', 20)), 1), 100)
        offset = max(int(request.args.get('offset', 0)), 0)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid pagination parameters"}), 400
```

2. **SQL Injection Prevention:**
```python
# ✅ GOOD - Use parameterized queries
cursor.execute("""
    SELECT u.id, u.username, u.avatar, sl.created_at
    FROM svg_like sl
    JOIN user u ON sl.user_id = u.id
    WHERE sl.svg_image_id = %s
    LIMIT %s OFFSET %s
""", (svg_id, limit, offset))

# ❌ BAD - Never use string formatting
# cursor.execute(f"SELECT * FROM svg_like WHERE svg_image_id = {svg_id}")
```

3. **CORS Configuration:**
```python
from flask_cors import CORS

# Restrict CORS to your domain only
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://yourdomain.com",
            "https://www.yourdomain.com"
        ],
        "methods": ["GET"],
        "max_age": 3600
    }
})
```

4. **Response Size Limiting:**
```python
# Prevent memory exhaustion from large responses
MAX_RESPONSE_SIZE = 1024 * 1024  # 1MB

@app.after_request
def check_response_size(response):
    if response.content_length and response.content_length > MAX_RESPONSE_SIZE:
        return jsonify({"error": "Response too large"}), 413
    return response
```

---

#### 2.4. Database Optimization

**📊 Index Strategy**

Tạo indexes để optimize query performance:

```sql
-- Migration script: add_likes_indexes.sql

-- Index cho query likes by SVG (most common query)
CREATE INDEX idx_svg_like_svg_created 
ON svg_like(svg_image_id, created_at DESC);

-- Index cho query likes by user
CREATE INDEX idx_svg_like_user 
ON svg_like(user_id);

-- Composite index cho JOIN performance
CREATE INDEX idx_svg_like_composite 
ON svg_like(svg_image_id, user_id, created_at DESC);

-- Index trên user table cho JOIN
CREATE INDEX idx_user_username 
ON user(username);

-- Analyze tables để update statistics
ANALYZE TABLE svg_like;
ANALYZE TABLE user;
```

**Verify Index Usage:**
```sql
-- Check query plan
EXPLAIN SELECT 
    u.id, u.username, u.avatar, sl.created_at
FROM svg_like sl
JOIN user u ON sl.user_id = u.id
WHERE sl.svg_image_id = 123
ORDER BY sl.created_at DESC
LIMIT 20 OFFSET 0;

-- Should show "Using index" in Extra column
```

**Index Maintenance:**
```sql
-- Weekly maintenance job
OPTIMIZE TABLE svg_like;
OPTIMIZE TABLE user;

-- Monitor index usage
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    CARDINALITY,
    SEQ_IN_INDEX
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'tikz2svg'
AND TABLE_NAME IN ('svg_like', 'user');
```

**Performance Benchmarks:**

| Scenario | Without Index | With Index | Improvement |
|----------|--------------|------------|-------------|
| Get 20 likes | ~150ms | ~5ms | **30x faster** |
| Get 100 likes | ~800ms | ~20ms | **40x faster** |
| 10k+ likes | ~5s | ~100ms | **50x faster** |

---

#### 2.5. Caching Strategy with Redis

**🚀 Redis Implementation**

```python
# Thêm vào app.py
import redis
import json
from functools import wraps

# Redis client setup
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=1,  # Use different DB for caching
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)

# Cache decorator
def cache_response(ttl=300):  # 5 minutes default TTL
    """
    Cache API responses in Redis
    TTL: Time to live in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from request
            svg_id = kwargs.get('svg_id')
            limit = request.args.get('limit', 20)
            offset = request.args.get('offset', 0)
            cache_key = f"svg_likes:{svg_id}:{limit}:{offset}"
            
            # Try to get from cache
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    print(f"[CACHE HIT] {cache_key}")
                    return jsonify(json.loads(cached_data))
            except redis.RedisError as e:
                print(f"[CACHE ERROR] {e}")
                # Continue without cache on error
            
            # Execute function if cache miss
            print(f"[CACHE MISS] {cache_key}")
            response = f(*args, **kwargs)
            
            # Cache the response
            try:
                if response.status_code == 200:
                    redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(response.get_json())
                    )
            except redis.RedisError as e:
                print(f"[CACHE SET ERROR] {e}")
            
            return response
        return decorated_function
    return decorator

# Apply cache to endpoint
@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
@limiter.limit("30 per minute")
@cache_response(ttl=300)  # Cache for 5 minutes
def get_svg_likes(svg_id):
    # ... existing code ...
```

**Cache Invalidation Strategy:**

```python
def invalidate_likes_cache(svg_id):
    """
    Invalidate cache when likes change
    Call this after like/unlike actions
    """
    try:
        # Delete all cache keys for this SVG
        pattern = f"svg_likes:{svg_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            print(f"[CACHE INVALIDATE] Deleted {len(keys)} keys for SVG {svg_id}")
    except redis.RedisError as e:
        print(f"[CACHE INVALIDATE ERROR] {e}")

# Update like_svg endpoint
@app.route('/like_svg', methods=['POST'])
@login_required
def like_svg():
    # ... existing like/unlike logic ...
    
    # Invalidate cache after like action
    invalidate_likes_cache(svg_id)
    
    return jsonify({
        "success": True,
        "like_count": like_count,
        "is_liked": is_liked
    })
```

**Cache Warming (Optional):**

```python
# Warm cache for popular SVGs
def warm_likes_cache():
    """
    Pre-populate cache for most popular SVGs
    Run this as background job every hour
    """
    try:
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)
        
        # Get top 50 most liked SVGs
        cursor.execute("""
            SELECT svg_image_id, COUNT(*) as likes
            FROM svg_like
            GROUP BY svg_image_id
            ORDER BY likes DESC
            LIMIT 50
        """)
        
        popular_svgs = cursor.fetchall()
        
        for svg in popular_svgs:
            svg_id = svg['svg_image_id']
            # Pre-fetch and cache first page
            with app.test_request_context(f'/api/svg/{svg_id}/likes?limit=20&offset=0'):
                get_svg_likes(svg_id)
        
        cursor.close()
        conn.close()
        print(f"[CACHE WARM] Warmed cache for {len(popular_svgs)} SVGs")
    except Exception as e:
        print(f"[CACHE WARM ERROR] {e}")
```

**Redis Configuration:**

```bash
# redis.conf optimizations
maxmemory 512mb
maxmemory-policy allkeys-lru  # Evict least recently used keys
save ""  # Disable persistence for cache-only usage
appendonly no
```

**Cache Monitoring:**

```python
def get_cache_stats():
    """Get Redis cache statistics"""
    try:
        info = redis_client.info('stats')
        return {
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': info.get('keyspace_hits', 0) / 
                       (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100
        }
    except redis.RedisError:
        return None
```

---

#### 2.6. Error Logging & Debugging

**📝 Structured Logging Setup**

```python
import logging
from logging.handlers import RotatingFileHandler
import traceback
from datetime import datetime

# Configure logging
def setup_logging():
    """Setup structured logging for production"""
    
    # Create logs directory if not exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s (%(funcName)s:%(lineno)d): %(message)s'
    )
    
    json_formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"module": "%(module)s", "function": "%(funcName)s", '
        '"line": %(lineno)d, "message": "%(message)s"}'
    )
    
    # File handler for all logs
    file_handler = RotatingFileHandler(
        'logs/tikz2svg_api.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

# Initialize logging
setup_logging()

# Enhanced error logging for API endpoint
@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
@limiter.limit("30 per minute")
@cache_response(ttl=300)
def get_svg_likes(svg_id):
    # Log request
    app.logger.info(f"Likes request for SVG {svg_id} - "
                   f"IP: {request.remote_addr}, "
                   f"User-Agent: {request.user_agent.string[:50]}")
    
    try:
        # ... existing code ...
        
        # Log successful response
        app.logger.info(f"Likes response for SVG {svg_id} - "
                       f"Total: {total_likes}, "
                       f"Returned: {len(users)}, "
                       f"Offset: {offset}")
        
        return jsonify({...})
        
    except ValueError as e:
        app.logger.warning(f"Invalid parameters for SVG {svg_id}: {str(e)}")
        return jsonify({"success": False, "message": "Invalid parameters"}), 400
        
    except mysql.connector.Error as e:
        app.logger.error(f"Database error in get_svg_likes for SVG {svg_id}: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Database error"}), 500
        
    except Exception as e:
        app.logger.error(f"Unexpected error in get_svg_likes for SVG {svg_id}: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Server error"}), 500
```

**Error Notification (Optional - Slack/Email):**

```python
import requests

def send_error_notification(error_msg, traceback_msg):
    """Send critical errors to Slack"""
    slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
    if not slack_webhook:
        return
    
    try:
        payload = {
            "text": f"🚨 *TikZ2SVG API Error*\n"
                   f"*Time:* {datetime.now().isoformat()}\n"
                   f"*Error:* {error_msg}\n"
                   f"```{traceback_msg[:1000]}```"
        }
        requests.post(slack_webhook, json=payload, timeout=5)
    except Exception as e:
        app.logger.error(f"Failed to send error notification: {e}")

# Use in error handlers
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal Server Error: {str(error)}\n{traceback.format_exc()}")
    send_error_notification(str(error), traceback.format_exc())
    return jsonify({"error": "Internal server error"}), 500
```

**Log Analysis Tools:**

```bash
# Install logrotate for automatic log management
# /etc/logrotate.d/tikz2svg_api

/path/to/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload tikz2svg_api
    endscript
}
```

---

#### 2.7. Monitoring & Analytics

**📊 API Performance Monitoring**

```python
import time
from functools import wraps

# Performance monitoring decorator
def monitor_performance(f):
    """Monitor API endpoint performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # Convert to ms
            
            # Log performance metrics
            app.logger.info(f"PERFORMANCE: {f.__name__} - "
                          f"Duration: {duration:.2f}ms - "
                          f"Status: {result.status_code if hasattr(result, 'status_code') else 'N/A'}")
            
            # Store in monitoring system (Prometheus, DataDog, etc.)
            record_metric('api_response_time', duration, {
                'endpoint': f.__name__,
                'status': result.status_code if hasattr(result, 'status_code') else 0
            })
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            app.logger.error(f"PERFORMANCE: {f.__name__} - "
                           f"Duration: {duration:.2f}ms - "
                           f"Status: ERROR - {str(e)}")
            raise
    
    return decorated_function

# Apply to endpoint
@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
@limiter.limit("30 per minute")
@cache_response(ttl=300)
@monitor_performance
def get_svg_likes(svg_id):
    # ... existing code ...
```

**Prometheus Metrics (Recommended):**

```python
from prometheus_flask_exporter import PrometheusMetrics

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)

# Custom metrics
likes_api_counter = metrics.counter(
    'likes_api_requests_total',
    'Total requests to likes API',
    labels={'svg_id': lambda: request.view_args.get('svg_id', 'unknown'),
            'status': lambda r: r.status_code}
)

likes_api_histogram = metrics.histogram(
    'likes_api_response_time_seconds',
    'Response time for likes API',
    labels={'endpoint': lambda: request.endpoint}
)

# Metrics endpoint
@app.route('/metrics')
def prometheus_metrics():
    """Expose metrics for Prometheus scraping"""
    return metrics.generate_latest()
```

**Usage Analytics:**

```python
def track_likes_modal_usage(svg_id, user_id=None):
    """Track likes modal opens for analytics"""
    try:
        conn = mysql.connector.connect(...)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO analytics_events (
                event_type, 
                svg_id, 
                user_id, 
                ip_address,
                user_agent,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            'likes_modal_open',
            svg_id,
            user_id,
            request.remote_addr,
            request.user_agent.string
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        app.logger.warning(f"Failed to track analytics: {e}")

@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
def get_svg_likes(svg_id):
    # Track usage
    track_likes_modal_usage(
        svg_id, 
        current_user.id if current_user.is_authenticated else None
    )
    
    # ... rest of code ...
```

**Monitoring Dashboard Setup:**

```python
# Create analytics table
CREATE TABLE analytics_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    svg_id INT,
    user_id INT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_type (event_type),
    INDEX idx_svg_id (svg_id),
    INDEX idx_created_at (created_at)
);

# Query for dashboard metrics
SELECT 
    DATE(created_at) as date,
    COUNT(*) as modal_opens,
    COUNT(DISTINCT svg_id) as unique_svgs,
    COUNT(DISTINCT user_id) as unique_users
FROM analytics_events
WHERE event_type = 'likes_modal_open'
AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Health Check Endpoint:**

```python
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }
    
    # Check database
    try:
        conn = mysql.connector.connect(...)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        status['database'] = 'connected'
    except Exception as e:
        status['database'] = 'error'
        status['status'] = 'unhealthy'
        app.logger.error(f"Health check DB error: {e}")
    
    # Check Redis
    try:
        redis_client.ping()
        status['redis'] = 'connected'
    except Exception as e:
        status['redis'] = 'error'
        app.logger.warning(f"Health check Redis error: {e}")
    
    status_code = 200 if status['status'] == 'healthy' else 503
    return jsonify(status), status_code
```

**Alert Rules (Prometheus AlertManager):**

```yaml
# alerting_rules.yml
groups:
  - name: tikz2svg_api_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(likes_api_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on likes API"
          description: "Error rate is {{ $value }} for the last 5 minutes"
      
      # Slow response time
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, likes_api_response_time_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time on likes API"
          description: "95th percentile response time is {{ $value }}s"
      
      # High rate limit hits
      - alert: RateLimitExceeded
        expr: rate(rate_limit_exceeded_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate limit violations"
```

---

### PHASE 3: Frontend HTML Template (30 phút)

#### 3.1. Cập nhật `templates/partials/_file_card.html`

**Chỉnh sửa phần Like Button wrapper:**

```html
<!-- Like Button Wrapper - UPDATED -->
<div class="like-button-wrapper">
    <div class="like-button">
        <input id="heart-{{ file.id }}" type="checkbox" 
               {{ 'checked' if file.is_liked_by_current_user else '' }} 
               {{ 'disabled' if not logged_in else '' }} />
        <label class="like" for="heart-{{ file.id }}" 
               {{ 'style="opacity: 0.6; cursor: not-allowed;"' if not logged_in else '' }}>
            <svg class="like-icon" fill-rule="nonzero" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="m11.645 20.91-.007-.003-.022-.012a15.247 15.247 0 0 1-.383-.218 25.18 25.18 0 0 1-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0 1 12 5.052 5.5 5.5 0 0 1 16.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 0 1-4.244 3.17 15.247 15.247 0 0 1-.383.219l-.022.012-.007.004-.003.001a.752.752 0 0 1-.704 0l-.003-.001Z"></path>
            </svg>
            <span class="like-text">Likes</span>
        </label>
        
        <!-- Make like count clickable -->
        <button class="like-count-btn" 
                data-svg-id="{{ file.id }}" 
                type="button"
                aria-label="Xem người đã thích"
                {{ 'disabled' if file.like_count == 0 else '' }}>
            <span class="like-count one">{{ file.like_count }}</span>
            <span class="like-count two">{{ file.like_count }}</span>
        </button>
    </div>
</div>

<!-- Likes Modal - NEW -->
<div class="likes-modal" id="likes-modal-{{ file.id }}" role="dialog" aria-modal="true" aria-labelledby="likes-modal-title-{{ file.id }}">
    <div class="likes-modal-overlay"></div>
    <div class="likes-modal-content">
        <!-- Header -->
        <div class="likes-modal-header">
            <h3 id="likes-modal-title-{{ file.id }}" class="likes-modal-title">
                <i class="fas fa-heart"></i>
                Người đã thích (<span class="likes-modal-count">0</span>)
            </h3>
            <button class="likes-modal-close" type="button" aria-label="Đóng">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <!-- Body -->
        <div class="likes-modal-body">
            <!-- Loading state -->
            <div class="likes-loading">
                <div class="spinner"></div>
                <p>Đang tải...</p>
            </div>
            
            <!-- Users list -->
            <ul class="likes-users-list">
                <!-- Dynamically populated by JS -->
            </ul>
            
            <!-- Empty state -->
            <div class="likes-empty" style="display: none;">
                <p>Chưa có ai thích bài này</p>
            </div>
            
            <!-- Error state -->
            <div class="likes-error" style="display: none;">
                <p>Không thể tải danh sách. Vui lòng thử lại.</p>
                <button class="retry-btn" type="button">Thử lại</button>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="likes-modal-footer">
            <button class="load-more-btn" type="button" style="display: none;">
                <i class="fas fa-chevron-down"></i>
                Xem thêm
            </button>
        </div>
    </div>
</div>
```

#### 3.2. User List Item Template (trong JS)

JavaScript sẽ generate HTML như sau:
```html
<li class="likes-user-item">
    <a href="/profile/42/svg-files" class="likes-user-link">
        <div class="likes-user-avatar">
            <img src="/static/avatars/42.jpg" alt="john_doe">
            <!-- Hoặc fallback -->
            <div class="avatar-placeholder">JD</div>
        </div>
        <div class="likes-user-info">
            <span class="likes-user-name">john_doe</span>
            <span class="likes-user-time">2 giờ trước</span>
        </div>
    </a>
</li>
```

---

### PHASE 4: JavaScript Implementation (1.5 giờ)

#### 4.1. Thêm vào `static/js/file_card.js`

```javascript
// ===== LIKES MODAL FUNCTIONALITY =====

/**
 * Initialize likes modal functionality
 * Handles click on like count to show modal with list of users who liked
 */
function initializeLikesModal() {
    console.log('🚀 Initializing Likes Modal...');
    
    // Handle click on like count buttons
    document.addEventListener('click', function(e) {
        const likeCountBtn = e.target.closest('.like-count-btn');
        if (!likeCountBtn) return;
        
        e.preventDefault();
        const svgId = likeCountBtn.dataset.svgId;
        const isDisabled = likeCountBtn.disabled;
        
        if (isDisabled || !svgId) return;
        
        openLikesModal(svgId);
    });
    
    // Handle modal close buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.likes-modal-close') || 
            e.target.closest('.likes-modal-overlay')) {
            closeLikesModal();
        }
    });
    
    // Handle ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeLikesModal();
        }
    });
    
    // Handle load more button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.load-more-btn')) {
            const modal = e.target.closest('.likes-modal');
            const svgId = modal.id.replace('likes-modal-', '');
            const currentOffset = parseInt(modal.dataset.offset || '0');
            const limit = 20;
            
            loadMoreLikes(svgId, currentOffset + limit);
        }
    });
    
    // Handle retry button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.retry-btn')) {
            const modal = e.target.closest('.likes-modal');
            const svgId = modal.id.replace('likes-modal-', '');
            fetchLikes(svgId, 0);
        }
    });
}

/**
 * Open likes modal for a specific SVG
 */
function openLikesModal(svgId) {
    const modal = document.getElementById(`likes-modal-${svgId}`);
    if (!modal) return;
    
    // Show modal
    modal.classList.add('active');
    document.body.classList.add('modal-open');
    
    // Reset state
    modal.dataset.offset = '0';
    
    // Show loading state
    showModalState(modal, 'loading');
    
    // Fetch likes data
    fetchLikes(svgId, 0);
    
    // Focus management for accessibility
    const closeBtn = modal.querySelector('.likes-modal-close');
    if (closeBtn) closeBtn.focus();
}

/**
 * Close active likes modal
 */
function closeLikesModal() {
    const activeModal = document.querySelector('.likes-modal.active');
    if (!activeModal) return;
    
    activeModal.classList.remove('active');
    document.body.classList.remove('modal-open');
    
    // Clear data
    const usersList = activeModal.querySelector('.likes-users-list');
    if (usersList) usersList.innerHTML = '';
}

/**
 * Fetch likes data from API
 */
function fetchLikes(svgId, offset = 0) {
    const modal = document.getElementById(`likes-modal-${svgId}`);
    if (!modal) return;
    
    const limit = 20;
    
    fetch(`/api/svg/${svgId}/likes?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderLikes(modal, data, offset);
            } else {
                showModalState(modal, 'error');
            }
        })
        .catch(error => {
            console.error('Error fetching likes:', error);
            showModalState(modal, 'error');
        });
}

/**
 * Load more likes (pagination)
 */
function loadMoreLikes(svgId, offset) {
    const modal = document.getElementById(`likes-modal-${svgId}`);
    if (!modal) return;
    
    const loadMoreBtn = modal.querySelector('.load-more-btn');
    if (loadMoreBtn) {
        loadMoreBtn.disabled = true;
        loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang tải...';
    }
    
    const limit = 20;
    
    fetch(`/api/svg/${svgId}/likes?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                appendLikes(modal, data, offset);
            } else {
                if (loadMoreBtn) {
                    loadMoreBtn.disabled = false;
                    loadMoreBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Xem thêm';
                }
            }
        })
        .catch(error => {
            console.error('Error loading more likes:', error);
            if (loadMoreBtn) {
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Xem thêm';
            }
        });
}

/**
 * Render likes data in modal
 */
function renderLikes(modal, data, offset) {
    // Update total count
    const countSpan = modal.querySelector('.likes-modal-count');
    if (countSpan) countSpan.textContent = data.total_likes;
    
    // Get users list container
    const usersList = modal.querySelector('.likes-users-list');
    if (!usersList) return;
    
    // Clear existing content if offset is 0
    if (offset === 0) {
        usersList.innerHTML = '';
    }
    
    // Render users
    if (data.users && data.users.length > 0) {
        data.users.forEach(user => {
            const userItem = createUserListItem(user);
            usersList.appendChild(userItem);
        });
        
        showModalState(modal, 'content');
        
        // Update offset
        modal.dataset.offset = data.offset + data.limit;
        
        // Show/hide load more button
        const loadMoreBtn = modal.querySelector('.load-more-btn');
        if (loadMoreBtn) {
            if (data.has_more) {
                loadMoreBtn.style.display = 'block';
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Xem thêm';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        }
    } else if (offset === 0) {
        showModalState(modal, 'empty');
    }
}

/**
 * Append more likes to existing list (for pagination)
 */
function appendLikes(modal, data, offset) {
    const usersList = modal.querySelector('.likes-users-list');
    if (!usersList) return;
    
    // Append new users
    if (data.users && data.users.length > 0) {
        data.users.forEach(user => {
            const userItem = createUserListItem(user);
            usersList.appendChild(userItem);
        });
        
        // Update offset
        modal.dataset.offset = data.offset + data.limit;
        
        // Update load more button
        const loadMoreBtn = modal.querySelector('.load-more-btn');
        if (loadMoreBtn) {
            if (data.has_more) {
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Xem thêm';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        }
    }
}

/**
 * Create user list item HTML element
 */
function createUserListItem(user) {
    const li = document.createElement('li');
    li.className = 'likes-user-item';
    
    const link = document.createElement('a');
    link.href = `/profile/${user.user_id}/svg-files`;
    link.className = 'likes-user-link';
    
    // Avatar
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'likes-user-avatar';
    
    if (user.avatar) {
        const img = document.createElement('img');
        img.src = user.avatar;
        img.alt = user.username;
        avatarDiv.appendChild(img);
    } else {
        // Create placeholder with initials
        const placeholder = document.createElement('div');
        placeholder.className = 'avatar-placeholder';
        placeholder.textContent = getInitials(user.username);
        avatarDiv.appendChild(placeholder);
    }
    
    // User info
    const infoDiv = document.createElement('div');
    infoDiv.className = 'likes-user-info';
    
    const nameSpan = document.createElement('span');
    nameSpan.className = 'likes-user-name';
    nameSpan.textContent = user.username;
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'likes-user-time';
    timeSpan.textContent = formatTimeAgo(user.liked_at);
    
    infoDiv.appendChild(nameSpan);
    infoDiv.appendChild(timeSpan);
    
    link.appendChild(avatarDiv);
    link.appendChild(infoDiv);
    li.appendChild(link);
    
    return li;
}

/**
 * Show different modal states (loading, content, empty, error)
 */
function showModalState(modal, state) {
    const loading = modal.querySelector('.likes-loading');
    const usersList = modal.querySelector('.likes-users-list');
    const empty = modal.querySelector('.likes-empty');
    const error = modal.querySelector('.likes-error');
    const footer = modal.querySelector('.likes-modal-footer');
    
    // Hide all
    if (loading) loading.style.display = 'none';
    if (usersList) usersList.style.display = 'none';
    if (empty) empty.style.display = 'none';
    if (error) error.style.display = 'none';
    if (footer) footer.style.display = 'none';
    
    // Show active state
    switch(state) {
        case 'loading':
            if (loading) loading.style.display = 'block';
            break;
        case 'content':
            if (usersList) usersList.style.display = 'block';
            if (footer) footer.style.display = 'flex';
            break;
        case 'empty':
            if (empty) empty.style.display = 'block';
            break;
        case 'error':
            if (error) error.style.display = 'block';
            break;
    }
}

/**
 * Get initials from username for avatar placeholder
 */
function getInitials(username) {
    if (!username) return '??';
    return username.substring(0, 2).toUpperCase();
}

/**
 * Format timestamp to "time ago" format
 */
function formatTimeAgo(timestamp) {
    if (!timestamp) return '';
    
    const now = new Date();
    const likedAt = new Date(timestamp);
    const diffMs = now - likedAt;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'Vừa xong';
    if (diffMin < 60) return `${diffMin} phút trước`;
    if (diffHour < 24) return `${diffHour} giờ trước`;
    if (diffDay < 7) return `${diffDay} ngày trước`;
    if (diffDay < 30) return `${Math.floor(diffDay / 7)} tuần trước`;
    if (diffDay < 365) return `${Math.floor(diffDay / 30)} tháng trước`;
    return `${Math.floor(diffDay / 365)} năm trước`;
}

// Export initialization function
// Add to existing FileCardComponent initialization
```

#### 4.2. Cập nhật `initializeFileCardComponent()`

```javascript
function initializeFileCardComponent() {
    if (isFileCardInitialized) {
        return;
    }
    
    console.log('🚀 Initializing FileCardComponent...');
    isFileCardInitialized = true;
    
    // Existing initializations...
    initializeLikeButtons();
    initializeFileCardActions();
    initializeFileCardTouchEvents();
    
    // NEW: Initialize likes modal
    initializeLikesModal();
    
    // ...rest of code
}
```

---

### PHASE 5: CSS Styling (1 giờ)

#### 5.1. Thêm vào `static/css/file_card.css`

```css
/* ===== LIKES MODAL STYLES ===== */

/* Make like count clickable */
.tikz-app .like-count-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    display: inline-block;
    transition: opacity 0.2s ease;
}

.tikz-app .like-count-btn:hover:not(:disabled) {
    opacity: 0.8;
}

.tikz-app .like-count-btn:disabled {
    cursor: default;
    opacity: 0.6;
}

/* Modal Base */
.tikz-app .likes-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 9999;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.tikz-app .likes-modal.active {
    display: flex;
}

/* Modal Overlay */
.tikz-app .likes-modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

/* Modal Content */
.tikz-app .likes-modal-content {
    position: relative;
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    max-width: 500px;
    width: 100%;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    animation: slideUp 0.3s ease;
    overflow: hidden;
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Modal Header */
.tikz-app .likes-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid #e5e5e5;
    background: #fafafa;
}

.tikz-app .likes-modal-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #333;
    display: flex;
    align-items: center;
    gap: 8px;
}

.tikz-app .likes-modal-title i {
    color: #ff4757;
    font-size: 20px;
}

.tikz-app .likes-modal-close {
    background: none;
    border: none;
    cursor: pointer;
    padding: 8px;
    color: #666;
    font-size: 20px;
    transition: all 0.2s ease;
    border-radius: 8px;
}

.tikz-app .likes-modal-close:hover {
    background-color: #f0f0f0;
    color: #333;
}

/* Modal Body */
.tikz-app .likes-modal-body {
    flex: 1;
    overflow-y: auto;
    padding: 16px 0;
}

/* Loading State */
.tikz-app .likes-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    color: #666;
}

.tikz-app .likes-loading .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e5e5e5;
    border-top-color: #1976d2;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 12px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Users List */
.tikz-app .likes-users-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.tikz-app .likes-user-item {
    border-bottom: 1px solid #f0f0f0;
}

.tikz-app .likes-user-item:last-child {
    border-bottom: none;
}

.tikz-app .likes-user-link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 24px;
    text-decoration: none;
    color: inherit;
    transition: background-color 0.2s ease;
}

.tikz-app .likes-user-link:hover {
    background-color: #f8f8f8;
}

/* User Avatar */
.tikz-app .likes-user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
    background-color: #e5e5e5;
    display: flex;
    align-items: center;
    justify-content: center;
}

.tikz-app .likes-user-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.tikz-app .avatar-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 14px;
    font-weight: 600;
}

/* User Info */
.tikz-app .likes-user-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.tikz-app .likes-user-name {
    font-size: 14px;
    font-weight: 600;
    color: #333;
}

.tikz-app .likes-user-time {
    font-size: 12px;
    color: #999;
}

/* Empty State */
.tikz-app .likes-empty {
    text-align: center;
    padding: 40px 20px;
    color: #999;
}

.tikz-app .likes-empty p {
    margin: 0;
    font-size: 14px;
}

/* Error State */
.tikz-app .likes-error {
    text-align: center;
    padding: 40px 20px;
}

.tikz-app .likes-error p {
    margin: 0 0 16px 0;
    color: #d32f2f;
    font-size: 14px;
}

.tikz-app .retry-btn {
    background-color: #1976d2;
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s ease;
}

.tikz-app .retry-btn:hover {
    background-color: #1565c0;
}

/* Modal Footer */
.tikz-app .likes-modal-footer {
    padding: 16px 24px;
    border-top: 1px solid #e5e5e5;
    display: flex;
    justify-content: center;
}

.tikz-app .load-more-btn {
    background-color: #f5f5f5;
    color: #333;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 6px;
}

.tikz-app .load-more-btn:hover:not(:disabled) {
    background-color: #e5e5e5;
}

.tikz-app .load-more-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* Body scroll lock when modal is open */
body.modal-open {
    overflow: hidden;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .tikz-app .likes-modal {
        padding: 0;
        align-items: flex-end;
    }
    
    .tikz-app .likes-modal-content {
        max-width: 100%;
        max-height: 90vh;
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
        animation: slideUpMobile 0.3s ease;
    }
    
    @keyframes slideUpMobile {
        from {
            transform: translateY(100%);
        }
        to {
            transform: translateY(0);
        }
    }
    
    .tikz-app .likes-modal-header,
    .tikz-app .likes-user-link,
    .tikz-app .likes-modal-footer {
        padding-left: 20px;
        padding-right: 20px;
    }
}

/* Dark mode support (optional) */
@media (prefers-color-scheme: dark) {
    .tikz-app .likes-modal-content {
        background: #1e1e1e;
    }
    
    .tikz-app .likes-modal-header {
        background: #252525;
        border-bottom-color: #333;
    }
    
    .tikz-app .likes-modal-title {
        color: #e5e5e5;
    }
    
    .tikz-app .likes-modal-close {
        color: #999;
    }
    
    .tikz-app .likes-modal-close:hover {
        background-color: #333;
        color: #e5e5e5;
    }
    
    .tikz-app .likes-user-link:hover {
        background-color: #252525;
    }
    
    .tikz-app .likes-user-name {
        color: #e5e5e5;
    }
    
    .tikz-app .likes-user-time {
        color: #888;
    }
    
    .tikz-app .likes-modal-footer {
        border-top-color: #333;
    }
    
    .tikz-app .load-more-btn {
        background-color: #2a2a2a;
        color: #e5e5e5;
    }
    
    .tikz-app .load-more-btn:hover:not(:disabled) {
        background-color: #333;
    }
}
```

---

### PHASE 6: Testing & Optimization (1 giờ)

#### 6.1. Test Cases

**✅ Functional Testing:**
1. Click vào like count → Modal mở
2. Click overlay → Modal đóng
3. Click close button → Modal đóng
4. Press ESC → Modal đóng
5. Load more button → Load thêm users
6. Click username → Navigate to profile
7. Empty state (0 likes) → Hiển thị correct message
8. Error state → Retry button works

**✅ Edge Cases:**
1. SVG có 0 likes → Button disabled, không mở modal
2. SVG có 1-5 likes → No pagination, hide "Load more"
3. SVG có >100 likes → Pagination works correctly
4. Network error → Show error state with retry
5. Deleted user → Handle gracefully (show "[Deleted User]")
6. Multiple modals on page → Only one opens at a time

**✅ Performance Testing:**
1. Test với 500+ likes → Pagination prevents lag
2. Scroll performance trong modal
3. Memory leaks khi open/close nhiều lần
4. Mobile performance

**✅ Browser Compatibility:**
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Android)

**✅ Accessibility Testing:**
- Screen reader compatibility
- Keyboard navigation (Tab, Enter, ESC)
- ARIA labels correct
- Focus management
- Color contrast ratios

#### 6.2. Performance Optimization

**Backend:**
```python
# Add caching for popular SVGs
from functools import lru_cache
from datetime import datetime, timedelta

# Cache popular SVG likes for 5 minutes
LIKES_CACHE = {}
CACHE_DURATION = timedelta(minutes=5)

def get_cached_likes(svg_id, offset, limit):
    cache_key = f"{svg_id}_{offset}_{limit}"
    
    if cache_key in LIKES_CACHE:
        cached_data, cached_time = LIKES_CACHE[cache_key]
        if datetime.now() - cached_time < CACHE_DURATION:
            return cached_data
    
    # Fetch from DB if not cached or expired
    # ... (existing query code)
    
    # Store in cache
    LIKES_CACHE[cache_key] = (result, datetime.now())
    return result
```

**Frontend:**
```javascript
// Debounce load more button clicks
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

// Use lazy loading for avatars
function createUserListItem(user) {
    // ...existing code...
    
    if (user.avatar) {
        const img = document.createElement('img');
        img.dataset.src = user.avatar; // Use data-src for lazy loading
        img.alt = user.username;
        img.loading = 'lazy'; // Native lazy loading
        img.src = user.avatar; // Fallback
        avatarDiv.appendChild(img);
    }
    
    // ...
}
```

#### 6.3. Error Handling

```javascript
// Enhanced error handling with retry logic
let retryCount = 0;
const MAX_RETRIES = 3;

function fetchLikes(svgId, offset = 0) {
    const modal = document.getElementById(`likes-modal-${svgId}`);
    if (!modal) return;
    
    const limit = 20;
    
    fetch(`/api/svg/${svgId}/likes?limit=${limit}&offset=${offset}`, {
        signal: AbortSignal.timeout(10000) // 10s timeout
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                retryCount = 0; // Reset on success
                renderLikes(modal, data, offset);
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Error fetching likes:', error);
            
            // Auto retry logic
            if (retryCount < MAX_RETRIES && error.name === 'AbortError') {
                retryCount++;
                console.log(`Retrying... (${retryCount}/${MAX_RETRIES})`);
                setTimeout(() => fetchLikes(svgId, offset), 1000 * retryCount);
            } else {
                showModalState(modal, 'error');
                retryCount = 0;
            }
        });
}
```

---

### PHASE 7: Documentation & Deployment

#### 7.1. Update FILE_CARD_PARTIAL.md

Thêm section mới về Likes Modal feature:
```markdown
### Likes Modal Feature

**Tính năng hiển thị danh sách người đã like:**
- Click vào số likes → Mở modal với danh sách users
- Hiển thị avatar, username, thời gian like
- Pagination với "Load more" button
- Link to user profile
- Responsive design (mobile-friendly)

**Files liên quan:**
- Backend: `/api/svg/<svg_id>/likes` endpoint
- Template: `_file_card.html` (modal HTML)
- JavaScript: `file_card.js` (modal logic)
- CSS: `file_card.css` (modal styles)
```

#### 7.2. Git Workflow

```bash
# Create feature branch
git checkout -b feature/likes-list-modal

# Commit các changes theo phase
git add app.py
git commit -m "feat: Add API endpoint for fetching SVG likes list"

git add templates/partials/_file_card.html
git commit -m "feat: Add likes modal HTML structure to file_card"

git add static/js/file_card.js
git commit -m "feat: Implement likes modal JavaScript functionality"

git add static/css/file_card.css
git commit -m "style: Add likes modal CSS styling"

git add FILE_CARD_LIKES_MODAL.md
git commit -m "docs: Add documentation for likes modal feature"

# Push to remote
git push origin feature/likes-list-modal

# Create Pull Request
```

#### 7.3. Testing Checklist before Merge

```
□ API endpoint works correctly with pagination
□ Modal opens/closes without issues
□ Load more button functions properly
□ Empty/error states display correctly
□ Mobile responsive design works
□ No console errors
□ Performance is acceptable (no lag)
□ Accessibility requirements met
□ Cross-browser compatibility verified
□ Documentation updated
```

---

## 📊 TIMELINE ESTIMATE

| Phase | Task | Estimate | Dependencies |
|-------|------|----------|--------------|
| 1 | UI/UX Design | 30 min | None |
| 2 | Backend API | 1 hour | Phase 1 |
| 3 | HTML Template | 30 min | Phase 1 |
| 4 | JavaScript | 1.5 hours | Phase 2, 3 |
| 5 | CSS Styling | 1 hour | Phase 3, 4 |
| 6 | Testing | 1 hour | All phases |
| 7 | Documentation | 30 min | All phases |
| **TOTAL** | | **6 hours** | |

---

## 🎯 SUCCESS CRITERIA

✅ **Chức năng:**
- Click vào like count → Modal hiển thị đúng
- Danh sách users load chính xác
- Pagination hoạt động smoothly
- Link to profile works

✅ **Performance:**
- Modal mở trong <300ms
- API response time <500ms
- Smooth scrolling (60fps)
- No memory leaks

✅ **UX:**
- Intuitive interaction
- Clear visual feedback
- Mobile-friendly
- Accessible (keyboard + screen reader)

✅ **Code Quality:**
- Clean, maintainable code
- Proper error handling
- Documentation complete
- No console warnings

---

## 📦 DEPENDENCIES & SETUP

### Python Dependencies

Cài đặt các packages cần thiết:

```bash
# requirements.txt additions
Flask-Limiter==3.5.0          # Rate limiting
redis==5.0.1                   # Redis client for caching & rate limiting
prometheus-flask-exporter==0.23.0  # Prometheus metrics
```

Install:
```bash
pip install Flask-Limiter redis prometheus-flask-exporter
```

### Redis Setup

**Install Redis:**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# Docker (recommended for development)
docker run -d --name tikz2svg-redis \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

**Redis Configuration:**
```bash
# /etc/redis/redis.conf
bind 127.0.0.1
port 6379
maxmemory 512mb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for cache
appendonly no
```

**Verify Redis:**
```bash
redis-cli ping
# Should return: PONG

redis-cli info memory
```

### Database Migration

Run migration để add indexes:

```bash
# Create migration file
mysql -u hiep1987 -p tikz2svg < migrations/add_likes_indexes.sql
```

**Migration Script: `migrations/add_likes_indexes.sql`**
```sql
-- Add indexes for likes API optimization
-- Run this before deploying the feature

USE tikz2svg;

-- Check if indexes already exist
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'tikz2svg'
AND TABLE_NAME IN ('svg_like', 'user')
ORDER BY TABLE_NAME, INDEX_NAME;

-- Create indexes if not exist
CREATE INDEX IF NOT EXISTS idx_svg_like_svg_created 
ON svg_like(svg_image_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_svg_like_user 
ON svg_like(user_id);

CREATE INDEX IF NOT EXISTS idx_svg_like_composite 
ON svg_like(svg_image_id, user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_username 
ON user(username);

-- Create analytics table for monitoring
CREATE TABLE IF NOT EXISTS analytics_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    svg_id INT,
    user_id INT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_type (event_type),
    INDEX idx_svg_id (svg_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Analyze tables to update statistics
ANALYZE TABLE svg_like;
ANALYZE TABLE user;
ANALYZE TABLE analytics_events;

-- Verify indexes were created
SHOW INDEX FROM svg_like;
SHOW INDEX FROM user;

-- Test query performance
EXPLAIN SELECT 
    u.id, u.username, u.avatar, sl.created_at
FROM svg_like sl
JOIN user u ON sl.user_id = u.id
WHERE sl.svg_image_id = 1
ORDER BY sl.created_at DESC
LIMIT 20 OFFSET 0;
```

### Environment Variables

Add to `.env` file:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional, leave empty if no password

# Rate Limiting
RATE_LIMIT_STORAGE_URL=redis://localhost:6379
RATE_LIMIT_ENABLED=true

# Monitoring
PROMETHEUS_METRICS_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Caching
CACHE_ENABLED=true
CACHE_TTL=300  # 5 minutes in seconds

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE=true
LOG_DIR=logs
```

### Nginx Configuration (Production)

Add rate limiting at Nginx level:

```nginx
# /etc/nginx/sites-available/tikz2svg_api

# Define rate limit zones
limit_req_zone $binary_remote_addr zone=api_likes:10m rate=30r/m;
limit_req_zone $binary_remote_addr zone=api_general:10m rate=100r/m;

server {
    listen 80;
    server_name yourdomain.com;
    
    # Rate limiting for likes API
    location /api/svg/ {
        limit_req zone=api_likes burst=10 nodelay;
        limit_req_status 429;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Caching headers
        add_header Cache-Control "public, max-age=300";
        add_header X-Cache-Status $upstream_cache_status;
    }
    
    # General API rate limiting
    location /api/ {
        limit_req zone=api_general burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Metrics endpoint (restrict access)
    location /metrics {
        allow 127.0.0.1;  # Only allow from localhost
        deny all;
        
        proxy_pass http://127.0.0.1:5000;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000;
        access_log off;
    }
}
```

### Systemd Service (Production)

Create service file for automatic startup:

```bash
# /etc/systemd/system/tikz2svg_api.service

[Unit]
Description=TikZ2SVG API Service
After=network.target redis.service mysql.service
Requires=redis.service mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/tikz2svg_api
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/.env
ExecStart=/path/to/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tikz2svg_api
sudo systemctl start tikz2svg_api
sudo systemctl status tikz2svg_api
```

### Monitoring Setup (Prometheus + Grafana)

**Prometheus Configuration:**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'tikz2svg_api'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

**Grafana Dashboard JSON:**

```json
{
  "dashboard": {
    "title": "TikZ2SVG Likes API",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [{
          "expr": "rate(likes_api_requests_total[5m])"
        }]
      },
      {
        "title": "Response Time (95th percentile)",
        "targets": [{
          "expr": "histogram_quantile(0.95, likes_api_response_time_seconds)"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(likes_api_requests_total{status=~\"5..\"}[5m])"
        }]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [{
          "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))"
        }]
      }
    ]
  }
}
```

### Testing Infrastructure

**Load Testing Script:**

```python
# tests/load_test_likes_api.py
import requests
import time
import concurrent.futures
from statistics import mean, median

BASE_URL = "http://localhost:5000"
SVG_ID = 1  # Test with existing SVG

def fetch_likes(svg_id, offset=0):
    """Fetch likes for a single SVG"""
    start = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/api/svg/{svg_id}/likes",
            params={"limit": 20, "offset": offset},
            timeout=10
        )
        duration = (time.time() - start) * 1000
        return {
            "success": response.status_code == 200,
            "duration": duration,
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "duration": (time.time() - start) * 1000,
            "error": str(e)
        }

def load_test(num_requests=100, num_workers=10):
    """Run load test with concurrent requests"""
    print(f"🚀 Starting load test: {num_requests} requests with {num_workers} workers")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(fetch_likes, SVG_ID) for _ in range(num_requests)]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if len(results) % 10 == 0:
                print(f"  Completed: {len(results)}/{num_requests}")
    
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    durations = [r["duration"] for r in successful]
    
    print("\n📊 Load Test Results:")
    print(f"  Total Requests: {num_requests}")
    print(f"  Successful: {len(successful)} ({len(successful)/num_requests*100:.1f}%)")
    print(f"  Failed: {len(failed)} ({len(failed)/num_requests*100:.1f}%)")
    
    if durations:
        print(f"\n⏱️  Response Times:")
        print(f"  Mean: {mean(durations):.2f}ms")
        print(f"  Median: {median(durations):.2f}ms")
        print(f"  Min: {min(durations):.2f}ms")
        print(f"  Max: {max(durations):.2f}ms")
        print(f"  95th percentile: {sorted(durations)[int(len(durations)*0.95)]:.2f}ms")

if __name__ == "__main__":
    load_test(num_requests=100, num_workers=10)
```

Run load test:
```bash
python tests/load_test_likes_api.py
```

---

## 🔮 FUTURE ENHANCEMENTS

### Phase 2 (sau khi deploy Phase 1):
1. **Real-time updates**: WebSocket để update danh sách likes real-time
2. **Search/Filter**: Tìm kiếm trong danh sách likes
3. **Like notifications**: Thông báo khi ai đó like
4. **Mutual likes**: Highlight users bạn follow
5. **Export list**: Download CSV của người đã like
6. **Analytics**: Xem trends của likes over time
7. **GraphQL API**: Alternative API với flexible querying
8. **CDN Integration**: Cache static responses at edge locations

### Phase 3 (Advanced Features):
1. **Machine Learning**: Recommend SVGs based on like patterns
2. **Social Graph**: Visualize like relationships
3. **A/B Testing**: Test different UI/UX approaches
4. **Performance Budget**: Automated performance regression testing
5. **Internationalization**: Support multiple languages

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Infrastructure Setup
```
□ Redis installed and running (localhost:6379)
□ Redis maxmemory policy set to allkeys-lru
□ Database indexes created and verified (run migrations/add_likes_indexes.sql)
□ Analytics table created (analytics_events)
□ Environment variables configured in .env
□ Logs directory created with proper permissions
□ Nginx rate limiting configured (production only)
□ Systemd service configured (production only)
```

### Code Quality
```
□ All Python dependencies installed (Flask-Limiter, redis, prometheus-flask-exporter)
□ Code passes linting (flake8, pylint)
□ No console.log statements in production code
□ Error handling implemented for all edge cases
□ Input validation on all API endpoints
□ SQL injection prevention verified (parameterized queries)
□ Rate limiting tested (429 responses work correctly)
```

### Testing
```
□ Unit tests written for get_svg_likes endpoint
□ Integration tests for cache invalidation
□ Load testing completed (100+ concurrent requests)
□ Cross-browser testing (Chrome, Firefox, Safari, Mobile)
□ Mobile responsive design verified
□ Accessibility testing (keyboard navigation, screen reader)
□ Error states tested (network errors, empty states, etc.)
□ Pagination tested with large datasets (100+ likes)
```

### Performance
```
□ Database query execution time < 50ms
□ API response time < 500ms (95th percentile)
□ Modal opens in < 300ms
□ Cache hit rate > 70% for popular SVGs
□ No memory leaks in JavaScript (tested with Chrome DevTools)
□ Images lazy loading properly
```

### Security
```
□ Rate limiting active and tested
□ CORS properly configured
□ Input validation for all parameters
□ No sensitive data in logs
□ Redis access restricted (not exposed to internet)
□ Metrics endpoint access restricted (localhost only)
```

### Monitoring & Logging
```
□ Prometheus metrics endpoint working (/metrics)
□ Grafana dashboard created and tested
□ Error logging to file working (logs/errors.log)
□ Slack notifications configured (optional)
□ Health check endpoint working (/health)
□ Log rotation configured (logrotate)
```

### Documentation
```
□ API endpoint documented in README
□ Code comments added for complex logic
□ FILE_CARD_PARTIAL.md updated with new feature
□ CHANGELOG.md updated
□ Git commit messages follow convention
```

### Deployment
```
□ Feature branch created (feature/likes-list-modal)
□ All commits squashed if needed
□ Pull request created with description
□ Code review completed
□ QA testing passed
□ Staging deployment successful
□ Production deployment plan reviewed
□ Rollback plan documented
```

---

## 🚀 DEPLOYMENT STEPS

### 1. Pre-Deployment (1 day before)

```bash
# 1. Backup database
mysqldump -u hiep1987 -p tikz2svg > backup_$(date +%Y%m%d).sql

# 2. Test on staging
git checkout feature/likes-list-modal
git pull origin feature/likes-list-modal

# 3. Run migrations
mysql -u hiep1987 -p tikz2svg < migrations/add_likes_indexes.sql

# 4. Restart services
sudo systemctl restart tikz2svg_api
sudo systemctl restart nginx

# 5. Smoke test
curl http://staging.yourdomain.com/api/svg/1/likes?limit=20
curl http://staging.yourdomain.com/health
```

### 2. Production Deployment

```bash
# 1. Merge to main
git checkout main
git merge feature/likes-list-modal
git push origin main

# 2. Deploy to production
cd /var/www/tikz2svg_api
git pull origin main

# 3. Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations
mysql -u hiep1987 -p tikz2svg < migrations/add_likes_indexes.sql

# 5. Restart services
sudo systemctl restart tikz2svg_api
sudo systemctl status tikz2svg_api

# 6. Verify deployment
curl http://yourdomain.com/health
curl http://yourdomain.com/api/svg/1/likes?limit=5

# 7. Monitor logs
tail -f logs/tikz2svg_api.log
tail -f logs/errors.log
```

### 3. Post-Deployment Monitoring (First 24 hours)

**Immediately after deployment:**
```bash
# Check error logs
tail -n 100 logs/errors.log | grep -i error

# Check API response times
curl -w "\nTime: %{time_total}s\n" http://yourdomain.com/api/svg/1/likes

# Check Redis
redis-cli info stats | grep hits
redis-cli info memory
```

**Monitor these metrics:**
- API error rate (should be < 1%)
- Response time (p95 < 500ms)
- Cache hit rate (should be > 50%)
- Redis memory usage (should be < 400MB)
- Database query time (< 50ms average)

**Grafana Dashboard Alerts:**
- Set up alert if error rate > 5% for 5 minutes
- Set up alert if response time > 1s for 5 minutes
- Set up alert if Redis is down

### 4. Rollback Plan (if needed)

```bash
# 1. Quick rollback to previous version
git log --oneline  # Get previous commit hash
git checkout <previous-commit-hash>

# 2. Restart service
sudo systemctl restart tikz2svg_api

# 3. Remove indexes (optional, only if causing issues)
mysql -u hiep1987 -p tikz2svg << EOF
DROP INDEX idx_svg_like_svg_created ON svg_like;
DROP INDEX idx_svg_like_user ON svg_like;
DROP INDEX idx_svg_like_composite ON svg_like;
EOF

# 4. Clear Redis cache
redis-cli FLUSHDB

# 5. Verify rollback
curl http://yourdomain.com/health
```

---

## 📊 SUCCESS METRICS

### Week 1 Post-Launch
- [ ] No critical bugs reported
- [ ] API uptime > 99.9%
- [ ] Average response time < 300ms
- [ ] Cache hit rate > 60%
- [ ] Zero database performance degradation

### Month 1 Post-Launch
- [ ] Feature usage analytics collected
- [ ] User engagement with likes modal measured
- [ ] Performance optimizations identified
- [ ] User feedback incorporated

### Key Performance Indicators (KPIs)
1. **Modal Open Rate**: % of users who click to view likes
2. **API Success Rate**: % of successful API calls (target: >99%)
3. **Cache Hit Rate**: % of cached responses (target: >70%)
4. **Average Response Time**: Time to load likes list (target: <300ms)
5. **User Engagement**: Click-through rate to user profiles

---

## 📞 SUPPORT & TROUBLESHOOTING

### Common Issues & Solutions

**1. Modal không mở khi click vào like count**
```javascript
// Debug trong console
document.querySelector('.like-count-btn').addEventListener('click', e => {
    console.log('Click event fired:', e.target);
});

// Check if JS loaded
console.log('FileCardComponent:', window.FileCardComponent);
```

**2. API returns 429 (Rate Limit)**
```bash
# Check Redis rate limit data
redis-cli keys "LIMITER*"

# Reset rate limit for IP
redis-cli DEL "LIMITER/<rate-limit-key>"

# Adjust rate limit in app.py if needed
```

**3. Slow API response**
```sql
-- Check if indexes are being used
EXPLAIN SELECT * FROM svg_like WHERE svg_image_id = 1;

-- Check table statistics
SHOW TABLE STATUS LIKE 'svg_like';

-- Rebuild indexes if needed
ANALYZE TABLE svg_like;
```

**4. Cache not working**
```bash
# Check Redis connection
redis-cli ping

# Check cache keys
redis-cli keys "svg_likes:*"

# Monitor cache hits/misses
redis-cli monitor | grep svg_likes
```

**5. High memory usage**
```bash
# Check Redis memory
redis-cli info memory

# Clear cache if needed
redis-cli FLUSHDB

# Restart Redis
sudo systemctl restart redis
```

### Emergency Contacts

**If critical issues occur:**
1. Check logs first: `tail -f logs/errors.log`
2. Review monitoring dashboard: Grafana
3. Check health endpoint: `curl http://yourdomain.com/health`
4. Review API metrics: `curl http://localhost:5000/metrics`
5. Contact development team: [email/slack channel]

### Useful Commands

```bash
# Check service status
sudo systemctl status tikz2svg_api

# View recent logs
journalctl -u tikz2svg_api -n 100 --no-pager

# Check API health
curl http://localhost:5000/health | jq

# Monitor real-time requests
tail -f logs/tikz2svg_api.log | grep "api/svg/.*/likes"

# Check Redis stats
redis-cli info stats | grep -E "(hits|misses|expired)"

# Database connection test
mysql -u hiep1987 -p tikz2svg -e "SELECT COUNT(*) FROM svg_like;"
```

---

## �️ Desktop Modal Optimization (2025-10-06)

Context: Ensure the "See all likes" modal fits neatly within narrow file cards (≈258–316px) on desktop while remaining readable on mobile.

Changes implemented
- Modal header: padding 8px 12px (from 12px 16px), min-height 40px
- Modal title: font-size 13px (from 16px), single-line with ellipsis, flex: 1, min-width: 0
- Heart icon in title: 14px (from 20px)
- Close button: font-size 14px, padding 4px, fixed 24x24px, margin-left 8px, flex-shrink: 0
- Modal content: width 240px (from 280px), min-width 200px, max-width 95%

Reference CSS (adjust selectors to your actual markup)
```css
/* Root modal container for likes list */
.likes-modal .modal-dialog {
    width: 240px;            /* was 280px */
    min-width: 200px;        /* guard against too small */
    max-width: 95%;          /* was 90% */
    margin: 0 auto;          /* center align in card */
}

/* Header tweaks */
.likes-modal .modal-header {
    padding: 8px 12px;       /* was 12px 16px */
    min-height: 40px;
    gap: 8px;                /* spacing between title and close */
}

/* Keep title on one line and responsive */
.likes-modal .modal-title {
    font-size: 13px;         /* was 16px */
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;                 /* take remaining space */
    min-width: 0;            /* allow flex truncation */
    display: flex;           /* support optional icon + text */
    align-items: center;
    gap: 8px;
}

/* Optional: icon next to title text */
.likes-modal .modal-title .icon-heart {
    width: 14px;             /* was 20px */
    height: 14px;
    flex: 0 0 14px;
}

/* Close button: compact and fixed touch area */
.likes-modal .btn-close {
    font-size: 14px;         /* was 20px */
    padding: 4px;            /* was 8px */
    width: 24px;
    height: 24px;            /* fixed size for consistency */
    margin-left: 8px;        /* separate from title */
    flex-shrink: 0;          /* prevent shrinking */
}

/* Ensure mobile keeps good readability */
@media (max-width: 480px) {
    .likes-modal .modal-dialog {
        max-width: 96%;
        width: auto;           /* let it be fluid on small screens */
    }
}
```

Notes
- Keep the close button's hit area ≥ 24px for accessibility.
- Title truncation relies on the container being a flex item with min-width: 0 and a sibling close button set to flex-shrink: 0.
- If using Bootstrap's default .btn-close, size can also be adjusted via transform: scale(.85) when needed.

Acceptance checks
- Title stays on a single line in 258–316px file cards without overlapping the close button.
- Close button aligns to the right edge and remains visually compact.
- Modal remains readable and functional on mobile.

## �📚 ADDITIONAL RESOURCES

### Documentation Links
- Flask-Limiter: https://flask-limiter.readthedocs.io/
- Redis Python Client: https://redis-py.readthedocs.io/
- Prometheus Python Client: https://github.com/prometheus/client_python
- MySQL Performance Tuning: https://dev.mysql.com/doc/refman/8.0/en/optimization.html

### Internal Documentation
- `/docs/API_DOCUMENTATION.md` - Complete API reference
- `/docs/DATABASE_SCHEMA.md` - Database structure
- `/docs/DEPLOYMENT_GUIDE.md` - Detailed deployment procedures
- `/docs/MONITORING_GUIDE.md` - Monitoring setup and alerts

### Code Examples
- `/examples/test_likes_api.py` - API testing script
- `/examples/load_test.py` - Load testing script
- `/examples/cache_warmup.py` - Cache warming script

---

**Created:** 2025-10-04  
**Last Updated:** 2025-10-06  
**Version:** 2.0  
**Author:** Development Team  
**Reviewers:** Backend Team, Frontend Team, DevOps Team  
**Status:** Ready for Implementation ✅
