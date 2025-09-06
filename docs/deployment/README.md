# 资源共享平台部署指南

## 系统要求

- **操作系统**: Ubuntu 22.04 LTS 或更高版本
- **磁盘空间**: 最小5GB，推荐20GB以上
- **内存**: 最小2GB，推荐4GB以上
- **网络**: 稳定的互联网连接

## Docker环境准备

### 1. 安装Docker

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y apt-transport-https ca-certificates curl gnupg software-properties-common

# 添加Docker GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu jammy stable" | sudo tee /etc/apt/sources.list.d/docker.list

# 安装Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组（无需root运行）
sudo usermod -aG docker $USER
# 重新登录使更改生效
```

### 2. 安装Docker Compose

```bash
# 安装Docker Compose v2
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose

# 验证安装
docker compose version
```

## 项目部署

### 1. 下载代码

```bash
# 克隆项目到本地
git clone [项目地址]
cd resource-sharing-platform
```

### 2. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

编辑`.env`文件，设置以下参数：

```bash
# 数据库配置
MYSQL_ROOT_PASSWORD=your-secure-root-password
MYSQL_DATABASE=resource_sharing
MYSQL_USER=app_user
MYSQL_PASSWORD=your-secure-db-password

# 应用配置
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key

# SSL配置（生产环境）
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# 邮件配置（可选）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
BACKUP_EMAIL=admin@yourcompany.com
```

### 3. 生成SSL证书（生产环境）

#### 使用Let's Encrypt

```bash
# 安装certbot
sudo apt install -y certbot

# 生成证书
sudo certbot certonly --standalone -d yourdomain.com

# 复制证书到容器卷
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
chmod 400 ./ssl/*.pem
```

#### 或者使用自签名证书（测试）

```bash
# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=YourCompany/CN=localhost"
```

### 4. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 5. 初始化数据库

数据库会自动初始化，包含默认的用户和权限设置：

- 管理员账号：admin / admin
- 首次登录后请修改密码

### 6. 验证部署

访问以下URL验证部署是否成功：
- Web界面：http://localhost (或 https://yourdomain.com)
- API文档：http://localhost/api/docs

## 管理命令

### 查看服务状态

```bash
docker compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs backend
docker compose logs mysql
```

### 停止服务

```bash
# 停止服务
docker compose stop

# 停止并删除容器
docker compose down

# 停止并清理数据
docker compose down -v
```

### 重建服务

```bash
# 重建并启动
docker compose up --build -d
```

## 备份与恢复

### 手动备份

```bash
# 启动备份容器
docker compose run --rm backup

# 备份文件将保存在 ./backups/ 目录
```

### 恢复备份

```bash
# 恢复数据库
mysql -u root -p resource_sharing < /backups/db/resource_sharing_YYYYMMDD_HHMMSS.sql

# 恢复文件
tar -xzvf /backups/files/files_YYYYMMDD_HHMMSS.tar.gz -C /
```

## 性能调优

### Nginx配置优化

编辑 `nginx/conf.d/default.conf`：

```nginx
# 添加性能优化配置
worker_connections 1024;
keepalive_timeout 65;
client_max_body_size 250M;

# 启用压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

# 缓存静态资源
location ~* \.(jpg|jpeg|png|gif|ico|pdf|zip|rar)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 数据库连接池优化

在backend容器中添加以下环境变量：

```bash
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
SQLALCHEMY_POOL_TIMEOUT=30
```

### 系统优化

```bash
# 增加文件描述符限制
echo "fs.file-max = 100000" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 设置Docker资源限制
# 在docker-compose.yml中添加资源限制：
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G
```

## 监控与维护

### 健康检查

在浏览器访问：
- http://localhost/health - 健康检查端点
- http://localhost/metrics - 系统指标

### 日志轮转

系统已配置自动logrotate，日志将定期清理：
- 访问日志保留90天
- 错误日志永久保留
- 自动压缩旧日志文件

### 定期维护

建议设置以下定时任务：

```bash
# 创建crontab
(crontab -l 2>/dev/null; echo "0 2 * * * docker compose run --rm backup") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * 0 docker compose run --rm log-cleanup") | crontab -
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库是否启动
   docker compose logs mysql
   
   # 检查连接参数
   docker exec -it resource-mysql mysql -u root -p
   ```

2. **文件上传失败**
   ```bash
   # 检查容器权限
   docker exec -it backend ls -la /app/uploads/
   
   # 修改权限
   docker exec -it backend chmod 755 /app/uploads
   ```

3. **SSL证书问题**
   ```bash
   # 检查证书路径
   docker exec -it nginx ls -la /etc/nginx/ssl/
   ```

### 性能监控

```bash
# 查看系统资源使用情况
docker stats

# 查看容器资源使用情况
docker compose stats

# 清理未使用镜像
docker system prune -a
```

## 更新升级

### 增量更新

```bash
# 拉取最新代码
git pull origin main

# 重启服务
docker compose down
docker compose build
docker compose up -d
```

### 版本升级

```bash
# 备份数据
docker compose run --rm backup

# 更新镜像
docker compose pull

# 重启服务
docker compose up --build -d
```

## 支持联系

如遇到问题，请通过以下方式联系技术支持：
- 邮件：support@yourcompany.com
- 电话：400-123-4567