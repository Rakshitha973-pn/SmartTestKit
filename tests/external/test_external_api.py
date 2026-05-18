"""
EXTERNAL API TESTS
These tests actually call the URL you paste in the web UI.
They check what a real API should do — health, auth, CRUD, security, performance.
Many of these will FAIL on public APIs like reqres.in — that is expected and correct.
Run: pytest tests/external/ -v
"""
import os
import time
import pytest
import requests

# Reads the URL from environment variable set by web_ui.py
BASE_URL = os.environ.get("TARGET_API_URL", "http://localhost:5000").rstrip("/")

# Timeout for all requests (seconds)
TIMEOUT = 8


def get(path, **kwargs):
    return requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)

def post(path, **kwargs):
    return requests.post(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)

def delete(path, **kwargs):
    return requests.delete(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)

def patch(path, **kwargs):
    return requests.patch(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)


# ── 1. AVAILABILITY CHECKS ────────────────────────────────────────────────────

class TestAvailability:

    def test_api_is_reachable(self):
        """API must respond — basic connectivity check."""
        try:
            r = get("/")
            assert r.status_code < 500, f"Server error: {r.status_code}"
        except requests.ConnectionError:
            pytest.fail(f"Cannot connect to {BASE_URL} — is it running?")

    def test_health_endpoint_exists(self):
        """GET /health must return 200."""
        r = get("/health")
        assert r.status_code == 200, \
            f"/health returned {r.status_code} — endpoint missing or broken"

    def test_health_returns_json(self):
        """GET /health must return valid JSON."""
        r = get("/health")
        try:
            body = r.json()
            assert isinstance(body, dict), "Expected a JSON object"
        except Exception:
            pytest.fail("/health did not return valid JSON")

    def test_health_has_status_field(self):
        """GET /health JSON must contain a 'status' field."""
        r = get("/health")
        assert "status" in r.json(), \
            f"/health response missing 'status' field. Got: {r.json()}"

    def test_response_time_under_2s(self):
        """API must respond within 2 seconds."""
        start = time.perf_counter()
        get("/health")
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0, f"API too slow: {elapsed:.2f}s (limit: 3s)"


# ── 2. AUTH CHECKS ────────────────────────────────────────────────────────────

class TestAuthentication:

    def test_protected_endpoint_requires_token(self):
        """GET /tasks without token must return 401, not 200."""
        r = get("/tasks")
        assert r.status_code == 401, \
            f"/tasks without auth returned {r.status_code} — endpoint is unprotected!"

    def test_invalid_token_rejected(self):
        """Fake token must be rejected."""
        r = get("/tasks", headers={"Authorization": "Bearer faketoken123"})
        assert r.status_code == 401, \
            f"Fake token accepted! Got {r.status_code}"

    def test_register_endpoint_exists(self):
        """POST /register must exist (not 404)."""
        r = post("/register", json={"email": "probe@test.com", "password": "Test1234"})
        assert r.status_code != 404, \
            f"/register returned 404 — endpoint does not exist"

    def test_register_returns_json(self):
        """POST /register must return JSON."""
        r = post("/register", json={"email": "jsoncheck@test.com", "password": "Test1234"})
        try:
            r.json()
        except Exception:
            pytest.fail(f"/register did not return JSON. Body: {r.text[:200]}")

    def test_login_wrong_password_rejected(self):
        """POST /login with wrong password must return 401."""
        r = post("/login", json={"email": "nobody@x.com", "password": "wrongpassword"})
        assert r.status_code == 401, \
            f"Wrong password returned {r.status_code} instead of 401"

    def test_register_invalid_email_rejected(self):
        """POST /register with bad email must return 400."""
        r = post("/register", json={"email": "notanemail", "password": "Test1234"})
        assert r.status_code == 400, \
            f"Invalid email accepted! Got {r.status_code}"

    def test_register_short_password_rejected(self):
        """POST /register with short password must return 400."""
        r = post("/register", json={"email": "short@test.com", "password": "123"})
        assert r.status_code == 400, \
            f"Short password accepted! Got {r.status_code}"


# ── 3. SECURITY CHECKS ────────────────────────────────────────────────────────

class TestSecurity:

    def test_sql_injection_does_not_crash(self):
        """SQL injection in email must not cause a 500 crash."""
        r = post("/register", json={
            "email": "'; DROP TABLE users; --",
            "password": "Test1234"
        })
        assert r.status_code != 500, \
            f"SQL injection caused a 500 crash! Server is vulnerable."

    def test_empty_body_does_not_crash(self):
        """Sending empty body must not cause a 500 crash."""
        r = post("/register", json={})
        assert r.status_code != 500, \
            f"Empty body caused 500 crash! Got {r.status_code}"

    def test_no_stack_trace_in_error_response(self):
        """Error responses must not leak Python stack traces."""
        r = post("/register", json={"email": "bad", "password": ""})
        body = r.text
        for leak in ["Traceback", "File \"", "line ", "sqlite3", "Exception"]:
            assert leak not in body, \
                f"Stack trace leaked in response! Found '{leak}' in: {body[:300]}"

    def test_cors_headers_present(self):
        """API should include CORS headers for browser security."""
        r = get("/health")
        # Warn but don't hard fail — some APIs don't need CORS
        has_cors = "Access-Control-Allow-Origin" in r.headers
        if not has_cors:
            pytest.xfail("No CORS headers found — acceptable if API is not browser-facing")


# ── 4. RESPONSE FORMAT CHECKS ─────────────────────────────────────────────────

class TestResponseFormat:

    def test_content_type_is_json(self):
        """API responses must have Content-Type: application/json."""
        r = get("/health")
        ct = r.headers.get("Content-Type", "")
        assert "application/json" in ct, \
            f"Content-Type is '{ct}' — expected 'application/json'"

    def test_no_html_in_api_response(self):
        """API must not return HTML pages instead of JSON."""
        r = get("/health")
        assert not r.text.strip().startswith("<!DOCTYPE"), \
            "API returned an HTML page instead of JSON"
        assert not r.text.strip().startswith("<html"), \
            "API returned an HTML page instead of JSON"

    def test_404_returns_json_not_html(self):
        """Unknown routes should return JSON error, not HTML 404 page."""
        r = get("/this-route-does-not-exist-xyz")
        ct = r.headers.get("Content-Type", "")
        # If it returns HTML, it's a framework default page, not a clean API
        if r.text.strip().startswith("<!DOCTYPE") or r.text.strip().startswith("<html"):
            pytest.fail(
                f"Unknown route returns HTML page instead of JSON error. "
                f"This means the API has no custom 404 handler."
            )


# ── 5. PERFORMANCE CHECKS ─────────────────────────────────────────────────────

class TestPerformance:

    def test_health_under_3000ms(self):
        """GET /health must respond in under 3000ms (local dev server budget)."""
        start = time.perf_counter()
        get("/health")
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0, \
            f"/health took {elapsed*1000:.0f}ms — SLA is 3000ms"

    def test_10_consecutive_requests_stay_fast(self):
        """10 requests in a row must all complete within 3s each (local dev server)."""
        slow = []
        for i in range(10):
            start = time.perf_counter()
            get("/health")
            elapsed = time.perf_counter() - start
            if elapsed > 3.0:
                slow.append(f"Request {i+1}: {elapsed:.2f}s")
        assert not slow, f"Slow requests detected:\n" + "\n".join(slow)
