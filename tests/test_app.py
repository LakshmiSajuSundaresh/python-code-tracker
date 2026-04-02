import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set DB to a temp path before importing app
os.environ['TESTING'] = '1'

from app import app
from models.db import init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret'
    # Use a temp database for tests
    import models.db as db_module
    db_module.DB = '/tmp/test_tracker.db'
    with app.test_client() as client:
        init_db()
        yield client
    # Cleanup
    if os.path.exists('/tmp/test_tracker.db'):
        os.remove('/tmp/test_tracker.db')

def test_login_page_loads(client):
    res = client.get('/login')
    assert res.status_code == 200

def test_register_page_loads(client):
    res = client.get('/register')
    assert res.status_code == 200

def test_dashboard_redirects_if_not_logged_in(client):
    res = client.get('/dashboard')
    assert res.status_code == 302

def test_register_and_login(client):
    res = client.post('/register', data={
        'username': 'testuser123',
        'password': 'testpass123'
    }, follow_redirects=True)
    assert res.status_code == 200

    res = client.post('/login', data={
        'username': 'testuser123',
        'password': 'testpass123'
    }, follow_redirects=True)
    assert res.status_code == 200

def test_duplicate_username_rejected(client):
    client.post('/register', data={'username': 'dupeuser', 'password': 'pass'})
    res = client.post('/register', data={'username': 'dupeuser', 'password': 'pass'})
    assert b'already taken' in res.data

def test_wrong_password_rejected(client):
    client.post('/register', data={'username': 'wrongpassuser', 'password': 'correctpass'})
    res = client.post('/login', data={'username': 'wrongpassuser', 'password': 'wrongpass'})
    assert b'Incorrect password' in res.data

def test_admin_login(client):
    res = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    assert res.status_code == 200