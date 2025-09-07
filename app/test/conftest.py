from app import create_app, db
import pytest

@pytest.fixture
def app():
    app = create_app()
    with app.app_context():
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
  

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user(app):
    from app.models.users import Users
    user = Users(nameUser="test_user", passwordUser="test_password")
    db.session.add(user)
    db.session.commit()
    yield user    
    