from flask import Flask, request, render_template, url_for, send_file, jsonify, session, redirect, flash, make_response, send_from_directory, render_template_string
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import subprocess
import uuid
from datetime import datetime, timezone, timedelta
import time
import glob
import cairosvg
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Tắt giới hạn decompression bomb
import re
import traceback
import random
import string
import json
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import mysql.connector
import threading
import psutil
from contextlib import contextmanager
from pathlib import Path
import hashlib
import logging
from typing import Iterable
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_service import init_email_service, get_email_service
from comments_helpers import add_security_headers
from comments_routes import comments_bp
from notification_service import init_notification_service, get_notification_service

load_dotenv()


# --- Static storage root (shared across releases) ---
STATIC_ROOT = os.environ.get('TIKZ_SVG_DIR', os.path.join(os.getcwd(), 'static'))
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(os.path.join(STATIC_ROOT, 'avatars'), exist_ok=True)
os.makedirs(os.path.join(STATIC_ROOT, 'images'), exist_ok=True)

app = Flask(__name__, static_folder=STATIC_ROOT)

# =====================================================
# RATE LIMITING CONFIGURATION (PHASE 2)
# =====================================================
# Detect environment: Development has more generous limits
IS_DEVELOPMENT = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('DEBUG') == '1'

# Storage: Use memory for development, Redis for production
# For production with multiple workers, set REDIS_URL in environment
RATE_LIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')

# Custom key function to get real IP from X-Forwarded-For header (behind Nginx proxy)
def get_real_ip():
    """Get real client IP from X-Forwarded-For header or fallback to remote_addr"""
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can be: "client, proxy1, proxy2"
        # We want the first (client) IP
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

# Initialize Flask-Limiter
# In development: disable rate limiting entirely for testing
# In production: use Redis storage with real IP tracking
limiter = Limiter(
    app=app,
    key_func=get_real_ip,  # Use custom function to get real IP
    storage_uri=RATE_LIMIT_STORAGE_URI,
    default_limits=[] if IS_DEVELOPMENT else ["200 per hour"],  # No limits in dev
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
    enabled=not IS_DEVELOPMENT,  # Disable limiter entirely in development
)

# Development: No limits (disabled entirely)
# Production: Balanced limits for real-world usage with lazy loading
RATE_LIMITS = {
    'api_likes_preview': "10000 per minute" if IS_DEVELOPMENT else "500 per minute",  # Higher for lazy loading
    'api_like_counts': "10000 per minute" if IS_DEVELOPMENT else "500 per minute",
    'api_general': "10000 per minute" if IS_DEVELOPMENT else "1000 per minute",
    'api_write': "10000 per minute" if IS_DEVELOPMENT else "50 per minute",
}

print(f"🔧 Rate Limiting: {'DEVELOPMENT' if IS_DEVELOPMENT else 'PRODUCTION'} mode")
print(f"📊 Storage: {RATE_LIMIT_STORAGE_URI}")
print(f"⚡ Limits: {RATE_LIMITS}")

# =====================================================
# RATE LIMITING ERROR HANDLERS
# =====================================================
@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Custom error handler for rate limit exceeded (429)
    Returns proper JSON response instead of HTML error page
    """
    # Check if request is API call (expects JSON)
    if request.path.startswith('/api/'):
        return jsonify({
            "success": False,
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down and try again later.",
            "retry_after": getattr(e, 'retry_after', 60)
        }), 429
    
    # For HTML pages, show user-friendly error
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Too Many Requests</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .error-container {
                    text-align: center;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 3rem;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                }
                h1 { font-size: 4rem; margin: 0; }
                p { font-size: 1.2rem; margin: 1rem 0; }
                .retry-info { font-size: 0.9rem; opacity: 0.8; }
                a {
                    display: inline-block;
                    margin-top: 1.5rem;
                    padding: 0.8rem 2rem;
                    background: white;
                    color: #667eea;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: bold;
                    transition: transform 0.2s;
                }
                a:hover { transform: translateY(-2px); }
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>⏱️ 429</h1>
                <p>Too Many Requests</p>
                <p class="retry-info">You're making requests too quickly. Please wait a moment and try again.</p>
                <a href="/">← Back to Home</a>
            </div>
        </body>
        </html>
    '''), 429

# =====================================================
# PAGINATION CONFIGURATION
# =====================================================
ITEMS_PER_PAGE = 50  # Number of items per page (configurable: 20, 50, 100)
MAX_PAGES_DISPLAY = 10  # Maximum page numbers to show in pagination UI

def get_pagination_params(request):
    """
    Extract and validate pagination parameters from request
    
    Args:
        request: Flask request object
        
    Returns:
        tuple: (page, per_page) - validated integers
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', ITEMS_PER_PAGE))
        
        # Validation: ensure reasonable bounds
        page = max(1, min(page, 10000))  # Between 1-10000
        per_page = max(10, min(per_page, 100))  # Between 10-100
        
        return page, per_page
    except (ValueError, TypeError):
        # If invalid parameters, return defaults
        return 1, ITEMS_PER_PAGE

def generate_page_numbers(current_page, total_pages, max_display=10):
    """
    Generate smart page numbers for pagination UI
    
    Example: Current=50, Total=200, Max=10
    Result: [1, '...', 46, 47, 48, 49, 50, 51, 52, 53, 54, '...', 200]
    
    Args:
        current_page: Current page number
        total_pages: Total number of pages
        max_display: Maximum page numbers to display
        
    Returns:
        list: Page numbers with ellipsis for gaps
    """
    if total_pages <= max_display:
        # If total pages fit in max_display, show all
        return list(range(1, total_pages + 1))
    
    half_display = max_display // 2
    pages = set()
    
    # Always include first and last page
    pages.add(1)
    pages.add(total_pages)
    
    # Add pages around current page
    for i in range(max(1, current_page - half_display), 
                   min(total_pages + 1, current_page + half_display + 1)):
        pages.add(i)
    
    # Convert to sorted list with ellipsis
    pages_list = sorted(pages)
    result = []
    prev = 0
    
    for page in pages_list:
        if page > prev + 1:
            result.append('...')
        result.append(page)
        prev = page
    
    return result

print(f"✅ Pagination configured: {ITEMS_PER_PAGE} items per page")

# Health check route
@app.route("/health")
def health():
    """Enhanced health check for Phase 3 production"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0",
        "platform": "Enhanced Whitelist + Resource Limits v2.0",
        "domain": "tikz2svg.com",
        "environment": "production",
        "features": {
            "security_patterns": 26,
            "cache_enabled": True,
            "monitoring": True,
            "backup_system": True
        }
    }, 200

app.config['UPLOAD_FOLDER'] = STATIC_ROOT
app.config['DEBUG'] = False # Tắt debug mode cho production

# ✅ FLASK-LOGIN SETUP
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'google.login'
login_manager.login_message = "Bạn cần đăng nhập để truy cập trang này."

# ✅ ENHANCED WHITELIST + RESOURCE LIMITS IMPLEMENTATION
# =================================================================

class CompilationLimits:
    """Resource limits for LaTeX compilation"""
    
    TIMEOUT_SECONDS = 45           # Max compilation time
    MAX_MEMORY_MB = 300           # Max memory per compilation
    MAX_CPU_PERCENT = 80          # Max CPU usage
    MAX_CONCURRENT = 5            # Max concurrent compilations
    
    _active_compilations = 0
    _compilation_lock = threading.Lock()

class LaTeXSecurityValidator:
    """Validate LaTeX code for security threats"""
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = {
        # Shell execution attempts
        r'\\write18': "Shell execution command detected",
        r'\\immediate\\write18': "Immediate shell execution detected", 
        r'\\special': "Special command detected",
        
        # File system access attempts  
        r'\\input\{[^}]*\.\./': "Directory traversal attempt",
        r'\\input\{/(?:etc|root|home)/': "System file access attempt",
        r'\\openin': "File input stream detected",
        r'\\openout': "File output stream detected",
        
        # Suspicious file operations
        r'\\verbatiminput\{[^}]*(?:/etc/|/root/|/home/)': "System file read attempt",
        r'\\lstinputlisting\{[^}]*(?:/etc/|/root/|/home/)': "System file listing attempt",
        
        # Network/URL attempts
        r'\\url\{(?:file://|ftp://)[^}]*\}': "Local/FTP URL detected",
        
        # Code injection attempts
        r'\\catcode.*=.*13': "Catcode manipulation detected",
        r'\\lowercase\{.*\\def': "Lowercase definition trick detected",
        r'\\csname.*\\endcsname': "Control sequence name manipulation",
        
        # Resource exhaustion patterns
        r'\\loop.*\\repeat': "Potentially infinite loop detected",
        r'\\foreach.*\\foreach.*\\foreach': "Nested loop with potential DoS",
        
        # Lua execution (for lualatex)
        r'\\directlua\{': "Direct Lua execution detected",
        r'\\luaexec\{': "Lua execution detected",
        
        # Advanced patterns (LaTeX3 and modern packages)
        r'\\__[\w_]+:': "LaTeX3 internal command access detected",
        r'\\exp_last_unbraced:': "Advanced expansion manipulation detected",
        
        # TikZ-specific abuses
        r'\\tikzset{.*execute\s*=.*begin': "TikZ code execution attempt",
        r'pgfinvokebeamer': "Beamer-specific command injection",
        
        # Memory-based attacks
        r'\\pgfmathdeclfunction.*\{.*\{.*\{.*': "Recursive function definition detected",
        r'\\def\\recursive.*\\recursive': "Recursive macro definition detected",
        
        # Advanced file operations
        r'\\pdffiledump': "PDF file dump attempt",
        r'\\pdfmdfivesum': "PDF checksum access attempt",
        r'\\pdfcreationdate': "PDF metadata access attempt",
    }
    
    @staticmethod
    def validate_tikz_security(tikz_code: str) -> dict:
        """
        Validate TikZ code for security threats
        Returns: {'safe': bool, 'reason': str, 'warnings': list}
        """
        
        warnings = []
        
        # Check dangerous patterns
        for pattern, description in LaTeXSecurityValidator.DANGEROUS_PATTERNS.items():
            if re.search(pattern, tikz_code, re.IGNORECASE | re.MULTILINE):
                return {
                    'safe': False,
                    'reason': description,
                    'warnings': warnings,
                    'pattern': pattern,
                    'severity': 'high'
                }
        
        # Check code size (basic DoS prevention)
        if len(tikz_code) > 50000:  # 50KB limit
            return {
                'safe': False,
                'reason': "Code too large (>50KB)",
                'warnings': warnings,
                'severity': 'medium'
            }
        
        # Check excessive nesting
        brace_count = tikz_code.count('{') - tikz_code.count('}')
        if abs(brace_count) > 5:  # Unbalanced braces
            warnings.append("Unbalanced braces detected")
        
        max_nesting = 0
        current_nesting = 0
        for char in tikz_code:
            if char == '{':
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif char == '}':
                current_nesting -= 1
        
        if max_nesting > 20:  # Deep nesting limit
            warnings.append("Deep nesting detected (potential DoS)")
        
        # Check for excessive repetition
        foreach_count = len(re.findall(r'\\foreach', tikz_code, re.IGNORECASE))
        if foreach_count > 5:
            warnings.append(f"Many foreach loops detected ({foreach_count})")
        
        return {
            'safe': True,
            'reason': "",
            'warnings': warnings,
            'severity': 'none'
        }

class ConcurrentCompilationManager:
    """Manage concurrent compilation limits"""
    
    def __init__(self, max_concurrent=5):
        self.max_concurrent = max_concurrent
        self.active_count = 0
        self.lock = threading.Lock()
        self.compilation_queue = []
    
    def can_start_compilation(self, user_id: str) -> bool:
        """Check if user can start new compilation"""
        with self.lock:
            # Check global limit
            if self.active_count >= self.max_concurrent:
                return False
            
            # Check per-user limit (max 2 concurrent per user)
            user_compilations = sum(1 for item in self.compilation_queue if item['user_id'] == user_id)
            if user_compilations >= 2:
                return False
                
            return True
    
    def start_compilation(self, user_id: str, compilation_id: str):
        """Register new compilation"""
        with self.lock:
            self.active_count += 1
            self.compilation_queue.append({
                'user_id': user_id,
                'compilation_id': compilation_id,
                'start_time': time.time()
            })
    
    def end_compilation(self, compilation_id: str):
        """Unregister completed compilation"""
        with self.lock:
            self.active_count = max(0, self.active_count - 1)
            self.compilation_queue = [
                item for item in self.compilation_queue 
                if item['compilation_id'] != compilation_id
            ]

class CompilationErrorClassifier:
    """Intelligent error classification for better UX"""
    
    ERROR_CATEGORIES = {
        'syntax': {
            'patterns': [r'Undefined control sequence', r'Missing \\begin', r'Extra \\end'],
            'user_message': "Lỗi cú pháp LaTeX: Kiểm tra lại cú pháp TikZ của bạn",
            'suggestions': ["Kiểm tra dấu ngoặc nhọn {}", "Xem lại \\begin và \\end", "Kiểm tra tên lệnh"]
        },
        'package': {
            'patterns': [r'Undefined.*package', r'Package.*not found', r'not in whitelist'],
            'user_message': "Package không được hỗ trợ: Sử dụng package từ danh sách cho phép",
            'suggestions': ["Xem danh sách 34 packages được hỗ trợ", "Thử package thay thế", "Liên hệ admin để thêm package"]
        },
        'memory': {
            'patterns': [r'TeX capacity exceeded', r'Memory', r'too large'],
            'user_message': "Biểu đồ quá phức tạp: Đơn giản hóa TikZ code",
            'suggestions': ["Giảm số điểm vẽ", "Chia thành nhiều hình nhỏ", "Sử dụng ít \\foreach"]
        },
        'timeout': {
            'patterns': [r'timeout', r'time limit', r'too long'],
            'user_message': "Thời gian xử lý quá lâu: Giảm độ phức tạp của TikZ",
            'suggestions': ["Tránh vòng lặp vô hạn", "Giảm số lần lặp", "Đơn giản hóa phép tính"]
        },
        'security': {
            'patterns': [r'Security', r'dangerous', r'blocked', r'not allowed'],
            'user_message': "Lệnh không được phép: Sử dụng các lệnh TikZ an toàn",
            'suggestions': ["Tránh lệnh file system", "Không dùng shell commands", "Chỉ dùng TikZ drawing commands"]
        }
    }
    
    @classmethod
    def classify_error(cls, error_message: str, tikz_code: str = "") -> dict:
        """Enhanced error classification with suggestions"""
        for category, config in cls.ERROR_CATEGORIES.items():
            for pattern in config['patterns']:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return {
                        'category': category,
                        'user_message': config['user_message'],
                        'suggestions': config['suggestions'],
                        'technical_details': error_message[:500],
                        'severity': cls._get_severity(category)
                    }
        
        return {
            'category': 'unknown',
            'user_message': f"Lỗi không xác định: {error_message[:200]}",
            'suggestions': ["Kiểm tra cú pháp TikZ", "Thử code đơn giản hơn", "Liên hệ hỗ trợ"],
            'technical_details': error_message,
            'severity': 'medium'
        }
    
    @staticmethod
    def _get_severity(category: str) -> str:
        """Get severity level for error category"""
        severity_map = {
            'security': 'high',
            'timeout': 'high', 
            'memory': 'high',
            'syntax': 'low',
            'package': 'medium'
        }
        return severity_map.get(category, 'medium')

class AdaptiveCompilationLimits:
    """Dynamic resource limits based on system load and user tier"""
    
    def __init__(self):
        self.base_timeout = 45          # Base timeout seconds
        self.base_memory_mb = 300       # Base memory MB
        self.base_concurrent = 5        # Base concurrent limit
        
        # User tier multipliers
        self.user_tier_multipliers = {
            'free': 1.0,
            'premium': 1.5,
            'enterprise': 2.0
        }
        
        # System load thresholds
        self.load_thresholds = {
            'low': 50,      # CPU < 50%
            'medium': 80,   # CPU < 80% 
            'high': 95      # CPU < 95%
        }
    
    def get_user_tier(self, user_id: str) -> str:
        """Determine user tier (free/premium/enterprise)"""
        # For Phase 2, everyone is 'free' - can be extended later
        return 'free'
    
    def get_system_load_level(self) -> str:
        """Get current system load level"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent < self.load_thresholds['low']:
                return 'low'
            elif cpu_percent < self.load_thresholds['medium']:
                return 'medium'
            else:
                return 'high'
        except:
            return 'medium'  # Default to medium if can't determine
    
    def get_adaptive_limits(self, user_id: str) -> dict:
        """Calculate adaptive limits based on user tier and system load"""
        
        user_tier = self.get_user_tier(user_id)
        system_load = self.get_system_load_level()
        
        # Base multiplier from user tier
        tier_multiplier = self.user_tier_multipliers.get(user_tier, 1.0)
        
        # System load adjustments
        load_adjustments = {
            'low': 1.2,     # 20% more resources when system is idle
            'medium': 1.0,  # Normal resources
            'high': 0.7     # 30% less resources when system is busy
        }
        
        load_multiplier = load_adjustments.get(system_load, 1.0)
        
        # Calculate final limits
        final_multiplier = tier_multiplier * load_multiplier
        
        adaptive_limits = {
            'timeout_seconds': int(self.base_timeout * final_multiplier),
            'max_memory_mb': int(self.base_memory_mb * final_multiplier),
            'max_concurrent': max(1, int(self.base_concurrent * load_multiplier)),
            'user_tier': user_tier,
            'system_load': system_load,
            'multiplier_applied': final_multiplier
        }
        
        # Ensure minimum limits
        adaptive_limits['timeout_seconds'] = max(15, adaptive_limits['timeout_seconds'])
        adaptive_limits['max_memory_mb'] = max(100, adaptive_limits['max_memory_mb'])
        adaptive_limits['max_concurrent'] = max(1, adaptive_limits['max_concurrent'])
        
        # Ensure maximum limits for safety
        adaptive_limits['timeout_seconds'] = min(120, adaptive_limits['timeout_seconds'])
        adaptive_limits['max_memory_mb'] = min(1000, adaptive_limits['max_memory_mb'])
        adaptive_limits['max_concurrent'] = min(10, adaptive_limits['max_concurrent'])
        
        return adaptive_limits

class CompilationCache:
    """Intelligent caching system for compilation results"""
    
    def __init__(self, max_cache_size_mb=50):
        self.cache = {}                    # SHA256 -> cache_entry
        self.max_cache_size_mb = max_cache_size_mb
        self.current_size_bytes = 0
        self.cache_lock = threading.Lock()
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def _calculate_cache_key(self, tikz_code: str, packages: list, tikz_libs: list, pgfplots_libs: list) -> str:
        """Generate SHA256 cache key from compilation parameters"""
        
        # Create consistent string representation
        cache_input = {
            'tikz_code': tikz_code.strip(),
            'packages': sorted(packages) if packages else [],
            'tikz_libs': sorted(tikz_libs) if tikz_libs else [],
            'pgfplots_libs': sorted(pgfplots_libs) if pgfplots_libs else []
        }
        
        # Convert to JSON and generate SHA256
        cache_string = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_string.encode('utf-8')).hexdigest()
    
    def _estimate_svg_size(self, svg_content: str) -> int:
        """Estimate SVG content size in bytes"""
        return len(svg_content.encode('utf-8'))
    
    def _evict_lru_entries(self, required_space: int):
        """Evict least recently used entries to make space"""
        
        if not self.cache:
            return
        
        # Sort by last_accessed (LRU eviction)
        sorted_entries = sorted(
            self.cache.items(), 
            key=lambda x: x[1]['last_accessed']
        )
        
        freed_space = 0
        evicted_count = 0
        
        for cache_key, entry in sorted_entries:
            entry_size = entry['size_bytes']
            
            del self.cache[cache_key]
            self.current_size_bytes -= entry_size
            freed_space += entry_size
            evicted_count += 1
            
            if freed_space >= required_space:
                break
        
        self.stats['evictions'] += evicted_count
        print(f"Cache: Evicted {evicted_count} entries, freed {freed_space} bytes")
    
    def get(self, tikz_code: str, packages: list = None, tikz_libs: list = None, pgfplots_libs: list = None) -> dict:
        """Get cached compilation result"""
        
        with self.cache_lock:
            self.stats['total_requests'] += 1
            
            cache_key = self._calculate_cache_key(tikz_code, packages or [], tikz_libs or [], pgfplots_libs or [])
            
            if cache_key in self.cache:
                # Cache hit
                self.stats['hits'] += 1
                entry = self.cache[cache_key]
                entry['last_accessed'] = time.time()
                entry['hit_count'] += 1
                
                return {
                    'found': True,
                    'svg_content': entry['svg_content'],
                    'cache_key': cache_key,
                    'cached_at': entry['cached_at'],
                    'hit_count': entry['hit_count']
                }
            else:
                # Cache miss
                self.stats['misses'] += 1
                return {
                    'found': False,
                    'cache_key': cache_key
                }
    
    def set(self, tikz_code: str, svg_content: str, packages: list = None, tikz_libs: list = None, pgfplots_libs: list = None):
        """Cache compilation result"""
        
        with self.cache_lock:
            cache_key = self._calculate_cache_key(tikz_code, packages or [], tikz_libs or [], pgfplots_libs or [])
            entry_size = self._estimate_svg_size(svg_content)
            
            # Check if we need to make space
            max_size_bytes = self.max_cache_size_mb * 1024 * 1024
            if self.current_size_bytes + entry_size > max_size_bytes:
                required_space = (self.current_size_bytes + entry_size) - max_size_bytes + (1024 * 1024)  # Extra 1MB buffer
                self._evict_lru_entries(required_space)
            
            # Add to cache
            self.cache[cache_key] = {
                'svg_content': svg_content,
                'cached_at': time.time(),
                'last_accessed': time.time(),
                'hit_count': 0,
                'size_bytes': entry_size,
                'tikz_code_preview': tikz_code[:100] + '...' if len(tikz_code) > 100 else tikz_code
            }
            
            self.current_size_bytes += entry_size
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self.cache_lock:
            hit_rate = (self.stats['hits'] / max(1, self.stats['total_requests'])) * 100
            
            return {
                'entries_count': len(self.cache),
                'size_mb': round(self.current_size_bytes / (1024 * 1024), 2),
                'max_size_mb': self.max_cache_size_mb,
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': self.stats['total_requests'],
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions']
            }
    
    def clear(self):
        """Clear all cached entries"""
        with self.cache_lock:
            self.cache.clear()
            self.current_size_bytes = 0
            print("Cache: All entries cleared")

# Global instances
compilation_manager = ConcurrentCompilationManager()
adaptive_limits = AdaptiveCompilationLimits()
compilation_cache = CompilationCache(max_cache_size_mb=50)  # 50MB cache

# Setup security logger
security_logger = logging.getLogger('tikz_security')
security_handler = logging.FileHandler('tikz_security.log')
security_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - User:%(user_id)s - IP:%(ip)s - %(message)s'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)

def log_security_event(event_type: str, user_id: str, ip_address: str, details: str):
    """Log security events"""
    security_logger.warning(
        f"{event_type}: {details}",
        extra={'user_id': user_id, 'ip': ip_address}
    )

