import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'qa-studio-secret-key-2024'
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    EXPORT_FOLDER = os.path.join('static', 'exports')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}
    
    # Answer length configurations by marks
    ANSWER_CONFIG = {
        '1': {'max_words': 2, 'max_lines': 1, 'description': 'Brief (2 words)'},
        '2': {'max_words': 20, 'max_lines': 2, 'description': 'Short (2 lines)'},
        '4': {'max_words': 80, 'max_lines': 5, 'description': 'Medium (5 lines)'},
        '7': {'max_words': 150, 'max_lines': 8, 'description': 'Detailed (8 lines)'}
    }
