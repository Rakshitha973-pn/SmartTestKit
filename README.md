# 🧪 SmartTestKit

**Automated API Testing Framework — All 5 Phases**

> Paste your API URL → Click Run → Get a beautiful report. No setup. No coding knowledge needed.

---

## 📁 What's inside

```
SmartTestKit/
├── app/
│   └── main.py                    ← The sample Task Manager API you are testing
├── tests/
│   ├── conftest.py                ← Shared fixtures (auto-loaded by pytest)
│   ├── unit/
│   │   └── test_validation.py     ← Phase 1: pure logic tests
│   ├── integration/
│   │   └── test_api.py            ← Phase 1: full HTTP + DB tests
│   ├── security/
│   │   └── test_owasp.py          ← Phase 1: OWASP security tests
│   ├── performance/
│   │   └── test_sla.py            ← Phase 1: SLA latency budgets
│   └── regression/
│       └── test_regression.py     ← Phase 1: schema drift + bug regression
├── scripts/
│   ├── generate_report.py         ← Phase 2: beautiful HTML dashboard
│   ├── ai_test_generator.py       ← Phase 3: Claude writes tests automatically
│   ├── ai_explain_failures.py     ← Phase 3: Claude explains failures in plain English
│   └── track_history.py           ← Phase 4: trend graph over time
├── notifications/
│   └── notify.py                  ← Phase 4: Slack + email alerts
├── reports/                       ← Auto-generated reports go here
├── web_ui.py                      ← Phase 5: web interface (no CLI needed)
├── pytest.ini                     ← pytest configuration
├── requirements.txt
└── .github/workflows/ci.yml       ← GitHub Actions CI/CD
```

---

## 🚀 STEP BY STEP — How to run

### Step 1 — Open your terminal

On Windows: press `Win + R`, type `cmd`, press Enter
On Mac: press `Cmd + Space`, type `terminal`, press Enter

---

### Step 2 — Install Python (if not installed)

Download from: https://www.python.org/downloads/
Choose Python 3.11 or 3.12. Check "Add to PATH" during install.

Verify it works:
```
python --version
```
You should see `Python 3.11.x` or `Python 3.12.x`

---

### Step 3 — Go into the project folder

```bash
cd SmartTestKit
```

---

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, pytest, and all libraries. Takes ~1 minute.

---

### Step 5 — Run ALL tests (the main command)

```bash
pytest tests/ -v
```

You will see each test run with PASSED or FAILED.
At the end: `79 passed` means everything works.

---

### Step 6 — Run a specific category only

```bash
pytest tests/unit/        -v    # only unit tests
pytest tests/integration/ -v    # only integration tests
pytest tests/security/    -v    # only OWASP security tests
pytest tests/performance/ -v    # only performance/SLA tests
pytest tests/regression/  -v    # only regression tests
```

---

### Step 7 — Generate the HTML report

```bash
pytest tests/ --json-report --json-report-file=reports/results.json
python scripts/generate_report.py reports/results.json
```

Then open `reports/report.html` in your browser.
You will see a dark-mode dashboard with pass/fail breakdown per category.

---

### Step 8 — Track history (optional)

```bash
python scripts/track_history.py reports/results.json
```

Open `reports/history.html` to see a trend graph of quality over time.
Run this after every test session to build up the graph.

---

### Step 9 — Run the Web UI (Phase 5)

```bash
python web_ui.py
```

Then open your browser: **http://localhost:8080**

You will see a web page. Paste your API URL, click "Run Tests", get a report.
No terminal needed after this point.

---

### Step 10 — AI features (Phase 3)

Set your Anthropic API key first:
```bash
# Mac/Linux:
export ANTHROPIC_API_KEY=your-key-here

# Windows:
set ANTHROPIC_API_KEY=your-key-here
```

Generate edge-case tests automatically:
```bash
python scripts/ai_test_generator.py
```

Explain failures in plain English:
```bash
python scripts/ai_explain_failures.py reports/results.json
```

---

### Step 11 — GitHub CI/CD setup

1. Push this folder to a GitHub repository
2. Go to Settings → Secrets → Actions
3. Add these secrets:
   - `SLACK_WEBHOOK_URL` (optional — get from Slack API)
   - `ANTHROPIC_API_KEY` (optional — for AI features)
4. Every time you push code, GitHub automatically runs all 79 tests
5. Download the HTML report from Actions → Artifacts

---

## 🧪 What the 79 tests check

| Category | Tests | What it catches |
|---|---|---|
| Unit | 22 | Wrong validation logic, bad input handling |
| Integration | 18 | Full request → DB → response failures |
| Security | 19 | OWASP vulnerabilities, SQL injection, data isolation |
| Performance | 7 | Slow endpoints, SLA violations |
| Regression | 13 | Old bugs coming back, schema changes |
| **Total** | **79** | |

---

## 🎯 What makes SmartTestKit unique

1. **AI test generation** — Claude reads your code and writes tests you'd miss
2. **AI failure explainer** — plain English explanation + exact fix suggestion
3. **SLA budgets per endpoint** — not just "works" but "works within 200ms"
4. **Schema drift detection** — catches silent API contract breakage
5. **OWASP security layer** — SQL injection, BOLA, mass assignment built in
6. **Web UI** — non-developers can run tests in a browser
7. **History trend graph** — quality over time, not just today's run

---

## 🔑 Key commands summary

| What you want | Command |
|---|---|
| Run all tests | `pytest tests/ -v` |
| Run only security | `pytest tests/security/ -v` |
| Get HTML report | `pytest tests/ --json-report --json-report-file=reports/results.json && python scripts/generate_report.py reports/results.json` |
| Open web UI | `python web_ui.py` |
| AI generate tests | `python scripts/ai_test_generator.py` |
| AI explain failures | `python scripts/ai_explain_failures.py reports/results.json` |
| Track history | `python scripts/track_history.py reports/results.json` |
