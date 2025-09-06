import multiprocessing

# Gunicorn 配置 - 用于高并发性能优化

# Server Socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = "resource-sharing-app"

# Server Mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL/Security
# 如果在Gunicorn层处理SSL，取消注释以下配置
# keyfile = "path/to/key.pem"
# certfile = "path/to/cert.pem"

# 调试/开发
reload = False
reload_engine = "auto"

# 限制资源使用
# limit_request_line = 8190
# limit_request_fields = 100
# limit_request_field_size = 8190