import os
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from PIL import Image
from app.models import File, db
from app.utils.security import SecurityManager

class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def get_file_type(filename, mime_type):
        """根据文件名和MIME类型确定文件类型"""
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'}
        document_extensions = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}
        archive_extensions = {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'}
        
        if file_ext in image_extensions or mime_type.startswith('image/'):
            return 'image'
        elif file_ext in document_extensions or mime_type.startswith('application/'):
            return 'document'
        elif file_ext in archive_extensions:
            return 'archive'
        else:
            return 'other'
    
    @staticmethod
    def save_uploaded_file(file, description=None, is_public=False, user=None):
        """保存上传的文件"""
        if not file or not file.filename:
            return None, '没有选择文件'
        
        # 验证文件
        if not SecurityManager.validate_file_upload(file.filename):
            return None, '文件类型不被允许'
        
        original_filename = secure_filename(file.filename)
        
        # 生成安全文件名
        safe_filename = SecurityManager.hash_filename(original_filename)
        
        # 确保上传目录存在
        upload_folder = os.getenv('UPLOAD_FOLDER', '/app/uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # 创建子目录按用户ID组织
        user_folder = os.path.join(upload_folder, str(user.id))
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        file_path = os.path.join(user_folder, safe_filename)
        file.save(file_path)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_type = FileUtils.get_file_type(original_filename, file.mimetype)
        
        # 保存文件记录到数据库
        new_file = File(
            original_filename=original_filename,
            filename=safe_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            mime_type=file.mimetype,
            uploaded_by=user.id,
            is_public=is_public,
            description=description
        )
        
        db.session.add(new_file)
        db.session.commit()
        
        return new_file, None
    
    @staticmethod
    def generate_thumbnail(file_path, thumbnail_path, max_size=(150, 150)):
        """为图片生成缩略图"""
        try:
            with Image.open(file_path) as img:
                img.thumbnail(max_size)
                thumbnail_dir = os.path.dirname(thumbnail_path)
                if not os.path.exists(thumbnail_dir):
                    os.makedirs(thumbnail_dir)
                img.save(thumbnail_path)
                return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_stats(user_id=None):
        """获取文件统计信息"""
        query = db.session.query(File)
        
        if user_id:
            query = query.filter(File.uploaded_by == user_id)
        
        total_files = query.count()
        total_size = query.with_entities(db.func.sum(File.file_size)).scalar() or 0
        
        file_type_stats = db.session.query(
            File.file_type,
            db.func.count(File.id).label('count'),
            db.func.sum(File.file_size).label('size')
        ).group_by(File.file_type).all()
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'file_types': {stat.file_type: {'count': stat.count, 'size': stat.size} 
                          for stat in file_type_stats}
        }
    
    @staticmethod
    def cleanup_file(file_record):
        """删除文件和数据库记录"""
        try:
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
            
            # 删除缩略图
            thumbnail_path = file_record.file_path.replace('/uploads/', '/uploads/thumbnails/')
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            
            db.session.delete(file_record)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False, str(e)