from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from app.models import File, User
from app.utils.file_utils import FileUtils
from app.utils.permissions import require_permission, can_access_file
from app.utils.security import SecurityManager

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/files', methods=['GET'])
@login_required
def api_files():
    """获取文件列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
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
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'files': [{
                'id': f.id,
                'filename': f.original_filename,
                'size': f.file_size,
                'type': f.file_type,
                'upload_date': f.upload_date.isoformat(),
                'uploaded_by': f.uploader.username,
                'is_public': f.is_public,
                'download_url': '/api/files/' + str(f.id) + '/download',
                'description': f.description
            } for f in files.items],
            'pagination': {
                'page': files.page,
                'per_page': files.per_page,
                'total': files.total,
                'pages': files.pages
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/files', methods=['POST'])
@login_required
@require_permission('files.upload')
def api_upload():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        description = request.form.get('description', '')
        is_public = request.form.get('is_public', 'false').lower() == 'true'
        
        saved_file, error = FileUtils.save_uploaded_file(
            file, description, is_public, current_user
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': '文件上传成功',
            'file': {
                'id': saved_file.id,
                'filename': saved_file.original_filename,
                'size': saved_file.file_size,
                'type': saved_file.file_type,
                'upload_date': saved_file.upload_date.isoformat(),
                'download_url': '/api/files/' + str(saved_file.id) + '/download'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/files/<int:file_id>/download', methods=['GET'])
@login_required
def api_download(file_id):
    """下载文件"""
    if not can_access_file(file_id, 'read'):
        return jsonify({'error': '没有权限访问此文件'}), 403
    
    file = File.query.get_or_404(file_id)
    
    if not os.path.exists(file.file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        file.download_count += 1
        db.session.commit()
        
        return send_file(
            file.file_path,
            as_attachment=True,
            download_name=file.original_filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/files/<int:file_id>', methods=['DELETE'])
@login_required
def api_delete_file(file_id):
    """删除文件"""
    if not can_access_file(file_id, 'delete'):
        return jsonify({'error': '没有权限删除此文件'}), 403
    
    file = File.query.get_or_404(file_id)
    
    try:
        success = FileUtils.cleanup_file(file)
        if not success:
            return jsonify({'error': '删除文件失败'}), 500
        
        return jsonify({'message': '文件删除成功'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/files/<int:file_id>', methods=['GET'])
@login_required
def api_file_detail(file_id):
    """获取文件详情"""
    if not can_access_file(file_id, 'read'):
        return jsonify({'error': '没有权限访问此文件'}), 403
    
    file = File.query.get_or_404(file_id)
    
    return jsonify({
        'id': file.id,
        'filename': file.original_filename,
        'size': file.file_size,
        'type': file.file_type,
        'mime_type': file.mime_type,
        'upload_date': file.upload_date.isoformat(),
        'uploaded_by': file.uploader.username,
        'download_count': file.download_count,
        'description': file.description,
        'is_public': file.is_public
    })

@api_bp.route('/public/files', methods=['GET'])
def api_public_files():
    """获取公共文件列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        search = request.args.get('search', '')
        
        query = File.query.filter_by(is_public=True)
        
        if search:
            query = query.filter(
                File.original_filename.contains(search) |
                File.description.contains(search)
            )
        
        files = query.order_by(File.upload_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'files': [{
                'id': f.id,
                'filename': f.original_filename,
                'size': f.file_size,
                'type': f.file_type,
                'upload_date': f.upload_date.isoformat(),
                'uploaded_by': f.uploader.username,
                'download_count': f.download_count,
                'description': f.description,
                'download_url': '/api/files/' + str(f.id) + '/download'
            } for f in files.items],
            'pagination': {
                'page': files.page,
                'per_page': files.per_page,
                'total': files.total,
                'pages': files.pages
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API文档
@api_bp.route('/docs')
def api_docs():
    """API文档"""
    return jsonify({
        'description': '资源共享平台RESTful API',
        'version': 'v1.0',
        'endpoints': [
            {
                'path': '/api/files',
                'method': 'GET',
                'description': '获取文件列表',
                'authentication': '需要'
            },
            {
                'path': '/api/files',
                'method': 'POST',
                'description': '上传文件',
                'authentication': '需要'
            },
            {
                'path': '/api/files/{file_id}',
                'method': 'GET',
                'description': '获取文件详情',
                'authentication': '需要'
            },
            {
                'path': '/api/files/{file_id}/download',
                'method': 'GET',
                'description': '下载文件',
                'authentication': '需要'
            },
            {
                'path': '/api/files/{file_id}',
                'method': 'DELETE',
                'description': '删除文件',
                'authentication': '需要'
            },
            {
                'path': '/api/public/files',
                'method': 'GET',
                'description': '获取公共文件列表',
                'authentication': '不需要'
            }
        ]
    })