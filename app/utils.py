import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

def save_attachment(file):
    """Сохраняет вложение и возвращает (уникальное_имя, оригинальное_имя, путь)."""
    if not file:
        return None, None, None
    filename = secure_filename(file.filename)
    if not filename:
        return None, None, None
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_name)
    file.save(file_path)
    return unique_name, file.filename, file_path

def save_image(file):
    """Сохраняет изображение и возвращает только имя файла."""
    if not file:
        return None
    filename = secure_filename(file.filename)
    if not filename:
        return None
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_name)
    file.save(file_path)
    return unique_name
