from functools import wraps
from flask import jsonify, request
from flask_login import current_user
from app.models import File

def has_permission(permission_name):
    """Check if current user has a specific permission"""
    if not current_user.is_authenticated:
        return False
    return current_user.has_permission(permission_name)

def can_access_file(file_id, permission_type='read'):
    """Check if user can access a specific file"""
    if not current_user.is_authenticated:
        return False
    
    file = File.query.get(file_id)
    if not file:
        return False
    
    # Owner can access their own files
    if file.uploaded_by == current_user.id:
        return True
    
    # Admin can access all files
    if current_user.is_admin:
        return True
    
    # Check file permissions
    for permission in file.permissions:
        if permission.user_id == current_user.id and permission.permission_type == permission_type:
            return True
    
    # Public files can be read by anyone
    if permission_type == 'read' and file.is_public:
        return True
    
    return False

def require_permission(permission_name):
    """Decorator to require a specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(permission_name):
                return jsonify({'error': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_file_access(permission_type='read'):
    """Decorator to require file access permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            file_id = request.view_args.get('file_id') or request.args.get('file_id')
            if not file_id:
                return jsonify({'error': '未指定文件ID'}), 400
            
            if not can_access_file(file_id, permission_type):
                return jsonify({'error': '没有权限访问此文件'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class PermissionManager:
    """权限管理器"""
    
    PERMISSIONS = {
        'files.upload': '上传文件',
        'files.download': '下载文件', 
        'files.delete': '删除文件',
        'files.view_all': '查看所有文件',
        'admin.manage_users': '管理用户',
        'admin.manage_permissions': '管理权限',
        'admin.view_logs': '查看日志',
        'admin.backup': '执行备份'
    }
    
    ROLES = {
        'admin': ['files.upload', 'files.download', 'files.delete', 'files.view_all',
                  'admin.manage_users', 'admin.manage_permissions', 'admin.view_logs',
                  'admin.backup'],
        'editor': ['files.upload', 'files.download', 'files.view_all'],
        'user': ['files.upload', 'files.download'],
        'viewer': ['files.download']
    }
    
    @staticmethod
    def init_permissions():
        """初始化权限和角色数据"""
        from app.models import Role, Permission, db
        
        # Clean existing data
        Role.query.delete()
        Permission.query.delete()
        db.session.commit()
        
        # Create permissions
        for permission_name, description in PermissionManager.PERMISSIONS.items():
            permission = Permission(name=permission_name, description=description)
            db.session.add(permission)
        
        # Create roles
        for role_name, permissions in PermissionManager.ROLES.items():
            role = Role(name=role_name, description=f'{role_name}角色')
            
            # Add permissions to role
            for permission_name in permissions:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission:
                    role.permissions.append(permission)
            
            db.session.add(role)
        
        db.session.commit()