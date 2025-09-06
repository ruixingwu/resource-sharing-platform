from datetime import datetime
from app import db

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500))
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time = db.Column(db.Float)  # in milliseconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)
    action = db.Column(db.String(50))  # 'upload', 'download', 'delete', 'view', 'login', 'logout'
    details = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref='access_logs')
    file = db.relationship('File', backref='access_logs')
    
    def __repr__(self):
        return f'<AccessLog {self.user_id}:{self.endpoint}>'
    
    @staticmethod
    def log_access(user_id, ip_address, endpoint, method, status_code, 
                   response_time=None, file_id=None, action=None, details=None, user_agent=None):
        """Log an access event"""
        log_entry = AccessLog(
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
        db.session.add(log_entry)
        db.session.commit()
        return log_entry