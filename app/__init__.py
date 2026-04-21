import os
import subprocess
import sys
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

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

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Автоматическое применение миграций
    with app.app_context():
        apply_migrations()

    from app.routes import auth, main, admin, operator, client, executor, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(operator.bp, url_prefix='/operator')
    app.register_blueprint(client.bp, url_prefix='/client')
    app.register_blueprint(executor.bp, url_prefix='/executor')
    app.register_blueprint(api.bp, url_prefix='/api')

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
