from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class CodeLength:
    min = 10
    max = 2500


class MessageForm(FlaskForm):
    code = StringField(
        "code", [
            DataRequired(message="Данное поле не может быть пустым!"),
            Length(
                min=CodeLength.min,
                max=CodeLength.max,
                message="Код должен содержать как минимум 10 символов!",
            ),
        ],
    )
