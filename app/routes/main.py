from flask import Blueprint, render_template
from app.models import Service

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Получаем все активные услуги с категориями
    services = Service.query.filter_by(is_active=True).order_by(Service.name).all()
    return render_template('index.html', services=services)