def log_compilation_metrics(user_id: str, compilation_time: float, memory_used: float, success: bool):
    """Log compilation performance metrics"""
    metrics_logger = logging.getLogger('tikz_metrics')
    metrics_logger.info(
        f"Compilation - Time:{compilation_time:.2f}s Memory:{memory_used:.1f}MB Success:{success}",
        extra={'user_id': user_id}
    )

@contextmanager
def compilation_resource_monitor():
    """Context manager to monitor and limit compilation resources"""
    
    # Check concurrent limit
    with CompilationLimits._compilation_lock:
        if CompilationLimits._active_compilations >= CompilationLimits.MAX_CONCURRENT:
            raise Exception(f"Too many concurrent compilations (max: {CompilationLimits.MAX_CONCURRENT})")
        CompilationLimits._active_compilations += 1
    
    try:
        # Monitor process during compilation
        start_time = time.time()
        initial_memory = psutil.virtual_memory().used / (1024**2)  # MB
        
        yield {
            'start_time': start_time,
            'initial_memory': initial_memory
        }
        
    finally:
        # Always decrement counter
        with CompilationLimits._compilation_lock:
            CompilationLimits._active_compilations -= 1

def compile_tikz_enhanced_whitelist(tikz_code: str, work_dir: str, user_id: str = "anonymous") -> tuple[bool, str, str]:
    """
    Enhanced TikZ compilation with caching, adaptive limits, and security
    Returns: (success, svg_content, error_message)
    """
    
    try:
        with compilation_resource_monitor() as monitor:
            
            # 1. Pattern Security Check
            security_check_result = LaTeXSecurityValidator.validate_tikz_security(tikz_code)
            if not security_check_result['safe']:
                return False, "", f"Security validation failed: {security_check_result['reason']}"
            
            # 2. Generate LaTeX (existing whitelist logic)
            extra_packages, extra_tikz_libs, extra_pgfplots_libs = detect_required_packages(tikz_code)
            
            try:
                latex_source = generate_latex_source(
                    tikz_code=tikz_code,
                    extra_packages=extra_packages,
                    extra_tikz_libs=extra_tikz_libs,
                    extra_pgfplots_libs=extra_pgfplots_libs
                )
            except ValueError as e:
                # Package not in whitelist - use basic template
                print(f"[WARN] Package not allowed: {e}")
                latex_source = TEX_TEMPLATE.replace("{tikz_code}", tikz_code)
                extra_packages, extra_tikz_libs, extra_pgfplots_libs = [], [], []
            
            # 3. Check cache for existing compilation
            cache_result = compilation_cache.get(
                tikz_code=tikz_code,
                packages=extra_packages,
                tikz_libs=extra_tikz_libs,
                pgfplots_libs=extra_pgfplots_libs
            )
            
            if cache_result['found']:
                print(f"✅ Cache HIT! Returning cached result (hit #{cache_result['hit_count']})")
                return True, cache_result['svg_content'], ""
            
            print(f"⚪ Cache MISS. Proceeding with compilation...")
            
            # 4. Get adaptive resource limits
            limits = adaptive_limits.get_adaptive_limits(user_id)
            timeout_seconds = limits['timeout_seconds']
            
            print(f"🚀 Starting enhanced compilation with adaptive limits:")
            print(f"   User: {user_id} (tier: {limits['user_tier']})")
            print(f"   System load: {limits['system_load']}")
            print(f"   Timeout: {timeout_seconds}s (multiplier: {limits['multiplier_applied']:.2f})")
            
            # 5. Write TEX file
            tex_path = os.path.join(work_dir, "tikz.tex")
            pdf_path = os.path.join(work_dir, "tikz.pdf")
            svg_path = os.path.join(work_dir, "tikz.svg")
            
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_source)
            
            # 6. Enhanced compilation with adaptive limits
            try:
                # Run with adaptive timeout and resource monitoring
                lualatex_process = subprocess.run([
                    "lualatex", 
                    "-interaction=nonstopmode", 
                    "-halt-on-error",
                    "--output-directory=.", 
                    "tikz.tex"
                ],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds  # ADAPTIVE TIMEOUT
                )
                
                # Check if process succeeded
                if lualatex_process.returncode != 0:
                    error_output = lualatex_process.stderr or lualatex_process.stdout
                    return False, "", f"LaTeX compilation failed: {error_output}"
                
                # 7. Convert to SVG with timeout
                subprocess.run([
                    "pdf2svg", pdf_path, svg_path
                ], 
                cwd=work_dir, 
                check=True, 
                timeout=15,  # PDF2SVG timeout
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
                )
                
                # 8. Read SVG result
                if os.path.exists(svg_path):
                    with open(svg_path, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                    
                    # Check SVG size limit
                    if len(svg_content) > 5 * 1024 * 1024:  # 5MB limit
                        return False, "", "Generated SVG too large (>5MB)"
                    
                    # 9. Cache successful compilation
                    compilation_cache.set(
                        tikz_code=tikz_code,
                        svg_content=svg_content,
                        packages=extra_packages,
                        tikz_libs=extra_tikz_libs,
                        pgfplots_libs=extra_pgfplots_libs
                    )
                    
                    compilation_time = time.time() - monitor['start_time']
                    print(f"✅ Enhanced compilation successful in {compilation_time:.2f}s (cached for future)")
                    
                    return True, svg_content, ""
                else:
                    return False, "", "SVG file not generated"
                    
            except subprocess.TimeoutExpired:
                return False, "", f"Compilation timeout ({timeout_seconds}s adaptive limit)"
                
            except Exception as e:
                return False, "", f"Compilation error: {str(e)}"
    
    except Exception as e:
        return False, "", f"Resource limit error: {str(e)}"

# =================================================================
# ✅ USER CLASS
class User(UserMixin):
    def __init__(self, id, email, username=None, avatar=None, bio=None, identity_verified=False):
        self.id = id
        self.email = email
        self.username = username
        self.avatar = avatar
        self.bio = bio
        self.identity_verified = identity_verified
    
    def get_id(self):
        return str(self.id)

# ✅ USER LOADER
@login_manager.user_loader
def load_user(user_id):
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, username, avatar, bio, identity_verified FROM user WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                avatar=user_data['avatar'],
                bio=user_data['bio'],
                identity_verified=bool(user_data.get('identity_verified', 0))
            )
        return None
    except Exception as e:
        print(f"Error loading user: {e}", flush=True)
        return None

# Cleanup thread
import threading
import time

def cleanup_tmp_folder():
    while True:
        try:
            now = time.time()
            tmp_root = '/tmp'
            for folder in os.listdir(tmp_root):
                folder_path = os.path.join(tmp_root, folder)
                if os.path.isdir(folder_path):
                    if len(folder) >= 30 and '-' in folder:
                        mtime = os.path.getmtime(folder_path)
                        if now - mtime > 600:  # hơn 10 phút
                            print(f"[CLEANUP] Removing old tmp folder: {folder_path}", flush=True)
                            try:
                                import shutil
                                shutil.rmtree(folder_path)
                            except Exception as e:
                                print(f"[CLEANUP] Error removing {folder_path}: {e}", flush=True)
        except Exception as e:
            print(f"[CLEANUP] Error in cleanup: {e}", flush=True)
        time.sleep(300)  # Chạy mỗi 5 phút

cleanup_thread = threading.Thread(target=cleanup_tmp_folder, daemon=True)
cleanup_thread.start()

# Session config
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

print("DEBUG: Google OAuth blueprint being created...")

# 1) Khai báo allowlist (có thể mở rộng dần)
SAFE_PACKAGES = {
    # nền tảng
    "fontspec", "polyglossia", "xcolor", "graphicx", "geometry", "setspace",
    # toán
    "amsmath", "amssymb", "amsfonts", "mathtools", "physics", "siunitx", "cancel", "cases",
          # tikz/pgf
      "tikz", "pgfplots", "tikz-3dplot", "tkz-euclide", "tkz-tab", "pgf", "pgfkeys", "pgfornament",
    # chuyên biệt
    "circuitikz", "tikz-timing", "tikz-cd", "tikz-network", "tikzpeople", "tikzmark",
    # bổ sung
    "array", "booktabs", "multirow", "colortbl", "longtable", "tabularx",
}

# (tuỳ chọn) allowlist cho \usetikzlibrary và \usepgfplotslibrary
SAFE_TIKZ_LIBS = {
    "calc","math","positioning","arrows.meta","intersections","angles","quotes",
    "decorations.markings","decorations.pathreplacing","decorations.text",
    "patterns","patterns.meta","shadings","hobby","spy","backgrounds",
    "shapes.geometric","shapes.symbols","shapes.arrows","shapes.multipart",
    "fit","matrix","chains","automata","petri","mindmap","trees",
    "graphs","graphdrawing","lindenmayersystems","fadings","shadows",
    "external","datavisualization","datavisualization.formats.files",
    "datavisualization.formats.files.csv","datavisualization.formats.files.json"
}
SAFE_PGFPLOTS_LIBS = {
    "polar","statistics","dateplot","fillbetween","colorbrewer",
    "groupplots","ternary","smithchart","units"
}

_pkg_re = re.compile(r"^[A-Za-z0-9\-_.]+$")

def _sanitize_name(name: str, *, kind: str, allowed: set[str]) -> str:
    name = (name or "").strip()
    if not _pkg_re.match(name):
        raise ValueError(f"{kind} không hợp lệ: {name!r}")
    if name not in allowed:
        raise ValueError(f"{kind} '{name}' không trong danh sách cho phép")
    return name

def _lines_for_usepackage(pkgs: Iterable[str]) -> str:
    if not pkgs: return ""
    safe = [_sanitize_name(p, kind="Gói", allowed=SAFE_PACKAGES) for p in pkgs]
    # gom các gói phổ biến theo nhóm để gọn, phần còn lại nạp từng cái
    groups = {"ams": {"amsmath","amssymb","amsfonts"}}
    out = []
    ams_in = [p for p in safe if p in groups["ams"]]
    others = [p for p in safe if p not in groups["ams"]]
    if ams_in:
        out.append(r"\usepackage{amsmath,amssymb,amsfonts}")
    for p in others:
        out.append(fr"\usepackage{{{p}}}")
    return "\n".join(dict.fromkeys(out))  # dedupe, giữ thứ tự

def _lines_for_tikz_libs(libs: Iterable[str]) -> str:
    if not libs: return ""
    safe = [_sanitize_name(l, kind="Thư viện TikZ", allowed=SAFE_TIKZ_LIBS) for l in libs]
    return "\n".join(fr"\usetikzlibrary{{{lib}}}" for lib in dict.fromkeys(safe))

def _lines_for_pgfplots_libs(libs: Iterable[str]) -> str:
    if not libs: return ""
    safe = [_sanitize_name(l, kind="Thư viện pgfplots", allowed=SAFE_PGFPLOTS_LIBS) for l in libs]
    return "\n".join(fr"\usepgfplotslibrary{{{l}}}" for l in dict.fromkeys(safe))

# 2) Template FULL (double braces), giữ nguyên {tikz_code}
TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{standalone}

% Unicode & ngôn ngữ
\usepackage{fontspec}

% Toán & đồ hoạ
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{xcolor}
\usepackage{graphicx}

% Hệ sinh thái TikZ/PGF
\usepackage{tikz}
\usepackage{tikz-3dplot}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
\usepackage{tkz-euclide}
\usepackage{tkz-tab}

% Thư viện TikZ mặc định
\usetikzlibrary{calc}
\usetikzlibrary{math}
\usetikzlibrary{positioning}
\usetikzlibrary{arrows.meta}
\usetikzlibrary{intersections}
\usetikzlibrary{angles}
\usetikzlibrary{quotes}
\usetikzlibrary{decorations.markings}
\usetikzlibrary{decorations.pathreplacing}
\usetikzlibrary{decorations.text}
\usetikzlibrary{patterns}
\usetikzlibrary{patterns.meta}
\usetikzlibrary{shadings}
\usetikzlibrary{hobby}
\usetikzlibrary{spy}
\usetikzlibrary{backgrounds}

% Thư viện pgfplots mặc định
\usepgfplotslibrary{polar}

% ==== EXTRA AUTO-INJECT START ====
% (Sẽ được chèn thêm ở đây)
% ==== EXTRA AUTO-INJECT END ====

