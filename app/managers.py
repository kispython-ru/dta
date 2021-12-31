from typing import Union
from flask_bcrypt import Bcrypt
from flask import current_app as app
from app.models import User
from sqlalchemy.orm import Session


class UserManager():
    def __init__(self, session: Session):
        self.session = session
        self.bcrypt = Bcrypt(app)

    def register(self, email: str, password: str) -> User:
        app.logger.info(f'Registering user {email}')
        password_hash = self.bcrypt.generate_password_hash(
            password).decode('utf8')
        user = User(email=email, password=password_hash)
        self.session.add(user)
        self.session.commit()
        return user

    def check_password(self, email: str, password: str) -> Union[User, None]:
        app.logger.info(f'Checking password for user {email}')
        user = self.session.query(User).filter_by(email=email).first()
        if user is None:
            return None
        check_result = self.bcrypt.check_password_hash(
            user.password, password)
        if check_result:
            return user
        return None

    def get_by_id(self, id: int) -> User:
        user = self.session.query(User).get(id)
        return user
