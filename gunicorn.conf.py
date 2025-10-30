# Gunicorn Production Configuration for Enhanced Whitelist + Resource Limits v2.0
# ===============================================================================
#
# Optimized for VPS deployment with enterprise-grade performance,
# security, and monitoring capabilities.
#
# Usage:
#   gunicorn --config gunicorn.conf.py wsgi_production:application

import os
import multiprocessing
from pathlib import Path

# ================================
# 🔧 SERVER CONFIGURATION
# ================================

# Server socket
bind = "127.0.0.1:5000"  # Bind to localhost (Nginx will proxy)
backlog = 2048           # Maximum number of pending connections

# Worker processes (Conservative for VPS)
workers = int(os.environ.get("GUNICORN_WORKERS", 2))  # 2 workers for VPS
worker_class = "sync"    # Sync workers for LaTeX compilation (CPU intensive)
worker_connections = 1000
max_requests = 1000      # Restart workers after 1000 requests
max_requests_jitter = 50 # Add randomness to prevent thundering herd

# Worker timeout (Allow time for LaTeX compilation)
timeout = 120            # 2 minutes for complex compilations
keepalive = 5            # Keep connections alive for 5 seconds
graceful_timeout = 30    # Graceful shutdown timeout

# ================================
# 🔒 SECURITY CONFIGURATION
# ================================

# User/Group (Run as non-root user in production)
# user = "tikz2svg"
# group = "tikz2svg"

# Security limits
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8192

# ================================
# 📊 LOGGING CONFIGURATION
# ================================

# Create logs directory
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# Logging settings
loglevel = "info"
accesslog = str(log_dir / "gunicorn_access.log")
errorlog = str(log_dir / "gunicorn_error.log")
capture_output = True
logger_class = "gunicorn.glogging.Logger"

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Enable detailed logging
enable_stdio_inheritance = True

# ================================
# ⚡ PERFORMANCE CONFIGURATION
# ================================

# Preload application (Better memory usage)
preload_app = True

# Enable reuse port (Linux kernel load balancing)
reuse_port = True

# Worker memory management
max_worker_memory_mb = int(os.environ.get("MAX_WORKER_MEMORY", 512))  # 512MB per worker
worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance

# ================================
# 🔄 PROCESS MANAGEMENT
# ================================

# PID file
pidfile = "/tmp/gunicorn_tikz2svg.pid"

# Daemon mode (set to True for systemd service)
daemon = False

# Worker recycling
max_worker_memory = max_worker_memory_mb * 1024 * 1024  # Convert to bytes

# ================================
# 🌐 NETWORKING CONFIGURATION
# ================================

# Enable HTTP/1.1 keep-alive
keepalive = 5

# SSL configuration (if terminating SSL at Gunicorn)
# keyfile = "/path/to/private.key"
# certfile = "/path/to/certificate.crt"
# ssl_version = ssl.PROTOCOL_TLSv1_2
# cert_reqs = ssl.CERT_NONE
# ca_certs = None
# suppress_ragged_eofs = True
# do_handshake_on_connect = False
# ciphers = "TLSv1.2"

# ================================
# 📈 MONITORING HOOKS
# ================================

def when_ready(server):
    """Called just after the server is started"""
    print("🚀 Gunicorn server started successfully")
    print(f"   Workers: {workers}")
    print(f"   Bind: {bind}")
    print(f"   PID: {os.getpid()}")
    
    # Log startup to file
    with open(log_dir / "startup.log", "a") as f:
        import datetime
        f.write(f"{datetime.datetime.now()}: Server started with {workers} workers\n")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal"""
    print(f"🔄 Worker {worker.pid} interrupted")

def pre_fork(server, worker):
    """Called just before a worker is forked"""
    print(f"🍴 Forking worker {worker.age}")

def post_fork(server, worker):
    """Called just after a worker has been forked"""
    print(f"👶 Worker {worker.pid} started")
    
    # Set process title for monitoring
    try:
        import setproctitle
        setproctitle.setproctitle(f"tikz2svg-worker-{worker.age}")
    except ImportError:
        pass

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal"""
    print(f"💥 Worker {worker.pid} aborted")
    
    # Log worker abort
    with open(log_dir / "worker_errors.log", "a") as f:
        import datetime
        f.write(f"{datetime.datetime.now()}: Worker {worker.pid} aborted\n")

def pre_exec(server):
    """Called just before a new master process is forked"""
    print("🔄 Pre-exec: Preparing to restart server")

def on_exit(server):
    """Called when gunicorn is about to exit"""
    print("👋 Gunicorn server shutting down")
    
    # Log shutdown
    with open(log_dir / "startup.log", "a") as f:
        import datetime
        f.write(f"{datetime.datetime.now()}: Server shutdown\n")

def child_exit(server, worker):
    """Called when a worker exits"""
    print(f"👻 Worker {worker.pid} exited")

# ================================
# 🛠️ ENVIRONMENT VARIABLES
# ================================

# Environment variables to pass to workers
raw_env = [
    'PATH=/usr/local/bin:/usr/bin:/bin',
    'LANG=en_US.UTF-8',
    'LC_ALL=en_US.UTF-8',
    'PYTHONPATH=/opt/tikz2svg_api',
    'FLASK_ENV=production',
    'FLASK_CONFIG=config_production'
]

# ================================
# 🔍 DEVELOPMENT OVERRIDES
# ================================

# Override settings for development
if os.environ.get('FLASK_ENV') == 'development':
    workers = 1
    reload = True
    reload_extra_files = ['templates/', 'static/']
    loglevel = 'debug'
    print("🛠️ Development mode: Single worker with auto-reload")

# ================================
# 💡 PERFORMANCE TIPS
# ================================

# For better performance on multi-core systems:
# workers = multiprocessing.cpu_count() * 2 + 1  # Uncomment for CPU-bound apps

# For memory-constrained VPS:
# workers = 2  # Current setting - good for 2GB RAM VPS

# For high-traffic production:
# worker_class = "gevent"  # Async workers for I/O bound
# worker_connections = 1000

# ================================
# 📝 CONFIGURATION SUMMARY
# ================================

print("=" * 60)
print("🚀 GUNICORN PRODUCTION CONFIGURATION")
print("=" * 60)
print(f"Bind: {bind}")
print(f"Workers: {workers}")
print(f"Worker Class: {worker_class}")
print(f"Timeout: {timeout}s")
print(f"Max Requests: {max_requests}")
print(f"Preload App: {preload_app}")
print(f"Access Log: {accesslog}")
print(f"Error Log: {errorlog}")
print(f"Log Level: {loglevel}")
print("=" * 60)
