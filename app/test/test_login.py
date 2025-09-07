from flask_login import login_user


def test_login_success(client, user):
  response = client.post('/', data={
    'nameUser': user.nameUser,
    'passwordUser': user.passwordUser
  }, follow_redirects=True)
  assert response.status_code == 200
  expected_message = b"Welcome"
  assert expected_message in response.data


def test_login_invalid_credentials(client):
  response = client.post('/', data={
    'nameUser': 'wronguser',
    'passwordUser': 'wrongpassword'
  }, follow_redirects=True)
  assert response.status_code == 200
  assert b"Invalid credentials. Please try again." in response.data


def test_login_already_authenticated(client, user):
  with client:
    with client.session_transaction() as session:
      session['_user_id'] = str(user.idUser)
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b"This is your dashboard" in response.data
