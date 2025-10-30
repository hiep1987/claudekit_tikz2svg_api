#!/usr/bin/env python3
"""
WSGI Production Entry Point for Enhanced Whitelist + Resource Limits v2.0
=========================================================================

Production-optimized WSGI application with security hardening,
performance monitoring, and error handling.

Usage:
    gunicorn --config gunicorn.conf.py wsgi_production:application
"""

import os
import sys
import logging
import logging.config
from pathlib import Path

# Ensure proper path for imports
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# Import configuration
try:
    from config_production import Config
    print(f"✅ Production configuration loaded from {Config.__class__.__name__}")
except ImportError as e:
    print(f"❌ Failed to load production config: {e}")
    sys.exit(1)

# Import main application
try:
    from app import app
    print("✅ Main application imported successfully")
except ImportError as e:
    print(f"❌ Failed to import main application: {e}")
    sys.exit(1)

def create_production_app():
    """Create and configure production Flask application"""
    
    # ================================
    # 🔧 PRODUCTION CONFIGURATION
    # ================================
    
    # Apply production configuration
    app.config.update({
        'DEBUG': Config.DEBUG,
        'TESTING': Config.TESTING,
        'ENV': Config.ENV,
        'SECRET_KEY': Config.SECRET_KEY,
        
        # Session Security
        'SESSION_COOKIE_SECURE': Config.SESSION_COOKIE_SECURE,
        'SESSION_COOKIE_HTTPONLY': Config.SESSION_COOKIE_HTTPONLY,
        'SESSION_COOKIE_SAMESITE': Config.SESSION_COOKIE_SAMESITE,
        'PERMANENT_SESSION_LIFETIME': Config.PERMANENT_SESSION_LIFETIME,
        
        # File Upload
        'MAX_CONTENT_LENGTH': Config.MAX_CONTENT_LENGTH,
        'UPLOAD_FOLDER': Config.UPLOAD_FOLDER,
        
        # Enhanced Whitelist Configuration
        'ENHANCED_WHITELIST_CONFIG': Config.ENHANCED_WHITELIST_CONFIG,
        
        # Database Configuration
        'DATABASE_CONFIG': Config.DATABASE_CONFIG,
        
        # Email Configuration
        'EMAIL_CONFIG': Config.EMAIL_CONFIG,
        
        # Rate Limiting
        'RATE_LIMIT_CONFIG': Config.RATE_LIMIT_CONFIG,
        
        # Monitoring
        'MONITORING_CONFIG': Config.MONITORING_CONFIG
    })
    
    # ================================
    # 📊 LOGGING CONFIGURATION
    # ================================
    
    # Create log directories
    log_dirs = [
        os.path.join(BASE_DIR, 'logs'),
        os.path.join(BASE_DIR, 'logs', 'errors'),
        os.path.join(BASE_DIR, 'logs', 'security')
    ]
    
    for log_dir in log_dirs:
        os.makedirs(log_dir, exist_ok=True)
        print(f"📁 Log directory created: {log_dir}")
    
    # Configure logging
    try:
        logging.config.dictConfig(Config.LOGGING_CONFIG)
        app.logger.info("✅ Production logging configured successfully")
        print("✅ Production logging configured")
    except Exception as e:
        print(f"⚠️ Logging configuration warning: {e}")
        # Fallback logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'app.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        app.logger.info("✅ Fallback logging configured")
    
    # ================================
    # 🛡️ SECURITY HEADERS
    # ================================
    
    try:
        from flask_talisman import Talisman
        
        # Configure Content Security Policy
        csp = Config.CSP_POLICY
        
        # Apply security headers
        Talisman(app, 
                content_security_policy=csp,
                strict_transport_security=True,
                strict_transport_security_max_age=31536000,
                content_security_policy_nonce_in=['script-src', 'style-src'],
                feature_policy={
                    'geolocation': "'none'",
                    'camera': "'none'",
                    'microphone': "'none'",
                    'payment': "'none'"
                })
        app.logger.info("✅ Security headers configured with Talisman")
        print("✅ Security headers configured")
        
    except ImportError:
        app.logger.warning("⚠️ Flask-Talisman not available, security headers not configured")
        print("⚠️ Flask-Talisman not available")
    
    # ================================
    # 🔄 RATE LIMITING
    # ================================
    
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        # Configure rate limiter
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=["1000 per hour", "60 per minute"],
            storage_uri=Config.RATE_LIMIT_CONFIG['storage_uri'],
            storage_options={"socket_connect_timeout": 30},
            strategy="fixed-window"
        )
        
        app.logger.info("✅ Rate limiting configured")
        print("✅ Rate limiting configured")
        
    except ImportError:
        app.logger.warning("⚠️ Flask-Limiter not available, rate limiting not configured")
        print("⚠️ Rate limiting not configured")
    
    # ================================
    # 📈 MONITORING & METRICS
    # ================================
    
    try:
        from prometheus_client import Counter, Histogram, generate_latest
        
        # Define metrics
        REQUEST_COUNT = Counter('flask_requests_total', 'Total Flask requests', ['method', 'endpoint', 'status'])
        REQUEST_LATENCY = Histogram('flask_request_duration_seconds', 'Flask request latency')
        
        @app.before_request
        def before_request():
            """Track request metrics"""
            import time
            from flask import request, g
            g.start_time = time.time()
        
        @app.after_request 
        def after_request(response):
            """Record request completion metrics"""
            import time
            from flask import request, g
            
            if hasattr(g, 'start_time'):
                request_latency = time.time() - g.start_time
                REQUEST_LATENCY.observe(request_latency)
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status=response.status_code
                ).inc()
            
            return response
        
        # Metrics endpoint
        @app.route('/metrics')
        def metrics():
            """Prometheus metrics endpoint"""
            return generate_latest()
        
        app.logger.info("✅ Prometheus metrics configured")
        print("✅ Monitoring metrics configured")
        
    except ImportError:
        app.logger.warning("⚠️ Prometheus client not available, metrics not configured")
        print("⚠️ Metrics not configured")
    
    # ================================
    # 🚨 ERROR HANDLING
    # ================================
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        app.logger.warning(f"404 error: {error}")
        return {"error": "Resource not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f"500 error: {error}")
        return {"error": "Internal server error"}, 500
    
    @app.errorhandler(413)
    def too_large(error):
        """Handle file too large errors"""
        app.logger.warning(f"413 error: {error}")
        return {"error": "File too large"}, 413
    
    @app.errorhandler(429)
    def rate_limit_handler(error):
        """Handle rate limit errors"""
        app.logger.warning(f"429 error: {error}")
        return {"error": "Rate limit exceeded"}, 429
    
    # ================================
    # 🏃 HEALTH CHECK ENDPOINT
    # ================================
    
    @app.route('/health')
    def health_check():
        """Production health check endpoint"""
        import time
        import psutil
        
        try:
            # System health metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine health status
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
                status = "critical"
                http_status = 503
            elif cpu_percent > 70 or memory.percent > 80 or disk.percent > 90:
                status = "degraded"
                http_status = 200
            else:
                status = "healthy"
                http_status = 200
            
            health_data = {
                "status": status,
                "timestamp": time.time(),
                "version": "2.0",
                "platform": "Enhanced Whitelist + Resource Limits",
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                },
                "features": {
                    "security_patterns": 26,
                    "cache_enabled": True,
                    "adaptive_limits": True,
                    "monitoring": True
                }
            }
            
            return health_data, http_status
            
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "timestamp": time.time(),
                "error": str(e)
            }, 503
    
    # ================================
    # 🔧 STARTUP VALIDATION
    # ================================
    
    def validate_production_environment():
        """Validate production environment setup"""
        
        validation_errors = []
        
        # Check required environment variables
        required_env_vars = [
            'SECRET_KEY',
            'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
            'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET',
            'SMTP_USERNAME', 'SMTP_PASSWORD'
        ]
        
        for var in required_env_vars:
            if not os.environ.get(var):
                validation_errors.append(f"Missing environment variable: {var}")
        
        # Check required directories
        required_dirs = [
            Config.UPLOAD_FOLDER,
            Config.TEMP_FOLDER,
            Config.ERROR_LOG_DIR,
            Config.SECURITY_LOG_DIR
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    print(f"📁 Created directory: {directory}")
                except Exception as e:
                    validation_errors.append(f"Cannot create directory {directory}: {e}")
        
        # Check system dependencies
        system_deps = ['lualatex', 'pdf2svg']
        for dep in system_deps:
            import shutil
            if not shutil.which(dep):
                validation_errors.append(f"Missing system dependency: {dep}")
        
        if validation_errors:
            print("❌ Production environment validation failed:")
            for error in validation_errors:
                print(f"   - {error}")
            app.logger.error(f"Production validation failed: {validation_errors}")
            # Don't exit, but log warnings
            for error in validation_errors:
                app.logger.warning(f"Validation warning: {error}")
        else:
            print("✅ Production environment validation passed")
            app.logger.info("Production environment validation passed")
    
    # Run validation
    validate_production_environment()
    
    # ================================
    # 🚀 FINAL SETUP
    # ================================
    
    app.logger.info("🚀 Production application configured successfully")
    print("🚀 Production application ready")
    
    return app

# Create the production application
application = create_production_app()

# WSGI compliance check
if __name__ == "__main__":
    print("❌ This is a WSGI application. Use a WSGI server like Gunicorn:")
    print("   gunicorn --config gunicorn.conf.py wsgi_production:application")
    sys.exit(1)
