"""
PHASE 1 — INTEGRATION TESTS
Tests full request → DB → response cycle. Real HTTP, real database.
Run: pytest tests/integration/ -v
"""


class TestUserRegistration:

    def test_register_new_user(self, client):
        r = client.post("/register", json={"email": "new@test.com", "password": "Password123"})
        assert r.status_code == 201
        assert r.get_json()["message"] == "User created"

    def test_duplicate_email_rejected(self, client):
        payload = {"email": "dup@test.com", "password": "Password123"}
        client.post("/register", json=payload)
        r = client.post("/register", json=payload)
        assert r.status_code == 409
        assert "already" in r.get_json()["error"].lower()

    def test_register_missing_body(self, client):
        r = client.post("/register", json={})
        assert r.status_code == 400


class TestUserLogin:

    def test_login_correct_credentials(self, client, registered_user):
        r = client.post("/login", json=registered_user)
        assert r.status_code == 200
        assert "token" in r.get_json()

    def test_login_wrong_password(self, client, registered_user):
        r = client.post("/login", json={**registered_user, "password": "WrongPass999"})
        assert r.status_code == 401

    def test_login_nonexistent_user(self, client):
        r = client.post("/login", json={"email": "ghost@x.com", "password": "Password123"})
        assert r.status_code == 401

    def test_token_is_string(self, client, registered_user):
        r = client.post("/login", json=registered_user)
        token = r.get_json().get("token")
        assert isinstance(token, str) and len(token) > 10


class TestTaskCRUD:

    def test_create_task(self, client, auth_headers):
        r = client.post("/tasks", json={"title": "Write tests"}, headers=auth_headers)
        assert r.status_code == 201
        body = r.get_json()
        assert body["title"] == "Write tests"
        assert "id" in body

    def test_get_tasks_empty(self, client, auth_headers):
        r = client.get("/tasks", headers=auth_headers)
        assert r.status_code == 200
        assert r.get_json() == []

    def test_get_tasks_returns_created_task(self, client, auth_headers, sample_task):
        r = client.get("/tasks", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.get_json()) == 1
        assert r.get_json()[0]["title"] == "Buy groceries"

    def test_update_task_done(self, client, auth_headers, sample_task):
        task_id = sample_task["id"]
        r = client.patch(f"/tasks/{task_id}", json={"done": True}, headers=auth_headers)
        assert r.status_code == 200
        assert r.get_json()["done"] is True

    def test_delete_task(self, client, auth_headers, sample_task):
        task_id = sample_task["id"]
        r = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert r.status_code == 200
        # Confirm it's gone
        tasks = client.get("/tasks", headers=auth_headers).get_json()
        assert all(t["id"] != task_id for t in tasks)

    def test_delete_nonexistent_task(self, client, auth_headers):
        r = client.delete("/tasks/99999", headers=auth_headers)
        assert r.status_code == 404

    def test_filter_tasks_by_priority(self, client, auth_headers):
        client.post("/tasks", json={"title": "High task", "priority": "high"}, headers=auth_headers)
        client.post("/tasks", json={"title": "Low task",  "priority": "low"},  headers=auth_headers)
        r = client.get("/tasks?priority=high", headers=auth_headers)
        tasks = r.get_json()
        assert all(t["priority"] == "high" for t in tasks)
        assert len(tasks) == 1

    def test_create_multiple_tasks(self, client, auth_headers):
        for i in range(5):
            client.post("/tasks", json={"title": f"Task {i}"}, headers=auth_headers)
        r = client.get("/tasks", headers=auth_headers)
        assert len(r.get_json()) == 5
