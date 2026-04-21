import os
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

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Создание папки uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Регистрация blueprints
    from app.routes import auth, main, admin, operator, client
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(operator.bp, url_prefix='/operator')
    app.register_blueprint(client.bp, url_prefix='/client')

    # Обработчики ошибок (теперь внутри create_app)
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    # CLI команда для создания админа
    @app.cli.command("create-admin")
    def create_admin():
        """Создать администратора."""
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
