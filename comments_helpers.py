"""
COMMENTS SYSTEM - HELPER FUNCTIONS
Version: 1.2.1 Final
Date: 2025-10-22

Production-ready helper functions for Comments feature including:
- Error handling
- Security headers
- Database connection pooling
- Content moderation / spam detection
- Environment validation
- Performance monitoring
"""

import os
import re
import hashlib
import time
import logging
from functools import wraps
from flask import jsonify, request, after_this_request
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling, Error as MySQLError

load_dotenv()

# =====================================================
# LOGGING CONFIGURATION
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================
# DATABASE CONNECTION POOLING
# =====================================================

try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="comments_pool",
        pool_size=5,
        pool_reset_session=True,
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'hiep1987'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'tikz2svg_local')
    )
    logger.info("✅ Database connection pool initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize connection pool: {e}")
    connection_pool = None

def get_db_connection():
    """
    Get a database connection from the pool.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Database connection
    
    Raises:
        Exception: If connection pool is not available or connection fails
    """
    if connection_pool is None:
        # Fallback to direct connection if pool is not available
        logger.warning("⚠️ Using direct connection (pool not available)")
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'hiep1987'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'tikz2svg_local')
        )
    return connection_pool.get_connection()

# =====================================================
# ENVIRONMENT VALIDATION
# =====================================================

def validate_environment():
    """
    Validate that all required environment variables are set.
    
    Raises:
        SystemExit: If critical environment variables are missing
    """
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"❌ Missing environment variables: {missing}")
        logger.error("💡 Please set these variables in your .env file")
        raise SystemExit(1)
    
    logger.info("✅ All required environment variables are set")

# Call validation on import
try:
    validate_environment()
except SystemExit:
    logger.warning("⚠️ Environment validation failed, some features may not work")

# =====================================================
# SECURITY HEADERS
# =====================================================

