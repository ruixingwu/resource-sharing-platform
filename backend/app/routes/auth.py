from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app.models import User, Role, db
from app.utils.security import SecurityManager

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember = data.get('remember', False)
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            
            SecurityManager.log_access(
                endpoint='auth.login',
                method='POST', 
                status_code=200,
                user_id=user.id,
                action='login',
                details={'username': username}
            )
            
            return jsonify({'message': '登录成功', 'redirect': url_for('files.index')})
        
        SecurityManager.log_access(
            endpoint='auth.login',
            method='POST',
            status_code=401,
            action='login_failed',
            details={'username': username}
        )
        
        return jsonify({'error': '用户名或密码错误'}), 401

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': '请填写所有必填字段'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已存在'}), 400
        
        if len(password) < 6:
            return jsonify({'error': '密码长度至少为6位'}), 400
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Assign default user role
        user_role = Role.query.filter_by(name='user').first()
        if user_role:
            user.roles.append(user_role)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': '注册成功，请登录', 'redirect': url_for('auth.login')})

@auth_bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id if current_user.is_authenticated else None
    logout_user()
    
    SecurityManager.log_access(
        endpoint='auth.logout',
        method='GET',
        status_code=302,
        user_id=user_id,
        action='logout'
    )
    
    flash('您已成功退出登录', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)