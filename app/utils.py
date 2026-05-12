import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

def save_attachment(file):
    """Сохраняет вложение и возвращает (уникальное_имя, оригинальное_имя, mimetype, бинарные_данные)."""
    if not file:
        return None, None, None, None
    filename = secure_filename(file.filename)
    if not filename:
        return None, None, None, None
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    mimetype = file.content_type
    file_data = file.read()
    return unique_name, file.filename, mimetype, file_data

def save_image(file):
    """Сохраняет изображение и возвращает (mimetype, бинарные_данные)."""
    if not file:
        return None, None
    mimetype = file.content_type
    file_data = file.read()
    return mimetype, file_data