\begin{document}
{tikz_code}
\end{document}
"""

# 3) Hàm tạo nguồn LaTeX, chèn động \usepackage / \usetikzlibrary / \usepgfplotslibrary
def generate_latex_source(
    tikz_code: str,
    extra_packages: Iterable[str] = (),
    extra_tikz_libs: Iterable[str] = (),
    extra_pgfplots_libs: Iterable[str] = (),
    base_template: str = TEX_TEMPLATE,
) -> str:
    # Loại bỏ các dòng %!<...> khỏi TikZ code trước khi chèn vào template
    import re
    cleaned_tikz_code = "\n".join([
        line for line in tikz_code.split('\n') 
        if not re.match(r'^%!<.*>$', line.strip())
    ])
    
    pkg_lines   = _lines_for_usepackage(extra_packages)
    tikz_lines  = _lines_for_tikz_libs(extra_tikz_libs)
    pgfl_lines  = _lines_for_pgfplots_libs(extra_pgfplots_libs)

    inject = "\n".join([s for s in (pkg_lines, tikz_lines, pgfl_lines) if s])
    if inject:
        full = base_template.replace(
            "% (Sẽ được chèn thêm ở đây)",
            "% (Sẽ được chèn thêm ở đây)\n" + inject
        )
    else:
        full = base_template
    return full.replace("{tikz_code}", cleaned_tikz_code)

# 4) Hàm helper để tự động phát hiện packages cần thiết từ TikZ code
def detect_required_packages(tikz_code: str) -> tuple[list[str], list[str], list[str]]:
    """
    Tự động phát hiện packages, tikz libraries và pgfplots libraries cần thiết từ code TikZ
    Hỗ trợ cú pháp thủ công: %!<...> để chỉ định packages
    Returns: (packages, tikz_libs, pgfplots_libs)
    """
    code_lower = tikz_code.lower()
    
    # Phát hiện packages từ cú pháp thủ công %!<...>
    manual_packages = []
    manual_tikz_libs = []
    manual_pgfplots_libs = []
    
    # Tìm tất cả các dòng bắt đầu bằng %!<
    import re
    manual_pattern = r'^%!<(.*?)>'
    for line in tikz_code.split('\n'):
        match = re.match(manual_pattern, line.strip())
        if match:
            manual_content = match.group(1)
            # Phân tích nội dung trong %!<...>
            for item in manual_content.split(','):
                item = item.strip()
                if item.startswith('\\usepackage{'):
                    # Trích xuất tên package
                    pkg_match = re.search(r'\\usepackage\{([^}]+)\}', item)
                    if pkg_match:
                        pkg_name = pkg_match.group(1).strip()
                        manual_packages.append(pkg_name)
                elif item.startswith('\\usetikzlibrary{'):
                    # Trích xuất tên tikz library
                    lib_match = re.search(r'\\usetikzlibrary\{([^}]+)\}', item)
                    if lib_match:
                        lib_name = lib_match.group(1).strip()
                        manual_tikz_libs.append(lib_name)
                elif item.startswith('\\usepgfplotslibrary{'):
                    # Trích xuất tên pgfplots library
                    lib_match = re.search(r'\\usepgfplotslibrary\{([^}]+)\}', item)
                    if lib_match:
                        lib_name = lib_match.group(1).strip()
                        manual_pgfplots_libs.append(lib_name)
    
    # Phát hiện packages tự động
    packages = []
    
    # siunitx - cho đơn vị đo lường
    if any(cmd in tikz_code for cmd in ["\\si{", "\\SI{", "\\num{", "\\ang{", "\\unit{"]):
        packages.append("siunitx")
    
    # circuitikz - cho mạch điện
    if any(cmd in tikz_code for cmd in ["\\ohm", "\\volt", "\\ampere", "\\resistor", "\\capacitor", "\\inductor", "\\battery", "\\lamp"]):
        packages.append("circuitikz")
    
    # tikz-timing - cho timing diagrams
    if any(cmd in tikz_code for cmd in ["\\timing", "\\timingD{", "\\timingL{", "\\timingH{", "\\timingX{"]):
        packages.append("tikz-timing")
    
    # physics - cho ký hiệu vật lý
    if any(cmd in tikz_code for cmd in ["\\vec{", "\\abs{", "\\norm{", "\\order{", "\\qty{", "\\mrm{"]):
        packages.append("physics")
    
    # mathtools - cho toán học nâng cao
    if any(cmd in tikz_code for cmd in ["\\DeclarePairedDelimiter", "\\DeclareMathOperator", "\\mathclap", "\\mathllap", "\\mathrlap"]):
        packages.append("mathtools")
    
    # tikz-cd - cho commutative diagrams
    if any(cmd in tikz_code for cmd in ["\\begin{tikzcd}", "\\arrow[", "\\arrow{r}", "\\arrow{d}"]):
        packages.append("tikz-cd")
    
    # tikz-network - cho network diagrams
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[network]", "\\Vertex[", "\\Edge[", "\\tikzstyle{VertexStyle}"]):
        packages.append("tikz-network")
    
    # tikzpeople - cho people diagrams
    if any(cmd in tikz_code for cmd in ["\\person[", "\\tikzstyle{PersonStyle}", "\\begin{tikzpicture}[person"]):
        packages.append("tikzpeople")
    
    # tikzmark - cho annotations
    if any(cmd in tikz_code for cmd in ["\\tikzmark{", "\\tikzmarkin{", "\\tikzmarkend{"]):
        packages.append("tikzmark")
    
    # pgfornament - cho ornaments
    if any(cmd in tikz_code for cmd in ["\\pgfornament{", "\\pgfornament[", "\\pgfornament["]):
        packages.append("pgfornament")
    
    # Phát hiện tikz libraries
    tikz_libs = []
    
    # decorations
    if any(cmd in tikz_code for cmd in ["\\draw[decorate", "\\draw[decoration", "\\decorate", "\\decoration{"]):
        tikz_libs.extend(["decorations.markings", "decorations.pathreplacing"])
    
    # patterns
    if any(cmd in tikz_code for cmd in ["\\draw[pattern", "\\pattern", "\\fill[pattern"]):
        tikz_libs.append("patterns")
    
    # shadings
    if any(cmd in tikz_code for cmd in ["\\draw[shade", "\\shade", "\\shadedraw", "\\shading"]):
        tikz_libs.append("shadings")
    
    # hobby curves
    if any(cmd in tikz_code for cmd in ["\\draw[hobby", "\\hobby", "\\curve{"]):
        tikz_libs.append("hobby")
    
    # spy (magnifying glass)
    if "\\spy" in tikz_code:
        tikz_libs.append("spy")
    
    # backgrounds
    if any(cmd in tikz_code for cmd in ["\\begin{scope}[on background layer]", "\\begin{background}", "\\background"]):
        tikz_libs.append("backgrounds")
    
    # intersections
    if any(cmd in tikz_code for cmd in ["\\path[name intersections", "\\coordinate[name intersections", "\\draw[name intersections"]):
        tikz_libs.append("intersections")
    
    # angles
    if any(cmd in tikz_code for cmd in ["\\pic[angle", "\\angle", "\\draw pic[angle"]):
        tikz_libs.append("angles")
    
    # quotes
    if any(cmd in tikz_code for cmd in ["\\draw[quotes", "\\quotes", "\\draw[quotes="]):
        tikz_libs.append("quotes")
    
    # positioning
    if any(cmd in tikz_code for cmd in ["\\node[above", "\\node[below", "\\node[left", "\\node[right", "\\node[above left", "\\node[above right", "\\node[below left", "\\node[below right"]):
        tikz_libs.append("positioning")
    
    # arrows.meta
    if any(cmd in tikz_code for cmd in ["\\draw[-{", "\\draw[->{", "\\draw[<->{", "\\draw[arrows="]):
        tikz_libs.append("arrows.meta")
    
    # shapes.geometric
    if any(cmd in tikz_code for cmd in ["\\draw[regular polygon", "\\draw[star", "\\draw[diamond", "\\draw[ellipse", "\\draw[circle"]):
        tikz_libs.append("shapes.geometric")
    
    # shapes.symbols
    if any(cmd in tikz_code for cmd in ["\\draw[signal", "\\draw[tape", "\\draw[magnifying glass", "\\draw[cloud"]):
        tikz_libs.append("shapes.symbols")
    
    # shapes.arrows
    if any(cmd in tikz_code for cmd in ["\\draw[arrow box", "\\draw[strike out", "\\draw[rounded rectangle"]):
        tikz_libs.append("shapes.arrows")
    
    # fit
    if any(cmd in tikz_code for cmd in ["\\node[fit=", "\\fit{", "\\draw[fit="]):
        tikz_libs.append("fit")
    
    # matrix
    if any(cmd in tikz_code for cmd in ["\\matrix[", "\\matrix of", "\\matrix (", "\\matrix{"]):
        tikz_libs.append("matrix")
    
    # chains
    if any(cmd in tikz_code for cmd in ["\\begin{scope}[start chain", "\\chainin", "\\chainin (", "\\onchain"]):
        tikz_libs.append("chains")
    
    # automata
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[automaton", "\\node[state", "\\path[->] node[state"]):
        tikz_libs.append("automata")
    
    # petri
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[petri", "\\place[", "\\transition[", "\\arc["]):
        tikz_libs.append("petri")
    
    # mindmap
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[mindmap", "\\concept[", "\\concept color="]):
        tikz_libs.append("mindmap")
    
    # trees
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[tree", "\\node[level", "\\child[", "\\child {"]):
        tikz_libs.append("trees")
    
    # graphs
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[graph", "\\graph[", "\\graph {", "\\graph ("]):
        tikz_libs.append("graphs")
    
    # shadows
    if any(cmd in tikz_code for cmd in ["\\draw[shadow", "\\shadow", "\\shadow{", "\\draw[drop shadow"]):
        tikz_libs.append("shadows")
    
    # fadings
    if any(cmd in tikz_code for cmd in ["\\begin{tikzfadingfrompicture", "\\tikzfading", "\\path[fading="]):
        tikz_libs.append("fadings")
    
    # Phát hiện pgfplots libraries
    pgfplots_libs = []
    
    # fillbetween
    if any(cmd in tikz_code for cmd in ["\\addplot[fill between", "\\addplot[fillbetween", "\\fillbetween"]):
        pgfplots_libs.append("fillbetween")
    
    # statistics
    if any(cmd in tikz_code for cmd in ["\\addplot[statistics", "\\addplot[hist", "\\addplot[boxplot", "\\addplot[error bars"]):
        pgfplots_libs.append("statistics")
    
    # dateplot
    if any(cmd in tikz_code for cmd in ["\\addplot[date coordinates", "\\addplot[dateplot", "\\dateplot"]):
        pgfplots_libs.append("dateplot")
    
    # colorbrewer
    if any(cmd in tikz_code for cmd in ["\\addplot[colorbrewer", "\\colormap[colorbrewer", "\\pgfplotsset{colormap name="]):
        pgfplots_libs.append("colorbrewer")
    
    # groupplots
    if any(cmd in tikz_code for cmd in ["\\begin{groupplot}", "\\nextgroupplot", "\\groupplot[", "\\pgfplotsset{groupplot"]):
        pgfplots_libs.append("groupplots")
    
    # ternary
    if any(cmd in tikz_code for cmd in ["\\begin{ternaryaxis}", "\\ternaryaxis[", "\\addplot3[ternary", "\\ternaryaxis"]):
        pgfplots_libs.append("ternary")
    
    # smithchart
    if any(cmd in tikz_code for cmd in ["\\begin{smithchart}", "\\smithchart[", "\\addplot[smithchart", "\\smithchart"]):
        pgfplots_libs.append("smithchart")
    
    # units
    if any(cmd in tikz_code for cmd in ["\\begin{axis}[x unit=", "\\begin{axis}[y unit=", "\\addplot[unit="]):
        pgfplots_libs.append("units")
    
    # Kết hợp packages tự động và thủ công
    all_packages = list(dict.fromkeys(packages + manual_packages))  # Loại bỏ trùng lặp
    all_tikz_libs = list(dict.fromkeys(tikz_libs + manual_tikz_libs))  # Loại bỏ trùng lặp
    all_pgfplots_libs = list(dict.fromkeys(pgfplots_libs + manual_pgfplots_libs))  # Loại bỏ trùng lặp
    
    return all_packages, all_tikz_libs, all_pgfplots_libs

try:
    from zoneinfo import ZoneInfo
    tz_vn = ZoneInfo("Asia/Ho_Chi_Minh")
except ImportError:
    from pytz import timezone
    tz_vn = timezone('Asia/Ho_Chi_Minh')

ERROR_TIKZ_DIR = 'error_tikz'
if not os.path.exists(ERROR_TIKZ_DIR):
    os.makedirs(ERROR_TIKZ_DIR)

def get_svg_files():
    """Lấy danh sách các SVG đã lưu trong MySQL"""
    svg_files = []
    current_user_id = current_user.id if current_user and current_user.is_authenticated else None
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # ✅ Query đúng với cấu trúc database
        cursor.execute("""
            SELECT 
                s.id, 
                s.filename, 
                s.tikz_code, 
                s.keywords,
                s.caption,
                s.created_at, 
                u.id as owner_id, 
                u.username, 
                u.email as owner_email,
                COUNT(sl.id) as like_count,
                CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
            FROM svg_image s
            LEFT JOIN user u ON s.user_id = u.id
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
            GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.caption, s.created_at, u.id, u.username, u.email, user_like.id
            ORDER BY s.created_at DESC
            LIMIT 100
        """, (current_user_id,))
        
        rows = cursor.fetchall()
        for row in rows:
            try:
                static_dir = app.config['UPLOAD_FOLDER']
                filepath = os.path.join(static_dir, row['filename'])
                if os.path.exists(filepath):
                    file_size_kb = round(os.path.getsize(filepath) / 1024, 2)
                else:
                    file_size_kb = None
            except Exception:
                file_size_kb = None
                
            try:
                url = url_for('static', filename=row['filename'])
            except:
                url = f"/static/{row['filename']}"
                
            svg_files.append({
                'id': row['id'],
                'filename': row['filename'],
                'display_name': f"Người tạo: {row['username']}" if row.get('username') else row['filename'],
                'url': url,
                'size': file_size_kb,
                'created_time': format_time_vn(row['created_at']),
                'file_time': row['created_at'] if row['created_at'] else datetime.now(),
                'tikz_code': row['tikz_code'] or "",
                'caption': row.get('caption', ''),
                'owner_id': row.get('owner_id'),
                'owner_email': row.get('owner_email'),
                'like_count': row['like_count'] or 0,
                'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
            })
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] get_svg_files(): {e}", flush=True)
    return svg_files

def get_svg_files_with_likes(user_id=None):
    """Lấy files với thông tin like cho user đã đăng nhập - Format thống nhất với search_results"""
    svg_files = []
    current_user_id = user_id or (current_user.id if current_user and current_user.is_authenticated else None)
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query tương tự như search_results nhưng cho tất cả files
        # Try with comment_count first, fallback if table doesn't exist
        try:
            cursor.execute("""
                SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                       (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                       (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user,
                       COALESCE((SELECT COUNT(*) FROM svg_comments WHERE svg_filename = s.filename), 0) as comment_count
                FROM svg_image s
                JOIN user u ON s.user_id = u.id
                ORDER BY s.created_at DESC
                LIMIT 100
            """, (current_user_id or 0,))
        except mysql.connector.errors.ProgrammingError as e:
            if 'svg_comments' in str(e) and "doesn't exist" in str(e):
                # Fallback: Query without comment_count if table doesn't exist
                print(f"[WARN] svg_comments table doesn't exist, using fallback query", flush=True)
                cursor.execute("""
                    SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                           (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                           (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user,
                           0 as comment_count
                    FROM svg_image s
                    JOIN user u ON s.user_id = u.id
                    ORDER BY s.created_at DESC
                    LIMIT 100
                """, (current_user_id or 0,))
            else:
                raise
        
        rows = cursor.fetchall()
        
        # Format results giống như search_results
        for row in rows:
            row['url'] = f"/static/{row['filename']}"
            row['created_time_vn'] = row['created_at'].strftime('%d/%m/%Y %H:%M') if row['created_at'] else ''
            row['is_liked_by_current_user'] = bool(row['is_liked_by_current_user'])
            svg_files.append(row)
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] get_svg_files_with_likes(): {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    return svg_files

def get_public_svg_files():
    """Lấy public files cho user chưa đăng nhập - Format thống nhất với search_results"""
    svg_files = []
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query cho public files (không có like info)
        # Try with comment_count first, fallback if table doesn't exist
        try:
            cursor.execute("""
                SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                       (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                       0 as is_liked_by_current_user,
                       COALESCE((SELECT COUNT(*) FROM svg_comments WHERE svg_filename = s.filename), 0) as comment_count
                FROM svg_image s
                JOIN user u ON s.user_id = u.id
                ORDER BY s.created_at DESC
                LIMIT 100
            """)
        except mysql.connector.errors.ProgrammingError as e:
            if 'svg_comments' in str(e) and "doesn't exist" in str(e):
                # Fallback: Query without comment_count if table doesn't exist
                print(f"[WARN] svg_comments table doesn't exist, using fallback query", flush=True)
                cursor.execute("""
                    SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                           (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                           0 as is_liked_by_current_user,
                           0 as comment_count
                    FROM svg_image s
                    JOIN user u ON s.user_id = u.id
                    ORDER BY s.created_at DESC
                    LIMIT 100
                """)
            else:
                raise
        
        rows = cursor.fetchall()
        
        # Format results giống như search_results
        for row in rows:
            row['url'] = f"/static/{row['filename']}"
            row['created_time_vn'] = row['created_at'].strftime('%d/%m/%Y %H:%M') if row['created_at'] else ''
            row['is_liked_by_current_user'] = False  # User chưa đăng nhập
            svg_files.append(row)
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] get_public_svg_files(): {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    return svg_files

def clean_control_chars(text):
    return re.sub(r'[\x00-\x08\x0B-\x1F\x7F]', '', text)

def format_time_vn(dt):
    """Format thời gian theo múi giờ Việt Nam"""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    vn_time = dt.astimezone(tz_vn)
    return vn_time.strftime("%H:%M:%S - %d/%m/%Y")

# Secret key và Google OAuth blueprint
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secret-key')

google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', 'GOOGLE_CLIENT_SECRET'),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ],
    reprompt_select_account=True,
    redirect_to="login_success"
)

app.register_blueprint(google_bp, url_prefix="/login")

@app.route("/login_success")
def login_success():
    """Xử lý sau khi đăng nhập thành công"""
    # Redirect về trang được lưu trong session hoặc trang chủ
    next_url = session.get('next_url')
    if next_url:
        session.pop('next_url', None)  # Xóa sau khi sử dụng
        return redirect(next_url)
    else:
        return redirect(url_for("index"))

@app.route("/set_next_url")
def set_next_url():
    """Lưu URL hiện tại để redirect sau khi đăng nhập"""
    next_url = request.args.get('url')
    if next_url and next_url.startswith('/'):
        session['next_url'] = next_url
    return redirect(url_for("google.login"))


@app.route("/force_logout_dance")
def force_logout_dance():
    print("DEBUG: Force logout Dance endpoint accessed.", flush=True)
    if hasattr(google, 'token'):
        del google.token

    logout_user()  # ✅ Flask-Login logout
    session.clear()
    session.modified = True
    flash("Tất cả session và token Flask-Dance đã được xóa. Vui lòng đăng nhập lại.", "info")
    return redirect(url_for("index"))

def clear_oauth_session():
    session.clear()
    session.modified = True
    logout_user()  # ✅ Flask-Login logout
    
    try:
        del google.token
    except:
        pass

def is_logged_in():
    return google.authorized

@app.before_request
def load_user_info_if_missing():
    # Bỏ qua kiểm tra cho một số route
    if request.path.startswith('/login/google/authorized') or \
       request.path.startswith('/login/google/login') or \
       request.path.startswith('/static/') or \
       request.path.startswith('/temp_svg/') or \
       request.path.startswith('/temp_img/') or \
       request.path.startswith('/logout'): 
        return

    if google.authorized:
        # Nếu session chưa có thông tin user
        if "user_email" not in session:
            print("DEBUG: User authorized but user_email missing from session. Attempting to re-fetch userinfo.", flush=True)
            try:
                resp = google.get("/oauth2/v2/userinfo")
                if resp.ok:
                    info = resp.json()
                    session["user_email"] = info.get("email")
                    session["google_id"] = info.get("id")
                    session.modified = True
                    print(f"DEBUG: Userinfo re-fetched successfully: {session['user_email']}", flush=True)
                else:
                    del google.token
                    print("DEBUG: Failed to re-fetch userinfo. Clearing google.token.", flush=True)
            except Exception as e:
                del google.token
                print(f"DEBUG: Exception during userinfo re-fetch: {e}. Clearing google.token.", flush=True)

        # Nếu session đã có user_email thì đảm bảo có trong DB
        if "user_email" in session:
            if not get_user_by_email(session["user_email"]):
                print(f"DEBUG: User {session['user_email']} not found in DB. Inserting...", flush=True)
                try:
                    conn = mysql.connector.connect(
                        host=os.environ.get('DB_HOST', 'localhost'),
                        user=os.environ.get('DB_USER', 'hiep1987'),
                        password=os.environ.get('DB_PASSWORD', ''),
                        database=os.environ.get('DB_NAME', 'tikz2svg')
                    )
                    cursor = conn.cursor()
                    default_username = re.sub(r'[^a-zA-Z0-9_-]', '_', session['user_email'].split('@')[0])
                    cursor.execute(
                        "INSERT INTO user (email, google_id, username) VALUES (%s, %s, %s)",
                        (session["user_email"], session["google_id"], default_username)
                    )
                    conn.commit()
                    print(f"DEBUG: User {session['user_email']} INSERTED successfully in DB.", flush=True)
                    
                    # ✅ Gửi email welcome cho user mới
                    try:
                        email_service = get_email_service()
                        if email_service:
                            success = email_service.send_welcome_email(session["user_email"], default_username)
                            if success:
                                print(f"DEBUG: Welcome email sent successfully to {session['user_email']}", flush=True)
                            else:
                                print(f"DEBUG: Failed to send welcome email to {session['user_email']}", flush=True)
                        else:
                            print(f"DEBUG: Email service not available for welcome email to {session['user_email']}", flush=True)
                    except Exception as email_error:
                        print(f"ERROR sending welcome email: {email_error}", flush=True)
                    
                    cursor.close()
                    conn.close()
                except Exception as e:
                    print(f"ERROR inserting user into DB: {e}", flush=True)
                    try:
                        cursor.close()
                        conn.close()
                    except:
                        pass
            
            # ✅ Login user vào Flask-Login nếu chưa login
            if not current_user.is_authenticated:
                user_id = get_user_id_from_session()
                if user_id:
                    user = load_user(user_id)
                    if user:
                        login_user(user, remember=True)
                        print(f"DEBUG: User {user.email} logged into Flask-Login", flush=True)

# Test route for base template
@app.route("/test-base-template")
def test_base_template():
    """Route để test base template với example_using_base.html"""
    logged_in = current_user.is_authenticated
    user_email = current_user.email if logged_in else None
    
    # Tạo app_state giống như trang chủ
    app_state = {
        'loggedIn': logged_in,
        'userEmail': user_email
    }
    
    return render_template('example_using_base.html', 
                         app_state=app_state,
                         logged_in=logged_in,
                         current_user_email=user_email)

# Privacy Policy route - Required for Google OAuth
@app.route("/privacy-policy")
def privacy_policy():
    """Route cho trang Privacy Policy - yêu cầu của Google OAuth Platform"""
    from datetime import datetime
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    return render_template('privacy_policy.html', current_date=current_date)

# Terms of Service route
@app.route("/terms-of-service")
def terms_of_service():
    """Route cho trang Terms of Service"""
    from datetime import datetime
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    return render_template('terms_of_service.html', current_date=current_date)

@app.route("/", methods=["GET", "POST"])
def index():
    print(f"DEBUG: Index route accessed - method: {request.method}")
    logged_in = current_user.is_authenticated
    user_email = current_user.email if logged_in else None
    username = current_user.username if logged_in else None  # ✅ THÊM
    avatar = current_user.avatar if logged_in else None      # ✅ THÊM
    svg_url = None
    svg_full_url = None
    svg_content = None
    file_info = None
    error = None
    svg_temp_url = None
    svg_temp_id = None
    tikz_code = ""
    error_log_full = None
    
    # Cho phép preview khi chưa đăng nhập
    # Chỉ yêu cầu đăng nhập khi lưu server (xử lý ở route /save_svg)
        
    if request.method == "POST":
        tikz_code = request.form.get("code", "")
        tikz_code = clean_control_chars(tikz_code)
        if not tikz_code.strip():
            error = "Vui lòng nhập code TikZ!"
        else:
            now = datetime.now(tz_vn)
            file_id = str(uuid.uuid4())
            work_dir = f"/tmp/{file_id}"
            os.makedirs(work_dir, exist_ok=True)
            tex_path = os.path.join(work_dir, "tikz.tex")
            pdf_path = os.path.join(work_dir, "tikz.pdf")
            svg_path_tmp = os.path.join(work_dir, "tikz.svg")
            
            # ✅ ENHANCED COMPILATION WITH SECURITY & RESOURCE LIMITS
            print(f"🚀 Starting enhanced TikZ compilation for user: {user_email}")
            
            try:
                # Use enhanced compilation function with user context
                user_id = str(current_user.id) if current_user.is_authenticated else "anonymous"
                success, svg_content, compilation_error = compile_tikz_enhanced_whitelist(tikz_code, work_dir, user_id)
                
                if success:
                    # Enhanced compilation successful
                    svg_temp_url = f"/temp_svg/{file_id}"
                    svg_temp_id = file_id
                    
                    # ✅ IMPORTANT: Save SVG to temp file even when from cache
                    # Frontend expects file to exist at /temp_svg/{file_id}
                    svg_path_tmp = os.path.join(work_dir, "tikz.svg")
                    if not os.path.exists(svg_path_tmp) and svg_content:
                        try:
                            with open(svg_path_tmp, 'w', encoding='utf-8') as f:
                                f.write(svg_content)
                            print(f"✅ SVG saved to temp file: {svg_path_tmp}")
                        except Exception as write_err:
                            print(f"⚠️  Warning: Failed to save temp SVG: {write_err}")
                    
                    # Log successful compilation
                    if current_user.is_authenticated:
                        log_compilation_metrics(
                            user_id=str(current_user.id),
                            compilation_time=0.0,  # Will be calculated in function
                            memory_used=0.0,       # Will be calculated in function
                            success=True
                        )
                    
                    print(f"✅ Enhanced compilation successful - SVG generated")
                else:
                    # Enhanced compilation failed
                    print(f"❌ Enhanced compilation failed: {compilation_error}")
                    
                    # Classify error for better user experience
                    error_classification = CompilationErrorClassifier.classify_error(compilation_error, tikz_code)
                    
                    # Log security events if applicable
                    if error_classification['category'] == 'security':
                        log_security_event(
                            event_type="DANGEROUS_PATTERN_BLOCKED",
                            user_id=str(current_user.id) if current_user.is_authenticated else "anonymous",
                            ip_address=request.remote_addr or "unknown",
                            details=compilation_error
                        )
                    
                    # ✅ FIX: Read full log file for display
                    log_path = os.path.join(work_dir, "tikz.log")
                    if os.path.exists(log_path):
                        try:
                            with open(log_path, 'r', encoding='utf-8') as log_file:
                                error_log_full = log_file.read()
                            print(f"✅ Read error log: {len(error_log_full)} characters")
                        except Exception as log_err:
                            print(f"⚠️  Failed to read log file: {log_err}")
                            error_log_full = compilation_error  # Fallback to compilation error
                    else:
                        print(f"⚠️  Log file not found: {log_path}")
                        error_log_full = compilation_error  # Use compilation error as log
                    
                    # ✅ FIX: Format error as HTML string for template
                    error_html = f"<strong>{error_classification['user_message']}</strong>"
                    
                    if error_classification['suggestions']:
                        error_html += "<br><br><strong>💡 Gợi ý:</strong><ul>"
                        for suggestion in error_classification['suggestions']:
                            error_html += f"<li>{suggestion}</li>"
                        error_html += "</ul>"
                    
                    # Add category badge
                    category_colors = {
                        'syntax': '#ff6b6b',
                        'package': '#4ecdc4',
                        'security': '#ffe66d',
                        'resource': '#95e1d3',
                        'unknown': '#9b59b6'
                    }
                    category_color = category_colors.get(error_classification['category'], '#9b59b6')
                    error_html += f"<br><br><span style='background:{category_color};color:#fff;padding:4px 8px;border-radius:4px;font-size:0.85em;'>Category: {error_classification['category']}</span>"
                    
                    error = error_html
                    
                    # Set svg_content to None for failed compilation
                    svg_content = None
            
            except Exception as ex:
                # Lưu code TikZ lỗi và log lỗi
                timestamp = now.strftime('%Y%m%d_%H%M%S')
                error_tex = os.path.join(ERROR_TIKZ_DIR, f'{timestamp}_{file_id}.tex')
                with open(error_tex, 'w', encoding='utf-8') as f:
                    f.write(tikz_code)
                    
                log_path = os.path.join(work_dir, "tikz.log")
                if os.path.exists(log_path):
                    error_log = os.path.join(ERROR_TIKZ_DIR, f'{timestamp}_{file_id}.log')
                    with open(log_path, 'r', encoding='utf-8') as src, open(error_log, 'w', encoding='utf-8') as dst:
                        log_content = src.read()
                        dst.write(log_content)
                        error_log_full = log_content
                        
                error = "Lỗi khi biên dịch hoặc chuyển đổi SVG."
                if hasattr(ex, 'stderr') and ex.stderr:
                    error += f"<br><br><b>Chi tiết lỗi từ LaTeX:</b><pre>{ex.stderr}</pre>"
                    
                error_details = []
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r', encoding='utf-8') as log_file:
                            for line in log_file:
                                if line.startswith("!") or 'error' in line.lower():
                                    error_details.append(line.strip())
                            if error_details:
                                error += "<br><br><b>Chi tiết lỗi từ Log:</b><pre>" + "\n".join(error_details) + "</pre>"
                    except Exception:
                        pass
                        
    # =====================================================
    # PAGINATION: Lấy danh sách SVG với phân trang
    # =====================================================
    page, per_page = get_pagination_params(request)
    offset = (page - 1) * per_page
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get total count for pagination (all items for now)
        cursor.execute("SELECT COUNT(*) as total FROM svg_image")
        total_items = cursor.fetchone()['total']
        
        # Calculate pagination metadata
        total_pages = max(1, (total_items + per_page - 1) // per_page)  # Ceiling division
        has_prev = page > 1
        has_next = page < total_pages
        
        # Fetch paginated data - match structure of profile_followed_posts
        user_id_for_like = current_user.id if logged_in else 0
        cursor.execute("""
            SELECT 
                s.id,
                s.filename,
                s.created_at,
                s.user_id,
                s.tikz_code,
                s.keywords,
                u.id as creator_id,
                COALESCE(u.username, 'Anonymous') as creator_username,
                COUNT(DISTINCT c.id) as comment_count,
                COUNT(DISTINCT sl.id) as like_count,
                CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
            FROM svg_image s
            LEFT JOIN user u ON s.user_id = u.id
            LEFT JOIN svg_comments c ON s.filename = c.svg_filename
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
            GROUP BY s.id, s.filename, s.created_at, s.user_id, s.tikz_code, s.keywords, u.id, u.username, user_like.id
            ORDER BY s.created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id_for_like, per_page, offset))
        
        svg_files = cursor.fetchall()
        
        # Format svg_files to match profile_followed_posts structure exactly
        for svg in svg_files:
            # Format timestamps
            created_at = svg.get('created_at')
            if created_at:
                svg['created_time_vn'] = created_at.strftime('%d/%m/%Y %H:%M')
                svg['created_time'] = str(created_at)
            else:
                svg['created_time_vn'] = ''
                svg['created_time'] = ''
            
            # URL using url_for (same as profile_followed_posts)
            svg['url'] = f"/static/{svg['filename']}"
            
            # Convert is_liked to boolean
            svg['is_liked_by_current_user'] = bool(svg.get('is_liked_by_current_user', 0))
            
            # Ensure counts are integers
            svg['like_count'] = svg.get('like_count', 0) or 0
            svg['comment_count'] = svg.get('comment_count', 0) or 0
            
            # creator_id and creator_username already from SQL query
        
        cursor.close()
        conn.close()
        
        # Generate page numbers for UI
        page_numbers = generate_page_numbers(page, total_pages, MAX_PAGES_DISPLAY)
        
        print(f"✅ Pagination: Page {page}/{total_pages}, showing {len(svg_files)} of {total_items} items")
        
    except Exception as e:
        print(f"❌ Pagination error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to old method if pagination fails
        if logged_in:
            svg_files = get_svg_files_with_likes()
        else:
            svg_files = get_public_svg_files()
        
        # Default pagination values
        total_items = len(svg_files)
        total_pages = 1
        has_prev = False
        has_next = False
        page_numbers = [1]
        page = 1
    
    return render_template("index.html",
                           tikz_code=tikz_code,
                           svg_url=svg_url,
                           svg_full_url=svg_full_url,
                           svg_content=svg_content,
                           file_info=file_info,
                           svg_files=svg_files,
                           error=error,
                           svg_temp_url=svg_temp_url,
                           svg_temp_id=svg_temp_id,
                           error_log_full=error_log_full,
                           logged_in=logged_in,
                           user_email=user_email,
                           username=username,
                           avatar=avatar,
                           # Pagination data
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           total_items=total_items,
                           has_prev=has_prev,
                           has_next=has_next,
                           page_numbers=page_numbers
    )

@app.route('/temp_svg/<file_id>')
def serve_temp_svg(file_id):
    svg_path = f"/tmp/{file_id}/tikz.svg"
    if os.path.exists(svg_path):
        return send_file(svg_path, mimetype='image/svg+xml')
    return "Not found", 404

@app.route('/save_svg', methods=['POST'])
@login_required
def save_svg():
    data = request.json
    file_id = data.get('file_id')
    tikz_code = data.get('tikz_code', '')
    keywords_raw = data.get('keywords', '').strip()

    if not file_id:
        return jsonify({"error": "Thiếu file_id"}), 400

    work_dir = f"/tmp/{file_id}"
    svg_path_tmp = os.path.join(work_dir, "tikz.svg")
    if not os.path.exists(svg_path_tmp):
        return jsonify({"error": "Không tìm thấy file tạm"}), 404

    now = datetime.now(tz_vn)
    
    # ✅ Sửa đổi: Lấy google_id từ database thay vì session
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT google_id FROM user WHERE id = %s", (current_user.id,))
        row = cursor.fetchone()
        google_id = row[0] if row and row[0] else "anonymous"
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ ERROR getting google_id from DB: {e}", flush=True)
        # Fallback to session if DB query fails
        google_id = session.get("google_id", "anonymous")
    
    timestamp = now.strftime("%H%M%S%d%m%y")
    svg_filename = f"{google_id}_{timestamp}.svg"
    svg_path_final = os.path.join(app.config['UPLOAD_FOLDER'], svg_filename)

    # Ghi file SVG
    with open(svg_path_tmp, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    with open(svg_path_final, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    # Tự động convert sang PNG
    try:
        import io
        from PIL import Image
        with open(svg_path_final, 'rb') as fsvg:
            svg_data = fsvg.read()

        import re
        m = re.search(r'width=["\'](\d+)', svg_content)
        n = re.search(r'height=["\'](\d+)', svg_content)
        if m and n:
            width_svg = int(m.group(1))
            height_svg = int(n.group(1))
        else:
            width_svg = 1000
            height_svg = 1000

        max_w, max_h = 1200, 630
        ratio_svg = width_svg / height_svg
        ratio_fb = max_w / max_h

        if ratio_svg > ratio_fb:
            out_w = max_w
            out_h = int(max_w / ratio_svg)
        else:
            out_h = max_h
            out_w = int(max_h * ratio_svg)

        png_bytes = cairosvg.svg2png(bytestring=svg_data, output_width=out_w, output_height=out_h, dpi=300)
        bg = Image.new("RGB", (max_w, max_h), (255, 230, 240))
        fg = Image.open(io.BytesIO(png_bytes))
        x = (max_w - out_w) // 2
        y = (max_h - out_h) // 2
        bg.paste(fg, (x, y), fg if fg.mode == "RGBA" else None)
        png_path_final = svg_path_final.replace('.svg', '.png')
        bg.save(png_path_final)

    except Exception as e:
        print(f"[WARN] Không thể convert SVG sang PNG: {e}", flush=True)

    # ✅ Thêm vào CSDL với cấu trúc đúng
    try:
        user_id = current_user.id

        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()

        # ✅ INSERT với cấu trúc database đúng
        cursor.execute("""
            INSERT INTO svg_image (filename, tikz_code, keywords, user_id)
            VALUES (%s, %s, %s, %s)
        """, (svg_filename, tikz_code, keywords_raw, user_id))
        conn.commit()

        svg_image_id = cursor.lastrowid
        print(f"✅ svg_image inserted, id={svg_image_id}")

        # Xử lý keywords
        if keywords_raw:
            keywords_list = [kw.strip() for kw in keywords_raw.split(',') if kw.strip()]
            for kw in keywords_list:
                cursor.execute("SELECT id FROM keyword WHERE word = %s", (kw,))
                row = cursor.fetchone()
                if row:
                    keyword_id = row[0]
                else:
                    cursor.execute("INSERT INTO keyword (word) VALUES (%s)", (kw,))
                    conn.commit()
                    keyword_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO svg_image_keyword (svg_image_id, keyword_id) VALUES (%s, %s)",
                    (svg_image_id, keyword_id)
                )
                conn.commit()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ ERROR inserting into DB: {e}", flush=True)

    # Xóa thư mục tạm
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)

    return jsonify({"success": True, "filename": svg_filename, "url": f"/static/{svg_filename}"})

@app.route('/api/keywords/search')
def api_search_keywords():
    q = request.args.get('q', '').strip()
    if not q:
        # Khi query rỗng, trả về tất cả keywords (giới hạn 20 từ)
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM keyword ORDER BY word LIMIT 20")
            results = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return jsonify(results)
        except Exception as e:
            print(f"[ERROR] /api/keywords/search (empty query): {e}", flush=True)
            return jsonify([])

    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM keyword WHERE word LIKE %s COLLATE utf8mb4_general_ci LIMIT 10", (f"%{q}%",))
        results = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(results)
    except Exception as e:
        print(f"[ERROR] /api/keywords/search: {e}", flush=True)
        return jsonify([])

@app.route('/search')
def search_results():
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'keywords')  # Default to keywords search

    if not query:
        return redirect(url_for('index'))

    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        if search_type == 'username':
            # Search for SVG files by username
            cursor.execute("""
                SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                       (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                       (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user
                FROM svg_image s
                JOIN user u ON s.user_id = u.id
                WHERE u.username LIKE %s COLLATE utf8mb4_general_ci
                ORDER BY s.created_at DESC
            """, (get_user_id_from_session() or 0, f"%{query}%"))
        else:
            # Default: Search for SVG files by keywords
            cursor.execute("""
                SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                       (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                       (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user
                FROM svg_image s
                JOIN user u ON s.user_id = u.id
                JOIN svg_image_keyword sik ON s.id = sik.svg_image_id
                JOIN keyword k ON sik.keyword_id = k.id
                WHERE k.word LIKE %s COLLATE utf8mb4_general_ci
                ORDER BY s.created_at DESC
            """, (get_user_id_from_session() or 0, f"%{query}%"))

        search_results = cursor.fetchall()

        # Format the results
        for result in search_results:
            result['url'] = f"/static/{result['filename']}"
            result['created_time_vn'] = result['created_at'].strftime('%d/%m/%Y %H:%M') if result['created_at'] else ''
            result['is_liked_by_current_user'] = bool(result['is_liked_by_current_user'])

        cursor.close()
        conn.close()

        # Set search type description for template
        search_type_description = "Tên tài khoản" if search_type == 'username' else "Từ khóa"

        return render_template('search_results.html',
                             search_query=query,
                             search_type=search_type,
                             search_type_description=search_type_description,
                             search_results=search_results,
                             results_count=len(search_results),
                             logged_in=current_user.is_authenticated,
                             user_email=current_user.email if current_user.is_authenticated else None,
                             username=current_user.username if current_user.is_authenticated else None,
                             avatar=current_user.avatar if current_user.is_authenticated else None)

    except Exception as e:
        print(f"[ERROR] /search: {e}", flush=True)
        search_type_description = "Tên tài khoản" if search_type == 'username' else "Từ khóa"
        return render_template('search_results.html',
                             search_query=query,
                             search_type=search_type,
                             search_type_description=search_type_description,
                             search_results=[],
                             results_count=0,
                             logged_in=current_user.is_authenticated,
                             user_email=current_user.email if current_user.is_authenticated else None,
                             username=current_user.username if current_user.is_authenticated else None,
                             avatar=current_user.avatar if current_user.is_authenticated else None)

def get_user_id_from_session():
    """Helper function for backward compatibility"""
    if current_user.is_authenticated:
        return current_user.id
    
    # Fallback cho session cũ
    user_email = session.get('user_email')
    if not user_email:
        return None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"ERROR get_user_id_from_session: {e}", flush=True)
        return None

@app.route('/delete_svg', methods=['POST'])
@login_required
def delete_svg():
    # Validate request format
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type phải là application/json"}), 400
    
    data = request.json
    svg_image_id = data.get('svg_image_id')
    
    # Log security event
    print(f"🔍 DELETE_SVG request from user {current_user.id} for SVG {svg_image_id} at {datetime.now()}", flush=True)
    
    # Validate input
    try:
        svg_image_id = int(svg_image_id)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "ID không hợp lệ"}), 400

    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # ✅ KIỂM TRA FILE VÀ OWNERSHIP với cấu trúc database đúng
        cursor.execute("""
            SELECT filename, user_id 
            FROM svg_image 
            WHERE id = %s
        """, (svg_image_id,))
        
        row = cursor.fetchone()
        if not row:
            print(f"❌ File not found: SVG ID {svg_image_id}", flush=True)
            return jsonify({"success": False, "error": f"Không tìm thấy ảnh với ID {svg_image_id}"}), 404
        
        # ✅ KIỂM TRA QUYỀN SỞ HỮU với user_id
        if row['user_id'] != current_user.id:
            print(f"🚨 UNAUTHORIZED DELETE ATTEMPT:", flush=True)
            print(f"   - Attempting User ID: {current_user.id}", flush=True)
            print(f"   - File Owner ID: {row['user_id']}", flush=True)
            print(f"   - SVG ID: {svg_image_id}", flush=True)
            print(f"   - User IP: {request.remote_addr}", flush=True)
            
            return jsonify({
                "success": False,
                "error": "Bạn không có quyền xóa file này!"
            }), 403
            
        filename = row['filename']
        print(f"✅ Authorization passed - User {current_user.id} deleting own file {svg_image_id} ({filename})", flush=True)
        
        # Transaction handling
        if conn.in_transaction:
            conn.rollback()
        
        conn.start_transaction(isolation_level='READ COMMITTED')
        
        # Xóa liên kết keyword
        cursor.execute("DELETE FROM svg_image_keyword WHERE svg_image_id = %s", (svg_image_id,))
        keyword_deleted = cursor.rowcount
        print(f"🗑️ Đã xóa {keyword_deleted} liên kết keyword", flush=True)
        
        # Xóa likes
        cursor.execute("DELETE FROM svg_like WHERE svg_image_id = %s", (svg_image_id,))
        likes_deleted = cursor.rowcount
        print(f"🗑️ Đã xóa {likes_deleted} likes", flush=True)
        
        # Xóa action logs
        cursor.execute("DELETE FROM svg_action_log WHERE svg_image_id = %s", (svg_image_id,))
        logs_deleted = cursor.rowcount
        print(f"🗑️ Đã xóa {logs_deleted} action logs", flush=True)
        
        # Xóa user action logs
        cursor.execute("DELETE FROM user_action_log WHERE target_svg_id = %s", (svg_image_id,))
        user_logs_deleted = cursor.rowcount
        print(f"🗑️ Đã xóa {user_logs_deleted} user action logs", flush=True)
        
        # Xóa bản ghi chính
        cursor.execute("DELETE FROM svg_image WHERE id = %s", (svg_image_id,))
        svg_deleted = cursor.rowcount
        if svg_deleted == 0:
            conn.rollback()
            return jsonify({"success": False, "error": "Không thể xóa bản ghi"}), 500
            
        print(f"🗑️ Đã xóa bản ghi svg_image: id={svg_image_id}", flush=True)
        
        # Commit transaction
        conn.commit()
        print(f"✅ Transaction committed thành công", flush=True)
        
        # Xóa file vật lý
        if filename:
            svg_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            png_filename = filename.replace('.svg', '.png')
            png_file_path = os.path.join(app.config['UPLOAD_FOLDER'], png_filename)
            
            def safe_delete_file(file_path, file_type):
                if not os.path.exists(file_path):
                    return False
                try:
                    os.remove(file_path)
                    print(f"✅ Đã xóa file {file_type}: {file_path}", flush=True)
                    return True
                except Exception as e:
                    print(f"❌ Lỗi xóa file {file_type}: {e}", flush=True)
                    return False
            
            svg_deleted = safe_delete_file(svg_file_path, "SVG")
            png_deleted = safe_delete_file(png_file_path, "PNG")
        
        print(f"✅ File successfully deleted by authorized user {current_user.id}: {filename}", flush=True)
        return jsonify({"success": True, "message": "Đã xóa ảnh thành công"})
        
    except mysql.connector.Error as db_error:
        print(f"❌ Lỗi database: {db_error}", flush=True)
        if conn:
            try:
                if conn.in_transaction:
                    conn.rollback()
            except:
                pass
        return jsonify({"success": False, "error": f"Lỗi database: {str(db_error)}"}), 500
        
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}", flush=True)
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        if conn:
            try:
                if conn.in_transaction:
                    conn.rollback()
            except:
                pass
        return jsonify({"success": False, "error": "Lỗi khi xóa ảnh"}), 500
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

