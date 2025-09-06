import os
import mimetypes
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file, url_for, current_app
from flask_login import login_required, current_user
from app.models import File, db
from app.utils.file_utils import FileUtils
from app.utils.permissions import require_permission, require_file_access, can_access_file
from app.utils.security import SecurityManager

files_bp = Blueprint('files', __name__, url_prefix='/files')

@files_bp.route('/')  
@login_required
def index():
    """文件列表页面"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = File.query
    
    # 普通用户只能看到自己上传的文件
    if not current_user.is_admin:
        query = query.filter_by(uploaded_by=current_user.id)
    
    if search:
        query = query.filter(
            File.original_filename.contains(search) |
            File.description.contains(search)
        )
    
    files = query.order_by(File.upload_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('files/index.html', files=files, search=search)

@files_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@require_permission('files.upload')
def upload():
    """文件上传"""
    if request.method == 'GET':
        return render_template('files/upload.html')
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        description = request.form.get('description', '')
        is_public = request.form.get('is_public', 'false').lower() == 'true'
        
        try:
            saved_file, error = FileUtils.save_uploaded_file(
                file, description, is_public, current_user
            )
            
            if error:
                return jsonify({'error': error}), 400
            
            SecurityManager.log_access(
                endpoint='files.upload',
                method='POST',
                status_code=200,
                user_id=current_user.id,
                file_id=saved_file.id,
                action='upload',
                details={'filename': saved_file.original_filename, 'size': saved_file.file_size}
            )
            
            return jsonify({
                'message': '文件上传成功',
                'file': {
                    'id': saved_file.id,
                    'filename': saved_file.original_filename,
                    'url': url_for('files.download', file_id=saved_file.id)
                }
            })
            
        except Exception as e:
            SecurityManager.log_access(
                endpoint='files.upload',
                method='POST',
                status_code=500,
                user_id=current_user.id,
                action='upload_failed',
                details={'error': str(e)}
            )
            return jsonify({'error': '上传失败，请重试'}), 500

@files_bp.route('/download/<int:file_id>')
@login_required
@require_file_access('read')
def download(file_id):
    """文件下载"""
    file = File.query.get_or_404(file_id)
    
    if not os.path.exists(file.file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        file.download_count += 1
        db.session.commit()
        
        SecurityManager.log_access(
            endpoint='files.download',
            method='GET',
            status_code=200,
            user_id=current_user.id,
            file_id=file.id,
            action='download',
            details={'filename': file.original_filename, 'size': file.file_size}
        )
        
        # 设置正确的文件名
        filename = file.original_filename.encode('utf-8').decode('latin-1')
        
        return send_file(
            file.file_path,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': '下载失败'}), 500

@files_bp.route('/delete/<int:file_id>', methods=['DELETE'])
@login_required
@require_file_access('delete')
def delete(file_id):
    """删除文件"""
    file = File.query.get_or_404(file_id)
    
    if file.uploaded_by != current_user.id and not current_user.is_admin:
        return jsonify({'error': '没有权限删除此文件'}), 403
    
    try:
        success = FileUtils.cleanup_file(file)
        if not success:
            return jsonify({'error': '删除文件失败'}), 500
        
        SecurityManager.log_access(
            endpoint='files.delete',
            method='DELETE',
            status_code=200,
            user_id=current_user.id,
            file_id=file_id,
            action='delete',
            details={'filename': file.original_filename}
        )
        
        return jsonify({'message': '文件删除成功'})
        
    except Exception as e:
        return jsonify({'error': '删除失败'}), 500

@files_bp.route('/public')
def public_files():
    """公共文件列表"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = File.query.filter_by(is_public=True)
    
    if search:
        query = query.filter(
            File.original_filename.contains(search) |
            File.description.contains(search)
        )
    
    files = query.order_by(File.upload_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('files/public.html', files=files, search=search)

@files_bp.route('/detail/<int:file_id>')
@login_required
def detail(file_id):
    """文件详情"""
    file = File.query.get_or_404(file_id)
    
    if file.uploaded_by != current_user.id and not file.is_public and not current_user.is_admin:
        if not any(p.user_id == current_user.id for p in file.permissions):
            return jsonify({'error': '没有权限查看此文件'}), 403
    
    return render_template('files/detail.html', file=file)