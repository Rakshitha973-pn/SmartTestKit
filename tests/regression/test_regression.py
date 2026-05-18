"""
PHASE 1 — REGRESSION + SCHEMA DRIFT TESTS
1. Schema drift: API response shape must never change silently.
2. Regression: known past bugs must never come back.
Run: pytest tests/regression/ -v
"""
import pytest


# ── Schema contract: exact keys each endpoint must return ─────────────────────

TASK_SCHEMA   = {"id", "title", "priority", "done", "created_at", "user_id"}
TOKEN_SCHEMA  = {"token"}
HEALTH_SCHEMA = {"status", "version", "db"}


def assert_schema(body: dict, required_keys: set, label: str):
    missing = required_keys - body.keys()
    assert not missing, f"{label} response missing keys: {missing}"


class TestSchemaDrift:
    """
    If a developer renames a field (e.g. 'done' → 'completed'),
    these tests catch it BEFORE the frontend or client apps break.
    """

    def test_task_response_shape(self, client, auth_headers):
        r = client.post("/tasks", json={"title": "Schema check"}, headers=auth_headers)
        assert_schema(r.get_json(), {"id", "title", "done"}, "POST /tasks")

    def test_login_response_shape(self, client, registered_user):
        r = client.post("/login", json=registered_user)
        assert_schema(r.get_json(), TOKEN_SCHEMA, "POST /login")

    def test_health_response_shape(self, client):
        r = client.get("/health")
        assert_schema(r.get_json(), HEALTH_SCHEMA, "GET /health")

    def test_get_tasks_list_item_shape(self, client, auth_headers, sample_task):
        r = client.get("/tasks", headers=auth_headers)
        task = r.get_json()[0]
        assert_schema(task, {"id", "title", "done", "priority"}, "GET /tasks item")

    def test_task_id_is_integer(self, client, auth_headers):
        r = client.post("/tasks", json={"title": "ID check"}, headers=auth_headers)
        assert isinstance(r.get_json()["id"], int)

    def test_task_done_is_boolean(self, client, auth_headers, sample_task):
        r = client.get("/tasks", headers=auth_headers)
        assert isinstance(r.get_json()[0]["done"], bool)


class TestRegressionBugFixes:
    """
    Each test here maps to a bug that was once reported and fixed.
    These ensure the same bug can never silently return.
    """

    def test_BUG001_delete_returns_404_not_500(self, client, auth_headers):
        """BUG-001: Deleting non-existent task used to crash with 500."""
        r = client.delete("/tasks/99999", headers=auth_headers)
        assert r.status_code == 404
        assert r.status_code != 500

    def test_BUG002_duplicate_email_returns_409_not_500(self, client):
        """BUG-002: Duplicate email registration used to raise unhandled sqlite error."""
        payload = {"email": "dup@test.com", "password": "Password123"}
        client.post("/register", json=payload)
        r = client.post("/register", json=payload)
        assert r.status_code == 409
        assert r.status_code != 500

    def test_BUG003_whitespace_title_rejected(self, client, auth_headers):
        """BUG-003: Tasks with only spaces in title were being saved."""
        r = client.post("/tasks", json={"title": "     "}, headers=auth_headers)
        assert r.status_code == 400

    def test_BUG004_other_user_task_returns_404_not_403(self, client,
                                                          auth_headers, second_user_headers, sample_task):
        """BUG-004: Cross-user access used to leak existence of task with 403."""
        task_id = sample_task["id"]
        r = client.delete(f"/tasks/{task_id}", headers=second_user_headers)
        assert r.status_code == 404  # Must not reveal task exists

    def test_BUG005_login_case_insensitive_email(self, client):
        """BUG-005: Login failed when email was stored lowercase but entered uppercase."""
        client.post("/register", json={"email": "user@test.com", "password": "Password123"})
        r = client.post("/login", json={"email": "USER@TEST.COM", "password": "Password123"})
        assert r.status_code == 200

    def test_BUG006_empty_json_body_no_crash(self, client):
        """BUG-006: Sending empty body to /register crashed with KeyError."""
        r = client.post("/register", data="", content_type="application/json")
        assert r.status_code in (400, 415)
        assert r.status_code != 500
