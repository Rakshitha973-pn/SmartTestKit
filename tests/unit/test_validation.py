"""
PHASE 1 — UNIT TESTS
Tests single functions in isolation. No DB, no network. Pure logic.
Run: pytest tests/unit/ -v
"""
import pytest


class TestEmailValidation:

    @pytest.mark.parametrize("bad_email", [
        "plainaddress", "double-dot..com", "missingdomain",
        "", "   ", "no-at-sign", 
    ])
    def test_invalid_emails_rejected(self, client, bad_email):
        r = client.post("/register", json={"email": bad_email, "password": "Password123"})
        assert r.status_code == 400, f"Should reject email: '{bad_email}'"

    def test_valid_email_accepted(self, client):
        r = client.post("/register", json={"email": "user@example.com", "password": "Password123"})
        assert r.status_code == 201

    def test_email_stored_lowercase(self, client):
        client.post("/register", json={"email": "UPPER@EXAMPLE.COM", "password": "Password123"})
        r = client.post("/login", json={"email": "upper@example.com", "password": "Password123"})
        assert r.status_code == 200


class TestPasswordValidation:

    @pytest.mark.parametrize("weak,label", [
        ("abc",     "3 chars"),
        ("1234567", "7 chars"),
        ("",        "empty"),
    ])
    def test_weak_passwords_rejected(self, client, weak, label):
        r = client.post("/register", json={"email": "x@y.com", "password": weak})
        assert r.status_code == 400, f"Should reject {label}"

    def test_exactly_8_chars_accepted(self, client):
        r = client.post("/register", json={"email": "a@b.com", "password": "Abcde123"})
        assert r.status_code == 201

    def test_long_password_accepted(self, client):
        r = client.post("/register", json={"email": "a@b.com", "password": "A" * 100})
        assert r.status_code == 201


class TestTaskValidation:

    def test_empty_title_rejected(self, client, auth_headers):
        r = client.post("/tasks", json={"title": ""}, headers=auth_headers)
        assert r.status_code == 400

    def test_whitespace_title_rejected(self, client, auth_headers):
        r = client.post("/tasks", json={"title": "   "}, headers=auth_headers)
        assert r.status_code == 400

    def test_title_200_chars_accepted(self, client, auth_headers):
        r = client.post("/tasks", json={"title": "a" * 200}, headers=auth_headers)
        assert r.status_code == 201

    def test_title_201_chars_rejected(self, client, auth_headers):
        r = client.post("/tasks", json={"title": "a" * 201}, headers=auth_headers)
        assert r.status_code == 400

    @pytest.mark.parametrize("bad_priority", ["urgent", "HIGH", "0", "critical", ""])
    def test_invalid_priority_rejected(self, client, auth_headers, bad_priority):
        r = client.post("/tasks", json={"title": "Task", "priority": bad_priority},
                        headers=auth_headers)
        assert r.status_code == 400

    @pytest.mark.parametrize("good_priority", ["low", "medium", "high"])
    def test_valid_priorities_accepted(self, client, auth_headers, good_priority):
        r = client.post("/tasks", json={"title": "Task", "priority": good_priority},
                        headers=auth_headers)
        assert r.status_code == 201


class TestHealthEndpoint:

    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_returns_ok_status(self, client):
        assert client.get("/health").get_json()["status"] == "ok"

    def test_returns_version(self, client):
        assert "version" in client.get("/health").get_json()
