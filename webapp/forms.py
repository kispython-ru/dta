from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo


class CodeLength:
    min = 10
    max = 10000


class MessageForm(FlaskForm):
    code = StringField("code", [
        DataRequired(message="Данное поле не может быть пустым!"),
        Length(min=CodeLength.min, max=CodeLength.max, message="Код должен содержать как минимум 10 символов!"),
    ])
    password = PasswordField('password', [
        DataRequired(message="Данное поле не может быть пустым!"),
        Length(min=8, message="Пароль содержит как минимум 8 символов."),
    ])


class TeacherLoginForm(FlaskForm):
    login = StringField('login', [DataRequired(message="Данное поле не может быть пустым!")])
    password = PasswordField('password', [
        DataRequired(message="Данное поле не может быть пустым!"),
        Length(min=8, message="Пароль содержит как минимум 8 символов."),
    ])


class StudentLoginForm(FlaskForm):
    login = StringField('email', [
        DataRequired(message="Данное поле не может быть пустым!"),
        Regexp(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message="Должен быть введён корректный адрес электронной почты. Убедитесь, что строка не включает пробелы.")
    ])
    password = PasswordField('password', [
        DataRequired(message="Данное поле не может быть пустым!"),
        Length(min=8, message="Пароль содержит как минимум 8 символов."),
    ])


class StudentRegisterForm(StudentLoginForm):
    confirm = PasswordField('password', [
        DataRequired(message="Данное поле не может быть пустым!"),
        EqualTo('password', message="Пароли не совпадают!")
    ])
