from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.decorators import role_required
from app.models import User, Service, ClientService, Ticket, Message, Attachment
from app.forms import ClientRegistrationByOperatorForm, TicketForm, MessageForm
from app.utils import save_attachment


bp = Blueprint('operator', __name__)

@bp.route('/')
@login_required
@role_required('operator', 'admin')
def dashboard():
    stats = {
        'clients': User.query.filter_by(role='client').count(),
        'open_tickets': Ticket.query.filter(Ticket.status.in_(['new', 'in_progress', 'waiting_client', 'waiting_operator'])).count(),
        'my_tickets': Ticket.query.filter_by(operator_id=current_user.id).filter(Ticket.status != 'closed').count()
    }
    return render_template('operator/dashboard.html', stats=stats)

@bp.route('/clients')
@login_required
@role_required('operator', 'admin')
def clients():
    clients = User.query.filter_by(role='client').order_by(User.created_at.desc()).all()
    return render_template('operator/clients.html', clients=clients)

@bp.route('/clients/create', methods=['GET', 'POST'])
@login_required
@role_required('operator', 'admin')
def create_client():
    form = ClientRegistrationByOperatorForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            contract_number=form.contract_number.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            role='client'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Клиент успешно создан.', 'success')
        return redirect(url_for('operator.clients'))
    return render_template('operator/client_form.html', form=form)

@bp.route('/clients/<int:id>/services', methods=['GET', 'POST'])
@login_required
@role_required('operator', 'admin')
def client_services(id):
    client = User.query.get_or_404(id)
    if client.role != 'client':
        flash('Пользователь не является клиентом.', 'danger')
        return redirect(url_for('operator.clients'))
    if request.method == 'POST':
        selected_services = request.form.getlist('services')
        ClientService.query.filter_by(client_id=client.id).delete()
        for service_id in selected_services:
            cs = ClientService(client_id=client.id, service_id=int(service_id))
            db.session.add(cs)
        db.session.commit()
        flash('Услуги клиента обновлены.', 'success')
        return redirect(url_for('operator.client_services', id=client.id))
    services = Service.query.filter_by(is_active=True).order_by(Service.name).all()
    client_service_ids = [cs.service_id for cs in client.client_services]
    return render_template('operator/client_services.html', client=client, services=services, client_service_ids=client_service_ids)

@bp.route('/tickets')
@login_required
@role_required('operator', 'admin')
def tickets():
    # Оператор видит все заявки (можно оставить так или ограничить по operator_id)
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('operator/tickets.html', tickets=tickets)

@bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
@role_required('operator', 'admin')
def create_ticket():
    form = TicketForm()
    clients = User.query.filter_by(role='client', is_active=True).order_by(User.full_name).all()
    form.client_id.choices = [(c.id, f"{c.full_name} ({c.contract_number})") for c in clients]
    # Услуги можно привязать к выбранному клиенту, но упростим: все активные услуги
    form.service_id.choices = [(s.id, s.name) for s in Service.query.filter_by(is_active=True).order_by(Service.name).all()]
    if form.validate_on_submit():
        client_id = form.client_id.data if form.client_id.data else None
        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            client_id=client_id,
            operator_id=current_user.id,
            service_id=form.service_id.data if form.service_id.data else None,
            status='new',
            created_by_operator=True
        )
        db.session.add(ticket)
        db.session.flush()
        attachments = form.attachments.data
        if attachments:
            for file in attachments:
                if file:
                    unique_name, original_name, file_path = save_attachment(file)
                    if unique_name:
                        db.session.add(Attachment(filename=unique_name, original_name=original_name, file_path=file_path, ticket_id=ticket.id))
        db.session.commit()
        flash('Заявка создана.', 'success')
        return redirect(url_for('operator.tickets'))
    return render_template('operator/create_ticket.html', form=form)

@bp.route('/tickets/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('operator', 'admin')
def ticket_detail(id):
    ticket = Ticket.query.get_or_404(id)
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(
            content=form.content.data,
            ticket_id=ticket.id,
            author_id=current_user.id,
            is_operator_reply=True
        )
        db.session.add(message)
        db.session.flush()
        attachments = form.attachments.data
        if attachments:
            for file in attachments:
                if file:
                    unique_name, original_name, file_path = save_attachment(file)
                    if unique_name:
                        db.session.add(Attachment(filename=unique_name, original_name=original_name, file_path=file_path, message_id=message.id))
        if ticket.status == 'new':
            ticket.status = 'in_progress'
        if not ticket.operator_id:
            ticket.operator_id = current_user.id
        db.session.commit()
        flash('Сообщение отправлено.', 'success')
        return redirect(url_for('operator.ticket_detail', id=ticket.id))

    executors = User.query.filter_by(role='executor', is_active=True).all()
    return render_template('operator/ticket_detail.html', ticket=ticket, form=form, executors=executors)

@bp.route('/tickets/<int:id>/assign')
@login_required
@role_required('operator', 'admin')
def assign_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    ticket.operator_id = current_user.id
    if ticket.status == 'new':
        ticket.status = 'in_progress'
    db.session.commit()
    flash('Заявка назначена на вас.', 'success')
    return redirect(url_for('operator.ticket_detail', id=id))

@bp.route('/tickets/<int:id>/status', methods=['POST'])
@login_required
@role_required('operator', 'admin')
def change_status(id):
    ticket = Ticket.query.get_or_404(id)
    new_status = request.form.get('status')
    executor_id = request.form.get('executor_id')
    if new_status in ['new', 'in_progress', 'waiting_client', 'waiting_operator', 'closed', 'cancelled']:
        ticket.status = new_status
        if new_status == 'closed':
            ticket.resolved_at = db.func.now()
    if executor_id:
        ticket.executor_id = int(executor_id)
    else:
        ticket.executor_id = None
    db.session.commit()
    flash('Статус заявки обновлён.', 'success')
    return redirect(url_for('operator.ticket_detail', id=id))
