from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, EqualTo, Length, NoneOf, Regexp


class CodeLength:
    min = 10
    max = 10000


class StudentMessageForm(FlaskForm):
    code = StringField("code", [
        DataRequired(message="Данное поле не может быть пустым!"),
        Length(min=CodeLength.min, max=CodeLength.max, message="Код должен содержать от 10 до 10⁴ символов!"),
    ])


class StudentLoginForm(FlaskForm):
    def __init__(self, lks_oauth_enabled: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lks_oauth_enabled = lks_oauth_enabled

    login = StringField('email', [
        DataRequired(message="Данное поле не может быть пустым!"),
        Regexp(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message=(
            "Должен быть введён корректный адрес электронной почты. "
            "Убедитесь, что строка не включает пробелы."
        ))
    ])
    password = PasswordField('password', [
        DataRequired(message="Данное поле не может быть пустым!"),
        Length(min=8, message="Пароль содержит как минимум 8 символов."),
        NoneOf(["12345678", "password"], message="Не используйте такие пароли, как 12345678 и password.")
    ])


class StudentRegisterForm(StudentLoginForm):
    confirm = PasswordField('password', [
        DataRequired(message="Данное поле не может быть пустым!"),
        EqualTo('password', message="Пароли не совпадают!")
    ])


class StudentChangePasswordForm(StudentRegisterForm):
    pass
