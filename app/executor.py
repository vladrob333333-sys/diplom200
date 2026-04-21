from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.decorators import role_required
from app.models import Ticket, Message, Attachment
from app.forms import MessageForm
from app.utils import save_attachment

bp = Blueprint('executor', __name__, url_prefix='/executor')

@bp.route('/')
@login_required
@role_required('executor')
def dashboard():
    assigned = Ticket.query.filter_by(executor_id=current_user.id).filter(Ticket.status != 'closed').count()
    available = Ticket.query.filter_by(executor_id=None).filter(Ticket.status.in_(['new', 'in_progress'])).count()
    return render_template('executor/dashboard.html', assigned_tickets=assigned, available_tickets=available)

@bp.route('/tickets')
@login_required
@role_required('executor')
def tickets():
    my = Ticket.query.filter_by(executor_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    available = Ticket.query.filter_by(executor_id=None).filter(Ticket.status.in_(['new', 'in_progress'])).order_by(Ticket.created_at.desc()).all()
    return render_template('executor/tickets.html', my_tickets=my, available=available)

@bp.route('/tickets/<int:id>/take')
@login_required
@role_required('executor')
def take_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    if ticket.executor_id is None and ticket.status in ['new', 'in_progress']:
        ticket.executor_id = current_user.id
        if ticket.status == 'new':
            ticket.status = 'in_progress'
        db.session.commit()
        flash('Заявка принята.', 'success')
    else:
        flash('Невозможно принять заявку.', 'danger')
    return redirect(url_for('executor.tickets'))

@bp.route('/tickets/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('executor')
def ticket_detail(id):
    ticket = Ticket.query.get_or_404(id)
    # Исполнитель может просматривать только свои заявки или те, где он назначен, или свободные (если решит принять)
    if ticket.executor_id != current_user.id and ticket.executor_id is not None:
        flash('У вас нет доступа к этой заявке.', 'danger')
        return redirect(url_for('executor.tickets'))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(content=form.content.data, ticket_id=ticket.id, author_id=current_user.id)
        db.session.add(msg)
        db.session.flush()
        attachments = form.attachments.data
        if attachments:
            for file in attachments:
                if file:
                    uname, oname, path = save_attachment(file)
                    if uname:
                        db.session.add(Attachment(filename=uname, original_name=oname, file_path=path, message_id=msg.id))
        db.session.commit()
        flash('Сообщение отправлено.', 'success')
        return redirect(url_for('executor.ticket_detail', id=ticket.id))
    return render_template('executor/ticket_detail.html', ticket=ticket, form=form)
