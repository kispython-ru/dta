from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField('email', [Email(), DataRequired()])
    password = PasswordField('password', [Length(min=8), DataRequired()])


class RegisterForm(FlaskForm):
    email = StringField('email', [Email(), DataRequired()])
    password = PasswordField('password', [Length(min=8), DataRequired()])
    password_repeat = PasswordField(
        'password_repeat', [EqualTo('password'), DataRequired()])
