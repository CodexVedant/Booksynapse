"""
Configuration module - loads environment variables and sets up paths
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory - ensure it's absolute
BASE_DIR = Path(__file__).parent.resolve()

# Create required directories
INSTANCE_FOLDER = BASE_DIR / 'instance'
DATA_FOLDER = BASE_DIR / 'data'
UPLOAD_FOLDER = DATA_FOLDER / 'raw'

for folder in [INSTANCE_FOLDER, DATA_FOLDER, UPLOAD_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# Compute database URI at module level (after directories are created)
_db_uri_env = os.getenv('DATABASE_URL')
if _db_uri_env and _db_uri_env.startswith('sqlite:///'):
    # If relative path in env, convert to absolute
    db_path_str = _db_uri_env.replace('sqlite:///', '')
    if not os.path.isabs(db_path_str):
        # Convert relative path to absolute based on BASE_DIR
        db_path = (BASE_DIR / db_path_str).resolve()
        _default_db_uri = f'sqlite:///{db_path.as_posix()}'
    else:
        # Already absolute, just convert slashes
        _default_db_uri = f'sqlite:///{db_path_str.replace(chr(92), "/")}'
elif _db_uri_env:
    _default_db_uri = _db_uri_env
else:
    # Use absolute path - convert to forward slashes using as_posix()
    # Build path directly from BASE_DIR to ensure it's absolute
    _db_file_path = BASE_DIR / 'instance' / 'ai_book_recommender.db'
    _abs_path = _db_file_path.as_posix()
    _default_db_uri = f'sqlite:///{_abs_path}'


class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-2024')
    
    # Database URI (computed at module level)
    SQLALCHEMY_DATABASE_URI = _default_db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Paths
    EMBEDDINGS_PATH = DATA_FOLDER / 'embeddings.pkl'
    BOOKS_INDEX_PATH = DATA_FOLDER / 'books_index.pkl'
    CF_MATRIX_PATH = DATA_FOLDER / 'cf_matrix.pkl'
    
    # CSV paths (optional)
    GOODREADS_BOOKS_PATH = os.getenv('GOODREADS_BOOKS_PATH', '')
    GOODREADS_RATINGS_PATH = os.getenv('GOODREADS_RATINGS_PATH', '')
    GOODREADS_TAGS_PATH = os.getenv('GOODREADS_TAGS_PATH', '')
    GOODREADS_BOOK_TAGS_PATH = os.getenv('GOODREADS_BOOK_TAGS_PATH', '')
    GOODREADS_RATINGS_LIMIT = int(os.getenv('GOODREADS_RATINGS_LIMIT', '0'))
    
    # Upload settings
    UPLOAD_FOLDER = str(UPLOAD_FOLDER)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Debug
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Admin credentials (for create_admin.py)
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

