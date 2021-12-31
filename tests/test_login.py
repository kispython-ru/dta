def test_blank_login_view(client):
    response = client.get('/login')
    html = str(response.data)
    assert 'This field is required.' not in html


def test_validated_login_view(client):
    response = client.post('/login')
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
