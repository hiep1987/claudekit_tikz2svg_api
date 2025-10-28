"""
COMMENTS SYSTEM - HELPER FUNCTIONS
Version: 1.0.0
Date: 2025-10-26

Utility functions for the Comments system
"""

import logging
import hashlib
import time
import re
from functools import wraps
from flask import request, jsonify, g
import mysql.connector
from mysql.connector import Error as MySQLError
import os
from datetime import datetime

# Configure logger
logger = logging.getLogger('comments_system')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_db_connection():
    """Get database connection using environment variables"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DATABASE_HOST', 'localhost'),
            database=os.getenv('DATABASE_NAME', 'tikz2svg_local'),
            user=os.getenv('DATABASE_USER', 'root'),
            password=os.getenv('DATABASE_PASSWORD', ''),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=False
        )
        return connection
    except MySQLError as e:
        logger.error(f"Database connection error: {e}")
        raise

def api_response(success=True, message="", data=None, status_code=200):
    """Standardized API response format"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    try:
        return jsonify(response), status_code
    except RuntimeError:
        # No application context available, return dict instead
        return response, status_code

def handle_db_error(error, operation="database operation"):
    """Handle database errors with logging"""
    error_msg = f"Database error during {operation}: {str(error)}"
    logger.error(error_msg)
    
    if "1062" in str(error):  # Duplicate entry
        return api_response(False, "Duplicate entry detected", status_code=409)
    elif "1452" in str(error):  # Foreign key constraint
        return api_response(False, "Referenced record not found", status_code=400)
    elif "1406" in str(error):  # Data too long
        return api_response(False, "Content too long", status_code=400)
    else:
        return api_response(False, "Database operation failed", status_code=500)

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > 1.0:  # Log slow operations
                logger.warning(f"Slow operation: {func.__name__} took {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {execution_time:.2f}s: {e}")
            raise
    return wrapper

def get_client_ip():
    """Get client IP address from request headers"""
    # Check for forwarded IP first (common in production with reverse proxy)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr or 'unknown'

def generate_content_hash(content, user_id=None):
    """Generate hash for content (used for spam detection)"""
    # Normalize content for consistent hashing
    normalized_content = re.sub(r'\s+', ' ', content.strip().lower())
    
    # Include user_id in hash to allow same content from different users
    hash_input = f"{normalized_content}_{user_id or 'anonymous'}"
    
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

def detect_spam(content, user_id=None, ip_address=None):
    """Basic spam detection"""
    if not content:
        return True, "Empty content"
    
    # Length checks
    if len(content) < 2:
        return True, "Content too short"
    if len(content) > 2000:
        return True, "Content too long"
    
    # Basic spam patterns
    spam_patterns = [
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
        r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',  # Email addresses
        r'(viagra|cialis|casino|lottery|winner|congratulations)',  # Common spam words
        r'(.)\1{10,}',  # Repeated characters
    ]
    
    content_lower = content.lower()
    for pattern in spam_patterns:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return True, f"Spam pattern detected: {pattern}"
    
    # Rate limiting could be added here based on user_id and ip_address
    
    return False, "Content appears to be legitimate"

def sanitize_comment_text(text):
    """Sanitize comment text for safe storage and display"""
    if not text:
        return ""
    
    # Remove potentially dangerous HTML tags but keep basic formatting
    # This is a basic implementation - consider using a library like bleach for production
    text = str(text).strip()
    
    # Remove script tags and their content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous attributes
    text = re.sub(r'on\w+="[^"]*"', '', text, flags=re.IGNORECASE)
    text = re.sub(r"on\w+='[^']*'", '', text, flags=re.IGNORECASE)
    
    # Allow only basic HTML tags
    allowed_tags = ['b', 'i', 'em', 'strong', 'br', 'p']
    text = re.sub(r'<(?!/?(?:' + '|'.join(allowed_tags) + r')\b)[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Limit length
    if len(text) > 2000:
        text = text[:2000] + "..."
    
    return text

# Additional utility functions that might be used by the comments system

def validate_filename(filename):
    """Validate SVG filename"""
    if not filename:
        return False
    
    # Check if it's a valid filename pattern
    if not re.match(r'^[a-zA-Z0-9_-]+\.svg$', filename):
        return False
    
    return True

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if not timestamp:
        return "Unknown time"
    
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        now = datetime.now()
        diff = now - dt.replace(tzinfo=None)
        
        if diff.days > 7:
            return dt.strftime("%Y-%m-%d")
        elif diff.days > 0:
            return f"{diff.days} ngày trước"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} giờ trước"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} phút trước"
        else:
            return "Vừa xong"
    except Exception:
        return "Unknown time"
