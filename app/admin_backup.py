import os
import json
import zipfile
import tempfile
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required
from sqlalchemy import inspect, MetaData, Table
from app import db
from app.decorators import role_required
from app.models import User, Category, Service, ClientService, Ticket, Message, Attachment

bp = Blueprint('admin_backup', __name__, url_prefix='/admin/backup')

def get_table_data():
    """Возвращает словарь с данными всех таблиц в виде списков словарей."""
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    data = {}
    metadata = MetaData()
    for table_name in tables:
        # Исключаем таблицу миграций alembic
        if table_name == 'alembic_version':
            continue
        table = Table(table_name, metadata, autoload_with=db.engine)
        rows = db.session.execute(table.select()).mappings().all()
        # Преобразуем datetime в строки
        serializable_rows = []
        for row in rows:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
            serializable_rows.append(row_dict)
        data[table_name] = serializable_rows
    return data

def restore_from_data(data):
    """Восстанавливает данные из словаря (удаляет существующие и вставляет новые)."""
    metadata = MetaData()
    # Удаляем данные в порядке обратном зависимостям (грубо, но для демо сойдёт)
    # Лучше использовать транзакцию и отключить проверку внешних ключей
    with db.engine.connect() as conn:
        # Отключаем проверку внешних ключей (для PostgreSQL)
        if 'postgresql' in db.engine.url.drivername:
            conn.execute(db.text("SET session_replication_role = 'replica';"))
        else:
            conn.execute(db.text("PRAGMA foreign_keys = OFF;"))
        try:
            for table_name, rows in data.items():
                table = Table(table_name, metadata, autoload_with=db.engine)
                conn.execute(table.delete())
                if rows:
                    conn.execute(table.insert(), rows)
            conn.commit()
        finally:
            if 'postgresql' in db.engine.url.drivername:
                conn.execute(db.text("SET session_replication_role = 'origin';"))
            else:
                conn.execute(db.text("PRAGMA foreign_keys = ON;"))

@bp.route('/')
@login_required
@role_required('admin')
def index():
    return render_template('admin/backup.html')

@bp.route('/create')
@login_required
@role_required('admin')
def create_backup():
    # Создаём временный ZIP-архив
    temp_dir = tempfile.mkdtemp()
    try:
        # Сохраняем дамп данных в JSON
        data = get_table_data()
        dump_path = os.path.join(temp_dir, 'db_dump.json')
        with open(dump_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Копируем папку uploads
        uploads_src = current_app.config['UPLOAD_FOLDER']
        uploads_dst = os.path.join(temp_dir, 'uploads')
        if os.path.exists(uploads_src):
            import shutil
            shutil.copytree(uploads_src, uploads_dst)

        # Создаём ZIP
        zip_path = os.path.join(temp_dir, 'backup.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(dump_path, 'db_dump.json')
            if os.path.exists(uploads_dst):
                for root, dirs, files in os.walk(uploads_dst):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, temp_dir)
                        zf.write(full_path, arcname)

        return send_file(zip_path, as_attachment=True, download_name=f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip')
    except Exception as e:
        flash(f'Ошибка создания бэкапа: {e}', 'danger')
        return redirect(url_for('admin_backup.index'))
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

@bp.route('/restore', methods=['POST'])
@login_required
@role_required('admin')
def restore_backup():
    if 'backup_file' not in request.files:
        flash('Файл не выбран', 'danger')
        return redirect(url_for('admin_backup.index'))
    file = request.files['backup_file']
    if file.filename == '':
        flash('Файл не выбран', 'danger')
        return redirect(url_for('admin_backup.index'))

    temp_dir = tempfile.mkdtemp()
    try:
        zip_path = os.path.join(temp_dir, 'backup.zip')
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir)

        dump_path = os.path.join(temp_dir, 'db_dump.json')
        if not os.path.exists(dump_path):
            flash('Неверный формат бэкапа: отсутствует db_dump.json', 'danger')
            return redirect(url_for('admin_backup.index'))

        with open(dump_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Восстанавливаем данные
        restore_from_data(data)

        # Восстанавливаем файлы uploads
        uploads_dst = current_app.config['UPLOAD_FOLDER']
        uploads_src = os.path.join(temp_dir, 'uploads')
        if os.path.exists(uploads_src):
            import shutil
            if os.path.exists(uploads_dst):
                shutil.rmtree(uploads_dst)
            shutil.copytree(uploads_src, uploads_dst)

        flash('База данных успешно восстановлена.', 'success')
    except Exception as e:
        flash(f'Ошибка восстановления: {e}', 'danger')
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    return redirect(url_for('admin_backup.index'))