# ✅ API LIKE/UNLIKE
@app.route('/like_svg', methods=['POST'])
@login_required
def like_svg():
    data = request.json
    svg_id = data.get('svg_id')
    action = data.get('action')  # 'like' or 'unlike'
    
    if not svg_id or action not in ['like', 'unlike']:
        return jsonify({"success": False, "message": "Invalid parameters"}), 400
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Kiểm tra SVG tồn tại
        cursor.execute("SELECT id FROM svg_image WHERE id = %s", (svg_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "SVG not found"}), 404
            
        if action == 'like':
            # Thêm like (nếu chưa like)
            cursor.execute("""
                INSERT IGNORE INTO svg_like (user_id, svg_image_id) 
                VALUES (%s, %s)
            """, (current_user.id, svg_id))
            
            rows_affected = cursor.rowcount
            
            # Log action
            cursor.execute("""
                INSERT INTO user_action_log (user_id, target_svg_id, action_type) 
                VALUES (%s, %s, 'like')
            """, (current_user.id, svg_id))
            
            # Create notification for SVG owner (only if new like was added)
            if rows_affected > 0:
                try:
                    # Get SVG owner info
                    cursor.execute("""
                        SELECT user_id, filename 
                        FROM svg_image 
                        WHERE id = %s
                    """, (svg_id,))
                    svg_info = cursor.fetchone()
                    
                    if svg_info:
                        svg_owner_id = svg_info['user_id']
                        svg_filename = svg_info['filename']
                        
                        # Create notification
                        notification_service = get_notification_service()
                        notification_service.create_notification(
                            user_id=svg_owner_id,
                            actor_id=current_user.id,
                            notification_type='like',
                            target_type='svg_image',
                            target_id=svg_filename,
                            action_url=f'/view_svg/{svg_filename}'
                        )
                except Exception as e:
                    # Don't fail the like operation if notification fails
                    print(f"[WARN] Failed to create like notification: {e}", flush=True)
        else:
            # Xóa like
            cursor.execute("""
                DELETE FROM svg_like 
                WHERE user_id = %s AND svg_image_id = %s
            """, (current_user.id, svg_id))
            
            # Log action
            cursor.execute("""
                INSERT INTO user_action_log (user_id, target_svg_id, action_type) 
                VALUES (%s, %s, 'unlike')
            """, (current_user.id, svg_id))
        
        conn.commit()
        
        # Đếm tổng số likes
        cursor.execute("SELECT COUNT(*) as count FROM svg_like WHERE svg_image_id = %s", (svg_id,))
        like_count = cursor.fetchone()['count']
        
        # Kiểm tra user hiện tại đã like chưa
        cursor.execute("""
            SELECT COUNT(*) as count FROM svg_like 
            WHERE user_id = %s AND svg_image_id = %s
        """, (current_user.id, svg_id))
        is_liked = cursor.fetchone()['count'] > 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Successfully {action}d",
            "like_count": like_count,
            "is_liked": is_liked
        })
        
    except Exception as e:
        print(f"Error in like_svg: {e}", flush=True)
        return jsonify({"success": False, "message": "Database error"}), 500

