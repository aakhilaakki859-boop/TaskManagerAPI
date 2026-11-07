import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def client():
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)  # not used as context manager: skips startup create_all
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def auth_headers(client, username="alice", password="secret123"):
    client.post("/auth/register", json={"username": username, "password": password})
    res = client.post("/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_and_duplicate(client):
    body = {"username": "bob", "password": "secret123"}
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409


def test_login_wrong_password(client):
    client.post("/auth/register", json={"username": "bob", "password": "secret123"})
    res = client.post("/auth/login", data={"username": "bob", "password": "wrong"})
    assert res.status_code == 401


def test_tasks_require_auth(client):
    assert client.get("/tasks").status_code == 401


def test_task_crud(client):
    h = auth_headers(client)
    created = client.post("/tasks", json={"title": "Write tests"}, headers=h)
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["status"] == "todo"

    patched = client.patch(f"/tasks/{task_id}", json={"status": "done"}, headers=h)
    assert patched.json()["status"] == "done"
    assert patched.json()["title"] == "Write tests"  # untouched field preserved

    assert client.delete(f"/tasks/{task_id}", headers=h).status_code == 204
    assert client.get(f"/tasks/{task_id}", headers=h).status_code == 404


def test_users_cannot_see_each_others_tasks(client):
    alice = auth_headers(client, "alice")
    bob = auth_headers(client, "bob")
    task_id = client.post("/tasks", json={"title": "private"}, headers=alice).json()["id"]

    assert client.get(f"/tasks/{task_id}", headers=bob).status_code == 404
    assert client.get("/tasks", headers=bob).json() == []


def test_filter_and_pagination(client):
    h = auth_headers(client)
    for i in range(5):
        priority = "high" if i % 2 == 0 else "low"
        client.post("/tasks", json={"title": f"t{i}", "priority": priority}, headers=h)

    assert len(client.get("/tasks?priority=high", headers=h).json()) == 3
    assert len(client.get("/tasks?limit=2", headers=h).json()) == 2
    assert len(client.get("/tasks?limit=2&offset=4", headers=h).json()) == 1