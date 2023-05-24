import pytest
from flask.testing import FlaskClient

from tests.utils import unique_str, mode
from flask import current_app as app
from webapp.managers import StudentManager, AppConfigManager
from webapp.repositories import AppDatabase


@mode('registration')
def test_register_adds_user_to_db(db: AppDatabase, client: FlaskClient):
    email, password = arrange_student(db)
    response = client.post("/register", data={
        "login": email,
        "password": password,
        "confirm": password
    })

    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert f"Вы успешно зарегистрировались" in response.get_data(as_text=True)

    user = db.students.find_by_email(email)
    assert user is not None
    assert user.email == email
    assert user.unconfirmed_hash is not None
    assert user.unconfirmed_hash != password

    db.students.confirm(email)

    user = db.students.find_by_email(email)
    assert user is not None
    assert user.password_hash != password


def arrange_student(db):
    domain = 'example.com'
    email = f"{unique_str()}@{domain}"
    password = unique_str()
    db.mailers.create(domain=domain)
    return email, password


@mode('registration')
def test_login_without_input_data(client: FlaskClient, db: AppDatabase):
    email, _ = create_student(db)

    response = client.post("/login")
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert 'Данное поле не может быть пустым!' in response.get_data(as_text=True)


@mode('registration')
def test_success_login(client: FlaskClient, db: AppDatabase):
    email, password = create_student(db)
    db.students.confirm(email)

    response = client.post("/login", data={'login': email, 'password': password})
    assert response.status_code == 302
    assert response.location == 'http://localhost/'
    assert 'access_token' in response.headers.get('Set-Cookie')


@mode('registration')
def test_invalid_data_test(client: FlaskClient, db: AppDatabase):
    email, password = create_student(db)
    db.students.confirm(email)

    response = client.post("/login", data={'login': email, 'password': 'wrongpassword'})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert 'Неправильный пароль.' in response.get_data(as_text=True)


@mode('registration')
def test_login_without_confirm(client: FlaskClient, db: AppDatabase):
    email, password = create_student(db)

    response = client.post("/login", data={'login': email, 'password': 'wrongpassword'})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert 'Пользователь не подтверждён!' in response.get_data(as_text=True)


@mode('registration')
def test_login_with_incorrect_email(client: FlaskClient, db: AppDatabase):
    email, password = create_student(db)

    response = client.post("/login", data={'login': email[2:], 'password': 'wrongpassword'})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert 'Такой адрес почты не зарегистрирован!' in response.get_data(as_text=True)


def test_register_off_post(db: AppDatabase, client: FlaskClient):
    email, password = arrange_student(db)

    response = client.post("/register", data={
        "login": email,
        "password": password,
        "confirm": password
    })
    assert response.status_code == 302


def test_register_off_get(db: AppDatabase, client: FlaskClient):
    email, password = arrange_student(db)

    response = client.get("/register", data={
        "login": email,
        "password": password,
        "confirm": password
    })
    assert response.status_code == 302


def test_login_off_post(client: FlaskClient, db: AppDatabase):
    create_student(db)

    response = client.post("/login")
    assert response.status_code == 302


def test_login_off_get(client: FlaskClient, db: AppDatabase):
    create_student(db)

    response = client.get("/login")
    assert response.status_code == 302


@mode('registration')
@pytest.mark.parametrize("password, message", [
    ("1234", "Пароль содержит как минимум 8 символов."),
    ("", "Данное поле не может быть пустым!"),
    ("12345678", "Не используйте такие пароли, как 12345678 и password."),
    ("password", "Не используйте такие пароли, как 12345678 и password.")
])
def test_register_password_validation(db: AppDatabase, client: FlaskClient, password: str, message: str):
    domain = 'example.com'
    email = f"{unique_str()}@{domain}"
    db.mailers.create(domain=domain)

    response = client.post("/register", data={
        "login": email,
        "password": password,
        "confirm": password
    })
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert message in response.get_data(as_text=True)


@mode('registration')
@pytest.mark.parametrize("email, message", [
    ("какая-то строка", "Должен быть введён корректный адрес электронной почты."),
    ("", "Данное поле не может быть пустым!"),
    ("email@ gmail.com", "Убедитесь, что строка не включает пробелы."),
])
def test_register_email_validation(db: AppDatabase, client: FlaskClient, email: str, message: str):
    domain = 'example.com'
    db.mailers.create(domain=domain)
    password = "super-secret-password"

    response = client.post("/register", data={
        "login": email,
        "password": password,
        "confirm": password
    })
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert message in response.get_data(as_text=True)


def create_student(db):
    email = f"{unique_str()}@example.com"
    password = unique_str()
    students = StudentManager(AppConfigManager(lambda: app.config), db.students, db.mailers)
    students.create(email, password)
    return email, password
