from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.decorators import role_required
from app.models import User, Service, Category, Ticket, ClientService
from app.forms import UserForm, ServiceForm, CategoryForm
from app.utils import save_image

bp = Blueprint('admin', __name__)

@bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    stats = {
        'users': User.query.count(),
        'services': Service.query.count(),
        'tickets': Ticket.query.count(),
        'open_tickets': Ticket.query.filter(Ticket.status.in_(['new', 'in_progress', 'waiting_client', 'waiting_operator'])).count()
    }
    return render_template('admin/dashboard.html', stats=stats)

@bp.route('/users')
@login_required
@role_required('admin')
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            contract_number=form.contract_number.data,
            role=form.role.data,
            is_active=form.is_active.data
        )
        if form.password.data:
            user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь создан.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', form=form, title='Создать пользователя')

@bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.phone = form.phone.data
        user.contract_number = form.contract_number.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Пользователь обновлён.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', form=form, title='Редактировать пользователя')

@bp.route('/users/<int:id>/toggle_active')
@login_required
@role_required('admin')
def toggle_user_active(id):
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'Статус пользователя изменён.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/services')
@login_required
@role_required('admin')
def services():
    services = Service.query.order_by(Service.name).all()
    return render_template('admin/services.html', services=services)

@bp.route('/services/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_service():
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category_id=form.category_id.data,
            is_active=form.is_active.data
        )
        db.session.add(service)
        db.session.commit()
        flash('Услуга создана.', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_form.html', form=form, title='Создать услугу')

@bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_service(id):
    service = Service.query.get_or_404(id)
    form = ServiceForm(obj=service)
    if form.validate_on_submit():
        service.name = form.name.data
        service.description = form.description.data
        service.price = form.price.data
        service.category_id = form.category_id.data
        service.is_active = form.is_active.data
        db.session.commit()
        flash('Услуга обновлена.', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_form.html', form=form, title='Редактировать услугу')

@bp.route('/categories')
@login_required
@role_required('admin')
def categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            parent_id=form.parent_id.data if form.parent_id.data != 0 else None
        )
        db.session.add(category)
        db.session.commit()
        flash('Категория создана.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', form=form, title='Создать категорию')

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        db.session.commit()
        flash('Категория обновлена.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', form=form, title='Редактировать категорию')

@bp.route('/tickets')
@login_required
@role_required('admin')
def tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('admin/tickets.html', tickets=tickets)

# Новые маршруты для управления клиентами и их услугами
@bp.route('/clients')
@login_required
@role_required('admin')
def clients():
    clients = User.query.filter_by(role='client').order_by(User.created_at.desc()).all()
    return render_template('admin/clients.html', clients=clients)

@bp.route('/clients/<int:id>/services', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def client_services(id):
    client = User.query.get_or_404(id)
    if client.role != 'client':
        flash('Пользователь не является клиентом.', 'danger')
        return redirect(url_for('admin.clients'))
    if request.method == 'POST':
        selected_services = request.form.getlist('services')
        ClientService.query.filter_by(client_id=client.id).delete()
        for service_id in selected_services:
            cs = ClientService(client_id=client.id, service_id=int(service_id))
            db.session.add(cs)
        db.session.commit()
        flash('Услуги клиента обновлены.', 'success')
        return redirect(url_for('admin.client_services', id=client.id))
    services = Service.query.filter_by(is_active=True).order_by(Service.name).all()
    client_service_ids = [cs.service_id for cs in client.client_services]
    return render_template('admin/client_services.html', client=client, services=services, client_service_ids=client_service_ids)
