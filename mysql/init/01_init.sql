-- 初始化数据库
USE resource_sharing;

-- 创建基本权限
INSERT INTO permission (name, description) VALUES 
('files.upload', '上传文件'),
('files.download', '下载文件'),
('files.delete', '删除文件'),
('files.view_all', '查看所有文件'),
('admin.manage_users', '管理用户'),
('admin.manage_permissions', '管理权限'),
('admin.view_logs', '查看日志'),
('admin.backup', '执行备份');

-- 创建基本角色
INSERT INTO role (name, description) VALUES 
('admin', '管理员角色，拥有所有权限'),
('editor', '编辑角色，可以上传和查看文件'),
('user', '普通用户角色，可以上传和下载文件'),
('viewer', '浏览角色，只能下载文件');

-- 分配角色权限
-- admin角色的权限
INSERT INTO role_permissions (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'admin';

-- editor角色的权限
INSERT INTO role_permissions (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p 
WHERE r.name = 'editor' AND p.name IN ('files.upload', 'files.download', 'files.view_all');

-- user角色的权限
INSERT INTO role_permissions (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p 
WHERE r.name = 'user' AND p.name IN ('files.upload', 'files.download');

-- viewer角色的权限
INSERT INTO role_permissions (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p 
WHERE r.name = 'viewer' AND p.name = 'files.download';

-- 创建默认管理员用户
INSERT INTO user (username, email, password_hash, is_admin, is_active) VALUES 
('admin', 'admin@localhost', '$6$rounds=1000$/8W8pKx3G3h3JcZ8$4J9Z2h3J4k5L6M7N8P9Q0R1S2T3U4V5W6X7Y8Z9a0b1c2d3e4f5g6h7i8j9k0', 1, 1);

-- 给管理员分配admin角色
INSERT INTO user_roles (user_id, role_id) 
SELECT u.id, r.id FROM user u, role r WHERE u.username = 'admin' AND r.name = 'admin';

-- 设置字符集
ALTER DATABASE resource_sharing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;