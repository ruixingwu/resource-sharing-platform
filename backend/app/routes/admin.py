from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import User, File, AccessLog, Role, db
from app.utils.permissions import require_permission

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@require_permission('admin.manage_users')
def dashboard():
    """管理后台首页"""
    # 统计数据
    total_users = User.query.count()
    total_files = File.query.count()
    total_size = db.session.query(func.sum(File.file_size)).scalar() or 0
    
    # 获取最近7天的文件上传统计
    today = datetime.utcnow()
    seven_days_ago = today - timedelta(days=7)
    
    daily_uploads = db.session.query(
        func.date(File.upload_date).label('date'),
        func.count(File.id).label('count'),
        func.sum(File.file_size).label('size')
    ).filter(
        File.upload_date >= seven_days_ago
    ).group_by(
        func.date(File.upload_date)
    ).all()
    
    # 获取系统资源使用情况
    recent_logs = AccessLog.query.order_by(AccessLog.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', **{
        'total_users': total_users,
        'total_files': total_files,
        'total_size': total_size,
        'daily_uploads': daily_uploads,
        'recent_logs': recent_logs,
    })

@admin_bp.route('/users')
@login_required
@require_permission('admin.manage_users')
def users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            User.username.contains(search) |
            User.email.contains(search)
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>')
@login_required
@require_permission('admin.manage_users')
def user_detail(user_id):
    """用户详情"""
    user = User.query.get_or_404(user_id)
    user_files = File.query.filter_by(uploaded_by=user.id).order_by(File.upload_date.desc()).all()
    
    return render_template('admin/user_detail.html', user=user, user_files=user_files)

@admin_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@login_required
@require_permission('admin.manage_permissions')
def update_user_roles(user_id):
    """更新用户角色"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data or 'roles' not in data:
        return jsonify({'error': '缺少角色数据'}), 400
    
    role_names = data['roles']
    user.roles.clear()
    
    for role_name in role_names:
        role = Role.query.filter_by(name=role_name).first()
        if role:
            user.roles.append(role)
    
    db.session.commit()
    
    return jsonify({'message': '角色更新成功'})

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@login_required
@require_permission('admin.manage_users')
def update_user_status(user_id):
    """更新用户状态"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    is_active = data.get('is_active', True)
    user.is_active = is_active
    
    db.session.commit()
    
    return jsonify({'message': '用户状态更新成功'})

@admin_bp.route('/files')
@login_required
@require_permission('admin.view_logs')
def files():
    """文件管理"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = File.query
    
    if search:
        query = query.filter(
            File.original_filename.contains(search)
        )
    
    files = query.order_by(File.upload_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/files.html', files=files, search=search)

@admin_bp.route('/logs')
@login_required
@require_permission('admin.view_logs')
def logs():
    """系统日志"""
    page = request.args.get('page', 1, type=int)
    
    # 获取最近一个月的日志
    from datetime import datetime, timedelta
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    
    logs = AccessLog.query.filter(
        AccessLog.created_at >= one_month_ago
    ).order_by(
        AccessLog.created_at.desc()
    ).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/backup')
@login_required
@require_permission('admin.backup')
def backup():
    """备份管理"""
    return render_template('admin/backup.html')