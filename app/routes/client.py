from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.decorators import role_required
from app.models import Service, ClientService, Ticket, Message, Attachment
from app.forms import TicketForm, MessageForm
from app.utils import save_attachment

bp = Blueprint('client', __name__)

@bp.route('/')
@login_required
@role_required('client')
def dashboard():
    services_count = ClientService.query.filter_by(client_id=current_user.id).count()
    open_tickets = Ticket.query.filter_by(client_id=current_user.id).filter(Ticket.status != 'closed').count()
    return render_template('client/dashboard.html', services_count=services_count, open_tickets=open_tickets)

@bp.route('/services')
@login_required
@role_required('client')
def services():
    client_services = ClientService.query.filter_by(client_id=current_user.id).join(Service).filter(Service.is_active == True).all()
    return render_template('client/services.html', client_services=client_services)

@bp.route('/tickets')
@login_required
@role_required('client')
def tickets():
    tickets = Ticket.query.filter_by(client_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('client/tickets.html', tickets=tickets)

@bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
@role_required('client')
def create_ticket():
    form = TicketForm()
    client_services = ClientService.query.filter_by(client_id=current_user.id).join(Service).filter(Service.is_active == True).all()
    form.service_id.choices = [(cs.service.id, cs.service.name) for cs in client_services]
    if form.validate_on_submit():
        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            client_id=current_user.id,
            service_id=form.service_id.data if form.service_id.data else None,
            status='new'
        )
        db.session.add(ticket)
        db.session.flush()
        # Обработка вложений с проверкой на None
        attachments = form.attachments.data
        if attachments:
            for file in attachments:
                if file:
                    unique_name, original_name, file_path = save_attachment(file)
                    if unique_name:
                        attachment = Attachment(
                            filename=unique_name,
                            original_name=original_name,
                            file_path=file_path,
                            ticket_id=ticket.id
                        )
                        db.session.add(attachment)
        db.session.commit()
        flash('Заявка создана.', 'success')
        return redirect(url_for('client.tickets'))
    return render_template('client/create_ticket.html', form=form)

@bp.route('/tickets/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('client')
def ticket_detail(id):
    ticket = Ticket.query.filter_by(client_id=current_user.id, id=id).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(
            content=form.content.data,
            ticket_id=ticket.id,
            author_id=current_user.id,
            is_operator_reply=False
        )
        db.session.add(message)
        db.session.flush()
        # Обработка вложений с проверкой на None
        attachments = form.attachments.data
        if attachments:
            for file in attachments:
                if file:
                    unique_name, original_name, file_path = save_attachment(file)
                    if unique_name:
                        attachment = Attachment(
                            filename=unique_name,
                            original_name=original_name,
                            file_path=file_path,
                            message_id=message.id
                        )
                        db.session.add(attachment)
        # Если заявка ждала ответа клиента, перевести в ожидание оператора
        if ticket.status == 'waiting_client':
            ticket.status = 'waiting_operator'
        db.session.commit()
        flash('Сообщение отправлено.', 'success')
        return redirect(url_for('client.ticket_detail', id=ticket.id))
    return render_template('client/ticket_detail.html', ticket=ticket, form=form)