# ✅ API FOLLOW/UNFOLLOW
@app.route('/follow/<int:followee_id>', methods=['POST'])
@login_required
def follow_user(followee_id):
    if followee_id == current_user.id:
        return jsonify({"success": False, "message": "Cannot follow yourself"}), 400
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        
        # Kiểm tra user tồn tại
        cursor.execute("SELECT id FROM user WHERE id = %s", (followee_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Thêm follow
        cursor.execute("""
            INSERT IGNORE INTO user_follow (follower_id, followee_id) 
            VALUES (%s, %s)
        """, (current_user.id, followee_id))
        
        rows_affected = cursor.rowcount
        
        # Log action
        cursor.execute("""
            INSERT INTO user_action_log (user_id, target_user_id, action_type) 
            VALUES (%s, %s, 'follow')
        """, (current_user.id, followee_id))
        
        # Create notification for followed user (only if new follow was added)
        if rows_affected > 0:
            try:
                notification_service = get_notification_service()
                notification_service.create_notification(
                    user_id=followee_id,
                    actor_id=current_user.id,
                    notification_type='follow',
                    target_type='user',
                    target_id=str(followee_id),
                    action_url=f'/profile/{current_user.id}'
                )
            except Exception as e:
                # Don't fail the follow operation if notification fails
                print(f"[WARN] Failed to create follow notification: {e}", flush=True)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Successfully followed"})
        
    except Exception as e:
        print(f"Error in follow_user: {e}", flush=True)
        return jsonify({"success": False, "message": "Database error"}), 500

@app.route('/unfollow/<int:followee_id>', methods=['POST'])
@login_required
def unfollow_user(followee_id):
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        
        # Xóa follow
        cursor.execute("""
            DELETE FROM user_follow 
            WHERE follower_id = %s AND followee_id = %s
        """, (current_user.id, followee_id))
        
        # Log action
        cursor.execute("""
            INSERT INTO user_action_log (user_id, target_user_id, action_type) 
            VALUES (%s, %s, 'unfollow')
        """, (current_user.id, followee_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Successfully unfollowed"})
        
    except Exception as e:
        print(f"Error in unfollow_user: {e}", flush=True)
        return jsonify({"success": False, "message": "Database error"}), 500

# ✅ API FOLLOWED POSTS
@app.route('/api/followed_posts')
@login_required
@limiter.limit(RATE_LIMITS['api_general'])
def api_followed_posts():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Lấy posts từ người user đang follow
        cursor.execute("""
            SELECT 
                s.id, 
                s.filename, 
                s.tikz_code, 
                s.created_at,
                u.id as creator_id,
                u.username as creator_username,
                COUNT(sl.id) as like_count,
                CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            JOIN user_follow uf ON u.id = uf.followee_id
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
            WHERE uf.follower_id = %s
            GROUP BY s.id, s.filename, s.tikz_code, s.created_at, u.id, u.username, user_like.id
            ORDER BY s.created_at DESC
            LIMIT 50
        """, (current_user.id, current_user.id))
        
        posts = []
        for row in cursor.fetchall():
            posts.append({
                'id': row['id'],
                'filename': row['filename'],
                'tikz_code': row['tikz_code'],
                'url': url_for('static', filename=row['filename']),
                'creator_id': row['creator_id'],
                'creator_username': row['creator_username'],
                'created_time_vn': format_time_vn(row['created_at']),
                'like_count': row['like_count'] or 0,
                'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
            })
        
        cursor.close()
        conn.close()
        return jsonify(posts)
        
    except Exception as e:
        print(f"Error in api_followed_posts: {e}", flush=True)
        return jsonify([]), 500

@app.route('/api/files')
@login_required
@limiter.limit(RATE_LIMITS['api_general'])
def api_files():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Lấy tất cả files đã lưu
        cursor.execute("""
            SELECT 
                s.id, 
                s.filename, 
                s.tikz_code, 
                s.created_at,
                u.id as creator_id,
                u.username as creator_username,
                COUNT(sl.id) as like_count,
                CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
            GROUP BY s.id, s.filename, s.tikz_code, s.created_at, u.id, u.username, user_like.id
            ORDER BY s.created_at DESC
            LIMIT 50
        """, (current_user.id,))
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'id': row['id'],
                'filename': row['filename'],
                'tikz_code': row['tikz_code'],
                'url': url_for('static', filename=row['filename']),
                'creator_id': row['creator_id'],
                'creator_username': row['creator_username'],
                'created_time_vn': format_time_vn(row['created_at']),
                'like_count': row['like_count'] or 0,
                'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
            })
        
        cursor.close()
        conn.close()
        return jsonify(files)
        
    except Exception as e:
        print(f"Error in api_files: {e}", flush=True)
        return jsonify([]), 500

@app.route('/api/public/files')
@limiter.limit(RATE_LIMITS['api_general'])
def api_public_files():
    """API để lấy danh sách SVG files công khai (không cần đăng nhập)"""
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Lấy tất cả files đã lưu (công khai)
        cursor.execute("""
            SELECT 
                s.id, 
                s.filename, 
                s.tikz_code, 
                s.created_at,
                u.id as creator_id,
                u.username as creator_username,
                COUNT(sl.id) as like_count
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            GROUP BY s.id, s.filename, s.tikz_code, s.created_at, u.id, u.username
            ORDER BY s.created_at DESC
            LIMIT 50
        """)
        
        files = []
        for row in cursor.fetchall():
            try:
                static_dir = app.config['UPLOAD_FOLDER']
                filepath = os.path.join(static_dir, row['filename'])
                if os.path.exists(filepath):
                    file_size_kb = round(os.path.getsize(filepath) / 1024, 2)
                else:
                    file_size_kb = None
            except Exception:
                file_size_kb = None
                
            try:
                url = url_for('static', filename=row['filename'])
            except:
                url = f"/static/{row['filename']}"
                
            files.append({
                'id': row['id'],
                'filename': row['filename'],
                'tikz_code': row['tikz_code'],
                'url': url,
                'display_name': f"Người tạo: {row['creator_username']}" if row.get('creator_username') else row['filename'],
                'size': file_size_kb,
                'created_time': format_time_vn(row['created_at']),
                'creator_id': row['creator_id'],
                'creator_username': row['creator_username'],
                'like_count': row['like_count'] or 0,
                'is_liked_by_current_user': False  # Mặc định là False cho người chưa đăng nhập
            })
        
        cursor.close()
        conn.close()
        return jsonify({'files': files})
        
    except Exception as e:
        print(f"Error in api_public_files: {e}", flush=True)
        return jsonify({'files': []}), 500

@app.route('/delete_temp_svg', methods=['POST'])
def delete_temp_svg():
    data = request.json
    file_id = data.get('file_id')
    if not file_id:
        return jsonify({"error": "Thiếu file_id"}), 400
    work_dir = f"/tmp/{file_id}"
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)
    return jsonify({"success": True})

@app.route('/temp_convert', methods=['POST'])
def temp_convert():
    data = request.json
    file_id = data.get('file_id')
    fmt = data.get('fmt', 'png')
    width = data.get('width')
    height = data.get('height')
    dpi = data.get('dpi')
    if not file_id or fmt not in ('png', 'jpeg'):
        return jsonify({'error': 'Tham số không hợp lệ!'}), 400
    work_dir = f"/tmp/{file_id}"
    svg_path = os.path.join(work_dir, "tikz.svg")
    if not os.path.exists(svg_path):
        return jsonify({'error': 'Không tìm thấy file SVG tạm!'}), 404
    out_name = f"tikz.{fmt}"
    out_path = os.path.join(work_dir, out_name)
    try:
        with open(svg_path, 'rb') as f:
            svg_data = f.read()
        cairosvg_args = {}
        if width: cairosvg_args['output_width'] = int(width)
        if height: cairosvg_args['output_height'] = int(height)
        if dpi: cairosvg_args['dpi'] = int(dpi)
        if fmt == 'png':
            cairosvg.svg2png(bytestring=svg_data, write_to=out_path, **cairosvg_args)
        elif fmt == 'jpeg':
            tmp_png = out_path + '.tmp.png'
            cairosvg.svg2png(bytestring=svg_data, write_to=tmp_png, **cairosvg_args)
            with Image.open(tmp_png) as im:
                if im.mode == 'RGBA':
                    background = Image.new('RGB', im.size, (255, 255, 255))
                    background.paste(im, mask=im.split()[3])
                else:
                    background = im.convert('RGB')
                background.save(out_path, 'JPEG', quality=95)
            os.remove(tmp_png)
        url = f"/temp_img/{file_id}/{out_name}"

        # Add file size and actual image dimensions similar to /convert endpoint
        file_size = os.path.getsize(out_path) if os.path.exists(out_path) else None
        actual_size = None
        if os.path.exists(out_path):
            try:
                with Image.open(out_path) as im:
                    actual_size = f"{im.size[0]}x{im.size[1]} pixels"
            except Exception:
                actual_size = None

        return jsonify({'url': url, 'file_size': file_size, 'actual_size': actual_size})
    except Exception as e:
        return jsonify({'error': f'Lỗi chuyển đổi: {str(e)}'}), 500

@app.route('/temp_img/<file_id>/<filename>')
def serve_temp_img(file_id, filename):
    img_path = f"/tmp/{file_id}/{filename}"
    if os.path.exists(img_path):
        if filename.endswith('.png'):
            return send_file(img_path, mimetype='image/png')
        elif filename.endswith('.jpeg') or filename.endswith('.jpg'):
            return send_file(img_path, mimetype='image/jpeg')
    return "Not found", 404

@app.route('/convert', methods=['POST'])
def convert_svg():
    data = request.json
    filename = data.get('filename')
    fmt = data.get('fmt', 'png')
    width = data.get('width')
    height = data.get('height')
    dpi = data.get('dpi')

    if not filename or fmt not in ('png', 'jpeg'):
        return jsonify({'error': 'Tham số không hợp lệ!'}), 400

    # Validation kích thước ảnh
    max_pixels = 60000000  # 60MP giới hạn
    
    # Kiểm tra nếu có width và height
    if width and height:
        total_pixels = int(width) * int(height)
        if total_pixels > max_pixels:
            return jsonify({'error': f'Kích thước ảnh quá lớn! Tối đa {max_pixels//1000000}MP (hiện tại: {total_pixels//1000000}MP)'}), 400
    
    # Kiểm tra DPI quá cao
    if dpi and int(dpi) > 2000:
        return jsonify({'error': f'DPI quá cao! Tối đa 2000 DPI (hiện tại: {dpi} DPI)'}), 400

    svg_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(svg_path):
        return jsonify({'error': 'Không tìm thấy file SVG!'}), 404

    out_name = f"tikz.{fmt}"
    out_path = os.path.join(app.config['UPLOAD_FOLDER'], out_name)
    try:
        with open(svg_path, 'rb') as f:
            svg_data = f.read()
        

        cairosvg_args = {}
        if width: cairosvg_args['output_width'] = int(width)
        if height: cairosvg_args['output_height'] = int(height)
        if dpi: cairosvg_args['dpi'] = int(dpi)
        
        if fmt == 'png':
            cairosvg.svg2png(bytestring=svg_data, write_to=out_path, **cairosvg_args)
            # Kiểm tra kích thước ảnh PNG
            try:
                with Image.open(out_path) as im:
                    actual_pixels = im.size[0] * im.size[1]
                    if actual_pixels > max_pixels:
                        os.remove(out_path)
                        # Tính toán dung lượng ước tính
                        estimated_size_mb = (actual_pixels * 4) / (1024 * 1024)
                        return jsonify({
                            'error': f'Kích thước ảnh quá lớn! Tối đa {max_pixels//1000000}MP (hiện tại: {actual_pixels//1000000}MP)',
                            'estimated_size_mb': f'{estimated_size_mb:.1f}MB',
                            'note': 'Dung lượng thực tế có thể nhỏ hơn do nén'
                        }), 400
            except Exception as img_error:
                if os.path.exists(out_path):
                    os.remove(out_path)
                raise img_error
        elif fmt == 'jpeg':
            tmp_png = out_path + '.tmp.png'
            cairosvg.svg2png(bytestring=svg_data, write_to=tmp_png, **cairosvg_args)
            
            try:
                with Image.open(tmp_png) as im:
                    # Kiểm tra kích thước ảnh sau khi convert
                    actual_pixels = im.size[0] * im.size[1]
                    if actual_pixels > max_pixels:
                        os.remove(tmp_png)
                        # Tính toán dung lượng ước tính
                        estimated_size_mb = (actual_pixels * 4) / (1024 * 1024)
                        return jsonify({
                            'error': f'Kích thước ảnh quá lớn! Tối đa {max_pixels//1000000}MP (hiện tại: {actual_pixels//1000000}MP)',
                            'estimated_size_mb': f'{estimated_size_mb:.1f}MB',
                            'note': 'Dung lượng thực tế có thể nhỏ hơn do nén'
                        }), 400
                    
                    if im.mode == 'RGBA':
                        background = Image.new('RGB', im.size, (255, 255, 255))
                        background.paste(im, mask=im.split()[3])
                    else:
                        background = im.convert('RGB')
                    background.save(out_path, 'JPEG', quality=95)
            except Exception as img_error:
                if os.path.exists(tmp_png):
                    os.remove(tmp_png)
                raise img_error
            finally:
                if os.path.exists(tmp_png):
                    os.remove(tmp_png)
                    
        url = f"/static/{out_name}"
        
        # Lấy thông tin dung lượng file
        file_size = os.path.getsize(out_path) if os.path.exists(out_path) else None
        
        # Lấy thông tin kích thước ảnh thực tế
        actual_size = None
        if os.path.exists(out_path):
            try:
                with Image.open(out_path) as im:
                    actual_size = f"{im.size[0]}x{im.size[1]} pixels"
            except:
                pass
        
        return jsonify({
            'url': url,
            'file_size': file_size,
            'actual_size': actual_size
        })
    except Exception as e:
        # Cleanup file tạm nếu có lỗi
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except:
                pass
        return jsonify({'error': f'Lỗi chuyển đổi: {str(e)}'}), 500

@app.route('/view_svg/<filename>')
def view_svg(filename):
    svg_url = f"/static/{filename}"
    png_url = f"/static/{filename.replace('.svg', '.png')}"

    tikz_code = None
    display_name = filename
    caption = None
    owner_user_id = None

    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT tikz_code, user_id, caption
            FROM svg_image 
            WHERE filename = %s 
            LIMIT 1
        """, (filename,))
        row = cursor.fetchone()

        if row:
            tikz_code = row['tikz_code']
            owner_user_id = row['user_id']
            caption = row.get('caption', '')

            if owner_user_id:
                cursor.execute("SELECT username FROM user WHERE id = %s", (owner_user_id,))
                user_row = cursor.fetchone()
                if user_row and user_row['username']:
                    display_name = f"Người tạo: {user_row['username']}"

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] in /view_svg DB lookup: {e}", flush=True)

    # Lấy thông tin user hiện tại
    user_email = current_user.email if current_user.is_authenticated else None
    username = current_user.username if current_user.is_authenticated else None
    avatar = current_user.avatar if current_user.is_authenticated else None

    return render_template(
        "view_svg.html",
        svg_url=svg_url,
        png_url=png_url,
        tikz_code=tikz_code,
        filename=filename,
        display_name=display_name,
        caption=caption,
        user_id=owner_user_id,
        user_email=user_email,
        username=username,
        avatar=avatar
    )

@app.route('/api/update_caption/<filename>', methods=['POST'])
@login_required
def update_caption(filename):
    """
    Update caption for an SVG image.
    Only the owner can update the caption.
    """
    try:
        data = request.get_json()
        new_caption = data.get('caption', '').strip()
        
        # Validate caption length (max 5000 characters)
        if len(new_caption) > 5000:
            return jsonify({
                'success': False,
                'error': 'Caption quá dài. Tối đa 5000 ký tự.'
            }), 400
        
        # Sanitize input (remove dangerous HTML tags, keep LaTeX)
        import re
        # Remove script tags, iframes, and event handlers
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'on\w+\s*=',  # onclick, onload, etc.
        ]
        for pattern in dangerous_patterns:
            new_caption = re.sub(pattern, '', new_caption, flags=re.IGNORECASE | re.DOTALL)
        
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Check ownership
        cursor.execute("""
            SELECT user_id 
            FROM svg_image 
            WHERE filename = %s
        """, (filename,))
        
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy ảnh.'
            }), 404
        
        if row['user_id'] != current_user.id:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Bạn không có quyền chỉnh sửa caption của ảnh này.'
            }), 403
        
        # Update caption
        cursor.execute("""
            UPDATE svg_image 
            SET caption = %s 
            WHERE filename = %s AND user_id = %s
        """, (new_caption, filename, current_user.id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Caption đã được cập nhật thành công!',
            'caption': new_caption
        })
        
    except Exception as e:
        print(f"[ERROR] update_caption: {e}", flush=True)
        return jsonify({
            'success': False,
            'error': 'Lỗi server. Vui lòng thử lại.'
        }), 500

@app.route('/logout')
def logout():
    print("DEBUG: Logout called")
    logout_user()
    session.clear()
    next_url = request.args.get('next') or url_for('index')
    resp = make_response(redirect(next_url))
    print("DEBUG: About to clear cookies")
    resp.set_cookie('session', '', expires=0)
    resp.set_cookie('remember_token', '', expires=0)
    print("DEBUG: Logout finished, returning response")
    return resp

@app.route('/profile/me')
@login_required
def profile_me_redirect():
    return redirect(url_for('profile_user', user_id=current_user.id))

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile_user(user_id):
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        if is_owner and request.method == 'POST':
            new_username = request.form.get("username", "").strip()
            new_bio = request.form.get("bio", "").strip()
            cursor.execute("UPDATE user SET username=%s, bio=%s WHERE id=%s", (new_username, new_bio, user_id))
            conn.commit()
            flash("Đã cập nhật hồ sơ!", "success")
            # Redirect để reload trang và cập nhật tên mới
            return redirect(url_for('profile_user', user_id=user_id))

        cursor.execute("SELECT id, username, avatar, bio, email FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        # Lấy danh sách SVG với cấu trúc database đúng
        if current_user_id:
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.keywords, 
                    s.created_at,
                    s.user_id,
                    COUNT(sl.id) as like_count,
                    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
                WHERE s.user_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, s.user_id, user_like.id
                ORDER BY s.created_at DESC
            """, (current_user_id, user_id))
        else:
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.keywords, 
                    s.created_at,
                    s.user_id,
                    COUNT(sl.id) as like_count,
                    0 as is_liked_by_current_user
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                WHERE s.user_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, s.user_id
                ORDER BY s.created_at DESC
            """, (user_id,))
        
        svg_rows = cursor.fetchall()

        svg_files = []
        for row in svg_rows:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
            file_size_kb = round(os.path.getsize(filepath) / 1024, 2) if os.path.exists(filepath) else None
            
            like_count = row.get('like_count', 0) or 0
            is_liked = bool(row.get('is_liked_by_current_user', False))
            
            svg_files.append({
                'id': row['id'],
                'filename': row['filename'],
                'url': url_for('static', filename=row['filename']),
                'tikz_code': row['tikz_code'] or '',
                'created_time': format_time_vn(row['created_at']),
                'size': file_size_kb,
                'like_count': like_count,
                'is_liked_by_current_user': is_liked,
                'creator_id': row['user_id']  # ✅ Dùng user_id làm creator_id
            })

        # Follow logic
        is_followed = False
        follower_count = 0
        
        # Luôn tính follower_count bất kể đăng nhập hay không
        cursor.execute("SELECT COUNT(*) as count FROM user_follow WHERE followee_id=%s", (user_id,))
        follower_count = cursor.fetchone()['count']
        
        # Chỉ kiểm tra is_followed nếu đã đăng nhập và không phải owner
        if current_user_id and not is_owner:
            cursor.execute("SELECT 1 FROM user_follow WHERE follower_id=%s AND followee_id=%s", (current_user_id, user_id))
            is_followed = cursor.fetchone() is not None

        # Redirect đến trang profile SVG files (trang chính)
        return redirect(url_for('profile_svg_files', user_id=user_id))
    except Exception as e:
        print(f"❌ General error in profile_user: {e}", flush=True)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        return f"Error: {str(e)}", 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

# ✅ Thêm 3 routes mới cho các trang profile đã tách

@app.route('/profile/<int:user_id>/resend-verification', methods=['POST'])
@login_required
def resend_verification_code(user_id):
    """API endpoint để gửi lại mã xác thực profile settings"""
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)
    
    # Chỉ owner mới có thể resend verification code
    if not is_owner:
        return jsonify({'success': False, 'message': 'Không có quyền truy cập.'}), 403
    
    try:
        # Generate new verification code
        verification_code = str(random.randint(100000, 999999))
        
        # Set expiry time (10 minutes from now)
        expires_at = datetime.now() + timedelta(minutes=10)
        
        # Update database with new code
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user 
            SET profile_verification_code = %s,
                profile_verification_expires_at = %s,
                profile_verification_attempts = 0
            WHERE id = %s
        """, (verification_code, expires_at, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Send verification email
        email_service = get_email_service()
        if not email_service:
            return jsonify({'success': False, 'message': 'Email service không khả dụng.'}), 500
            
        email_sent = email_service.send_profile_settings_verification_email(current_user.email, current_user.username, verification_code)
        
        if email_sent:
            return jsonify({
                'success': True, 
                'message': 'Đã gửi mã xác thực mới đến email của bạn!',
                'expires_at': expires_at.isoformat(),
                'remaining_uses': 5
            })
        else:
            return jsonify({'success': False, 'message': 'Lỗi khi gửi email. Vui lòng thử lại.'}), 500
            
    except Exception as e:
        import traceback
        print(f"❌ Error resending verification: {e}")
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Debug: {str(e)}'}), 500

@app.route('/profile/<int:user_id>/settings', methods=['GET', 'POST'])
def profile_settings(user_id):
    """Trang cài đặt profile - chỉ owner mới có thể truy cập"""
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)
    
    # Chỉ owner mới có thể truy cập trang settings
    if not is_owner:
        return redirect(url_for('profile_user', user_id=user_id))

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            # Kiểm tra xem có phải là hủy bỏ xác thực không
            if request.form.get("cancel_verification"):
                # Xóa thông tin xác thực
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_code = NULL,
                        profile_verification_expires_at = NULL,
                        pending_profile_changes = NULL,
                        profile_verification_attempts = 0,
                        profile_verification_usage_count = 0
                    WHERE id = %s
                """, (user_id,))
                conn.commit()
                flash("Đã hủy bỏ thay đổi đang chờ xác thực.", "info")
                return redirect(url_for('profile_settings', user_id=user_id))
            
            # Kiểm tra xem có phải là xác thực không
            verification_code = request.form.get("verification_code", "").strip()
            
            if verification_code:
                # Xử lý xác thực
                return handle_profile_verification(user_id, verification_code, cursor, conn)
            
            # Xử lý thay đổi profile
            new_username = request.form.get("username", "").strip()
            new_bio = request.form.get("bio", "").strip()
            avatar_file = request.files.get('avatar')
            avatar_cropped_data = request.form.get('avatar_cropped')

            # Lấy thông tin hiện tại để so sánh
            cursor.execute("SELECT username, bio, avatar, email FROM user WHERE id = %s", (user_id,))
            current_data = cursor.fetchone()
            
            # Tạo tóm tắt thay đổi
            new_data = {
                'username': new_username,
                'bio': new_bio,
                'avatar': current_data['avatar']  # Giữ nguyên avatar cũ cho đến khi xác thực
            }
            
            # Kiểm tra thay đổi avatar
            has_avatar_change = bool(avatar_cropped_data and avatar_cropped_data.startswith('data:image'))
            print(f"🔍 DEBUG: has_avatar_change = {has_avatar_change}", flush=True)
            print(f"🔍 DEBUG: avatar_cropped_data exists = {bool(avatar_cropped_data)}", flush=True)
            if avatar_cropped_data:
                print(f"🔍 DEBUG: avatar_cropped_data starts with data:image = {avatar_cropped_data.startswith('data:image')}", flush=True)
            
            changes_summary = get_profile_changes_summary(current_data, new_data, has_avatar_change)
            print(f"🔍 DEBUG: changes_summary = {changes_summary}", flush=True)
            
            # Nếu có thay đổi, gửi email xác thực
            if changes_summary:
                # Kiểm tra xem đã có mã xác thực chưa hết hạn và chưa hết lượt sử dụng chưa
                try:
                    cursor.execute("""
                        SELECT profile_verification_code, profile_verification_expires_at, 
                               profile_verification_usage_count
                        FROM user WHERE id = %s
                    """, (user_id,))
                except Exception as e:
                    # Fallback nếu chưa có field usage_count
                    print(f"⚠️  DEBUG: Field profile_verification_usage_count chưa tồn tại: {e}", flush=True)
                    cursor.execute("""
                        SELECT profile_verification_code, profile_verification_expires_at
                        FROM user WHERE id = %s
                    """, (user_id,))
                existing_verification = cursor.fetchone()
                
                verification_code = None
                expires_at = None
                usage_count = 0
                
                # Kiểm tra có thể tái sử dụng mã hiện tại không
                if (existing_verification and 
                    existing_verification['profile_verification_code'] and
                    existing_verification['profile_verification_expires_at'] and
                    datetime.now() < existing_verification['profile_verification_expires_at'] and
                    (existing_verification.get('profile_verification_usage_count', 0) or 0) < 5):
                    
                    # Tái sử dụng mã hiện tại
                    verification_code = existing_verification['profile_verification_code']
                    expires_at = existing_verification['profile_verification_expires_at']
                    usage_count = existing_verification.get('profile_verification_usage_count', 0) or 0
                    print(f"🔄 DEBUG: Reusing existing code {verification_code}, usage: {usage_count}/5", flush=True)
                    
                    # UX Improvement: Nếu đã từng nhập mã thành công (usage_count > 0)
                    # thì tự động áp dụng thay đổi và tăng usage_count
                    if usage_count > 0:
                        print(f"🚀 DEBUG: Auto-applying changes without form (usage: {usage_count}/5)", flush=True)
                        return handle_auto_profile_update(user_id, new_username, new_bio, avatar_cropped_data, usage_count, cursor, conn)
                else:
                    # Tạo mã xác thực mới
                    verification_code = generate_verification_code(6)
                    expires_at = datetime.now() + timedelta(minutes=10)  # 10 phút thay vì 24 giờ
                    usage_count = 0
                    print(f"🆕 DEBUG: Generated new code {verification_code}", flush=True)
                
                # Lưu thay đổi tạm thời và mã xác thực
                pending_changes = {
                    'username': new_username,
                    'bio': new_bio,
                    'avatar_file': None,
                    'avatar_cropped_data': avatar_cropped_data
                }
                
                try:
                    cursor.execute("""
                        UPDATE user SET 
                            profile_verification_code = %s,
                            profile_verification_expires_at = %s,
                            pending_profile_changes = %s,
                            profile_verification_attempts = 0,
                            profile_verification_usage_count = %s
                        WHERE id = %s
                    """, (verification_code, expires_at, json.dumps(pending_changes), usage_count, user_id))
                except Exception as e:
                    # Fallback nếu chưa có field usage_count
                    print(f"⚠️  DEBUG: Fallback UPDATE without usage_count field: {e}", flush=True)
                    cursor.execute("""
                        UPDATE user SET 
                            profile_verification_code = %s,
                            profile_verification_expires_at = %s,
                            pending_profile_changes = %s,
                            profile_verification_attempts = 0
                        WHERE id = %s
                    """, (verification_code, expires_at, json.dumps(pending_changes), user_id))
                
                conn.commit()
                
                # Gửi email xác thực
                email_service = get_email_service()
                print(f"🔍 DEBUG: Email service = {email_service}", flush=True)
                
                if email_service:
                    print(f"🔍 DEBUG: Sending email to {current_data['email']} with code {verification_code}", flush=True)
                    try:
                        result = email_service.send_profile_settings_verification_email(
                            email=current_data['email'],
                            username=current_data['username'] or 'Người dùng',
                            verification_code=verification_code,
                            changes_summary=changes_summary,
                            user_id=user_id
                        )
                        print(f"🔍 DEBUG: Email send result = {result}", flush=True)
                    except Exception as e:
                        print(f"❌ DEBUG: Email send error = {e}", flush=True)
                        import traceback
                        print(f"❌ DEBUG: Email error traceback = {traceback.format_exc()}", flush=True)
                else:
                    print(f"❌ DEBUG: Email service is None!", flush=True)
                
                flash("Đã gửi mã xác thực đến email của bạn. Vui lòng kiểm tra email và nhập mã để hoàn tất thay đổi.", "success")
                return redirect(url_for('profile_settings', user_id=user_id))
            else:
                flash("Không có thay đổi nào được thực hiện.", "info")
                return redirect(url_for('profile_settings', user_id=user_id))
            
            # Avatar sẽ được xử lý trong hàm xác thực

        cursor.execute("""
            SELECT id, username, avatar, bio, email, 
                   profile_verification_code, profile_verification_expires_at,
                   pending_profile_changes, profile_verification_attempts,
                   profile_verification_usage_count,
                   identity_verified
            FROM user WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        # Kiểm tra xem có thay đổi đang chờ xác thực không
        has_pending_verification = (
            user['profile_verification_code'] is not None and 
            user['profile_verification_expires_at'] is not None and
            datetime.now() < user['profile_verification_expires_at']
        )
        
        # UX Improvement: Chỉ hiện form xác thực khi:
        # 1. Có pending verification VÀ
        # 2. (Chưa từng nhập mã thành công HOẶC đã hết lượt sử dụng >= 5)
        raw_usage_count = user.get('profile_verification_usage_count')
        usage_count = raw_usage_count or 0
        show_verification_form = has_pending_verification and (usage_count == 0 or usage_count >= 5)
        
        # Debug logging (can be removed in production)
        print(f"🔍 DEBUG: show_verification_form={show_verification_form}, usage_count={usage_count}", flush=True)

        return render_template("profile_settings.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            email_verified=True,
            identity_verified=user.get('identity_verified', False),
            is_owner=is_owner,
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None,
            has_pending_verification=has_pending_verification,
            show_verification_form=show_verification_form,
            verification_attempts=user.get('profile_verification_attempts', 0),
            usage_count=usage_count
        )
    except Exception as e:
        print(f"❌ General error in profile_settings: {e}", flush=True)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        return f"Error: {str(e)}", 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

