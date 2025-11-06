# 📡 API Endpoints Documentation - TikZ2SVG

> **Comprehensive API documentation for TikZ2SVG platform**  
> **Last Updated:** November 6, 2024  
> **Platform Version:** 2.0  
> **Base URL:** `https://tikz2svg.com`

---

## 📋 Table of Contents

1. [System Info & Status APIs](#1-system-info--status-apis)
2. [TikZ Compilation APIs](#2-tikz-compilation-apis)
3. [User Authentication APIs](#3-user-authentication-apis)
4. [Social Features APIs](#4-social-features-apis)
5. [Comments System APIs](#5-comments-system-apis)
6. [Search & Discovery APIs](#6-search--discovery-apis)
7. [Package Management APIs](#7-package-management-apis)
8. [File Management APIs](#8-file-management-apis)
9. [Notifications APIs](#9-notifications-apis)
10. [Admin APIs](#10-admin-apis)
11. [Rate Limits & Security](#11-rate-limits--security)

---

## 1. System Info & Status APIs

### 1.1 Platform Info
```
GET /api/platform-info
```

**Purpose:** Static platform capabilities and configuration

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "platform": "Enhanced Whitelist + Resource Limits v2.0",
  "backend_version": "2.0",
  "domain": "tikz2svg.com",
  "environment": "production",
  "security_features": [
    "25+ dangerous pattern detection",
    "Resource limits (timeout: 45s, memory: 300MB)",
    "Concurrent compilation limits (5 max)",
    "Security event logging",
    "Enhanced error classification"
  ],
  "whitelist_packages": 34,
  "tikz_libraries": 37,
  "pgfplots_libraries": 9,
  "security_level": "high",
  "features": {
    "timeout_protection": true,
    "memory_monitoring": true,
    "pattern_validation": true,
    "concurrent_limits": true,
    "error_classification": true,
    "security_logging": true
  }
}
```

**Use Cases:**
- Client capability detection
- Version compatibility checks
- Feature availability verification
- Integration testing

---

### 1.2 System Status
```
GET /api/system-status
```

**Purpose:** Real-time system performance metrics

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1699264832.123,
  "compilation": {
    "active_count": 2,
    "max_concurrent": 5,
    "available_slots": 3,
    "queue_status": "available"
  },
  "security": {
    "patterns_active": 25,
    "logging_enabled": true,
    "validation_enabled": true
  },
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "disk_percent": 78.3,
    "load_level": "medium"
  },
  "limits": {
    "timeout_seconds": 45,
    "max_memory_mb": 300,
    "max_concurrent": 5
  }
}
```

**Status Values:**
- `healthy` - System operating normally (CPU < 70%, Memory < 70%)
- `degraded` - System under stress (CPU 70-90%, Memory 70-90%)
- `critical` - System overloaded (CPU > 90%, Memory > 90%)

**Use Cases:**
- Load balancer health checks
- Monitoring dashboards
- Auto-scaling decisions
- Capacity planning

---

### 1.3 Health Check
```
GET /health
```

**Purpose:** Simple health check for load balancers

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1699264832.123,
  "version": "2.0.0",
  "platform": "Enhanced Whitelist + Resource Limits"
}
```

**Use Cases:**
- Load balancer health checks
- Uptime monitoring
- Service discovery

---

### 1.4 Security Events (Recent)
```
GET /api/security-events/recent
```

**Purpose:** Recent security events (last 24 hours)

**Authentication:** ✅ Admin required

**Response:**
```json
{
  "events": [
    {
      "timestamp": "2024-11-06T10:30:00Z",
      "type": "dangerous_pattern_detected",
      "user_id": 123,
      "ip_address": "192.168.1.1",
      "details": "\\write18 command blocked",
      "severity": "high"
    }
  ],
  "total": 5,
  "period": "24h"
}
```

**Event Types:**
- `dangerous_pattern_detected` - Malicious LaTeX pattern blocked
- `timeout_exceeded` - Compilation timeout
- `memory_exceeded` - Memory limit exceeded
- `concurrent_limit_reached` - Too many concurrent compilations

---

### 1.5 Adaptive Limits
```
GET /api/adaptive-limits
```

**Purpose:** Current dynamic resource limits

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "current_limits": {
    "timeout": 45,
    "memory": 300,
    "concurrent": 5
  },
  "system_load": "medium",
  "adjusted": false,
  "next_adjustment": "2024-11-06T11:00:00Z"
}
```

---

### 1.6 Cache Statistics
```
GET /api/cache-stats
```

**Purpose:** Compilation cache performance metrics

**Authentication:** ✅ Admin required

**Response:**
```json
{
  "cache": {
    "total_entries": 1523,
    "hit_rate": 0.87,
    "miss_rate": 0.13,
    "size_mb": 45.2,
    "oldest_entry": "2024-10-15T08:00:00Z"
  },
  "performance": {
    "avg_hit_time_ms": 15,
    "avg_miss_time_ms": 8500,
    "total_hits": 5234,
    "total_misses": 782
  }
}
```

---

### 1.7 Available Packages
```
GET /api/available_packages
```

**Purpose:** List of supported LaTeX packages and libraries

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "packages": [
    "tikz", "pgfplots", "amsmath", "amssymb", "xcolor",
    "graphicx", "geometry", "circuitikz", ...
  ],
  "tikz_libraries": [
    "calc", "positioning", "arrows.meta", "decorations.markings", ...
  ],
  "pgfplots_libraries": [
    "polar", "statistics", "fillbetween", "groupplots", ...
  ]
}
```

---

## 2. TikZ Compilation APIs

### 2.1 Compile TikZ Code
```
POST /compile
```

**Purpose:** Compile TikZ LaTeX code to SVG

**Authentication:** ✅ Login required

**Request Body:**
```json
{
  "code": "\\begin{tikzpicture}\n\\draw (0,0) circle (1cm);\n\\end{tikzpicture}",
  "filename": "optional_custom_name"
}
```

**Response (Success):**
```json
{
  "success": true,
  "svg_url": "/static/images/12345_user123.svg",
  "svg_temp_id": "temp_12345",
  "compilation_time_ms": 3500,
  "cached": false
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "LaTeX compilation error",
  "error_type": "syntax_error",
  "details": "! Undefined control sequence.\nl.5 \\invalidcommand",
  "line_number": 5
}
```

**Error Types:**
- `syntax_error` - LaTeX syntax error
- `timeout` - Compilation exceeded 45s
- `memory_exceeded` - Memory limit exceeded
- `dangerous_pattern` - Security pattern detected
- `package_not_allowed` - Unauthorized package used

**Features:**
- Auto-detection of 34 packages
- Manual package specification: `%!<\usepackage{...}>`
- Timeout protection (45s)
- Memory limit (300MB)
- Concurrent compilation limit (5 max)
- Compilation caching

---

### 2.2 Clear Compilation Cache
```
POST /api/clear_compilation_cache
```

**Purpose:** Clear compilation cache for current user

**Authentication:** ✅ Login required

**Response:**
```json
{
  "success": true,
  "cleared_entries": 23,
  "message": "Cache cleared successfully"
}
```

---

### 2.3 Debug Parse Packages
```
POST /api/debug_parse_packages
```

**Purpose:** Debug package detection without compilation

**Authentication:** ✅ Login required

**Request Body:**
```json
{
  "code": "\\usepackage{circuitikz}\n\\usetikzlibrary{angles}"
}
```

**Response:**
```json
{
  "detected_packages": ["circuitikz"],
  "detected_tikz_libraries": ["angles"],
  "detected_pgfplots_libraries": [],
  "manual_packages": []
}
```

---

## 3. User Authentication APIs

### 3.1 Check Login Status
```
GET /api/check_login_status
```

**Purpose:** Check if user is logged in

**Authentication:** ❌ None required

**Response:**
```json
{
  "logged_in": true,
  "user_id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "avatar": "/static/avatars/123.jpg",
  "verified": true
}
```

---

### 3.2 Send Verification Code
```
POST /api/send-verification-email
```

**Purpose:** Send 6-digit verification code to user email

**Authentication:** ✅ Login required

**Response:**
```json
{
  "success": true,
  "message": "Verification code sent to your email",
  "expires_at": "2024-11-07T10:30:00Z"
}
```

**Rate Limit:** 5 emails per hour

---

### 3.3 Verify Email Code
```
POST /api/verify-email-test
```

**Purpose:** Verify 6-digit code

**Authentication:** ✅ Login required

**Request Body:**
```json
{
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email verified successfully"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid or expired code",
  "attempts_remaining": 3
}
```

**Limits:**
- Max 5 attempts per code
- Code expires after 24 hours

---

## 4. Social Features APIs

### 4.1 Like SVG
```
POST /api/like/<svg_filename>
```

**Purpose:** Like an SVG file

**Authentication:** ✅ Login required

**Response:**
```json
{
  "success": true,
  "liked": true,
  "total_likes": 15
}
```

---

### 4.2 Unlike SVG
```
POST /api/unlike/<svg_filename>
```

**Purpose:** Unlike an SVG file

**Authentication:** ✅ Login required

**Response:**
```json
{
  "success": true,
  "liked": false,
  "total_likes": 14
}
```

---

### 4.3 Get Likes List
```
GET /api/svg/<svg_id>/likes?page=1&per_page=20
```

**Purpose:** Get paginated list of users who liked an SVG

**Authentication:** ❌ None required (Public)

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20, max: 100)

**Response:**
```json
{
  "likes": [
    {
      "user_id": 123,
      "username": "john_doe",
      "avatar": "/static/avatars/123.jpg",
      "liked_at": "2024-11-06T10:30:00Z",
      "verified": true
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "per_page": 20,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### 4.4 Get Likes Preview
```
GET /api/svg/<svg_id>/likes/preview?limit=3
```

**Purpose:** Get preview of first few likes (for UI)

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "preview_users": [
    {"username": "john", "avatar": "..."},
    {"username": "jane", "avatar": "..."}
  ],
  "total_likes": 50,
  "preview_text": "john, jane và 48 người khác"
}
```

---

### 4.5 Get Like Counts (Batch)
```
POST /api/like_counts
```

**Purpose:** Get like counts for multiple SVG files

**Authentication:** ❌ None required (Public)

**Request Body:**
```json
{
  "filenames": ["file1.svg", "file2.svg", "file3.svg"]
}
```

**Response:**
```json
{
  "file1.svg": 15,
  "file2.svg": 23,
  "file3.svg": 8
}
```

---

### 4.6 Follow User
```
POST /api/follow/<user_id>
```

**Purpose:** Follow another user

**Authentication:** ✅ Login + Verified account required

**Response:**
```json
{
  "success": true,
  "following": true,
  "follower_count": 123
}
```

---

### 4.7 Unfollow User
```
POST /api/unfollow/<user_id>
```

**Purpose:** Unfollow a user

**Authentication:** ✅ Login + Verified account required

**Response:**
```json
{
  "success": true,
  "following": false,
  "follower_count": 122
}
```

---

### 4.8 Check Follow Status
```
GET /api/follow_status/<user_id>
```

**Purpose:** Check if current user follows target user

**Authentication:** ✅ Login required

**Response:**
```json
{
  "following": true,
  "follower_count": 123
}
```

---

### 4.9 Get Follower Count
```
GET /api/follower_count/<user_id>
```

**Purpose:** Get follower count for a user

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "user_id": 123,
  "follower_count": 456,
  "following_count": 234
}
```

---

### 4.10 Get Followed Posts
```
GET /api/followed_posts?page=1&per_page=20
```

**Purpose:** Get SVG files from followed users

**Authentication:** ✅ Login + Verified account required

**Response:**
```json
{
  "files": [
    {
      "filename": "example.svg",
      "user_id": 123,
      "username": "john",
      "avatar": "...",
      "created_at": "2024-11-06T10:30:00Z",
      "likes": 15,
      "views": 234
    }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

---

## 5. Comments System APIs

### 5.1 Get Comments
```
GET /api/comments/<svg_filename>?page=1&per_page=20
```

**Purpose:** Get comments for an SVG file

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "comments": [
    {
      "id": 123,
      "user_id": 456,
      "username": "john_doe",
      "avatar": "/static/avatars/456.jpg",
      "verified": true,
      "content": "Great diagram! Here's the math: $E=mc^2$",
      "rendered_content": "Great diagram! Here's the math: <math>...</math>",
      "likes": 5,
      "created_at": "2024-11-06T10:30:00Z",
      "edited": false,
      "replies": [
        {
          "id": 124,
          "user_id": 789,
          "username": "jane_doe",
          "content": "Thanks!",
          "created_at": "2024-11-06T11:00:00Z"
        }
      ]
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "per_page": 20
  }
}
```

**Features:**
- LaTeX math rendering: `$...$` and `$$...$$`
- TikZ code blocks: `\code{...}`
- Nested replies support
- HTML escaping for security

---

### 5.2 Create Comment
```
POST /api/comments/
```

**Purpose:** Create new comment

**Authentication:** ✅ Login required

**Request Body:**
```json
{
  "svg_filename": "example.svg",
  "comment_text": "Great work! $E=mc^2$",
  "parent_id": null
}
```

**Response:**
```json
{
  "success": true,
  "comment_id": 123,
  "message": "Comment posted successfully"
}
```

**Limits:**
- Max 5000 characters
- Rate limit: 20 comments per hour

---

### 5.3 Edit Comment
```
PUT /api/comments/<comment_id>
```

**Purpose:** Edit own comment

**Authentication:** ✅ Login required (must be comment owner)

**Request Body:**
```json
{
  "comment_text": "Updated text with $x^2$"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Comment updated successfully"
}
```

---

### 5.4 Delete Comment
```
DELETE /api/comments/<comment_id>
```

**Purpose:** Delete own comment (cascade deletes replies)

**Authentication:** ✅ Login required (must be comment owner)

**Response:**
```json
{
  "success": true,
  "message": "Comment deleted successfully",
  "deleted_replies": 3
}
```

---

### 5.5 Like Comment
```
POST /api/comments/<comment_id>/like
```

**Purpose:** Toggle like/unlike on comment

**Authentication:** ✅ Login required

**Response:**
```json
{
  "success": true,
  "liked": true,
  "total_likes": 10
}
```

---

### 5.6 Reply to Comment
```
POST /api/comments/<comment_id>/reply
```

**Purpose:** Reply to a comment

**Authentication:** ✅ Login required

**Request Body:**
```json
{
  "comment_text": "Great point!"
}
```

**Response:**
```json
{
  "success": true,
  "reply_id": 125,
  "parent_id": 123
}
```

---

## 6. Search & Discovery APIs

### 6.1 Search SVG Files
```
GET /search?q={query}&type=keywords&page=1&per_page=20
GET /search?q={query}&type=username&page=1&per_page=20
```

**Purpose:** Search SVG files by keywords or username

**Authentication:** ❌ None required (Public)

**Query Parameters:**
- `q` - Search query (required)
- `type` - Search type: `keywords` or `username` (default: `keywords`)
- `page` - Page number (default: 1)
- `per_page` - Results per page (default: 20)

**Response:**
```json
{
  "results": [
    {
      "filename": "example.svg",
      "user_id": 123,
      "username": "john",
      "created_at": "2024-11-06T10:30:00Z",
      "likes": 15,
      "keywords": ["circle", "diagram"]
    }
  ],
  "search_type": "keywords",
  "query": "circle",
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 6.2 Keyword Suggestions
```
GET /api/keywords/search?q={query}
```

**Purpose:** Auto-suggestions for search keywords

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "suggestions": [
    "circle",
    "circular diagram",
    "circuit",
    "circuitikz"
  ],
  "query": "circ"
}
```

---

### 6.3 Get Files List
```
GET /api/files?page=1&per_page=20
GET /api/public/files?page=1&per_page=20
```

**Purpose:** Get paginated list of SVG files

**Authentication:** 
- `/api/files` - ✅ Login required (user's files)
- `/api/public/files` - ❌ None required (all public files)

**Response:**
```json
{
  "files": [
    {
      "filename": "example.svg",
      "created_at": "2024-11-06T10:30:00Z",
      "likes": 15,
      "views": 234,
      "keywords": ["circle", "diagram"]
    }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

---

## 7. Package Management APIs

### 7.1 Get Packages List
```
GET /packages
```

**Purpose:** View all supported packages (HTML page)

**Authentication:** ❌ None required (Public)

---

### 7.2 Search Packages
```
GET /api/packages/search?q={query}&type=all
```

**Purpose:** Search packages by name or type

**Authentication:** ❌ None required (Public)

**Query Parameters:**
- `q` - Search query
- `type` - Package type: `latex`, `tikz`, `pgfplots`, or `all`

**Response:**
```json
{
  "results": [
    {
      "name": "circuitikz",
      "type": "latex_package",
      "is_active": true,
      "requires_manual": true,
      "description": "Circuit diagrams"
    }
  ],
  "total": 5
}
```

---

### 7.3 Get Package Stats
```
GET /api/packages/stats
```

**Purpose:** Package system statistics

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "packages": {
    "total": 34,
    "active": 30,
    "manual": 4
  },
  "libraries": {
    "tikz": 37,
    "pgfplots": 9
  },
  "requests": {
    "pending": 5,
    "under_review": 3,
    "approved": 120,
    "rejected": 15
  }
}
```

---

### 7.4 Request New Package
```
POST /api/package_request
```

**Purpose:** Request addition of new package

**Authentication:** ✅ Login required

**Request Body:**
```json
{
  "package_name": "tikz-3dplot",
  "justification": "Needed for 3D diagrams",
  "use_case": "Creating 3D coordinate systems",
  "priority": "medium",
  "contact_name": "John Doe",
  "contact_email": "john@example.com"
}
```

**Priority Levels:**
- `low` - Can wait (2-4 weeks)
- `medium` - Needed soon (1-2 weeks)
- `high` - Important (3-5 days)
- `emergency` - Urgent (1-2 days)

**Response:**
```json
{
  "success": true,
  "request_id": 123,
  "message": "Package request submitted successfully",
  "status": "pending"
}
```

**Rate Limit:** 3 requests per hour

---

### 7.5 Get Popular Packages
```
GET /api/packages/popular?limit=10
```

**Purpose:** Get most requested/used packages

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "popular": [
    {
      "name": "circuitikz",
      "request_count": 45,
      "usage_count": 1234
    }
  ]
}
```

---

### 7.6 Get Package Recommendations
```
GET /api/packages/recommendations/<package_name>
```

**Purpose:** Get related package recommendations

**Authentication:** ❌ None required (Public)

**Response:**
```json
{
  "package": "tikz",
  "recommendations": [
    {
      "name": "pgfplots",
      "reason": "Often used together",
      "similarity": 0.85
    }
  ]
}
```

---

### 7.7 Get Package Analytics
```
GET /api/packages/analytics
```

**Purpose:** Package usage analytics

**Authentication:** ✅ Admin required

**Response:**
```json
{
  "most_used": [
    {"name": "tikz", "count": 5234},
    {"name": "pgfplots", "count": 3456}
  ],
  "trending": [
    {"name": "circuitikz", "growth": 0.45}
  ],
  "request_trends": {
    "last_7_days": 23,
    "last_30_days": 87
  }
}
```

---

## 8. File Management APIs

### 8.1 Save SVG
```
POST /save_svg
```

**Purpose:** Save compiled SVG to user account

**Authentication:** ✅ Login required

**Request Body:**
```json
{
  "svg_temp_id": "temp_12345",
  "filename": "my_diagram.svg",
  "keywords": "circle,diagram,math",
  "tikz_code": "\\begin{tikzpicture}...",
  "caption": "My circle diagram"
}
```

**Response:**
```json
{
  "success": true,
  "filename": "12345_user123_my_diagram.svg",
  "url": "/static/images/12345_user123_my_diagram.svg"
}
```

**Limits:**
- Max 10MB per file
- Max 10 files per day per user

---

### 8.2 Convert Format
```
POST /convert
```

**Purpose:** Convert SVG to PNG or JPEG

**Authentication:** ✅ Login required

**Request Body:**
```json
{
  "svg_filename": "example.svg",
  "format": "png",
  "width": 1920,
  "height": 1080,
  "dpi": 300
}
```

**Response:**
```json
{
  "success": true,
  "output_file": "example.png",
  "url": "/static/converted/example.png",
  "size_bytes": 234567,
  "dimensions": "1920x1080"
}
```

**Limits:**
- Max 60MP (60,000,000 pixels)
- Max DPI: 2000

---

### 8.3 Update Caption
```
POST /api/update_caption/<filename>
```

**Purpose:** Update SVG file caption

**Authentication:** ✅ Login required (must be file owner)

**Request Body:**
```json
{
  "caption": "Updated caption text"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Caption updated successfully"
}
```

---

### 8.4 Delete File
```
POST /delete/<filename>
```

**Purpose:** Delete SVG file

**Authentication:** ✅ Login required (must be file owner)

**Response:**
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

---

## 9. Notifications APIs

### 9.1 Get Unread Count
```
GET /api/notifications/unread-count
```

**Purpose:** Get unread notification count

**Authentication:** ✅ Login required

**Response:**
```json
{
  "count": 5,
  "has_unread": true
}
```

---

### 9.2 Get Notifications
```
GET /api/notifications?page=1&per_page=20&filter=all
```

**Purpose:** Get user notifications

**Authentication:** ✅ Login required

**Query Parameters:**
- `page` - Page number
- `per_page` - Items per page
- `filter` - Filter type: `all`, `unread`, `likes`, `follows`, `comments`

**Response:**
```json
{
  "notifications": [
    {
      "id": 123,
      "type": "like",
      "user_id": 456,
      "username": "john",
      "avatar": "...",
      "svg_filename": "example.svg",
      "message": "john liked your SVG",
      "created_at": "2024-11-06T10:30:00Z",
      "is_read": false
    }
  ],
  "pagination": {
    "total": 50,
    "unread": 5
  }
}
```

**Notification Types:**
- `like` - Someone liked your SVG
- `follow` - Someone followed you
- `comment` - Someone commented on your SVG
- `reply` - Someone replied to your comment
- `mention` - Someone mentioned you

---

### 9.3 Mark Notification as Read
```
POST /api/notifications/<notification_id>/read
```

**Purpose:** Mark single notification as read

**Authentication:** ✅ Login required

**Response:**
```json
{
  "success": true,
  "notification_id": 123
}
```

---

### 9.4 Mark All as Read
```
POST /api/notifications/mark-all-read
```

**Purpose:** Mark all notifications as read

**Authentication:** ✅ Login required

**Response:**
```json
{
  "success": true,
  "marked_count": 15
}
```

---

## 10. Admin APIs

### 10.1 Dashboard Metrics
```
GET /api/admin/dashboard-metrics
```

**Purpose:** Overall platform metrics

**Authentication:** ✅ Admin required

**Response:**
```json
{
  "users": {
    "total": 5432,
    "verified": 4123,
    "active_7d": 1234,
    "active_30d": 3456
  },
  "svg_files": {
    "total": 12345,
    "today": 45,
    "this_week": 234,
    "this_month": 1234
  },
  "compilation": {
    "total": 50000,
    "success_rate": 0.95,
    "avg_time_ms": 5600,
    "cache_hit_rate": 0.87
  },
  "storage": {
    "total_mb": 5678,
    "svg_files_mb": 3456,
    "avatars_mb": 234
  }
}
```

---

### 10.2 Package Requests Count
```
GET /api/admin/requests/count
```

**Purpose:** Count pending package requests

**Authentication:** ✅ Admin required

**Response:**
```json
{
  "pending": 5,
  "under_review": 3,
  "total_unprocessed": 8
}
```

---

### 10.3 Update Request Status
```
POST /api/admin/requests/<request_id>/status
```

**Purpose:** Update package request status

**Authentication:** ✅ Admin required

**Request Body:**
```json
{
  "status": "approved",
  "admin_notes": "Package added to whitelist"
}
```

**Status Values:**
- `pending` - Awaiting review
- `under_review` - Being evaluated
- `approved` - Accepted, will be added
- `rejected` - Declined

**Response:**
```json
{
  "success": true,
  "request_id": 123,
  "new_status": "approved"
}
```

---

### 10.4 Bulk Approve Packages
```
POST /api/admin/packages/bulk-approve
```

**Purpose:** Approve multiple package requests at once

**Authentication:** ✅ Admin required

**Request Body:**
```json
{
  "request_ids": [123, 124, 125],
  "admin_notes": "Batch approved"
}
```

**Response:**
```json
{
  "success": true,
  "approved_count": 3,
  "failed": []
}
```

---

### 10.5 Cache Control
```
POST /api/admin/cache-control
```

**Purpose:** Admin cache management

**Authentication:** ✅ Admin required

**Request Body:**
```json
{
  "action": "clear_all"
}
```

**Actions:**
- `clear_all` - Clear entire cache
- `clear_old` - Clear entries older than 7 days
- `refresh` - Refresh cache statistics

**Response:**
```json
{
  "success": true,
  "action": "clear_all",
  "cleared_entries": 1523
}
```

---

### 10.6 Refresh Cache
```
POST /api/admin/cache/refresh
```

**Purpose:** Refresh package cache

**Authentication:** ✅ Admin required

**Response:**
```json
{
  "success": true,
  "message": "Cache refreshed",
  "packages_loaded": 34
}
```

---

## 11. Rate Limits & Security

### Rate Limiting Rules

| Endpoint Category | Limit | Window | Applies To |
|------------------|-------|--------|------------|
| General API | 1000 requests | 1 minute | All endpoints |
| Package Requests | 3 requests | 1 hour | Per user |
| Email Verification | 5 emails | 1 hour | Per user |
| Comments | 20 comments | 1 hour | Per user |
| Compilation | 5 concurrent | - | Global |
| File Upload | 10 files | 1 day | Per user |

### Security Features

**1. Input Validation:**
- All user input is validated and sanitized
- XSS protection via HTML escaping
- SQL injection prevention via parameterized queries

**2. Authentication:**
- Google OAuth 2.0
- Session management with Flask-Login
- CSRF protection enabled

**3. LaTeX Security:**
- 25+ dangerous pattern detection
- Package whitelist enforcement
- Resource limits (timeout, memory)
- Concurrent compilation limits

**4. Rate Limiting:**
- Redis-based rate limiting
- IP-based tracking with ProxyFix
- Separate limits for different endpoints

**5. Monitoring:**
- Security event logging
- Error classification
- Performance metrics
- System health monitoring

---

## 12. Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": "Additional details if available",
  "timestamp": 1699264832.123
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `COMPILATION_ERROR` | 422 | LaTeX compilation failed |
| `TIMEOUT_ERROR` | 408 | Request timeout |
| `SERVER_ERROR` | 500 | Internal server error |

---

## 13. Webhooks (Future)

**Status:** 🚧 Planned for Q1 2025

Webhook events will include:
- `svg.created` - New SVG file created
- `comment.posted` - New comment on followed user's SVG
- `user.followed` - New follower
- `package.approved` - Package request approved

---

## 📞 API Support

**Documentation:** https://tikz2svg.com/docs  
**API Base URL:** https://tikz2svg.com  
**Support Email:** admin@tikz2svg.com  
**Status Page:** https://tikz2svg.com/api/system-status

---

## 📝 Changelog

### Version 2.0 (November 2024)
- ✨ Added comprehensive system monitoring APIs
- ✨ Enhanced security with 25+ pattern detection
- ✨ Package management system with request workflow
- ✨ Comments system with LaTeX math support
- 🔧 Improved rate limiting with Redis
- 🔧 Enhanced error classification

### Version 1.5 (October 2024)
- ✨ Likes modal with pagination
- ✨ Enhanced search with dual-mode
- 🔧 Timezone fixes for Vietnam

### Version 1.0 (September 2024)
- 🎉 Initial public release
- ✨ TikZ to SVG compilation
- ✨ User authentication with Google OAuth
- ✨ Basic social features (likes, follows)

---

**Last Updated:** November 6, 2024  
**API Version:** 2.0  
**Document Version:** 1.0

