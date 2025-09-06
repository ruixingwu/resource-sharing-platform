FROM nginx:1.24-alpine

# 安装nginx配置优化
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

# 创建必要目录
RUN mkdir -p /var/log/nginx && \
    mkdir -p /var/www/uploads && \
    touch /var/log/nginx/access.log /var/log/nginx/error.log && \
    chown -R nginx:nginx /var/log/nginx /var/www/uploads

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1