@app.route('/profile/<int:user_id>/svg-files')
def profile_svg_files(user_id):
    """Trang hiển thị các file SVG của user"""
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, username, avatar, bio, email FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        # Lấy danh sách SVG với cấu trúc database đúng
        if current_user_id:
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.keywords, 
                    s.created_at,
                    s.user_id,
                    COUNT(sl.id) as like_count,
                    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
                WHERE s.user_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, s.user_id, user_like.id
                ORDER BY s.created_at DESC
            """, (current_user_id, user_id))
        else:
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.keywords, 
                    s.created_at,
                    s.user_id,
                    COUNT(sl.id) as like_count,
                    0 as is_liked_by_current_user
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                WHERE s.user_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, s.user_id
                ORDER BY s.created_at DESC
            """, (user_id,))
        
        svg_rows = cursor.fetchall()

        svg_files = []
        for row in svg_rows:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
            file_size_kb = round(os.path.getsize(filepath) / 1024, 2) if os.path.exists(filepath) else None
            
            like_count = row.get('like_count', 0) or 0
            is_liked = bool(row.get('is_liked_by_current_user', False))
            
            svg_files.append({
                'id': row['id'],
                'filename': row['filename'],
                'url': url_for('static', filename=row['filename']),
                'tikz_code': row['tikz_code'] or '',
                'created_time': format_time_vn(row['created_at']),
                'size': file_size_kb,
                'like_count': like_count,
                'is_liked_by_current_user': is_liked,
                'creator_id': row['user_id']
            })

        # Follow logic
        is_followed = False
        follower_count = 0
        
        # Luôn tính follower_count bất kể đăng nhập hay không
        cursor.execute("SELECT COUNT(*) as count FROM user_follow WHERE followee_id=%s", (user_id,))
        follower_count = cursor.fetchone()['count']
        
        # Chỉ kiểm tra is_followed nếu đã đăng nhập và không phải owner
        if current_user_id and not is_owner:
            cursor.execute("SELECT 1 FROM user_follow WHERE follower_id=%s AND followee_id=%s", (current_user_id, user_id))
            is_followed = cursor.fetchone() is not None

        return render_template("profile_svg_files.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            email_verified=True,
            svg_files=svg_files,
            is_owner=is_owner,
            is_followed=is_followed,
            follower_count=follower_count,
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None
        )
    except Exception as e:
        print(f"❌ General error in profile_svg_files: {e}", flush=True)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        return f"Error: {str(e)}", 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

@app.route('/profile/<int:user_id>/followed-posts')
@login_required
def profile_followed_posts(user_id):
    """Trang hiển thị bài đăng theo dõi - chỉ owner mới có thể truy cập"""
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)
    
    # Chỉ owner mới có thể truy cập trang followed posts
    if not is_owner:
        return redirect(url_for('profile_user', user_id=user_id))

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, username, avatar, bio, email FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        # =====================================================
        # PHASE 3: PAGINATION FOR FOLLOWED POSTS
        # =====================================================
        # Get pagination parameters (same as index page)
        page, per_page = get_pagination_params(request)
        offset = (page - 1) * per_page
        
        # Fetch followed posts data with pagination
        followed_posts = []
        total_items = 0
        total_pages = 1
        has_prev = False
        has_next = False
        page_numbers = [1]
        
        if is_owner:  # Only fetch for owner
            # Get total count for pagination
            cursor.execute("""
                SELECT COUNT(DISTINCT s.id) as total
                FROM svg_image s
                JOIN user u ON s.user_id = u.id
                JOIN user_follow uf ON u.id = uf.followee_id
                WHERE uf.follower_id = %s
            """, (current_user.id,))
            
            total_items = cursor.fetchone()['total']
            
            # Calculate pagination metadata
            total_pages = max(1, (total_items + per_page - 1) // per_page)
            has_prev = page > 1
            has_next = page < total_pages
            page_numbers = generate_page_numbers(page, total_pages, MAX_PAGES_DISPLAY)
            
            # Fetch paginated data
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.created_at,
                    u.id as creator_id,
                    u.username as creator_username,
                    COUNT(sl.id) as like_count,
                    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
                FROM svg_image s
                JOIN user u ON s.user_id = u.id
                JOIN user_follow uf ON u.id = uf.followee_id
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
                WHERE uf.follower_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.created_at, u.id, u.username, user_like.id
                ORDER BY s.created_at DESC
                LIMIT %s OFFSET %s
            """, (current_user.id, current_user.id, per_page, offset))
            
            for row in cursor.fetchall():
                followed_posts.append({
                    'id': row['id'],
                    'filename': row['filename'],
                    'tikz_code': row['tikz_code'],
                    'url': url_for('static', filename=row['filename']),
                    'creator_id': row['creator_id'],
                    'creator_username': row['creator_username'],
                    'created_time_vn': format_time_vn(row['created_at']) if 'format_time_vn' in globals() else str(row['created_at']),
                    'created_time': str(row['created_at']),
                    'like_count': row['like_count'] or 0,
                    'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
                })

        cursor.close()
        conn.close()
        
        return render_template("profile_followed_posts.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            is_owner=is_owner,
            followed_posts=followed_posts,
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None,
            # Pagination metadata
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_prev=has_prev,
            has_next=has_next,
            page_numbers=page_numbers
        )
    except Exception as e:
        print(f"❌ General error in profile_followed_posts: {e}", flush=True)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        return f"Error: {str(e)}", 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

def get_user_by_email(email):
    """Lấy thông tin user từ database theo email"""
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, avatar FROM user WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return user_data
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None

@app.context_processor
def inject_user_info():
    """Context processor để truyền thông tin user ra mọi template"""
    if current_user.is_authenticated:
        return {
            'current_user_email': current_user.email,
            'current_username': current_user.username,
            'current_avatar': current_user.avatar,
            'current_identity_verified': getattr(current_user, 'identity_verified', False)
        }
    return {
        'current_user_email': None,
        'current_username': None,
        'current_avatar': None,
        'current_identity_verified': False
    }

@app.route('/api/like_counts', methods=['POST'])
@limiter.limit(RATE_LIMITS['api_like_counts'])
def api_like_counts():
    data = request.get_json()
    svg_ids = data.get('ids', [])
    filenames = data.get('filenames', [])
    
    # Hỗ trợ cả ids và filenames
    if not isinstance(svg_ids, list) and not isinstance(filenames, list):
        return jsonify({"error": "Invalid input"}), 400

    # ✅ Trả về cả like count và trạng thái like của user hiện tại
    result = {}
    current_user_id = current_user.id if current_user.is_authenticated else None
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Xử lý filenames nếu có
        if filenames:
            format_strings = ','.join(['%s'] * len(filenames))
            
            # Query để lấy like count theo filename
            cursor.execute(f"""
                SELECT 
                    s.filename,
                    COUNT(sl.id) as like_count
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                WHERE s.filename IN ({format_strings})
                GROUP BY s.filename
            """, tuple(filenames))
            
            for row in cursor.fetchall():
                filename = row['filename']
                result[filename] = {
                    'like_count': row['like_count']
                }
            
            # Đảm bảo trả về cho tất cả filenames, kể cả không có like
            for filename in filenames:
                if filename not in result:
                    result[filename] = {
                        'like_count': 0
                    }
        
        # Xử lý svg_ids nếu có (giữ nguyên logic cũ)
        if svg_ids:
            format_strings = ','.join(['%s'] * len(svg_ids))
            
            # ✅ Query để lấy cả like count và trạng thái like của user hiện tại
            if current_user_id:
                cursor.execute(f"""
                    SELECT 
                        s.id as svg_image_id,
                        COUNT(sl.id) as like_count,
                        CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
                    FROM svg_image s
                    LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                    LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
                    WHERE s.id IN ({format_strings})
                    GROUP BY s.id, user_like.id
                """, (current_user_id,) + tuple(svg_ids))
            else:
                cursor.execute(f"""
                    SELECT 
                        s.id as svg_image_id,
                        COUNT(sl.id) as like_count,
                        0 as is_liked_by_current_user
                    FROM svg_image s
                    LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                    WHERE s.id IN ({format_strings})
                    GROUP BY s.id
                """, tuple(svg_ids))
            
            for row in cursor.fetchall():
                svg_id = str(row['svg_image_id'])
                result[svg_id] = {
                    'like_count': row['like_count'],
                    'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
                }
            
            # ✅ Đảm bảo trả về cho tất cả svg_ids, kể cả không có like
            for svg_id in svg_ids:
                if str(svg_id) not in result:
                    result[str(svg_id)] = {
                        'like_count': 0,
                        'is_liked_by_current_user': False
                    }
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error in api_like_counts: {e}", flush=True)
        return jsonify({"error": "Database error"}), 500

    return jsonify(result)

@app.route('/api/svg/<int:svg_id>/likes', methods=['GET'])
@limiter.limit(RATE_LIMITS['api_general'])
def get_svg_likes(svg_id):
    """
    Lấy danh sách người dùng đã like một SVG file.
    Hỗ trợ pagination.
    """
    try:
        # Parse query params
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))

        # Validate parameters
        if svg_id <= 0:
            return jsonify({"success": False, "message": "Invalid SVG ID"}), 400
        if limit <= 0 or offset < 0:
            return jsonify({"success": False, "message": "Invalid pagination parameters"}), 400

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
            cursor.close()
            conn.close()
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

        # Format datetime và avatar paths cho JSON
        for user in users:
            if user['liked_at']:
                # Convert to VN timezone before sending to client
                liked_at_utc = user['liked_at'].replace(tzinfo=timezone.utc)
                liked_at_vn = liked_at_utc.astimezone(tz_vn)
                user['liked_at'] = liked_at_vn.isoformat()
            if user['avatar']:
                user['avatar'] = f"/static/avatars/{user['avatar']}"

        # Check if there are more results
        has_more = (offset + limit) < total_likes

        cursor.close()
        conn.close()

        print(f"✅ SVG {svg_id} likes: {len(users)} users returned, total: {total_likes}, has_more: {has_more}", flush=True)

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

@app.route('/api/svg/<int:svg_id>/likes/preview', methods=['GET'])
@limiter.limit(RATE_LIMITS['api_likes_preview'])
def get_svg_likes_preview(svg_id):
    """
    Lấy preview danh sách người đã like (3-5 users đầu tiên) để hiển thị text
    Rate Limited: 100/min (dev) or 30/min (prod)
    """
    try:
        # Validate parameters
        if svg_id <= 0:
            return jsonify({"success": False, "message": "Invalid SVG ID"}), 400

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
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "SVG not found"}), 404

        # Get total like count
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM svg_like
            WHERE svg_image_id = %s
        """, (svg_id,))
        total_likes = cursor.fetchone()['total']

        # Get first 3 users who liked (for preview text)
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
            LIMIT 3
        """, (svg_id,))

        users = cursor.fetchall()

        # Format avatar paths cho JSON
        for user in users:
            if user['avatar']:
                user['avatar'] = f"/static/avatars/{user['avatar']}"

        # Check if current user liked this SVG
        current_user_liked = False
        current_user_id = current_user.id if current_user.is_authenticated else None

        if current_user_id:
            cursor.execute("""
                SELECT id FROM svg_like
                WHERE svg_image_id = %s AND user_id = %s
            """, (svg_id, current_user_id))
            current_user_liked = cursor.fetchone() is not None

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "total_likes": total_likes,
            "preview_users": users,
            "current_user_liked": current_user_liked,
            "current_user_id": current_user_id
        })

    except Exception as e:
        print(f"Error in get_svg_likes_preview: {e}", flush=True)
        return jsonify({"success": False, "message": "Server error"}), 500

@app.route('/api/follower_count/<int:user_id>', methods=['GET'])
def api_follower_count(user_id):
    """API endpoint để lấy số follower count của một user"""
    print(f"🔄 API called: /api/follower_count/{user_id}")
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query để lấy số follower count
        cursor.execute("""
            SELECT COUNT(*) as follower_count
            FROM user_follow
            WHERE followee_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        follower_count = result['follower_count'] if result else 0
        
        print(f"🔄 Database result for user {user_id}: {follower_count} followers")
        
        cursor.close()
        conn.close()
        
        response_data = {
            "success": True,
            "follower_count": follower_count
        }
        print(f"🔄 API response: {response_data}")
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in api_follower_count: {e}")
        return jsonify({
            "success": False,
            "error": "Database error"
        }), 500

@app.route('/api/check_login_status')
def api_check_login_status():
    """API để kiểm tra trạng thái đăng nhập hiện tại"""
    return jsonify({
        'logged_in': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None
    })

@app.route('/api/follow_status/<int:user_id>', methods=['GET'])
def api_follow_status(user_id):
    """API endpoint để lấy trạng thái follow của current user với user_id"""
    print(f"🔄 API called: /api/follow_status/{user_id}")
    
    # Kiểm tra đăng nhập
    if not current_user.is_authenticated:
        return jsonify({
            "success": False,
            "error": "Not logged in"
        }), 401
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query để kiểm tra trạng thái follow
        cursor.execute("""
            SELECT COUNT(*) as is_following
            FROM user_follow
            WHERE follower_id = %s AND followee_id = %s
        """, (current_user.id, user_id))
        
        result = cursor.fetchone()
        is_following = result['is_following'] > 0 if result else False
        
        print(f"🔄 Follow status for user {user_id}: {is_following}")
        
        cursor.close()
        conn.close()
        
        response_data = {
            "success": True,
            "is_following": is_following
        }
        print(f"🔄 API response: {response_data}")
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in api_follow_status: {e}")
        return jsonify({
            "success": False,
            "error": "Database error"
        }), 500

@app.route('/compile_with_packages', methods=['POST'])
@login_required
def compile_with_packages():
    """API endpoint để biên dịch TikZ với packages tùy chỉnh"""
    data = request.json
    tikz_code = data.get('tikz_code', '').strip()
    extra_packages = data.get('extra_packages', [])
    extra_tikz_libs = data.get('extra_tikz_libs', [])
    extra_pgfplots_libs = data.get('extra_pgfplots_libs', [])
    
    if not tikz_code:
        return jsonify({"error": "Vui lòng nhập code TikZ!"}), 400
    
    tikz_code = clean_control_chars(tikz_code)
    
    try:
        # Tạo workspace tạm
        now = datetime.now(tz_vn)
        file_id = str(uuid.uuid4())
        work_dir = f"/tmp/{file_id}"
        os.makedirs(work_dir, exist_ok=True)
        tex_path = os.path.join(work_dir, "tikz.tex")
        pdf_path = os.path.join(work_dir, "tikz.pdf")
        svg_path_tmp = os.path.join(work_dir, "tikz.svg")
        
        # Tạo nguồn LaTeX với packages tùy chỉnh
        try:
            latex_source = generate_latex_source(
                tikz_code=tikz_code,
                extra_packages=extra_packages,
                extra_tikz_libs=extra_tikz_libs,
                extra_pgfplots_libs=extra_pgfplots_libs
            )
        except ValueError as e:
            return jsonify({"error": f"Package không hợp lệ: {str(e)}"}), 400
        
        # Ghi file TeX
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)
        
        # Biên dịch
        lualatex_process = subprocess.run([
            "lualatex", "-interaction=nonstopmode", "--output-directory=.", "tikz.tex"
        ],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=True
        )
        
        subprocess.run(["pdf2svg", pdf_path, svg_path_tmp],
                       cwd=work_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Đọc SVG content
        with open(svg_path_tmp, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        return jsonify({
            "success": True,
            "file_id": file_id,
            "svg_url": f"/temp_svg/{file_id}",
            "svg_content": svg_content
        })
        
    except subprocess.CalledProcessError as ex:
        # Xử lý lỗi biên dịch
        log_path = os.path.join(work_dir, "tikz.log")
        error_details = []
        
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as log_file:
                    for line in log_file:
                        if line.startswith("!") or 'error' in line.lower():
                            error_details.append(line.strip())
            except Exception:
                pass
        
        return jsonify({
            "error": "Lỗi khi biên dịch TikZ",
            "details": error_details,
            "stderr": ex.stderr if hasattr(ex, 'stderr') else None
        }), 400
        
    except Exception as e:
        return jsonify({"error": f"Lỗi không xác định: {str(e)}"}), 500

@app.route('/api/available_packages')
def api_available_packages():
    """API endpoint để lấy danh sách packages có sẵn"""
    return jsonify({
        "packages": list(SAFE_PACKAGES),
        "tikz_libraries": list(SAFE_TIKZ_LIBS),
        "pgfplots_libraries": list(SAFE_PGFPLOTS_LIBS)
    })

# ✅ ENHANCED WHITELIST API ENDPOINTS
@app.route('/api/platform-info')
def api_platform_info():
    """Return platform capabilities and security features"""
    return jsonify({
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
        "whitelist_packages": len(SAFE_PACKAGES),
        "tikz_libraries": len(SAFE_TIKZ_LIBS), 
        "pgfplots_libraries": len(SAFE_PGFPLOTS_LIBS),
        "security_level": "high",
        "features": {
            "timeout_protection": True,
            "memory_monitoring": True,
            "pattern_validation": True,
            "concurrent_limits": True,
            "error_classification": True,
            "security_logging": True
        }
    })

@app.route('/api/system-status')
def api_system_status():
    """Return system status and performance metrics"""
    
    with compilation_manager.lock:
        active_compilations = compilation_manager.active_count
        max_concurrent = compilation_manager.max_concurrent
    
    # Get system metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
    except:
        cpu_percent = 0
        memory = None
        disk = None
    
    system_health = "healthy"
    if cpu_percent > 90 or (memory and memory.percent > 90):
        system_health = "critical"
    elif cpu_percent > 70 or (memory and memory.percent > 70):
        system_health = "degraded"
    
    return jsonify({
        "status": system_health,
        "timestamp": time.time(),
        "compilation": {
            "active_count": active_compilations,
            "max_concurrent": max_concurrent,
            "available_slots": max_concurrent - active_compilations,
            "queue_status": "available" if active_compilations < max_concurrent else "full"
        },
        "security": {
            "patterns_active": len(LaTeXSecurityValidator.DANGEROUS_PATTERNS),
            "logging_enabled": True,
            "validation_enabled": True
        },
        "system": {
            "cpu_percent": cpu_percent if cpu_percent else 0,
            "memory_percent": memory.percent if memory else 0,
            "disk_percent": disk.percent if disk else 0,
            "load_level": "high" if cpu_percent > 80 else "medium" if cpu_percent > 50 else "low"
        },
        "limits": {
            "timeout_seconds": CompilationLimits.TIMEOUT_SECONDS,
            "max_memory_mb": CompilationLimits.MAX_MEMORY_MB,
            "max_concurrent": CompilationLimits.MAX_CONCURRENT
        }
    })

@app.route('/api/security-events/recent')
def api_recent_security_events():
    """Return recent security events (last 24h)"""
    try:
        # Read recent security log entries
        events = []
        log_file = 'tikz_security.log'
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Get last 50 events
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            
            for line in recent_lines:
                if line.strip():
                    events.append({
                        'timestamp': time.time(),
                        'event': line.strip(),
                        'severity': 'medium'
                    })
        
        return jsonify({
            "events": events[-10:],  # Last 10 events
            "total_events_24h": len(events),
            "log_file_exists": os.path.exists(log_file)
        })
        
    except Exception as e:
        return jsonify({
            "events": [],
            "error": f"Could not read security events: {str(e)}"
        })

# ✅ PHASE 2: ADVANCED MONITORING API ENDPOINTS

@app.route('/api/adaptive-limits')
def api_adaptive_limits():
    """Get current adaptive limits for user/system"""
    
    # Get user context
    user_id = str(current_user.id) if current_user.is_authenticated else "anonymous"
    
    # Get adaptive limits
    limits = adaptive_limits.get_adaptive_limits(user_id)
    
    return jsonify({
        "user_id": user_id,
        "adaptive_limits": limits,
        "timestamp": time.time(),
        "explanation": {
            "user_tier": f"User tier '{limits['user_tier']}' provides {limits['multiplier_applied']:.2f}x resource multiplier",
            "system_load": f"System load '{limits['system_load']}' affects resource allocation",
            "timeout_range": "15-120 seconds based on conditions",
            "memory_range": "100-1000 MB based on conditions",
            "concurrent_range": "1-10 based on system load"
        }
    })

@app.route('/api/cache-stats')
def api_cache_stats():
    """Get compilation cache statistics"""
    
    cache_stats = compilation_cache.get_stats()
    
    return jsonify({
        "cache_statistics": cache_stats,
        "timestamp": time.time(),
        "performance_analysis": {
            "efficiency": "excellent" if cache_stats['hit_rate_percent'] > 70 else 
                         "good" if cache_stats['hit_rate_percent'] > 40 else 
                         "needs_improvement",
            "memory_usage": f"{cache_stats['size_mb']}/{cache_stats['max_size_mb']} MB ({(cache_stats['size_mb']/cache_stats['max_size_mb']*100):.1f}%)",
            "recommendations": [
                "Cache is working effectively" if cache_stats['hit_rate_percent'] > 50 else "Consider clearing cache or adjusting size",
                f"Total requests: {cache_stats['total_requests']}" if cache_stats['total_requests'] > 0 else "No cache usage yet"
            ]
        }
    })

@app.route('/api/admin/dashboard-metrics')
def api_dashboard_metrics():
    """Comprehensive dashboard metrics for administrators"""
    
    # Get compilation metrics
    with compilation_manager.lock:
        compilation_metrics = {
            "active_compilations": compilation_manager.active_count,
            "max_concurrent": compilation_manager.max_concurrent,
            "queue_length": len(compilation_manager.compilation_queue),
            "available_slots": compilation_manager.max_concurrent - compilation_manager.active_count
        }
    
    # Get system metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "system_health": "healthy" if cpu_percent < 70 and memory.percent < 80 else 
                           "degraded" if cpu_percent < 90 and memory.percent < 90 else "critical"
        }
    except:
        system_metrics = {"error": "Could not retrieve system metrics"}
    
    # Get cache metrics
    cache_stats = compilation_cache.get_stats()
    
    # Get security metrics
    security_metrics = {
        "patterns_active": len(LaTeXSecurityValidator.DANGEROUS_PATTERNS),
        "logging_enabled": True,
        "validation_enabled": True
    }
    
    # Recent security events count
    try:
        with open('tikz_security.log', 'r') as f:
            recent_events = len(f.readlines())
    except:
        recent_events = 0
    
    security_metrics["total_security_events"] = recent_events
    
    # Get adaptive limits for anonymous user (system baseline)
    baseline_limits = adaptive_limits.get_adaptive_limits("anonymous")
    
    return jsonify({
        "dashboard_data": {
            "compilation": compilation_metrics,
            "system": system_metrics,
            "cache": cache_stats,
            "security": security_metrics,
            "adaptive_limits": {
                "baseline": baseline_limits,
                "current_system_load": baseline_limits['system_load']
            }
        },
        "alerts": [
            {"level": "warning", "message": "High system load detected"} if system_metrics.get('cpu_percent', 0) > 80 else None,
            {"level": "info", "message": f"Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%"} if cache_stats['total_requests'] > 0 else None,
            {"level": "success", "message": f"{security_metrics['patterns_active']} security patterns active"}
        ],
        "timestamp": time.time(),
        "uptime_info": {
            "platform": "Enhanced Whitelist + Resource Limits v2.0",
            "features_active": ["Security Validation", "Adaptive Limits", "Compilation Caching", "Real-time Monitoring"]
        }
    })

@app.route('/api/admin/cache-control', methods=['POST'])
def api_cache_control():
    """Cache management endpoint"""
    
    data = request.get_json() or {}
    action = data.get('action', '')
    
    if action == 'clear':
        compilation_cache.clear()
        return jsonify({
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": time.time()
        })
    
    elif action == 'stats':
        return jsonify({
            "success": True,
            "stats": compilation_cache.get_stats(),
            "timestamp": time.time()
        })
    
    else:
        return jsonify({
            "success": False,
            "error": "Invalid action. Use 'clear' or 'stats'",
            "available_actions": ["clear", "stats"]
        }), 400

# ✅ EMAIL SYSTEM ROUTES
def create_hosted_logo():
    """Tạo logo PNG được host trên server"""
    try:
        # Kiểm tra xem logo đã tồn tại chưa
        logo_path = os.path.join(STATIC_ROOT, 'images', 'email_logo.png')
        if os.path.exists(logo_path):
            print(f"✅ Logo đã tồn tại: {logo_path}")
            return True
        
        # Đọc SVG
        svg_path = os.path.join(STATIC_ROOT, 'logo.svg')
        if not os.path.exists(svg_path):
            print(f"❌ Không tìm thấy file SVG: {svg_path}")
            return False
            
        with open(svg_path, 'r') as f:
            svg_content = f.read()
        
        # Chuyển đổi SVG thành PNG với kích thước lớn hơn
        png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), output_width=120, output_height=120)
        
        # Lưu PNG vào static/images
        with open(logo_path, 'wb') as f:
            f.write(png_data)
        
        print(f"✅ Logo PNG created: {len(png_data)} bytes -> {logo_path}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi tạo logo: {e}")
        return False

