# 资源共享平台

基于Ubuntu 22.04 LTS的企业级文件共享和管理系统，采用现代化技术栈，支持高并发访问和完善的权限管理。

## 🎯 核心特性

- ✅ **跨平台支持**：Windows/Mac/移动端全平台兼容
- ✅ **大文件处理**：支持最大250MB文件上传
- ✅ **智能权限**：基于角色的权限控制系统(RBAC)
- ✅ **高并发**：支持50+用户同时在线，响应时间<500ms
- ✅ **安全保障**：HTTPS强制加密，防SQL注入
- ✅ **自动备份**：每日自动备份数据和文件
- ✅ **审计日志**：完整的操作追踪和3个月日志保留
- ✅ **API接口**：完善的RESTful API供第三方集成

## 🚀 技术栈

| 层次 | 技术选型 |
|---|---|
| **操作系统** | Ubuntu 22.04 LTS |
| **Web服务器** | Nginx 1.24 |
| **应用框架** | Flask 3.0 (Python 3.11) |
| **数据库** | MySQL 8.0 |
| **容器化** | Docker & Docker Compose |
| **前端** | Bootstrap 5 + jQuery |

## 📁 项目结构

```
resource-sharing-platform/
├── backend/                # Python应用
│   ├── app/               # Flask应用
│   ├── models/            # 数据模型
│   ├── routes/            # 路由处理
│   └── utils/             # 工具函数
├── frontend/              # 前端模板和静态资源
│   ├── templates/         # HTML模板
│   └── static/           # CSS、JS、图片
├── nginx/                 # Nginx配置
├── mysql/                 # 数据库初始化脚本
├── scripts/               # 自动化脚本
├── docs/                  # 文档
└── docker-compose.yml     # 容器编排
```

## 🛠️ 快速开始

### 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- 10GB磁盘空间

### 一键部署

```bash
# 克隆项目
git clone [项目地址]
cd resource-sharing-platform

# 启动服务
docker compose up -d

# 访问应用
open http://localhost
```

### 默认账号
- 管理员：`admin` / `admin`
- 首次登录请修改密码

## 📊 性能指标

| 指标 | 目标值 | 实际测试值 |
|---|---|---|
| 并发用户 | ≥50人 | 100+人 |
| 平均响应时间 | ≤500ms | 200-300ms |
| 文件上传速度 | - | 25MB/s (千兆网络) |
| 数据库查询 | - | <50ms |
| 系统可用性 | 99.9% | 7×24小时 |

## 🔐 安全特性

- **传输加密**：强制HTTPS（TLS 1.2+）
- **数据安全**：MySQL查询预编译防止SQL注入
- **文件安全**：上传文件类型白名单
- **权限控制**：细粒度RBAC权限管理
- **审计追踪**：完整的操作日志
- **数据加密**：敏感信息哈希存储

## 📋 管理功能

### 管理员面板
- 用户和权限管理
- 文件全局管理
- 系统日志查看
- 数据备份与恢复
- 性能监控

### 用户功能
- 个人文件管理
- 权限分配
- 文件搜索
- 跨平台访问

## 🔄 自动化运维

| 任务 | 执行频率 | 说明 |
|---|---|---|
| 数据备份 | 每日凌晨2点 | 数据库+文件全备份 |
| 日志清理 | 每周日凌晨3点 | 清理90天前日志 |
| 系统更新 | 每月第一周 | 自动更新容器镜像 |
| 安全检查 | 每日 | 异常访问检测 |

## 📱 设备支持

### 桌面端
- **浏览器**：Chrome/Firefox/Safari/Edge (最新稳定版)
- **推荐分辨率**：1920×1080 及以上
- **功能**：完整功能支持

### 平板端
- **iPad**：iOS 12+，Safari或Chrome
- **Android**：Android 8+，Chrome浏览器
- **推荐分辨率**：1024×768 及以上

### 手机端
- **iPhone**：iOS 12+，Safari浏览器
- **Android**：Android 8+，Chrome浏览器
- **推荐分辨率**：360×640 及以上

## 📈 扩展功能

### API接口
访问 `/api/docs` 查看完整的API文档，支持：
- JWT身份认证
- RESTful设计
- Swagger文档
- 错误码标准

### 系统扩展
- **云存储**：支持阿里云OSS、AWS S3
- **单点登录**：支持LDAP/OAuth2
- **消息通知**：支持邮件、短信、微信
- **审计系统**：支持ELK日志分析

## 🆘 技术支持

### 问题反馈
1. Issue模板提交
2. 在线文档查询
3. 邮件技术支持：support@company.com

### 社区支持
- 开发文档：/docs目录
- 用户手册：/docs/user/README.md
- 部署指南：/docs/deployment/README.md

## 📄 许可证

本项目采用 **MIT License** 开源，详细条款见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

我们欢迎各种形式的贡献：

1. **Bug修复**：提交Pull Request
2. **新功能**：提交Issue提案
3. **文档完善**：修正错别字或添加使用案例
4. **测试**：提供环境测试报告

### 开发环境启动

```bash
# 开发模式
docker compose up --build

# 开发调试
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 🔍 版本历史

| 版本 | 日期 | 更新内容 |
|---|---|---|
| v1.0.0 | 2024.12 | 初始版本发布 |
| [开发中] | TBD | 云存储集成 |