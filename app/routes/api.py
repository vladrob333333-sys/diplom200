from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import Ticket
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

bp = Blueprint('api', __name__)

@bp.route('/tickets/stats')
@login_required
@role_required('admin', 'operator')
def ticket_stats():
    period = request.args.get('period', 'week')
    now = datetime.now(timezone.utc)
    if period == 'day':
        start = now - timedelta(days=1)
    elif period == 'week':
        start = now - timedelta(weeks=1)
    elif period == 'month':
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(weeks=1)

    query = Ticket.query.filter(Ticket.created_at >= start)
    if current_user.role == 'operator':
        query = query.filter((Ticket.operator_id == current_user.id) | (Ticket.executor_id == current_user.id))
    stats = query.with_entities(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    return jsonify({status: count for status, count in stats})