def send_email(to_email, subject, html_content):
    """Gửi email"""
    try:
        smtp_server = os.getenv('ZOHO_SMTP_SERVER', 'smtp.zoho.com')
        smtp_port = int(os.getenv('ZOHO_SMTP_PORT', '587'))
        email = os.getenv('ZOHO_EMAIL', 'support@tikz2svg.com')
        password = os.getenv('ZOHO_APP_PASSWORD')
        
        if not password:
            return False, "Thiếu ZOHO_APP_PASSWORD trong .env"
        
        # Đảm bảo encoding đúng cho subject và content
        try:
            # Encode subject nếu cần
            if isinstance(subject, str):
                subject = subject.encode('utf-8').decode('utf-8')
            
            # Encode HTML content nếu cần
            if isinstance(html_content, str):
                html_content = html_content.encode('utf-8').decode('utf-8')
        except UnicodeError as ue:
            print(f"Unicode encoding error: {ue}", flush=True)
            # Fallback: encode as utf-8
            subject = subject.encode('utf-8', errors='ignore').decode('utf-8')
            html_content = html_content.encode('utf-8', errors='ignore').decode('utf-8')
        
        msg = MIMEMultipart('alternative')
        
        # Encode subject an toàn
        try:
            msg['Subject'] = subject
        except UnicodeEncodeError:
            safe_subject = subject.encode('utf-8', errors='ignore').decode('utf-8')
            msg['Subject'] = safe_subject
        
        msg['From'] = email
        msg['To'] = to_email
        
        # Sử dụng encoding rõ ràng và đảm bảo content an toàn
        try:
            html_part = MIMEText(html_content, 'html', 'utf-8')
        except UnicodeEncodeError:
            # Fallback: encode content trước khi tạo MIMEText
            safe_html_content = html_content.encode('utf-8', errors='ignore').decode('utf-8')
            html_part = MIMEText(safe_html_content, 'html', 'utf-8')
        
        msg.attach(html_part)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email, password)
        
        # Encode message string với UTF-8
        message_string = msg.as_string()
        try:
            # Thử encode với UTF-8
            message_bytes = message_string.encode('utf-8')
            server.sendmail(email, to_email, message_bytes)
        except UnicodeEncodeError:
            # Fallback: encode với ascii và ignore errors
            message_bytes = message_string.encode('ascii', errors='ignore')
            server.sendmail(email, to_email, message_bytes)
        server.quit()
        
        return True, "Email đã được gửi thành công!"
    except Exception as e:
        print(f"Email send error: {e}", flush=True)
        import traceback
        print(f"Email error traceback: {traceback.format_exc()}", flush=True)
        return False, f"Lỗi: {str(e)}"

@app.route('/static/images/<path:filename>')
def serve_logo(filename):
    """Serve logo files"""
    return send_from_directory(os.path.join(STATIC_ROOT, 'images'), filename)

@app.route('/email-test')
@login_required
def email_test_page():
    """Trang test email cho admin với xác thực mã"""
    # Kiểm tra mã xác thực từ session
    if not session.get('email_test_verified'):
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Xác thực - Test Email System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
                input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; text-align: center; letter-spacing: 2px; }
                button { background: #e74c3c; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }
                button:hover { background: #c0392b; }
                .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin-bottom: 20px; display: none; }
                .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Xác thực Truy cập</h1>
                    <p>Nhập mã xác thực để truy cập Email Test System</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Cảnh báo:</strong> Đây là trang quản trị nội bộ. Chỉ admin mới được phép truy cập.
                </div>
                
                <div class="error" id="error">
                    <strong>❌ Mã xác thực không đúng!</strong>
                </div>
                
                <form id="authForm">
                    <div class="form-group">
                        <label for="authCode">Mã xác thực:</label>
                        <input type="text" id="authCode" name="authCode" required placeholder="Nhập mã 6 chữ số" maxlength="6" pattern="[0-9]{6}">
                    </div>
                    
                    <button type="submit">🔓 Xác thực & Truy cập</button>
                </form>
            </div>
            
            <script>
                document.getElementById('authForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const authCode = document.getElementById('authCode').value;
                    const error = document.getElementById('error');
                    
                    if (authCode === '964454') {
                        // Gửi request để set session
                        try {
                            const response = await fetch('/api/verify-email-test', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ authCode: authCode })
                            });
                            
                            if (response.ok) {
                                window.location.reload();
                            } else {
                                error.style.display = 'block';
                            }
                        } catch (error) {
                            error.style.display = 'block';
                        }
                    } else {
                        error.style.display = 'block';
                        document.getElementById('authCode').value = '';
                        document.getElementById('authCode').focus();
                    }
                });
                
                // Auto-focus vào input
                document.getElementById('authCode').focus();
            </script>
        </body>
        </html>
        ''')
    
    # Nếu đã xác thực, hiển thị trang email test
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Email System - TikZ2SVG</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
            input, select, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
            button { background: #0984e3; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #74b9ff; }
            .result { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .loading { display: none; text-align: center; color: #666; }
            .logo-preview { text-align: center; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .logo-preview img { width: 60px; height: 60px; border-radius: 8px; }
            .logout-btn { background: #e74c3c; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; float: right; }
            .logout-btn:hover { background: #c0392b; }
            .status-bar { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <button class="logout-btn" onclick="logout()">🚪 Thoát</button>
                <h1>📧 Test Email System</h1>
                <p>Gửi email test với logo TikZ2SVG (hosted trên server)</p>
            </div>
            
            <div class="status-bar">
                <strong>✅ Đã xác thực:</strong> Bạn đã nhập đúng mã xác thực và được phép truy cập.
            </div>
            
            <div class="logo-preview">
                <h3>🎨 Logo Preview (Production):</h3>
                <img src="https://tikz2svg.com/static/images/email_logo.png" alt="TikZ2SVG Logo" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" style="width: 60px; height: 60px;">
                <p style="display:none; color: #999;">Logo sẽ được tải từ production server</p>
                <p>Logo được host trên production server: <code>https://tikz2svg.com/static/images/email_logo.png</code></p>
            </div>
            
            <form id="emailForm">
                <div class="form-group">
                    <label for="email">Email nhận:</label>
                    <input type="email" id="email" name="email" required placeholder="your@email.com">
                </div>
                
                <div class="form-group">
                    <label for="template">Loại email:</label>
                    <select id="template" name="template">
                        <option value="welcome">Welcome Email</option>
                        <option value="verification">Verification Email</option>
                        <option value="svg_verification">SVG Verification Email</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="username">Tên người dùng:</label>
                    <input type="text" id="username" name="username" placeholder="Tên người dùng">
                </div>
                
                <button type="submit">🚀 Gửi Email Test</button>
            </form>
            
            <div class="loading" id="loading">
                <p>⏳ Đang gửi email...</p>
            </div>
            
            <div class="result" id="result" style="display: none;"></div>
        </div>
        
        <script>
            function logout() {
                fetch('/api/logout-email-test', { method: 'POST' })
                    .then(() => window.location.reload());
            }
            
            document.getElementById('emailForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                
                loading.style.display = 'block';
                result.style.display = 'none';
                
                const formData = new FormData(this);
                
                try {
                    const response = await fetch('/api/send-test-email', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    result.className = 'result ' + (data.success ? 'success' : 'error');
                    result.innerHTML = '<strong>' + (data.success ? '✅' : '❌') + '</strong> ' + data.message;
                    result.style.display = 'block';
                } catch (error) {
                    result.className = 'result error';
                    result.innerHTML = '<strong>❌</strong> Lỗi kết nối: ' + error.message;
                    result.style.display = 'block';
                } finally {
                    loading.style.display = 'none';
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/api/verify-email-test', methods=['POST'])
@login_required
def verify_email_test():
    """Xác thực mã để truy cập email test"""
    try:
        data = request.get_json()
        auth_code = data.get('authCode')
        
        if auth_code == '964454':
            session['email_test_verified'] = True
            return jsonify({'success': True, 'message': 'Xác thực thành công'})
        else:
            return jsonify({'success': False, 'message': 'Mã xác thực không đúng'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/logout-email-test', methods=['POST'])
@login_required
def logout_email_test():
    """Đăng xuất khỏi email test"""
    session.pop('email_test_verified', None)
    return jsonify({'success': True, 'message': 'Đã đăng xuất'})

@app.route('/api/send-test-email', methods=['POST'])
@login_required
def send_test_email_api():
    """API gửi email test - yêu cầu xác thực"""
    # Kiểm tra xác thực email test
    if not session.get('email_test_verified'):
        return jsonify({'success': False, 'message': 'Chưa xác thực truy cập email test'}), 403
    try:
        email = request.form.get('email')
        template = request.form.get('template', 'welcome')
        username = request.form.get('username', 'User')
        
        if not email:
            return jsonify({'success': False, 'message': 'Thiếu email'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            if not create_hosted_logo():
                return jsonify({'success': False, 'message': 'Không thể tạo logo'})
        
        # Sử dụng email service thay vì hàm send_email cũ
        email_service = get_email_service()
        if not email_service:
            return jsonify({'success': False, 'message': 'Email service không khả dụng'})
        
        try:
            # Bypass rate limit cho email-test page
            bypass_rate_limit = True
            
            if template == 'welcome':
                success = email_service.send_email(email, 'welcome', context={'username': username, 'email': email}, bypass_rate_limit=bypass_rate_limit)
                message = "Email chào mừng đã được gửi thành công!" if success else "Không thể gửi email chào mừng"
            elif template == 'verification':
                verification_code = "123456"  # Trong thực tế sẽ tạo ngẫu nhiên
                success = email_service.send_email(email, 'account_verification', context={'username': username, 'email': email, 'verification_code': verification_code}, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực đã được gửi thành công!" if success else "Không thể gửi email xác thực"
            elif template == 'account_verification':
                verification_code = "123456"  # Trong thực tế sẽ tạo ngẫu nhiên
                success = email_service.send_email(email, 'account_verification', context={'username': username, 'email': email, 'verification_code': verification_code}, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực tài khoản đã được gửi thành công!" if success else "Không thể gửi email xác thực tài khoản"
            else:  # svg_verification
                success = email_service.send_email(email, 'svg_verification', context={
                    'username': username, 
                    'email': email, 
                    'verification_code': '123456', 
                    'svg_name': 'test.svg',
                    'svg_width': 800,
                    'svg_height': 600,
                    'svg_size': 2048,
                    'daily_limit': 10,
                    'verification_url': f"{os.environ.get('APP_URL', 'https://yourdomain.com')}/svg/verification"
                }, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực SVG đã được gửi thành công!" if success else "Không thể gửi email xác thực SVG"
            
            return jsonify({'success': success, 'message': message})
        except Exception as e:
            print(f"Email service error: {e}", flush=True)
            return jsonify({'success': False, 'message': f'Lỗi email service: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/send-welcome-email', methods=['POST'])
def send_welcome_email_api():
    """API gửi email chào mừng cho user mới"""
    try:
        data = request.json
        email = data.get('email')
        username = data.get('username', 'User')
        
        if not email:
            return jsonify({'success': False, 'message': 'Thiếu email'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            create_hosted_logo()
        
        subject = f"Chào mừng bạn đến với TikZ2SVG, {username}!"
        html_content = create_welcome_email(username)
        
        success, message = send_email(email, subject, html_content)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/test-email-direct', methods=['POST'])
def test_email_direct_api():
    """API test email trực tiếp - không cần authentication"""
    try:
        data = request.json or request.form
        email = data.get('email')
        template = data.get('template', 'welcome')
        username = data.get('username', 'User')
        
        if not email:
            return jsonify({'success': False, 'message': 'Thiếu email'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            if not create_hosted_logo():
                return jsonify({'success': False, 'message': 'Không thể tạo logo'})
        
        # Sử dụng email service với bypass rate limit
        email_service = get_email_service()
        if not email_service:
            return jsonify({'success': False, 'message': 'Email service không khả dụng'})
        
        try:
            # Bypass rate limit cho test
            bypass_rate_limit = True
            
            if template == 'welcome':
                success = email_service.send_email(email, 'welcome', context={'username': username, 'email': email}, bypass_rate_limit=bypass_rate_limit)
                message = "Email chào mừng đã được gửi thành công!" if success else "Không thể gửi email chào mừng"
            elif template == 'account_verification':
                verification_code = "123456"  # Test code
                success = email_service.send_email(email, 'account_verification', context={'username': username, 'email': email, 'verification_code': verification_code}, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực tài khoản đã được gửi thành công!" if success else "Không thể gửi email xác thực tài khoản"
            elif template == 'notification':
                success = email_service.send_email(email, 'notification', context={'title': 'Test Notification', 'message': f'Đây là email test cho {username}'}, bypass_rate_limit=bypass_rate_limit)
                message = "Email thông báo đã được gửi thành công!" if success else "Không thể gửi email thông báo"
            elif template == 'svg_verification':
                success = email_service.send_email(email, 'svg_verification', context={
                    'username': username, 
                    'email': email, 
                    'verification_code': '123456', 
                    'svg_name': 'test.svg',
                    'svg_width': 800,
                    'svg_height': 600,
                    'svg_size': 2048,
                    'daily_limit': 10,
                    'verification_url': f"{os.environ.get('APP_URL', 'https://yourdomain.com')}/svg/verification"
                }, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực SVG đã được gửi thành công!" if success else "Không thể gửi email xác thực SVG"
            else:
                return jsonify({'success': False, 'message': f'Template {template} không được hỗ trợ'})
            
            return jsonify({'success': success, 'message': message})
        except Exception as e:
            print(f"Email service error: {e}", flush=True)
            return jsonify({'success': False, 'message': f'Lỗi email service: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/send-verification-email', methods=['POST'])
def send_verification_email_api():
    """API gửi email xác thực tài khoản"""
    try:
        data = request.json
        email = data.get('email')
        username = data.get('username', 'User')
        verification_code = data.get('verification_code')
        
        if not email or not verification_code:
            return jsonify({'success': False, 'message': 'Thiếu email hoặc mã xác thực'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            create_hosted_logo()
        
        subject = f"Xác thực tài khoản - TikZ2SVG"
        html_content = create_verification_email(username, verification_code)
        
        success, message = send_email(email, subject, html_content)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/send-svg-verification-email', methods=['POST'])
def send_svg_verification_email_api():
    """API gửi email xác thực khi lưu nhiều SVG"""
    try:
        data = request.json
        email = data.get('email')
        username = data.get('username', 'User')
        svg_count = data.get('svg_count', 10)
        
        if not email:
            return jsonify({'success': False, 'message': 'Thiếu email'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            create_hosted_logo()
        
        subject = f"Xác thực lưu SVG - TikZ2SVG"
        html_content = create_svg_verification_email(username, svg_count)
        
        success, message = send_email(email, subject, html_content)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

def create_welcome_email(username):
    """Tạo email chào mừng với hosted logo"""
    # Đảm bảo username được encode đúng
    safe_username = str(username).encode('utf-8', errors='ignore').decode('utf-8')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Chào mừng đến với TikZ2SVG</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-radius: 10px;">
            <div style="display: inline-block; background: white; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                <img src="https://tikz2svg.com/static/images/email_logo.png" alt="TikZ2SVG Logo" style="width: 60px; height: 60px;">
            </div>
            <h1 style="color: white; margin: 0; font-size: 24px;">TikZ2SVG</h1>
            <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Chuyển đổi TikZ thành SVG</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #333; margin-top: 0;">🎉 Chào mừng {safe_username}!</h2>
            <p style="color: #666; line-height: 1.6;">
                Cảm ơn bạn đã đăng ký sử dụng TikZ2SVG. Chúng tôi rất vui mừng chào đón bạn!
            </p>
            <p style="color: #666; line-height: 1.6;">
                Với TikZ2SVG, bạn có thể dễ dàng chuyển đổi các file TikZ thành SVG một cách nhanh chóng và chính xác.
            </p>
        </div>
        
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #1976d2; margin-top: 0;">🚀 Bắt đầu ngay:</h3>
            <ul style="color: #666; line-height: 1.6;">
                <li>Tải lên file TikZ của bạn</li>
                <li>Chọn định dạng SVG mong muốn</li>
                <li>Tải xuống kết quả ngay lập tức</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© 2024 TikZ2SVG. All rights reserved.</p>
            <p>Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    '''

def create_verification_email(username, verification_code):
    """Tạo email xác thực với hosted logo"""
    # Đảm bảo username được encode đúng
    safe_username = str(username).encode('utf-8', errors='ignore').decode('utf-8')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Xác thực tài khoản - TikZ2SVG</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-radius: 10px;">
            <div style="display: inline-block; background: white; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                <img src="https://tikz2svg.com/static/images/email_logo.png" alt="TikZ2SVG Logo" style="width: 60px; height: 60px;">
            </div>
            <h1 style="color: white; margin: 0; font-size: 24px;">TikZ2SVG</h1>
            <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Xác thực tài khoản</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #333; margin-top: 0;">🔐 Xác thực tài khoản</h2>
            <p style="color: #666; line-height: 1.6;">
                Xin chào {safe_username}, vui lòng sử dụng mã xác thực sau để hoàn tất việc đăng ký tài khoản:
            </p>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <h3 style="color: #856404; margin-top: 0;">Mã xác thực:</h3>
                <div style="font-size: 32px; font-weight: bold; color: #856404; letter-spacing: 5px; font-family: monospace;">
                    {verification_code}
                </div>
            </div>
            
            <p style="color: #666; margin-top: 15px; font-size: 14px;">Mã này có hiệu lực trong 24 giờ</p>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h4 style="color: #856404; margin-top: 0;">⚠️ Lưu ý bảo mật:</h4>
            <ul style="color: #856404; margin: 0; padding-left: 20px;">
                <li>Không chia sẻ mã này với bất kỳ ai</li>
                <li>Mã chỉ có hiệu lực trong 24 giờ</li>
                <li>Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© 2024 TikZ2SVG. All rights reserved.</p>
            <p>Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    '''

def create_svg_verification_email(username, svg_count):
    """Tạo email xác thực khi lưu nhiều SVG"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Xác thực lưu SVG - TikZ2SVG</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-radius: 10px;">
            <div style="display: inline-block; background: white; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                <img src="https://tikz2svg.com/static/images/email_logo.png" alt="TikZ2SVG Logo" style="width: 60px; height: 60px;">
            </div>
            <h1 style="color: white; margin: 0; font-size: 24px;">TikZ2SVG</h1>
            <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Xác thực lưu SVG</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #333; margin-top: 0;">📊 Thông báo lưu SVG</h2>
            <p style="color: #666; line-height: 1.6;">
                Xin chào {username}, chúng tôi nhận thấy bạn đã lưu {svg_count} file SVG trong ngày hôm nay.
            </p>
            <p style="color: #666; line-height: 1.6;">
                Đây là một thông báo xác thực để đảm bảo tài khoản của bạn an toàn.
            </p>
        </div>
        
        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h3 style="color: #2e7d32; margin-top: 0;">✅ Hoạt động bình thường</h3>
            <p style="color: #2e7d32; line-height: 1.6;">
                Nếu đây là bạn, không cần thực hiện thêm hành động nào.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© 2024 TikZ2SVG. All rights reserved.</p>
            <p>Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    '''

def generate_verification_code(length=6):
    """Tạo mã xác thực ngẫu nhiên"""
    return ''.join(random.choices(string.digits, k=length))

def handle_auto_profile_update(user_id, new_username, new_bio, avatar_cropped_data, current_usage_count, cursor, conn):
    """
    Tự động áp dụng thay đổi profile khi user đã từng nhập mã thành công
    Không cần hiện form xác thực, chỉ tăng usage_count
    """
    try:
        # Tăng usage count
        new_usage_count = current_usage_count + 1
        
        # Cập nhật profile trực tiếp
        cursor.execute("UPDATE user SET username = %s, bio = %s WHERE id = %s", 
                      (new_username, new_bio, user_id))
        
        # Xử lý avatar nếu có
        if avatar_cropped_data and avatar_cropped_data.startswith('data:image'):
            try:
                # Extract image data
                header, b64_data = avatar_cropped_data.split(',', 1)
                image_format = header.split('/')[1].split(';')[0]  # Extract format (jpeg, png, etc.)
                
                # Validate format
                allowed_formats = ['jpeg', 'jpg', 'png', 'gif', 'webp']
                if image_format.lower() not in allowed_formats:
                    flash("❌ Định dạng ảnh không được hỗ trợ.", "error")
                    return redirect(url_for('profile_settings', user_id=user_id))
                
                ext = 'jpg' if image_format.lower() == 'jpeg' else image_format.lower()
                
                # Get current avatar to delete old file
                cursor.execute("SELECT avatar FROM user WHERE id = %s", (user_id,))
                current_avatar = cursor.fetchone()
                if current_avatar and current_avatar['avatar']:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', current_avatar['avatar'])
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            print(f"[WARN] Không thể xóa avatar cũ: {e}", flush=True)
                
                # Tạo tên file random
                unique_id = uuid.uuid4().hex
                filename = f"avatar_{unique_id}.{ext}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', filename)
                
                # Decode và lưu
                with open(save_path, 'wb') as f:
                    f.write(base64.b64decode(b64_data))
                
                # Update DB
                cursor.execute("UPDATE user SET avatar = %s WHERE id = %s", (filename, user_id))
            except Exception as e:
                print(f"[WARN] Error saving cropped avatar: {e}", flush=True)
                flash("Có lỗi khi lưu ảnh đại diện đã cắt.", "error")
        
        # Cập nhật usage count
        if new_usage_count >= 5:
            # Đã hết lượt sử dụng - xóa thông tin xác thực
            try:
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_code = NULL,
                        profile_verification_expires_at = NULL,
                        pending_profile_changes = NULL,
                        profile_verification_attempts = 0,
                        profile_verification_usage_count = 0
                    WHERE id = %s
                """, (user_id,))
                flash("✅ Hồ sơ đã được cập nhật thành công! Mã xác thực đã hết lượt sử dụng.", "success")
            except Exception as e:
                print(f"⚠️  DEBUG: Fallback final cleanup: {e}", flush=True)
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_code = NULL,
                        profile_verification_expires_at = NULL,
                        pending_profile_changes = NULL,
                        profile_verification_attempts = 0
                    WHERE id = %s
                """, (user_id,))
                flash("✅ Hồ sơ đã được cập nhật thành công!", "success")
        else:
            # Còn lượt sử dụng - tăng usage count và xóa pending changes
            try:
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_usage_count = %s,
                        pending_profile_changes = NULL
                    WHERE id = %s
                """, (new_usage_count, user_id))
                remaining_uses = 5 - new_usage_count
                flash(f"✅ Hồ sơ đã được cập nhật thành công! Mã xác thực còn {remaining_uses} lượt sử dụng.", "success")
            except Exception as e:
                print(f"⚠️  DEBUG: Fallback usage count update: {e}", flush=True)
                # Fallback: xóa luôn như cũ
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_code = NULL,
                        profile_verification_expires_at = NULL,
                        pending_profile_changes = NULL,
                        profile_verification_attempts = 0
                    WHERE id = %s
                """, (user_id,))
                flash("✅ Hồ sơ đã được cập nhật thành công!", "success")
        
        conn.commit()
        return redirect(url_for('profile_settings', user_id=user_id))
        
    except Exception as e:
        print(f"❌ Error in handle_auto_profile_update: {e}", flush=True)
        flash("Có lỗi xảy ra khi cập nhật hồ sơ.", "error")
        return redirect(url_for('profile_settings', user_id=user_id))

