from bs4 import BeautifulSoup
import uuid


def test_blank_registration_view(client):
    response = client.get('/register')
    html = str(response.data)
    assert 'This field is required.' not in html


def test_validated_registration_view(client):
    response = client.post('/register')
    html = str(response.data)
    assert 'This field is required.' in html


def test_specific_validation_messages(client):
    response = client.post(
        '/register',
        data=dict(
            email="invalid",
            password="short"))
    html = str(response.data)
    assert 'Invalid email address.' in html
    assert 'Field must be at least 8 characters long.' in html


def test_registration(client):
    response = client.get('/register')
    html = str(response.data)
    parser = BeautifulSoup(html, 'html.parser')
    csrf_token_input = parser.find('input', {'id': 'csrf_token'})
    csrf_token = csrf_token_input.get('value')

    email = f"{uuid.uuid4()}@example.com"
    password = "12345678"
    response = client.post(
        '/register',
        data=dict(
            email=email,
            password=password,
            password_repeat=password,
            csrf_token=csrf_token))
    html = str(response.data)
    assert 'Redirecting...' in html

    response = client.get('/')
    html = str(response.data)
    assert email in html
