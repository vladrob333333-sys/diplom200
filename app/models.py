from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='client')  # admin, operator, client
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    contract_number = db.Column(db.String(50), unique=True, nullable=True)  # для клиентов
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='client')  # admin, operator, client, executor
    # Связи
    client_services = db.relationship('ClientService', back_populates='client', lazy='dynamic')
    created_tickets = db.relationship('Ticket', foreign_keys='Ticket.client_id', back_populates='client')
    assigned_tickets = db.relationship('Ticket', foreign_keys='Ticket.operator_id', back_populates='operator')
    messages = db.relationship('Message', back_populates='author')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    services = db.relationship('Service', back_populates='category', lazy='dynamic')
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('Category', back_populates='services')
    client_services = db.relationship('ClientService', back_populates='service', lazy='dynamic')
    tickets = db.relationship('Ticket', back_populates='service', lazy='dynamic')

    def __repr__(self):
        return f'<Service {self.name}>'

class ClientService(db.Model):
    __tablename__ = 'client_services'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    client = db.relationship('User', back_populates='client_services')
    service = db.relationship('Service', back_populates='client_services')

    def __repr__(self):
        return f'<ClientService {self.client_id}:{self.service_id}>'

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    status = db.Column(db.String(30), default='new')  # new, in_progress, waiting_client, waiting_operator, closed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)

    client = db.relationship('User', foreign_keys=[client_id], back_populates='created_tickets')
    operator = db.relationship('User', foreign_keys=[operator_id], back_populates='assigned_tickets')
    service = db.relationship('Service', back_populates='tickets')
    messages = db.relationship('Message', back_populates='ticket', order_by='Message.created_at')
    attachments = db.relationship('Attachment', back_populates='ticket', lazy='dynamic')
    executor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    executor = db.relationship('User', foreign_keys=[executor_id], backref='executed_tickets')

    def __repr__(self):
        return f'<Ticket {self.id}: {self.title}>'

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_operator_reply = db.Column(db.Boolean, default=False)

    ticket = db.relationship('Ticket', back_populates='messages')
    author = db.relationship('User', back_populates='messages')
    attachments = db.relationship('Attachment', back_populates='message', lazy='dynamic')

    def __repr__(self):
        return f'<Message {self.id}>'

class Attachment(db.Model):
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship('Ticket', back_populates='attachments')
    message = db.relationship('Message', back_populates='attachments')

    def __repr__(self):
        return f'<Attachment {self.filename}>'