def add_security_headers(response):
    """
    Add OWASP recommended security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Content-Security-Policy: default-src 'self'
    - Strict-Transport-Security: max-age=31536000 (HTTPS only)
    
    Args:
        response: Flask response object
    
    Returns:
        response: Modified response with security headers
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # CSP header (adjust based on your needs)
    # Relaxed for development - allows CDN resources
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://www.googletagmanager.com https://cdnjs.cloudflare.com https://codemirror.net https://cdn.quilljs.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://codemirror.net https://fonts.googleapis.com https://cdn.quilljs.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "connect-src 'self' https://cdn.jsdelivr.net https://cdn.quilljs.com"
    )
    
    # HSTS (only add if using HTTPS)
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# =====================================================
# API RESPONSE HELPER
# =====================================================

def api_response(success=True, message='', data=None, status_code=200):
    """
    Standardized API response format.
    
    Args:
        success (bool): Whether the request was successful
        message (str): Human-readable message
        data (dict): Response data
        status_code (int): HTTP status code
    
    Returns:
        tuple: (jsonify response, status_code)
    """
    response = {
        'success': success,
        'message': message,
        'timestamp': int(time.time())
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code

# =====================================================
# ERROR HANDLING DECORATOR
# =====================================================

def handle_db_error(func):
    """
    Decorator to handle database errors gracefully.
    
    Usage:
        @handle_db_error
        def my_route():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MySQLError as e:
            logger.error(f"❌ Database error in {func.__name__}: {e}")
            return api_response(
                success=False,
                message='Lỗi kết nối cơ sở dữ liệu. Vui lòng thử lại sau.',
                status_code=500
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error in {func.__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return api_response(
                success=False,
                message='Có lỗi xảy ra. Vui lòng thử lại.',
                status_code=500
            )
    return wrapper

# =====================================================
# PERFORMANCE MONITORING DECORATOR
# =====================================================

def monitor_performance(func):
    """
    Decorator to monitor API performance and log slow requests.
    
    Logs warnings for requests taking > 300ms.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if elapsed_time > 300:  # Threshold: 300ms
            logger.warning(f"⚠️ Slow request: {func.__name__} took {elapsed_time:.2f}ms")
        else:
            logger.info(f"✅ {func.__name__} completed in {elapsed_time:.2f}ms")
        
        return result
    return wrapper

# =====================================================
# CLIENT IP HELPER
# =====================================================

def get_client_ip():
    """
    Get the client's IP address, considering proxies.
    
    Returns:
        str: Client IP address
    """
    if request.headers.get('X-Forwarded-For'):
        # Get first IP if there are multiple (in case of multiple proxies)
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    
    return ip or 'unknown'

# =====================================================
# CONTENT HASH GENERATOR
# =====================================================

def generate_content_hash(comment_text, user_id):
    """
    Generate SHA256 hash for duplicate comment detection.
    
    Args:
        comment_text (str): Comment text
        user_id (int): User ID
    
    Returns:
        str: SHA256 hash (64 characters)
    """
    content = f"{user_id}:{comment_text.strip()}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

# =====================================================
# SPAM DETECTION
# =====================================================

SPAM_KEYWORDS = [
    'buy now', 'click here', 'free money', 'win prize', 'make money fast',
    'limited time', 'act now', 'urgent', 'congratulations',
    'viagra', 'cialis', 'casino', 'lottery', 'winner'
]

def detect_spam(comment_text, user_ip=None, user_id=None):
    """
    Detect spam comments based on content analysis.
    
    Spam indicators:
    - Contains spam keywords (score +2 each)
    - Excessive links (score +3 per link)
    - ALL CAPS text > 20 chars (score +1)
    - Repeated characters (score +1)
    
    Args:
        comment_text (str): Comment text to analyze
        user_ip (str): User's IP address (for future IP-based filtering)
        user_id (int): User ID (for future user-based filtering)
    
    Returns:
        tuple: (is_spam: bool, spam_score: int, reasons: list)
    """
    spam_score = 0
    reasons = []
    
    # 1. Check for spam keywords
    text_lower = comment_text.lower()
    for keyword in SPAM_KEYWORDS:
        if keyword in text_lower:
            spam_score += 2
            reasons.append(f"Spam keyword: '{keyword}'")
    
    # 2. Check for excessive links
    import re
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, comment_text)
    if len(urls) > 2:
        spam_score += len(urls) * 3
        reasons.append(f"Excessive links: {len(urls)} URLs found")
    
    # 3. Check for ALL CAPS
    if comment_text.isupper() and len(comment_text) > 20:
        spam_score += 1
        reasons.append("All caps text")
    
    # 4. Check for repeated characters
    repeated_pattern = r'(.)\1{4,}'  # Same character repeated 5+ times
    if re.search(repeated_pattern, comment_text):
        spam_score += 1
        reasons.append("Repeated characters")
    
    # Spam threshold: score > 3
    is_spam = spam_score > 3
    
    if is_spam:
        logger.warning(f"🚨 Spam detected (score: {spam_score}): {reasons}")
    
    return is_spam, spam_score, reasons

# =====================================================
# INPUT SANITIZATION
# =====================================================

def sanitize_comment_text(text):
    """
    Sanitize comment text to prevent XSS attacks.
    
    - Removes dangerous HTML tags (<script>, <iframe>, etc.)
    - Removes event handlers (onclick, onerror, etc.)
    - Preserves LaTeX math delimiters ($...$, $$...$$)
    
    Args:
        text (str): Raw comment text
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ''
    
    # Remove dangerous HTML tags
    text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<embed\b[^<]*(?:(?!<\/embed>)<[^<]*)*<\/embed>', '', text, flags=re.IGNORECASE)
    
    # Remove event handlers
    text = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*on\w+\s*=\s*[^"\'\s>]*', '', text, flags=re.IGNORECASE)
    
    # Limit length to prevent abuse
    MAX_LENGTH = 5000
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH]
    
    return text.strip()

# =====================================================
# EXPORT
# =====================================================

__all__ = [
    'get_db_connection',
    'validate_environment',
    'add_security_headers',
    'api_response',
    'handle_db_error',
    'monitor_performance',
    'get_client_ip',
    'generate_content_hash',
    'detect_spam',
    'sanitize_comment_text',
    'logger'
]

