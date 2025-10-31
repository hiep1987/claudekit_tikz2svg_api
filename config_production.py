#!/usr/bin/env python3
"""
Production Configuration for Enhanced Whitelist + Resource Limits v2.0
========================================================================

Production-optimized settings for VPS deployment with enterprise-grade security,
performance tuning, and monitoring capabilities.

Usage:
    export FLASK_ENV=production
    export FLASK_CONFIG=config_production
    flask run
"""

import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration with security hardening"""
    
    # ================================
    # 🛡️ SECURITY CONFIGURATION
    # ================================
    
    # Flask Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Session Security
    SESSION_COOKIE_SECURE = True      # HTTPS only
    SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'   # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Content Security Policy
    CSP_POLICY = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net", "https://www.googletagmanager.com", "https://cdnjs.cloudflare.com", "https://codemirror.net", "https://cdn.quilljs.com"],  # Required for inline scripts and CDN resources
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "https://codemirror.net", "https://cdn.quilljs.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"],
        'img-src': ["'self'", "data:", "https:"],
        'connect-src': ["'self'", "https://cdn.jsdelivr.net", "https://cdn.quilljs.com"],
        'frame-ancestors': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
    }
    
    # ================================
    # 🚀 PERFORMANCE CONFIGURATION  
    # ================================
    
    # Enhanced Whitelist Settings (Production Optimized)
    ENHANCED_WHITELIST_CONFIG = {
        # Resource Limits (Conservative for VPS)
        'base_timeout': 30,           # Reduced from 45s for production
        'base_memory_mb': 256,        # Reduced from 300MB for VPS
        'base_concurrent': 3,         # Reduced from 5 for VPS stability
        'max_timeout': 90,            # Reduced from 120s
        'max_memory_mb': 512,         # Reduced from 1000MB for VPS
        'max_concurrent': 5,          # Reduced from 10
        
        # Cache Settings (Production Optimized)
        'cache_size_mb': 100,         # Increased from 50MB for production
        'cache_enabled': True,
        'cache_ttl_hours': 24,
        
        # Security Settings
        'security_patterns_enabled': True,
        'security_logging_enabled': True,
        'security_log_retention_days': 30,
        
        # System Load Thresholds (Stricter for VPS)
        'load_thresholds': {
            'low': 40,     # CPU < 40% (more conservative)
            'medium': 70,  # CPU < 70%
            'high': 85     # CPU < 85%
        },
        
        # User Tier Multipliers
        'user_tier_multipliers': {
            'free': 1.0,
            'premium': 1.3,        # Reduced from 1.5
            'enterprise': 1.6      # Reduced from 2.0
        }
    }
    
    # ================================
    # 🗄️ DATABASE CONFIGURATION
    # ================================
    
    # MySQL Production Settings
    DATABASE_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'user': os.environ.get('DB_USER', 'tikz2svg_user'),  
        'password': os.environ.get('DB_PASSWORD'),
        'database': os.environ.get('DB_NAME', 'tikz2svg_production'),
        'port': int(os.environ.get('DB_PORT', 3306)),
        
        # Connection Pool Settings
        'pool_name': 'tikz2svg_pool',
        'pool_size': 10,
        'pool_reset_session': True,
        'pool_pre_ping': True,
        
        # Performance Settings
        'autocommit': True,
        'use_unicode': True,
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        
        # Timeouts
        'connection_timeout': 10,
        'auth_plugin': 'mysql_native_password'
    }
    
    # ================================
    # 📁 FILE & DIRECTORY CONFIGURATION
    # ================================
    
    # Production Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
    UPLOAD_FOLDER = os.path.join(STATIC_ROOT, 'svg_files')
    TEMP_FOLDER = os.path.join(STATIC_ROOT, 'temp_svg')
    ERROR_LOG_DIR = os.path.join(BASE_DIR, 'logs', 'errors')
    SECURITY_LOG_DIR = os.path.join(BASE_DIR, 'logs', 'security')
    
    # File Upload Limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_EXTENSIONS = ['.tex', '.tikz']
    
    # ================================  
    # 📊 LOGGING CONFIGURATION
    # ================================
    
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'production': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'security': {
                'format': '%(asctime)s [SECURITY] %(levelname)s - User:%(user_id)s - IP:%(ip)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'file_app': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'formatter': 'production',
                'level': 'INFO'
            },
            'file_security': {
                'class': 'logging.handlers.RotatingFileHandler', 
                'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 10,  # Keep more security logs
                'formatter': 'security',
                'level': 'WARNING'
            },
            'file_error': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(BASE_DIR, 'logs', 'error.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'formatter': 'production', 
                'level': 'ERROR'
            }
        },
        'loggers': {
            'tikz_app': {
                'handlers': ['file_app'],
                'level': 'INFO',
                'propagate': False
            },
            'tikz_security': {
                'handlers': ['file_security'],
                'level': 'WARNING',
                'propagate': False
            },
            'tikz_error': {
                'handlers': ['file_error'],
                'level': 'ERROR',
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['file_app']
        }
    }
    
    # ================================
    # 🌐 GOOGLE OAUTH CONFIGURATION
    # ================================
    
    GOOGLE_OAUTH_CONFIG = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI', 'https://yourdomain.com/login/google/authorized'),
        
        # OAuth Security
        'scope': ['openid', 'email', 'profile'],
        'prompt': 'select_account',
        
        # Production URLs
        'discovery_url': 'https://accounts.google.com/.well-known/openid_identity_provider',
        'issuer': 'https://accounts.google.com',
        'authorization_endpoint': 'https://accounts.google.com/o/oauth2/auth',
        'token_endpoint': 'https://oauth2.googleapis.com/token',
        'userinfo_endpoint': 'https://openidconnect.googleapis.com/v1/userinfo'
    }
    
    # ================================
    # 📧 EMAIL CONFIGURATION
    # ================================
    
    EMAIL_CONFIG = {
        'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'), 
        'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
        'smtp_username': os.environ.get('SMTP_USERNAME'),
        'smtp_password': os.environ.get('SMTP_PASSWORD'),
        'use_tls': True,
        'use_ssl': False,
        
        # Email Settings
        'sender_email': os.environ.get('SENDER_EMAIL'),
        'sender_name': 'TikZ2SVG Service',
        'reply_to': os.environ.get('REPLY_TO_EMAIL'),
        
        # Rate Limiting
        'max_emails_per_hour': 50,
        'max_emails_per_day': 200
    }
    
    # ================================
    # 🔄 RATE LIMITING CONFIGURATION
    # ================================
    
    RATE_LIMIT_CONFIG = {
        # Compilation Rate Limits (Per User)
        'compilation_per_minute': 5,
        'compilation_per_hour': 50,
        'compilation_per_day': 200,
        
        # API Rate Limits
        'api_per_minute': 60,
        'api_per_hour': 1000,
        
        # Storage for rate limiting
        'storage_uri': 'redis://localhost:6379/1',  # Redis for production
        'fallback_storage': 'memory',  # Fallback if Redis unavailable
        
        # Rate limit headers
        'headers_enabled': True,
        'header_retry_after': 'Retry-After',
        'header_remaining': 'X-RateLimit-Remaining',
        'header_limit': 'X-RateLimit-Limit'
    }
    
    # ================================
    # 📈 MONITORING CONFIGURATION
    # ================================
    
    MONITORING_CONFIG = {
        # Health Check Settings
        'health_check_enabled': True,
        'health_check_interval': 60,  # seconds
        
        # Metrics Collection
        'metrics_enabled': True,
        'metrics_retention_days': 7,
        
        # Alerting Thresholds
        'alert_thresholds': {
            'cpu_percent': 85,
            'memory_percent': 85,
            'disk_percent': 90,
            'error_rate_per_hour': 10,
            'response_time_ms': 2000
        },
        
        # Dashboard Settings
        'dashboard_enabled': True,
        'dashboard_refresh_seconds': 30,
        'dashboard_history_hours': 24
    }
    
    # ================================
    # 🛠️ SYSTEM CONFIGURATION
    # ================================
    
    # Process Settings
    WORKERS = int(os.environ.get('GUNICORN_WORKERS', 2))  # Conservative for VPS
    WORKER_CONNECTIONS = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))
    WORKER_CLASS = 'sync'  # Sync workers for LaTeX compilation
    WORKER_TIMEOUT = 120   # Allow time for LaTeX compilation
    KEEPALIVE = 5
    
    # Nginx Integration
    NGINX_CONFIG = {
        'client_max_body_size': '16M',
        'proxy_read_timeout': '120s',
        'proxy_connect_timeout': '10s',
        'proxy_send_timeout': '60s',
        'proxy_buffering': 'on',
        'proxy_buffer_size': '4k',
        'proxy_buffers': '8 4k'
    }
    
    # SSL/TLS Configuration
    SSL_CONFIG = {
        'ssl_certificate': '/etc/ssl/certs/tikz2svg.crt',
        'ssl_certificate_key': '/etc/ssl/private/tikz2svg.key',
        'ssl_protocols': 'TLSv1.2 TLSv1.3',
        'ssl_ciphers': 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256',
        'ssl_prefer_server_ciphers': 'off',
        'add_header_strict_transport_security': 'max-age=63072000; includeSubDomains; preload'
    }

# Environment Detection
def get_config():
    """Get configuration based on environment"""
    config_name = os.environ.get('FLASK_CONFIG', 'production')
    
    if config_name == 'production':
        return ProductionConfig()
    else:
        # Fallback to production for safety
        return ProductionConfig()

# Export for easy import
Config = get_config()
