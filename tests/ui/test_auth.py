import bcrypt
from flask.testing import FlaskClient

from tests.utils import unique_str, mode
from webapp.repositories import AppDatabase


@mode('registration')
def test_register_adds_user_to_db(db: AppDatabase, client: FlaskClient):
    email, password = db_test_mailers_create(db)
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


def db_test_mailers_create(db):
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


def test_register_off(db: AppDatabase, client: FlaskClient):
    email, password = db_test_mailers_create(db)

    response = client.post("/register", data={
        "login": email,
        "password": password,
        "confirm": password
    })
    assert response.status_code == 302


def test_login_off(client: FlaskClient, db: AppDatabase):
    create_student(db)

    response = client.post("/login")
    assert response.status_code == 302


def create_student(db):
    email = f"{unique_str().replace('-', '')[:10]}@example.com"
    password = unique_str()
    hashed = bcrypt.hashpw(password.encode('UTF-8'), bcrypt.gensalt()).decode('UTF-8')
    db.students.create(email, hashed)
    return email, password
