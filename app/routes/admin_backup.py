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

bp = Blueprint('admin_backup', __name__, url_prefix='/admin/backup')

def get_table_data():
    """Возвращает словарь с данными всех таблиц в виде списков словарей."""
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    data = {}
    metadata = MetaData()
    for table_name in tables:
        if table_name == 'alembic_version':
            continue
        table = Table(table_name, metadata, autoload_with=db.engine)
        rows = db.session.execute(table.select()).mappings().all()
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
    """Восстанавливает данные из словаря с учётом порядка зависимостей."""
    metadata = MetaData()
    # Порядок удаления (от зависимых к независимым) и вставки (наоборот)
    table_order = [
        'attachments',
        'messages',
        'client_services',
        'tickets',
        'services',
        'categories',
        'users'
    ]
    with db.engine.connect() as conn:
        # Для SQLite отключаем проверку FK
        is_sqlite = 'sqlite' in db.engine.url.drivername
        if is_sqlite:
            conn.execute(db.text("PRAGMA foreign_keys = OFF;"))
        try:
            # Удаляем данные в порядке, обратном зависимостям
            for table_name in table_order:
                if table_name in data:
                    table = Table(table_name, metadata, autoload_with=db.engine)
                    conn.execute(table.delete())
            # Вставляем данные
            for table_name in reversed(table_order):
                if table_name in data and data[table_name]:
                    table = Table(table_name, metadata, autoload_with=db.engine)
                    conn.execute(table.insert(), data[table_name])
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            if is_sqlite:
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
    temp_dir = tempfile.mkdtemp()
    try:
        data = get_table_data()
        dump_path = os.path.join(temp_dir, 'db_dump.json')
        with open(dump_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        uploads_src = current_app.config['UPLOAD_FOLDER']
        uploads_dst = os.path.join(temp_dir, 'uploads')
        if os.path.exists(uploads_src):
            import shutil
            shutil.copytree(uploads_src, uploads_dst)

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

        restore_from_data(data)

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
