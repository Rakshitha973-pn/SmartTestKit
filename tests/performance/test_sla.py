"""
PHASE 1 — PERFORMANCE / SLA LATENCY TESTS
Each endpoint must respond within a time budget.
If it's slow, the test fails — before users complain.
Run: pytest tests/performance/ -v
"""
import time
import pytest


# SLA budgets in seconds — how fast each endpoint must respond
SLA = {
    "/health":   0.05,   # 50ms  — must be instant
    "/register": 0.50,   # 500ms — allows for password hashing
    "/login":    0.50,   # 500ms — allows for password checking
    "/tasks GET":0.20,   # 200ms — simple DB read
    "/tasks POST":0.30,  # 300ms — DB write
}


def measure(fn):
    """Run a function and return (result, elapsed_seconds)."""
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start


class TestSLABudgets:

    def test_health_under_50ms(self, client):
        _, elapsed = measure(lambda: client.get("/health"))
        assert elapsed < SLA["/health"], \
            f"/health took {elapsed*1000:.1f}ms — SLA is 50ms"

    def test_register_under_500ms(self, client):
        _, elapsed = measure(lambda: client.post("/register",
            json={"email": "perf@test.com", "password": "Password123"}))
        assert elapsed < SLA["/register"], \
            f"/register took {elapsed*1000:.1f}ms — SLA is 500ms"

    def test_login_under_500ms(self, client, registered_user):
        _, elapsed = measure(lambda: client.post("/login", json=registered_user))
        assert elapsed < SLA["/login"], \
            f"/login took {elapsed*1000:.1f}ms — SLA is 500ms"

    def test_get_tasks_under_200ms(self, client, auth_headers):
        _, elapsed = measure(lambda: client.get("/tasks", headers=auth_headers))
        assert elapsed < SLA["/tasks GET"], \
            f"GET /tasks took {elapsed*1000:.1f}ms — SLA is 200ms"

    def test_create_task_under_300ms(self, client, auth_headers):
        _, elapsed = measure(lambda: client.post("/tasks",
            json={"title": "Perf test task"}, headers=auth_headers))
        assert elapsed < SLA["/tasks POST"], \
            f"POST /tasks took {elapsed*1000:.1f}ms — SLA is 300ms"


class TestPerformanceUnderLoad:
    """Simulates multiple rapid calls to detect performance degradation."""

    def test_100_health_checks_stay_fast(self, client):
        times = []
        for _ in range(100):
            _, elapsed = measure(lambda: client.get("/health"))
            times.append(elapsed)
        avg = sum(times) / len(times)
        p95 = sorted(times)[94]  # 95th percentile
        assert avg < 0.05, f"Average health check: {avg*1000:.1f}ms (limit: 50ms)"
        assert p95 < 0.10, f"P95 health check: {p95*1000:.1f}ms (limit: 100ms)"

    def test_50_task_creates_stay_fast(self, client, auth_headers):
        times = []
        for i in range(50):
            _, elapsed = measure(lambda: client.post("/tasks",
                json={"title": f"Load task {i}"}, headers=auth_headers))
            times.append(elapsed)
        avg = sum(times) / len(times)
        assert avg < 0.30, f"Average task create: {avg*1000:.1f}ms (limit: 300ms)"
