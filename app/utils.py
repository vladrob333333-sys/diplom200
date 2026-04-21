import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

def save_attachment(file):
    """
    Сохраняет файл в папку uploads и возвращает кортеж:
    (уникальное_имя, оригинальное_имя, полный_путь)
    Если file == None или пустой, возвращает (None, None, None).
    """
    if not file:
        return None, None, None

    filename = secure_filename(file.filename)
    if not filename:
        return None, None, None

    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
    file.save(file_path)
    return unique_name, file.filename, file_path
