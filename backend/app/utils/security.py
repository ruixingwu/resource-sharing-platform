import os
import re
import hashlib
import secrets
from functools import wraps
from datetime import datetime
from flask import request, jsonify
from app.models import AccessLog, db

class SecurityManager:
    """安全管理器 - 防SQL注入和日志记录"""
    
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b).*(\bSELECT\b)",
        r"(\bINSERT\b).*(\bINTO\b)",
        r"(\bUPDATE\b).*(\bSET\b)",
        r"(\bDELETE\b).*(\bFROM\b)",
        r"(\bDROP\b).*(\bTABLE\b)",
        r"(\bSELECT\b).*\*",
        r"(\bOR\b)\s*1\s*=\s*1",
        r"(\bAND\b)\s*1\s*=\s*1",
        r"--",
        r"/\*.*\*/",
        r"'.*OR.*'.*=.*'",
        r"'.*AND.*'.*=.*'",
        r"chr\\(\\d+\\)",
        r"0x[0-9a-fA-F]+",
    ]
    
    @staticmethod
    def sanitize_input(input_str):
        """清理输入，防止SQL注入"""
        if not input_str:
            return input_str
        
        # 转义特殊字符
        input_str = str(input_str)
        
        # 检查SQL注入模式
        for pattern in SecurityManager.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return None
        
        return input_str
    
    @staticmethod
    def validate_file_upload(filename):
        """验证文件上传"""
        if not filename:
            return False
        
        ALLOWED_EXTENSIONS = {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx',
            'ppt', 'pptx', 'zip', 'rar', '7z', 'mp3', 'mp4', 'avi',
            'sql', 'py', 'js', 'html', 'css', 'json', 'xml'
        }
        
        ALLOWED_MIME_TYPES = {
            'text/plain', 'application/pdf', 'image/png', 'image/jpeg', 'image/gif',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
            'audio/mpeg', 'video/mp4', 'video/x-msvideo', 'application/sql',
            'text/x-python', 'application/javascript', 'text/html', 'text/css',
            'application/json', 'application/xml'
        }
        
        # 检查文件扩展名
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            return False
        
        return True
    
    @staticmethod
    def hash_filename(original_filename):
        """生成安全的文件名"""
        timestamp = str(datetime.utcnow().timestamp())
        random_str = secrets.token_hex(8)
        combined = f"{original_filename}_{timestamp}_{random_str}"
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        
        # 保留原始文件扩展名
        if '.' in original_filename:
            ext = original_filename.rsplit('.', 1)[1].lower()
            return f"{hashed}.{ext}"
        return hashed
    
    @staticmethod
    def log_access(endpoint, method, status_code, user_id=None, file_id=None, 
                   action=None, details=None, response_time=None):
        """记录访问日志"""
        ip_address = SecurityManager.get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        AccessLog.log_access(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            file_id=file_id,
            action=action,
            details=details
        )
    
    @staticmethod
    def get_client_ip():
        """获取客户端真实IP"""
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return request.remote_addr

def security_check(f):
    """安全检查的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.now()
        
        # 清理输入参数
        for key, value in request.args.items():
            sanitized = SecurityManager.sanitize_input(value)
            if sanitized is None:
                return jsonify({'error': '非法输入参数'}), 400
        
        # 清理JSON数据
        if request.is_json:
            for key, value in request.json.items():
                if isinstance(value, str):
                    sanitized = SecurityManager.sanitize_input(value)
                    if sanitized is None:
                        return jsonify({'error': '非法JSON数据'}), 400
        
        # 执行原函数
        response = f(*args, **kwargs)
        
        # 记录日志
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        user_id = None
        from flask_login import current_user
        if current_user.is_authenticated:
            user_id = current_user.id
        
        SecurityManager.log_access(
            endpoint=request.endpoint,
            method=request.method,
            status_code=response[1] if isinstance(response, tuple) else 200,
            user_id=user_id,
            response_time=response_time
        )
        
        return response
    return decorated_function