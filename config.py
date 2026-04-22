import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///' + os.path.join(basedir, 'app.db')

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    ITEMS_PER_PAGE = 20

    # Настройки сессий и куки
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)  # время жизни постоянной сессии
    SESSION_COOKIE_SECURE = True   # передавать куки только по HTTPS
    SESSION_COOKIE_HTTPONLY = True # запретить доступ к куки из JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # защита от CSRF
    REMEMBER_COOKIE_DURATION = timedelta(days=30)  # время жизни куки "запомнить меня"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
