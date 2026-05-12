from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, Regexp
from app.models import User, Service, Category
import re

def belarusian_phone(form, field):
    """Валидация белорусского номера телефона."""
    if field.data:
        # Очищаем от пробелов и тире
        cleaned = re.sub(r'[\s\-\(\)]', '', field.data)
        # Проверяем форматы: +375XXXXXXXXX, 375XXXXXXXXX, 80XXXXXXXXX
        if not re.match(r'^(\+?375|80)(29|33|44|25|17)\d{7}$', cleaned):
            raise ValidationError('Введите корректный белорусский номер телефона (+375XX XXXXXXX)')

def strong_password(form, field):
    """Валидация сложного пароля."""
    password = field.data
    if len(password) < 8:
        raise ValidationError('Пароль должен быть не менее 8 символов')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Пароль должен содержать хотя бы одну строчную букву')
    if not re.search(r'\d', password):
        raise ValidationError('Пароль должен содержать хотя бы одну цифру')
    if re.search(r'[^A-Za-z0-9]', password):
        raise ValidationError('Пароль не должен содержать специальные символы')

def contract_number_valid(form, field):
    """Валидация номера договора (только цифры)."""
    if field.data:
        if not re.match(r'^\d+$', field.data):
            raise ValidationError('Номер договора должен содержать только цифры')

class LoginForm(FlaskForm):
    username = StringField('Логин или Email', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(max=120, message='Слишком длинное значение')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=3, max=64, message='Логин должен быть от 3 до 64 символов'),
        Regexp(r'^[A-Za-z0-9_]+$', message='Логин может содержать только буквы, цифры и подчеркивание')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Email(message='Введите корректный email адрес'),
        Length(max=120, message='Слишком длинный email')
    ])
    contract_number = StringField('Номер договора', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=1, max=50, message='Номер договора должен быть от 1 до 50 символов'),
        contract_number_valid
    ])
    full_name = StringField('ФИО', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(max=120, message='Слишком длинное значение')
    ])
    phone = StringField('Телефон', validators=[
        Optional(),
        Length(max=20, message='Слишком длинный номер'),
        belarusian_phone
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        strong_password
    ])
    password2 = PasswordField('Повторите пароль', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        EqualTo('password', message='Пароли не совпадают')
    ])
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
    title = StringField('Тема', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(max=200, message='Тема не должна превышать 200 символов')
    ])
    priority = SelectField('Приоритет', choices=[
        ('low', 'Низкий'),
        ('normal', 'Нормальный'),
        ('high', 'Высокий'),
        ('critical', 'Критический')
    ], default='normal')
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    service_id = SelectField('Услуга', coerce=int, validators=[Optional()], choices=[])
    attachments = MultipleFileField('Добавить файл', validators=[
        FileAllowed(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'], 'Недопустимый тип файла!')
    ])
    submit = SubmitField('Отправить')

class MessageForm(FlaskForm):
    content = TextAreaField('Сообщение', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    attachments = MultipleFileField('Прикрепить файлы', validators=[
        FileAllowed(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'], 'Недопустимый тип файла!')
    ])
    submit = SubmitField('Отправить')

class ServiceForm(FlaskForm):
    name = StringField('Название', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(max=200, message='Название не должно превышать 200 символов')
    ])
    description = TextAreaField('Описание')
    price = FloatField('Цена', validators=[Optional()])
    category_id = SelectField('Категория', coerce=int, validators=[Optional()])
    is_active = BooleanField('Активна', default=True)
    image = FileField('Изображение', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]

class CategoryForm(FlaskForm):
    name = StringField('Название', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    description = TextAreaField('Описание')
    parent_id = SelectField('Родительская категория', coerce=int, validators=[Optional()])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.parent_id.choices = [(0, 'Нет')] + [(c.id, c.name) for c in Category.query.order_by('name').all()]

class UserForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=3, max=64, message='Логин должен быть от 3 до 64 символов'),
        Regexp(r'^[A-Za-z0-9_]+$', message='Логин может содержать только буквы, цифры и подчеркивание')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Email(message='Введите корректный email адрес'),
        Length(max=120, message='Слишком длинный email')
    ])
    full_name = StringField('ФИО', validators=[
        Optional(),
        Length(max=120, message='Слишком длинное значение')
    ])
    phone = StringField('Телефон', validators=[
        Optional(),
        Length(max=20, message='Слишком длинный номер'),
        belarusian_phone
    ])
    contract_number = StringField('Номер договора', validators=[
        Optional(),
        Length(max=50, message='Слишком длинный номер'),
        contract_number_valid
    ])
    role = SelectField('Роль', choices=[
        ('client', 'Клиент'),
        ('operator', 'Оператор'),
        ('executor', 'Исполнитель'),
        ('admin', 'Администратор')
    ])
    is_active = BooleanField('Активен', default=True)
    password = PasswordField('Пароль (оставьте пустым, чтобы не менять)')
    submit = SubmitField('Сохранить')

class ClientRegistrationByOperatorForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=3, max=64, message='Логин должен быть от 3 до 64 символов'),
        Regexp(r'^[A-Za-z0-9_]+$', message='Логин может содержать только буквы, цифры и подчеркивание')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Email(message='Введите корректный email адрес'),
        Length(max=120, message='Слишком длинный email')
    ])
    contract_number = StringField('Номер договора', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(min=1, max=50, message='Номер договора должен быть от 1 до 50 символов'),
        contract_number_valid
    ])
    full_name = StringField('ФИО', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Length(max=120, message='Слишком длинное значение')
    ])
    phone = StringField('Телефон', validators=[
        Optional(),
        Length(max=20, message='Слишком длинный номер'),
        belarusian_phone
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        strong_password
    ])
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
