from flask import Blueprint, render_template, request
from app.models import Service, Category

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    categories = Category.query.order_by(Category.name).all()
    category_id = request.args.get('category', type=int)
    query = Service.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    services = query.order_by(Service.name).all()
    return render_template('index.html', services=services, categories=categories, selected_category=category_id)
