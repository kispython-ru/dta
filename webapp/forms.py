from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length


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


class LoginForm(FlaskForm):
    login = StringField('login', [DataRequired(message="Данное поле не может быть пустым!")])
    password = PasswordField('password', [
        DataRequired(message="Данное поле не может быть пустым!"),
        Length(min=8, message="Пароль содержит как минимум 8 символов."),
    ])
