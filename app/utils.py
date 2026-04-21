import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

def save_attachment(file):
    """Сохраняет файл в uploads и возвращает имя файла."""
    if not file:
        return None
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
    file.save(file_path)
    return unique_name, file.filename, file_path