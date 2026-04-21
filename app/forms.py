from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.models import User, Service, Category

class LoginForm(FlaskForm):
    username = StringField('Логин или Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contract_number = StringField('Номер договора', validators=[DataRequired(), Length(min=1, max=50)])
    full_name = StringField('ФИО', validators=[DataRequired(), Length(max=120)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Этот логин уже занят.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже используется.')

    def validate_contract_number(self, contract_number):
        user = User.query.filter_by(contract_number=contract_number.data).first()
        if user:
            raise ValidationError('Клиент с таким номером договора уже зарегистрирован.')

class TicketForm(FlaskForm):
    title = StringField('Тема', validators=[DataRequired(), Length(max=200)])
    priority = SelectField('Приоритет', choices=[
        ('low', 'Низкий'),
        ('normal', 'Нормальный'),
        ('high', 'Высокий'),
        ('critical', 'Критический')
    ], default='normal')
    description = TextAreaField('Описание', validators=[DataRequired()])
    service_id = SelectField('Услуга', coerce=int, validators=[Optional()])
    client_id = SelectField('Клиент', coerce=int, validators=[Optional()])  # для оператора
    attachments = MultipleFileField('Добавить файл', validators=[
        FileAllowed(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'], 'Недопустимый тип файла!')
    ])
    submit = SubmitField('Отправить')

class MessageForm(FlaskForm):
    content = TextAreaField('Сообщение', validators=[DataRequired()])
    attachments = MultipleFileField('Прикрепить файлы', validators=[
        FileAllowed(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'], 'Недопустимый тип файла!')
    ])
    submit = SubmitField('Отправить')

class ServiceForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание')
    price = FloatField('Цена', validators=[Optional()])
    category_id = SelectField('Категория', coerce=int, validators=[Optional()])
    is_active = BooleanField('Активна', default=True)
    image = FileField('Изображение', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]

class CategoryForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание')
    parent_id = SelectField('Родительская категория', coerce=int, validators=[Optional()])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.parent_id.choices = [(0, 'Нет')] + [(c.id, c.name) for c in Category.query.order_by('name').all()]

class UserForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('ФИО', validators=[Optional(), Length(max=120)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    contract_number = StringField('Номер договора', validators=[Optional(), Length(max=50)])
    role = SelectField('Роль', choices=[('client', 'Клиент'), ('operator', 'Оператор'), ('executor', 'Исполнитель'), ('admin', 'Администратор')])
    is_active = BooleanField('Активен', default=True)
    password = PasswordField('Пароль (оставьте пустым, чтобы не менять)')
    submit = SubmitField('Сохранить')

class ClientRegistrationByOperatorForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contract_number = StringField('Номер договора', validators=[DataRequired(), Length(min=1, max=50)])
    full_name = StringField('ФИО', validators=[DataRequired(), Length(max=120)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Создать клиента')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Этот логин уже занят.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже используется.')

    def validate_contract_number(self, contract_number):
        user = User.query.filter_by(contract_number=contract_number.data).first()
        if user:
            raise ValidationError('Клиент с таким номером договора уже существует.')
