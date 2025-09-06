from datetime import datetime
from sqlalchemy.sql import func
from app import db

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), unique=True, nullable=False, index=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_files')
    permissions = db.relationship('FilePermission', backref='file', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<File {self.original_filename}>'
    
    @property
    def size_human_readable(self):
        """Return human-readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    @property
    def is_image(self):
        return self.mime_type.startswith('image/')
    
    @property
    def is_document(self):
        document_types = ['application/pdf', 'application/msword',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'application/vnd.ms-excel',
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        return self.mime_type in document_types

class FilePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_type = db.Column(db.String(20), nullable=False)  # 'read', 'write', 'delete'
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='file_permissions')
    granted_by_user = db.relationship('User', foreign_keys=[granted_by])
    
    def __repr__(self):
        return f'<FilePermission {self.permission_type} for {self.file_id}>'