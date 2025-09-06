from .auth import auth_bp
from .files import files_bp
from .admin import admin_bp
from .api import api_bp

__all__ = ['auth_bp', 'files_bp', 'admin_bp', 'api_bp']