def get_profile_changes_summary(old_data, new_data, has_avatar_change=False):
    """Tạo tóm tắt thay đổi profile"""
    changes = []
    
    if old_data.get('username') != new_data.get('username'):
        changes.append(f"Tên hiển thị: '{old_data.get('username', '')}' → '{new_data.get('username', '')}'")
    
    if old_data.get('bio') != new_data.get('bio'):
        old_bio = old_data.get('bio', '') or 'Không có'
        new_bio = new_data.get('bio', '') or 'Không có'
        if len(new_bio) > 50:
            new_bio = new_bio[:50] + '...'
        changes.append(f"Mô tả: '{old_bio}' → '{new_bio}'")
    
    # Kiểm tra thay đổi avatar - ưu tiên has_avatar_change nếu được truyền vào
    print(f"🔍 DEBUG: Checking avatar change - has_avatar_change={has_avatar_change}, old_avatar={old_data.get('avatar')}, new_avatar={new_data.get('avatar')}", flush=True)
    if has_avatar_change or old_data.get('avatar') != new_data.get('avatar'):
        print(f"🔍 DEBUG: Avatar change detected!", flush=True)
        if has_avatar_change or new_data.get('avatar'):
            changes.append("Ảnh đại diện: Thay đổi")
        else:
            changes.append("Ảnh đại diện: Xóa")
    
    return changes

def handle_profile_verification(user_id, verification_code, cursor, conn):
    """Xử lý xác thực thay đổi profile"""
    try:
        # Kiểm tra mã xác thực
        try:
            cursor.execute("""
                SELECT profile_verification_code, profile_verification_expires_at, 
                       pending_profile_changes, profile_verification_attempts,
                       profile_verification_usage_count
                FROM user WHERE id = %s
            """, (user_id,))
        except Exception as e:
            # Fallback nếu chưa có field usage_count
            print(f"⚠️  DEBUG: Field profile_verification_usage_count chưa tồn tại: {e}", flush=True)
            cursor.execute("""
                SELECT profile_verification_code, profile_verification_expires_at, 
                       pending_profile_changes, profile_verification_attempts
                FROM user WHERE id = %s
            """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            flash("Không tìm thấy thông tin xác thực.", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        stored_code = result['profile_verification_code']
        expires_at = result['profile_verification_expires_at']
        pending_changes = json.loads(result['pending_profile_changes']) if result['pending_profile_changes'] else {}
        attempts = result['profile_verification_attempts']
        usage_count = result.get('profile_verification_usage_count', 0) or 0
        
        # Kiểm tra đã hết lượt sử dụng chưa (chỉ khi có field usage_count)
        if 'profile_verification_usage_count' in result and usage_count >= 5:
            # Xóa thông tin xác thực khi hết lượt
            try:
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_code = NULL,
                        profile_verification_expires_at = NULL,
                        pending_profile_changes = NULL,
                        profile_verification_attempts = 0,
                        profile_verification_usage_count = 0
                    WHERE id = %s
                """, (user_id,))
            except Exception as e:
                print(f"⚠️  DEBUG: Fallback cleanup without usage_count: {e}", flush=True)
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_code = NULL,
                        profile_verification_expires_at = NULL,
                        pending_profile_changes = NULL,
                        profile_verification_attempts = 0
                    WHERE id = %s
                """, (user_id,))
            conn.commit()
            flash("Mã xác thực đã hết lượt sử dụng (5 lần). Vui lòng thực hiện thay đổi lại để nhận mã mới.", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        # Kiểm tra thời gian hết hạn
        if expires_at and datetime.now() > expires_at:
            # Xóa thông tin xác thực hết hạn
            cursor.execute("""
                UPDATE user SET 
                    profile_verification_code = NULL,
                    profile_verification_expires_at = NULL,
                    pending_profile_changes = NULL,
                    profile_verification_attempts = 0,
                    profile_verification_usage_count = 0
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            flash("Mã xác thực đã hết hạn. Vui lòng thực hiện lại thay đổi.", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        # Kiểm tra số lần thử sai
        if attempts >= 5:
            # Xóa thông tin xác thực khi đạt giới hạn thử sai
            cursor.execute("""
                UPDATE user SET 
                    profile_verification_code = NULL,
                    profile_verification_expires_at = NULL,
                    pending_profile_changes = NULL,
                    profile_verification_attempts = 0,
                    profile_verification_usage_count = 0
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            flash("Bạn đã nhập sai mã quá nhiều lần (5 lần). Thay đổi đã bị hủy bỏ. Vui lòng thực hiện lại thay đổi.", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        # Kiểm tra mã xác thực
        if verification_code != stored_code:
            # Tăng số lần thử sai
            cursor.execute("""
                UPDATE user SET profile_verification_attempts = %s WHERE id = %s
            """, (attempts + 1, user_id))
            conn.commit()
            remaining_attempts = 5 - attempts - 1
            if remaining_attempts > 0:
                flash(f"Mã xác thực không đúng. Còn {remaining_attempts} lần thử.", "error")
            else:
                flash("Mã xác thực không đúng. Đây là lần thử cuối cùng!", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        # Xác thực thành công - áp dụng thay đổi
        new_username = pending_changes.get('username', '')
        new_bio = pending_changes.get('bio', '')
        avatar_cropped_data = pending_changes.get('avatar_cropped_data')
        
        # Cập nhật username và bio
        cursor.execute("UPDATE user SET username = %s, bio = %s WHERE id = %s", 
                      (new_username, new_bio, user_id))
        
        # Xử lý avatar nếu có
        if avatar_cropped_data and avatar_cropped_data.startswith('data:image'):
            try:
                match = re.match(r'data:image/(png|jpeg|jpg|gif);base64,(.*)', avatar_cropped_data)
                if match:
                    ext = match.group(1)
                    b64_data = match.group(2)
                    
                    # Xoá avatar cũ
                    cursor.execute("SELECT avatar FROM user WHERE id = %s", (user_id,))
                    old_avatar_row = cursor.fetchone()
                    old_avatar = old_avatar_row['avatar'] if old_avatar_row else None
                    if old_avatar:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', old_avatar)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except Exception as e:
                                print(f"[WARN] Không thể xóa avatar cũ: {e}", flush=True)
                    
                    # Tạo tên file random
                    unique_id = uuid.uuid4().hex
                    filename = f"avatar_{unique_id}.{ext}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', filename)
                    
                    # Decode và lưu
                    with open(save_path, 'wb') as f:
                        f.write(base64.b64decode(b64_data))
                    
                    # Update DB
                    cursor.execute("UPDATE user SET avatar = %s WHERE id = %s", (filename, user_id))
            except Exception as e:
                print(f"[WARN] Error saving cropped avatar: {e}", flush=True)
                flash("Có lỗi khi lưu ảnh đại diện đã cắt.", "error")
        
        # Tăng usage count thay vì xóa mã (chỉ khi có field usage_count)
        if 'profile_verification_usage_count' in result:
            new_usage_count = usage_count + 1
            
            if new_usage_count >= 5:
                # Đã hết lượt sử dụng - xóa thông tin xác thực
                try:
                    cursor.execute("""
                        UPDATE user SET 
                            profile_verification_code = NULL,
                            profile_verification_expires_at = NULL,
                            pending_profile_changes = NULL,
                            profile_verification_attempts = 0,
                            profile_verification_usage_count = 0
                        WHERE id = %s
                    """, (user_id,))
                except Exception as e:
                    print(f"⚠️  DEBUG: Fallback final cleanup: {e}", flush=True)
                    cursor.execute("""
                        UPDATE user SET 
                            profile_verification_code = NULL,
                            profile_verification_expires_at = NULL,
                            pending_profile_changes = NULL,
                            profile_verification_attempts = 0
                        WHERE id = %s
                    """, (user_id,))
                flash("✅ Xác thực thành công! Hồ sơ đã được cập nhật. Mã xác thực đã hết lượt sử dụng.", "success")
            else:
                # Còn lượt sử dụng - chỉ tăng usage count
                try:
                    cursor.execute("""
                        UPDATE user SET 
                            pending_profile_changes = NULL,
                            profile_verification_attempts = 0,
                            profile_verification_usage_count = %s
                        WHERE id = %s
                    """, (new_usage_count, user_id,))
                    remaining_uses = 5 - new_usage_count
                    flash(f"✅ Xác thực thành công! Hồ sơ đã được cập nhật. Mã còn {remaining_uses} lượt sử dụng.", "success")
                except Exception as e:
                    print(f"⚠️  DEBUG: Fallback usage count update: {e}", flush=True)
                    # Fallback: xóa luôn như cũ
                    cursor.execute("""
                        UPDATE user SET 
                            profile_verification_code = NULL,
                            profile_verification_expires_at = NULL,
                            pending_profile_changes = NULL,
                            profile_verification_attempts = 0
                        WHERE id = %s
                    """, (user_id,))
                    flash("✅ Xác thực thành công! Hồ sơ đã được cập nhật.", "success")
        else:
            # Fallback: hoạt động như cũ khi chưa có field usage_count
            cursor.execute("""
                UPDATE user SET 
                    profile_verification_code = NULL,
                    profile_verification_expires_at = NULL,
                    pending_profile_changes = NULL,
                    profile_verification_attempts = 0
                WHERE id = %s
            """, (user_id,))
            flash("✅ Xác thực thành công! Hồ sơ đã được cập nhật.", "success")
        
        conn.commit()
        return redirect(url_for('profile_settings', user_id=user_id))
        
    except Exception as e:
        print(f"❌ Error in handle_profile_verification: {e}", flush=True)
        flash("Có lỗi xảy ra trong quá trình xác thực.", "error")
        return redirect(url_for('profile_settings', user_id=user_id))

@app.route('/profile/verification', methods=['GET', 'POST'])
@login_required
def profile_verification():
    """Trang xác thực danh tính tài khoản"""
    user_id = current_user.id
    
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Kiểm tra xem có phải là hủy bỏ xác thực không
            if request.form.get("cancel_verification"):
                # Xóa thông tin xác thực
                cursor.execute("""
                    UPDATE user SET 
                        identity_verification_code = NULL,
                        identity_verification_expires_at = NULL,
                        identity_verification_attempts = 0
                    WHERE id = %s
                """, (user_id,))
                conn.commit()
                flash("Đã hủy bỏ quá trình xác thực danh tính.", "info")
                return redirect(url_for('profile_settings', user_id=user_id))
            
            # Kiểm tra xem có phải là xác thực không
            verification_code = request.form.get("verification_code", "").strip()
            
            if verification_code:
                # Xử lý xác thực danh tính
                return handle_identity_verification(user_id, verification_code, cursor, conn)
            
            # Nếu không có mã xác thực, gửi email xác thực
            # Tạo mã xác thực
            verification_code = generate_verification_code(6)
            expires_at = datetime.now() + timedelta(hours=24)
            
            # Lưu mã xác thực
            cursor.execute("""
                UPDATE user SET 
                    identity_verification_code = %s,
                    identity_verification_expires_at = %s,
                    identity_verification_attempts = 0
                WHERE id = %s
            """, (verification_code, expires_at, user_id))
            
            conn.commit()
            
            # Gửi email xác thực
            email_service = get_email_service()
            if email_service:
                try:
                    result = email_service.send_identity_verification_email(
                        email=current_user.email,
                        username=current_user.username or current_user.email.split('@')[0],
                        verification_code=verification_code
                    )
                    if result:
                        flash("📧 Mã xác thực đã được gửi đến email của bạn. Vui lòng kiểm tra và nhập mã để hoàn tất xác thực.", "info")
                    else:
                        flash("❌ Có lỗi khi gửi email xác thực. Vui lòng thử lại.", "error")
                except Exception as e:
                    print(f"❌ Error sending identity verification email: {e}", flush=True)
                    flash("❌ Có lỗi khi gửi email xác thực. Vui lòng thử lại.", "error")
            else:
                flash("❌ Dịch vụ email không khả dụng. Vui lòng thử lại sau.", "error")
            
            return redirect(url_for('profile_verification'))
        
        # GET request - hiển thị trang
        # Lấy thông tin xác thực hiện tại
        cursor.execute("""
            SELECT identity_verified, identity_verification_code, 
                   identity_verification_expires_at, identity_verification_attempts
            FROM user WHERE id = %s
        """, (user_id,))
        user_data = cursor.fetchone()
        
        identity_verified = user_data.get('identity_verified', False) if user_data else False
        has_pending_verification = bool(user_data and user_data.get('identity_verification_code'))
        verification_attempts = user_data.get('identity_verification_attempts', 0) if user_data else 0
        
        # Nếu đã xác thực, redirect về profile settings
        if identity_verified:
            flash("✅ Tài khoản của bạn đã được xác thực danh tính.", "success")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        return render_template("profile_verification.html",
                             user_id=user_id,
                             has_pending_verification=has_pending_verification,
                             verification_attempts=verification_attempts)
        
    except Exception as e:
        print(f"❌ Error in profile_verification: {e}", flush=True)
        flash("Có lỗi xảy ra. Vui lòng thử lại.", "error")
        return redirect(url_for('profile_settings', user_id=user_id))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def handle_identity_verification(user_id, verification_code, cursor, conn):
    """Xử lý xác thực danh tính"""
    try:
        # Lấy thông tin xác thực
        cursor.execute("""
            SELECT identity_verification_code, identity_verification_expires_at, 
                   identity_verification_attempts
            FROM user WHERE id = %s
        """, (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data or not user_data['identity_verification_code']:
            flash("❌ Không tìm thấy mã xác thực. Vui lòng thử lại.", "error")
            return redirect(url_for('profile_verification'))
        
        stored_code = user_data['identity_verification_code']
        expires_at = user_data['identity_verification_expires_at']
        attempts = user_data['identity_verification_attempts']
        
        # Kiểm tra thời gian hết hạn
        if expires_at and datetime.now() > expires_at:
            # Xóa mã hết hạn
            cursor.execute("""
                UPDATE user SET 
                    identity_verification_code = NULL,
                    identity_verification_expires_at = NULL,
                    identity_verification_attempts = 0
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            flash("❌ Mã xác thực đã hết hạn. Vui lòng thử lại.", "error")
            return redirect(url_for('profile_verification'))
        
        # Kiểm tra số lần thử
        if attempts >= 5:
            # Xóa thông tin xác thực
            cursor.execute("""
                UPDATE user SET 
                    identity_verification_code = NULL,
                    identity_verification_expires_at = NULL,
                    identity_verification_attempts = 0
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            flash("❌ Bạn đã nhập sai mã quá nhiều lần (5 lần). Vui lòng thử lại.", "error")
            return redirect(url_for('profile_verification'))
        
        # Kiểm tra mã xác thực
        if verification_code != stored_code:
            # Tăng số lần thử sai
            cursor.execute("""
                UPDATE user SET identity_verification_attempts = %s WHERE id = %s
            """, (attempts + 1, user_id))
            conn.commit()
            remaining_attempts = 5 - attempts - 1
            if remaining_attempts > 0:
                flash(f"❌ Mã xác thực không đúng. Còn {remaining_attempts} lần thử.", "error")
            else:
                flash("❌ Mã xác thực không đúng. Đây là lần thử cuối cùng!", "error")
            return redirect(url_for('profile_verification'))
        
        # Xác thực thành công
        cursor.execute("""
            UPDATE user SET 
                identity_verified = TRUE,
                identity_verification_code = NULL,
                identity_verification_expires_at = NULL,
                identity_verification_attempts = 0
            WHERE id = %s
        """, (user_id,))
        
        conn.commit()
        flash("✅ Xác thực danh tính thành công! Tài khoản của bạn đã được xác thực.", "success")
        return redirect(url_for('profile_settings', user_id=user_id))
        
    except Exception as e:
        print(f"❌ Error in handle_identity_verification: {e}", flush=True)
        flash("Có lỗi xảy ra trong quá trình xác thực.", "error")
        return redirect(url_for('profile_verification'))

# Khởi tạo email service ngay khi import app
try:
    init_email_service(app)
    print("✅ Email service initialized successfully", flush=True)
except Exception as e:
    print(f"❌ Failed to initialize email service: {e}", flush=True)
    import traceback
    print(f"❌ Email service init error: {traceback.format_exc()}", flush=True)

# =====================================================
# NOTIFICATION SERVICE INITIALIZATION
# =====================================================
try:
    init_notification_service()
    print("✅ Notification service initialized successfully", flush=True)
except Exception as e:
    print(f"❌ Failed to initialize notification service: {e}", flush=True)
    import traceback
    print(f"❌ Notification service init error: {traceback.format_exc()}", flush=True)

# =====================================================
# SECURITY HEADERS - Comments System Enhancement
# =====================================================
@app.after_request
def apply_security_headers(response):
    """Apply OWASP recommended security headers to all responses"""
    return add_security_headers(response)

# =====================================================
# REGISTER COMMENTS BLUEPRINT
# =====================================================
app.register_blueprint(comments_bp)
print("✅ Comments API blueprint registered at /api/comments", flush=True)

# =====================================================
# NOTIFICATIONS API ENDPOINTS
# =====================================================

@app.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_notifications_count():
    """
    API lấy số lượng notifications chưa đọc (for badge display)
    
    Returns:
        JSON: {'count': int, 'timestamp': str}
    """
    try:
        notification_service = get_notification_service()
        count = notification_service.get_unread_count(current_user.id)
        
        return jsonify({
            'count': count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    
    except Exception as e:
        print(f"[ERROR] get_unread_notifications_count: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """
    API lấy danh sách notifications của user
    
    Query params:
        limit (int): Số lượng notifications (default 20, max 100)
        only_unread (bool): Chỉ lấy unread (default false)
    
    Returns:
        JSON: {'notifications': [...], 'count': int}
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100
        only_unread = request.args.get('only_unread', 'false').lower() == 'true'
        
        notification_service = get_notification_service()
        notifications = notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            only_unread=only_unread
        )
        
        return jsonify({
            'notifications': notifications,
            'count': len(notifications)
        }), 200
    
    except ValueError as e:
        return jsonify({'error': 'Invalid parameters'}), 400
    
    except Exception as e:
        print(f"[ERROR] get_notifications: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """
    API đánh dấu một notification đã đọc
    
    Args:
        notification_id (int): ID của notification
    
    Returns:
        JSON: {'success': bool}
    """
    try:
        notification_service = get_notification_service()
        success = notification_service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user.id  # Security: only owner can mark as read
        )
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Notification not found or already read'
            }), 404
    
    except Exception as e:
        print(f"[ERROR] mark_notification_read: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """
    API đánh dấu tất cả notifications của user đã đọc
    
    Returns:
        JSON: {'success': bool, 'count': int}
    """
    try:
        notification_service = get_notification_service()
        count = notification_service.mark_all_as_read(current_user.id)
        
        return jsonify({
            'success': True,
            'count': count
        }), 200
    
    except Exception as e:
        print(f"[ERROR] mark_all_notifications_read: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500

# =====================================================
# PACKAGE MANAGEMENT SYSTEM INTEGRATION
# =====================================================

# Import package routes
try:
    from package_routes import setup_package_routes, update_package_usage
    
    # Setup package management routes
    setup_package_routes(app, limiter=None)
    
    print("[INFO] Package Management System routes loaded successfully", flush=True)
    
except ImportError as e:
    print(f"[WARNING] Package Management System not available: {e}", flush=True)
except Exception as e:
    print(f"[ERROR] Failed to load Package Management System: {e}", flush=True)

# =====================================================
# ENHANCED COMPILATION WITH PACKAGE USAGE TRACKING
# =====================================================

# Modify the existing compilation function to track package usage
original_compile_tikz_enhanced_whitelist = compile_tikz_enhanced_whitelist

def compile_tikz_enhanced_whitelist_with_tracking(tikz_code, output_dir, filename_base):
    """Enhanced compilation with package usage tracking"""
    try:
        # Call original compilation function
        # Returns: (success: bool, svg_content: str, error_message: str)
        result = original_compile_tikz_enhanced_whitelist(tikz_code, output_dir, filename_base)
        
        # Check if result is a tuple (expected format)
        if isinstance(result, tuple) and len(result) >= 3:
            success, svg_content, error_message = result
            
            # Track package usage if compilation was successful
            if success:
                try:
                    # Extract packages from tikz_code
                    import re
                    
                    # Look for %!<package1,package2,package3> pattern
                    package_pattern = r'%!<([^>]+)>'
                    matches = re.findall(package_pattern, tikz_code)
                    
                    used_packages = set()
                    for match in matches:
                        packages = [pkg.strip() for pkg in match.split(',') if pkg.strip()]
                        used_packages.update(packages)
                    
                    if used_packages:
                        # Update package usage in background
                        try:
                            update_package_usage(list(used_packages))
                        except Exception as e:
                            print(f"[WARNING] Failed to update package usage: {e}", flush=True)
                            
                except Exception as e:
                    print(f"[WARNING] Failed to track package usage: {e}", flush=True)
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error in enhanced compilation with tracking: {e}", flush=True)
        # Fallback to original function
        return original_compile_tikz_enhanced_whitelist(tikz_code, output_dir, filename_base)

# Replace the compilation function
compile_tikz_enhanced_whitelist = compile_tikz_enhanced_whitelist_with_tracking

if __name__ == "__main__":
    import os
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    app.run(debug=True, host=host, port=port)