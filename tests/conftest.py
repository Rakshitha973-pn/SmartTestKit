"""
conftest.py — Shared fixtures loaded automatically by pytest.
Every test file can use these without importing them.
"""
import pytest, os, sys, sqlite3 as _sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DB_PATH"] = ":memory:"
os.environ["SECRET_KEY"] = "test-secret-key"

from app.main import app
from app import main as _main

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    email    TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role     TEXT DEFAULT 'user'
);
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    title      TEXT NOT NULL,
    priority   TEXT DEFAULT 'medium',
    done       INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


@pytest.fixture(scope="function")
def client():
    """Fresh test client + fresh in-memory DB for every test. 100% isolated."""
    conn = _sqlite3.connect(":memory:")
    conn.row_factory = _sqlite3.Row
    conn.executescript(CREATE_SQL)
    original_get_db = _main.get_db
    _main.get_db = lambda: conn
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    _main.get_db = original_get_db
    conn.close()


@pytest.fixture
def registered_user(client):
    client.post("/register", json={"email": "alice@test.com", "password": "Password123"})
    return {"email": "alice@test.com", "password": "Password123"}


@pytest.fixture
def auth_token(client, registered_user):
    r = client.post("/login", json=registered_user)
    return r.get_json()["token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def second_user_headers(client):
    client.post("/register", json={"email": "bob@test.com", "password": "Password456"})
    r = client.post("/login", json={"email": "bob@test.com", "password": "Password456"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


@pytest.fixture
def sample_task(client, auth_headers):
    r = client.post("/tasks", json={"title": "Buy groceries", "priority": "high"}, headers=auth_headers)
    return r.get_json()
