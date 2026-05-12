import os
from datetime import datetime
from flask import Flask, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from sqlalchemy import inspect, text
import io

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

def apply_migrations():
    """Автоматически применяет миграции Alembic."""
    try:
        from alembic.config import Config
        from alembic import command
        alembic_ini_path = os.path.join(os.getcwd(), 'migrations', 'alembic.ini')
        if os.path.exists(alembic_ini_path):
            alembic_cfg = Config(alembic_ini_path)
            command.upgrade(alembic_cfg, "head")
            print("Миграции успешно применены.")
    except Exception as e:
        print(f"Ошибка применения миграций: {e}")

def ensure_executor_column(app):
    """Проверяет наличие колонки executor_id в таблице tickets и добавляет её, если нет."""
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            if 'tickets' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('tickets')]
                if 'executor_id' not in columns:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE tickets ADD COLUMN executor_id INTEGER REFERENCES users(id)"))
                        conn.commit()
                        app.logger.info("Колонка executor_id добавлена в таблицу tickets.")
        except Exception as e:
            app.logger.error(f"Ошибка при добавлении колонки executor_id: {e}")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.remember_cookie_duration = app.config['REMEMBER_COOKIE_DURATION']
    login_manager.session_protection = "strong"
    csrf.init_app(app)
    limiter.init_app(app)

    # Создание папки uploads для временных файлов (больше не используется для хранения)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        apply_migrations()

    ensure_executor_column(app)

    # Импорт blueprints внутри функции для избежания циклических зависимостей
    from app.routes import auth, main, admin, operator, client, executor, api
    try:
        from app.routes import admin_backup
        has_backup = True
    except ImportError:
        has_backup = False

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(operator.bp, url_prefix='/operator')
    app.register_blueprint(client.bp, url_prefix='/client')
    app.register_blueprint(executor.bp, url_prefix='/executor')
    app.register_blueprint(api.bp, url_prefix='/api')
    if has_backup:
        app.register_blueprint(admin_backup.bp)

    # Маршрут для отдачи изображений услуг из БД
    @app.route('/service_image/<int:service_id>')
    def service_image(service_id):
        from app.models import Service
        service = Service.query.get_or_404(service_id)
        if service.image_data and service.image_mimetype:
            return send_file(
                io.BytesIO(service.image_data),
                mimetype=service.image_mimetype,
                as_attachment=False,
                download_name=f'image_{service_id}'
            )
        # Возвращаем заглушку, если изображения нет
        return '', 404

    # Маршрут для отдачи вложений из БД
    @app.route('/attachment/<int:attachment_id>')
    def attachment_file(attachment_id):
        from app.models import Attachment
        attachment = Attachment.query.get_or_404(attachment_id)
        if attachment.file_data and attachment.file_mimetype:
            return send_file(
                io.BytesIO(attachment.file_data),
                mimetype=attachment.file_mimetype,
                as_attachment=True,
                download_name=attachment.original_name or attachment.filename
            )
        # Если данных в БД нет, пробуем отдать файл с диска
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=attachment.original_name or attachment.filename)
        return '', 404

    # Контекстный процессор для отображения текущей даты в шаблонах
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"DB creation error: {e}")

        from app.models import User
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
            admin = User(
                username=admin_username,
                email=admin_email,
                role='admin',
                full_name='System Administrator',
                is_active=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            app.logger.info(f"Default admin created: {admin_username} / {admin_password}")

    @app.cli.command("create-admin")
    def create_admin():
        from app.models import User
        import getpass
        username = input("Username: ")
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        with app.app_context():
            if User.query.filter((User.username == username) | (User.email == email)).first():
                print("Пользователь уже существует.")
                return
            admin = User(username=username, email=email, role='admin')
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print("Администратор создан.")

    return app
