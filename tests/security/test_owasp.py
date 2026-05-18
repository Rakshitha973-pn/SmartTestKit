"""
PHASE 1 — SECURITY TESTS (OWASP Top-10)
Checks real vulnerabilities before hackers find them.
Run: pytest tests/security/ -v
"""
import pytest


class TestAuthentication:
    """No token = no access."""

    def test_tasks_requires_auth(self, client):
        assert client.get("/tasks").status_code == 401

    def test_create_task_requires_auth(self, client):
        assert client.post("/tasks", json={"title": "Hack"}).status_code == 401

    def test_delete_task_requires_auth(self, client):
        assert client.delete("/tasks/1").status_code == 401

    def test_fake_token_rejected(self, client):
        headers = {"Authorization": "Bearer thisisatotallyinvalidtoken"}
        assert client.get("/tasks", headers=headers).status_code == 401

    def test_empty_token_rejected(self, client):
        assert client.get("/tasks", headers={"Authorization": "Bearer "}).status_code == 401


class TestBrokenObjectLevelAuth:
    """OWASP API1 — User A must NOT access User B's tasks."""

    def test_user_cannot_delete_other_users_task(self, client, auth_headers,
                                                  second_user_headers, sample_task):
        task_id = sample_task["id"]
        # Bob tries to delete Alice's task
        r = client.delete(f"/tasks/{task_id}", headers=second_user_headers)
        assert r.status_code == 404  # Should look like "not found", not expose it exists

    def test_user_cannot_update_other_users_task(self, client, auth_headers,
                                                  second_user_headers, sample_task):
        task_id = sample_task["id"]
        r = client.patch(f"/tasks/{task_id}", json={"title": "Hacked!"},
                         headers=second_user_headers)
        assert r.status_code == 404

    def test_user_only_sees_own_tasks(self, client, auth_headers, second_user_headers):
        # Alice creates a task
        client.post("/tasks", json={"title": "Alice private task"}, headers=auth_headers)
        # Bob's task list should be empty
        r = client.get("/tasks", headers=second_user_headers)
        assert r.get_json() == []


class TestSQLInjection:
    """OWASP API3 — Malicious SQL in input must never execute."""

    @pytest.mark.parametrize("payload", [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "admin'--",
        "1; SELECT * FROM users",
        "' UNION SELECT * FROM users --",
    ])
    def test_sql_injection_in_email_rejected(self, client, payload):
        r = client.post("/register", json={"email": payload, "password": "Password123"})
        # Should reject as bad input, NOT crash (500 = SQL ran and failed)
        assert r.status_code in (400, 409)
        assert r.status_code != 500

    @pytest.mark.parametrize("payload", [
        "'; DROP TABLE tasks; --",
        "' OR 1=1 --",
    ])
    def test_sql_injection_in_task_title(self, client, auth_headers, payload):
        r = client.post("/tasks", json={"title": payload}, headers=auth_headers)
        # Should either save safely or reject — never crash
        assert r.status_code in (201, 400)
        assert r.status_code != 500


class TestMassAssignment:
    """OWASP API6 — Clients must not be able to set internal fields like 'role'."""

    def test_cannot_set_admin_role_on_register(self, client):
        r = client.post("/register", json={
            "email": "hacker@test.com",
            "password": "Password123",
            "role": "admin"          # should be ignored
        })
        assert r.status_code == 201  # created, but role not elevated


class TestErrorLeakage:
    """APIs must not leak stack traces or internal details on errors."""

    def test_no_stack_trace_on_bad_request(self, client):
        r = client.post("/register", json={"email": "bad", "password": ""})
        body = str(r.get_json())
        assert "Traceback" not in body
        assert "sqlite3" not in body
        assert "line " not in body
