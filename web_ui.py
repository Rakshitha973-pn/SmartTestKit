"""
SmartTestKit — Complete Web UI
Single file, no separate servers needed.
Run: python web_ui.py
Open: http://localhost:8080
"""
from flask import Flask, request, jsonify
import subprocess, json, os, threading, sys, time

ui = Flask(__name__)
_run_status = {}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SmartTestKit</title>
<style>
:root {
  --bg: #0F172A; --card: #1E293B; --card2: #243044;
  --border: #334155; --text: #E2E8F0; --muted: #94A3B8;
  --dim: #64748B; --green: #10B981; --red: #EF4444;
  --blue: #38BDF8; --purple: #818CF8; --amber: #F59E0B;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:var(--bg);color:var(--text);min-height:100vh}

/* NAV */
nav{background:var(--card);border-bottom:1px solid var(--border);
    padding:0 32px;display:flex;align-items:center;height:56px;gap:32px}
.nav-logo{font-size:18px;font-weight:800;color:var(--blue);margin-right:auto}
.nav-logo span{color:var(--purple)}
.nav-tab{font-size:13px;color:var(--muted);cursor:pointer;padding:4px 0;
         border-bottom:2px solid transparent;transition:all 0.2s}
.nav-tab.active{color:var(--text);border-color:var(--blue)}
.nav-tab:hover{color:var(--text)}

/* LAYOUT */
.page{display:none;max-width:900px;margin:0 auto;padding:32px 20px}
.page.active{display:block}

/* CARDS */
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:24px;margin-bottom:16px}
.card-title{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;
            letter-spacing:0.06em;margin-bottom:16px}

/* FORM */
label{font-size:13px;color:var(--muted);display:block;margin-bottom:6px}
input,select{width:100%;padding:10px 14px;background:var(--bg);border:1px solid var(--border);
             border-radius:8px;color:var(--text);font-size:14px;outline:none;margin-bottom:14px;
             transition:border 0.2s}
input:focus,select:focus{border-color:var(--blue)}
.run-btn{width:100%;padding:13px;background:linear-gradient(135deg,var(--blue),var(--purple));
         border:none;border-radius:10px;color:white;font-size:15px;font-weight:700;
         cursor:pointer;transition:opacity 0.2s;letter-spacing:0.02em}
.run-btn:disabled{opacity:0.4;cursor:not-allowed}
.run-btn:hover:not(:disabled){opacity:0.9}

/* PROGRESS */
.progress-wrap{margin-top:18px;display:none}
.prog-bar{background:var(--bg);border-radius:999px;height:6px;overflow:hidden;margin-bottom:8px}
.prog-fill{height:100%;width:0;background:linear-gradient(90deg,var(--green),var(--blue));
           border-radius:999px;transition:width 0.4s ease}
.prog-text{font-size:12px;color:var(--muted);text-align:center}

/* STATS ROW */
.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px;display:none}
.stat-box{background:var(--bg);border-radius:10px;padding:14px;text-align:center;
          border:1px solid var(--border)}
.stat-num{font-size:30px;font-weight:800;line-height:1}
.stat-label{font-size:11px;color:var(--dim);margin-top:4px}
.c-blue{color:var(--blue)} .c-green{color:var(--green)} .c-red{color:var(--red)}

/* LIVE LOG */
.log-wrap{margin-top:18px;display:none}
.log-box{background:#0a0f1a;border:1px solid var(--border);border-radius:10px;
         padding:14px;height:220px;overflow-y:auto;font-family:'SF Mono',monospace;font-size:12px;
         line-height:1.6;color:#94A3B8}
.log-pass{color:#10B981} .log-fail{color:#EF4444} .log-warn{color:#F59E0B}

/* DOWNLOAD BTN */
.dl-btn{display:block;margin-top:14px;padding:11px;background:var(--card2);
        border:1px solid var(--border);border-radius:10px;text-align:center;
        color:var(--blue);text-decoration:none;font-size:13px;font-weight:500;display:none}
.dl-btn:hover{background:var(--border)}

/* REPORT FRAME */
.report-frame{width:100%;border:1px solid var(--border);border-radius:12px;
              background:var(--card);min-height:500px;overflow:hidden}
.report-placeholder{display:flex;align-items:center;justify-content:center;
                    height:400px;flex-direction:column;gap:12px;color:var(--muted)}
.report-placeholder .icon{font-size:48px}

/* HISTORY */
.history-table{width:100%;border-collapse:collapse}
.history-table th{font-size:11px;font-weight:600;color:var(--dim);text-transform:uppercase;
                  letter-spacing:0.06em;padding:8px 12px;text-align:left;
                  border-bottom:1px solid var(--border)}
.history-table td{font-size:13px;padding:10px 12px;border-bottom:1px solid #1a2539}
.history-table tr:last-child td{border-bottom:none}
.badge{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;
       border-radius:20px}
.badge-pass{background:#1a3a2a;color:var(--green)}
.badge-fail{background:#3a1a1a;color:var(--red)}

/* FEATURES */
.features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.feature-card{background:var(--card2);border-radius:12px;padding:18px;
              border:1px solid var(--border)}
.feature-icon{font-size:24px;margin-bottom:10px}
.feature-title{font-size:14px;font-weight:600;margin-bottom:4px}
.feature-desc{font-size:12px;color:var(--muted);line-height:1.6}
.pill{display:inline-block;font-size:10px;font-weight:600;padding:2px 8px;
      border-radius:20px;margin:2px;background:var(--card2);border:1px solid var(--border)}

/* TOAST */
.toast{position:fixed;bottom:24px;right:24px;background:var(--card2);border:1px solid var(--border);
       border-radius:10px;padding:12px 18px;font-size:13px;transform:translateY(100px);
       transition:transform 0.3s;z-index:999}
.toast.show{transform:translateY(0)}
</style>
</head>
<body>

<nav>
  <div class="nav-logo">Smart<span>Test</span>Kit</div>
  <div class="nav-tab active" onclick="showPage('run',this)">&#9654; Run Tests</div>
  <div class="nav-tab" onclick="showPage('report',this)">&#128196; Report</div>
  <div class="nav-tab" onclick="showPage('history',this)">&#128200; History</div>
  <div class="nav-tab" onclick="showPage('about',this)">&#9432; About</div>
</nav>

<!-- PAGE: RUN TESTS -->
<div id="page-run" class="page active">
  <div class="card">
    <div class="card-title">&#127775; Run API Tests</div>

    <label>API Base URL to test</label>
    <input type="url" id="apiUrl" placeholder="https://your-api.com or http://localhost:5000"
           value="http://localhost:5000">

    <label>Test suite</label>
    <select id="suite">
      <option value="tests/external">&#127760; External API tests — tests the URL above (recommended)</option>
      <option value="tests">&#128203; All internal tests (unit + integration + security + performance + regression)</option>
      <option value="tests/unit">&#129513; Unit tests only</option>
      <option value="tests/integration">&#128279; Integration tests only</option>
      <option value="tests/security">&#128737; Security / OWASP tests only</option>
      <option value="tests/performance">&#9889; Performance / SLA tests only</option>
      <option value="tests/regression">&#128257; Regression tests only</option>
    </select>

    <label>Quick presets</label>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">
      <button onclick="setUrl('http://localhost:5000')"
              style="flex:none;width:auto;padding:6px 14px;font-size:12px;border-radius:8px;
                     background:var(--card2);border:1px solid var(--border);color:var(--text);cursor:pointer">
        localhost:5000</button>
      <button onclick="setUrl('https://reqres.in')"
              style="flex:none;width:auto;padding:6px 14px;font-size:12px;border-radius:8px;
                     background:var(--card2);border:1px solid var(--border);color:var(--text);cursor:pointer">
        reqres.in (will fail some)</button>
      <button onclick="setUrl('https://jsonplaceholder.typicode.com')"
              style="flex:none;width:auto;padding:6px 14px;font-size:12px;border-radius:8px;
                     background:var(--card2);border:1px solid var(--border);color:var(--text);cursor:pointer">
        jsonplaceholder (will fail many)</button>
    </div>

    <button class="run-btn" onclick="runTests()" id="runBtn">&#9654;&#160; Run Tests</button>

    <div class="progress-wrap" id="progressWrap">
      <div class="prog-bar"><div class="prog-fill" id="progFill"></div></div>
      <div class="prog-text" id="progText">Starting...</div>
    </div>

    <div class="log-wrap" id="logWrap">
      <div class="card-title" style="margin-top:16px;margin-bottom:8px">&#128196; Live Output</div>
      <div class="log-box" id="logBox"></div>
    </div>

    <div class="stats-row" id="statsRow">
      <div class="stat-box"><div class="stat-num c-blue" id="rTotal">0</div><div class="stat-label">Total</div></div>
      <div class="stat-box"><div class="stat-num c-green" id="rPassed">0</div><div class="stat-label">Passed</div></div>
      <div class="stat-box"><div class="stat-num c-red" id="rFailed">0</div><div class="stat-label">Failed</div></div>
    </div>

    <div id="xfailNote" style="display:none;margin-top:10px;font-size:12px;
         color:var(--amber);background:var(--card2);border-radius:8px;
         padding:8px 12px;border:1px solid #4a3800;text-align:center"></div>

    <a class="dl-btn" id="dlBtn" href="#" download="smarttestkit_report.html">
      &#11015;&#160; Download Full HTML Report
    </a>
  </div>

  <div class="card">
    <div class="card-title">&#128161; Tips</div>
    <p style="font-size:13px;color:var(--muted);line-height:1.7">
      &#9679; Select <b style="color:var(--text)">External API tests</b> to test any URL — your own API, or public ones like reqres.in.<br>
      &#9679; Select <b style="color:var(--text)">All internal tests</b> to run the full 79-test suite against your local Flask app.<br>
      &#9679; After running, go to the <b style="color:var(--text)">Report</b> tab to view the full dashboard.<br>
      &#9679; Start your local API first: <code style="background:var(--bg);padding:2px 6px;border-radius:4px">python app/main.py</code>
    </p>
  </div>
</div>

<!-- PAGE: REPORT -->
<div id="page-report" class="page">
  <div class="card">
    <div class="card-title">&#128196; Latest Test Report</div>
    <div id="reportContainer">
      <div class="report-placeholder">
        <div class="icon">&#128202;</div>
        <div style="font-size:15px;font-weight:600">No report yet</div>
        <div style="font-size:13px">Run tests first, then come back here</div>
      </div>
    </div>
  </div>
</div>

<!-- PAGE: HISTORY -->
<div id="page-history" class="page">
  <div class="card">
    <div class="card-title">&#128200; Run History</div>
    <div id="historyContainer">
      <p style="color:var(--muted);font-size:13px">No history yet. Run some tests first.</p>
    </div>
  </div>
</div>

<!-- PAGE: ABOUT -->
<div id="page-about" class="page">
  <div class="card">
    <div class="card-title">&#127775; What makes SmartTestKit unique</div>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">&#129302;</div>
        <div class="feature-title">AI Test Generation</div>
        <div class="feature-desc">Claude reads your source code and writes edge-case tests humans typically miss.</div>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#128737;</div>
        <div class="feature-title">OWASP Security Layer</div>
        <div class="feature-desc">SQL injection, BOLA, mass assignment, error leakage — all checked automatically.</div>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#9889;</div>
        <div class="feature-title">SLA Latency Budgets</div>
        <div class="feature-desc">Not just "does it work" but "does it respond within 300ms" — per endpoint.</div>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#128257;</div>
        <div class="feature-title">Schema Drift Detection</div>
        <div class="feature-desc">Alerts the team when API response shape changes silently — before clients break.</div>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#127760;</div>
        <div class="feature-title">External API Testing</div>
        <div class="feature-desc">Paste any API URL — yours, a colleague's, or a public API — and get a full report.</div>
      </div>
      <div class="feature-card">
        <div class="feature-icon">&#128200;</div>
        <div class="feature-title">History Trend Graph</div>
        <div class="feature-desc">Track quality over time. See if you're improving or declining across weeks.</div>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-title">&#128203; Test breakdown</div>
    <table class="history-table">
      <tr><th>Category</th><th>Tests</th><th>What it catches</th></tr>
      <tr><td>Unit</td><td>22</td><td style="color:var(--muted)">Wrong validation logic, bad input handling</td></tr>
      <tr><td>Integration</td><td>18</td><td style="color:var(--muted)">Full request &rarr; DB &rarr; response failures</td></tr>
      <tr><td>Security</td><td>19</td><td style="color:var(--muted)">OWASP vulnerabilities, SQL injection, data isolation</td></tr>
      <tr><td>Performance</td><td>7</td><td style="color:var(--muted)">Slow endpoints, SLA violations</td></tr>
      <tr><td>Regression</td><td>13</td><td style="color:var(--muted)">Old bugs coming back, schema changes</td></tr>
      <tr><td>External</td><td>21</td><td style="color:var(--muted)">Real HTTP checks against any live API</td></tr>
      <tr style="font-weight:600"><td>Total</td><td>100</td><td style="color:var(--muted)">Full coverage</td></tr>
    </table>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let _reportHtml = null;
const history_runs = [];

function showPage(name, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  el.classList.add('active');
  if (name === 'history') loadHistory();
}

function setUrl(url) {
  document.getElementById('apiUrl').value = url;
  toast('URL set to ' + url);
}

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function appendLog(text, cls) {
  const box = document.getElementById('logBox');
  const line = document.createElement('div');
  if (cls) line.className = cls;
  line.textContent = text;
  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}

async function runTests() {
  const url = document.getElementById('apiUrl').value.trim();
  const suite = document.getElementById('suite').value;

  // Client-side URL validation
  if (!url) { toast('Please enter an API URL'); return; }
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    toast('URL must start with http:// or https://');
    document.getElementById('apiUrl').style.borderColor = 'var(--red)';
    return;
  }
  try {
    const u = new URL(url);
    const host = u.hostname;
    const validLocal = ['localhost','127.0.0.1','0.0.0.0'];
    if (!host.includes('.') && !validLocal.includes(host)) {
      toast('Invalid URL — use a real domain like reqres.in or localhost');
      document.getElementById('apiUrl').style.borderColor = 'var(--red)';
      return;
    }
  } catch(e) {
    toast('Invalid URL format');
    document.getElementById('apiUrl').style.borderColor = 'var(--red)';
    return;
  }
  document.getElementById('apiUrl').style.borderColor = '';

  // reset UI
  document.getElementById('runBtn').disabled = true;
  document.getElementById('progressWrap').style.display = 'block';
  document.getElementById('logWrap').style.display = 'block';
  document.getElementById('statsRow').style.display = 'none';
  document.getElementById('dlBtn').style.display = 'none';
  document.getElementById('logBox').innerHTML = '';
  _reportHtml = null;

  appendLog('Starting test suite: ' + suite, 'log-warn');
  appendLog('Target API: ' + url, 'log-warn');

  // animate progress
  let pct = 0;
  const msgs = ['Running unit tests...', 'Checking security...', 'Measuring performance...', 'Verifying schema...', 'Generating report...'];
  const timer = setInterval(() => {
    pct = Math.min(pct + 1.5, 88);
    document.getElementById('progFill').style.width = pct + '%';
    document.getElementById('progText').textContent = msgs[Math.floor(pct / 20)] || 'Running...';
  }, 400);

  try {
    const r = await fetch('/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({api_url: url, suite})
    });
    const data = await r.json();
    if (!r.ok || data.error) {
      clearInterval(timer);
      document.getElementById('progText').textContent = 'Validation failed';
      appendLog('ERROR: ' + (data.error || 'Unknown error'), 'log-fail');
      document.getElementById('runBtn').disabled = false;
      document.getElementById('apiUrl').style.borderColor = 'var(--red)';
      return;
    }
    poll(data.run_id, timer);
  } catch(e) {
    clearInterval(timer);
    appendLog('Error: ' + e.message, 'log-fail');
    document.getElementById('runBtn').disabled = false;
  }
}

async function poll(runId, timer) {
  try {
    const r = await fetch('/status/' + runId);
    const data = await r.json();

    if (data.log_lines) {
      data.log_lines.forEach(line => {
        const cls = line.includes('PASSED') ? 'log-pass'
                  : line.includes('FAILED') || line.includes('ERROR') ? 'log-fail'
                  : line.includes('WARN') ? 'log-warn' : '';
        appendLog(line, cls);
      });
    }

    if (data.status === 'running') {
      setTimeout(() => poll(runId, timer), 1200);
    } else {
      clearInterval(timer);
      document.getElementById('progFill').style.width = '100%';
      document.getElementById('runBtn').disabled = false;

      if (data.status === 'done') {
        document.getElementById('progText').textContent = 'Complete!';
        const s = data.summary || {};
        const total   = s.total || 0;
        const passed  = s.passed || 0;
        const failed  = (s.failed || 0) + (s.error || 0);
        const xfailed = s.xfailed || 0;
        document.getElementById('rTotal').textContent   = total;
        document.getElementById('rPassed').textContent  = passed;
        document.getElementById('rFailed').textContent  = failed;
        // Show xfailed note if any
        const xNote = document.getElementById('xfailNote');
        if (xfailed > 0) {
          xNote.textContent = xfailed + ' expected failure(s) (xfail) not counted above';
          xNote.style.display = 'block';
        } else {
          xNote.style.display = 'none';
        }
        document.getElementById('statsRow').style.display = 'grid';

        if (data.report_html) {
          _reportHtml = data.report_html;
          const blob = new Blob([_reportHtml], {type: 'text/html;charset=utf-8'});
          const dlBtn = document.getElementById('dlBtn');
          dlBtn.href = URL.createObjectURL(blob);
          dlBtn.style.display = 'block';

          // update report tab
          document.getElementById('reportContainer').innerHTML =
            '<iframe srcdoc="' + _reportHtml.replace(/"/g, '&quot;') + '" ' +
            'style="width:100%;height:600px;border:none;border-radius:10px"></iframe>';
        }
        toast('Done! ' + (s.passed||0) + ' passed, ' + ((s.failed||0)+(s.error||0)) + ' failed');
      } else {
        document.getElementById('progText').textContent = 'Error';
        appendLog('Run failed: ' + data.status, 'log-fail');
      }
    }
  } catch(e) {
    clearInterval(timer);
    appendLog('Poll error: ' + e.message, 'log-fail');
    document.getElementById('runBtn').disabled = false;
  }
}

async function loadHistory() {
  try {
    const r = await fetch('/history');
    const runs = await r.json();
    const container = document.getElementById('historyContainer');
    if (!runs.length) {
      container.innerHTML = '<p style="color:var(--muted);font-size:13px">No history yet. Run some tests first.</p>';
      return;
    }
    let rows = runs.slice().reverse().map(run => {
      const pass = run.passed || 0;
      const fail = (run.failed || 0) + (run.error || 0);
      const total = run.total || 0;
      const rate = total ? Math.round(pass/total*100) : 0;
      const badge = fail === 0
        ? '<span class="badge badge-pass">&#10003; All passed</span>'
        : '<span class="badge badge-fail">&#10007; ' + fail + ' failed</span>';
      return '<tr>' +
        '<td>' + (run.timestamp||'').replace('T',' ').slice(0,19) + '</td>' +
        '<td>' + (run.url || run.api_url || '—') + '</td>' +
        '<td style="color:var(--blue)">' + total + '</td>' +
        '<td style="color:var(--green)">' + pass + '</td>' +
        '<td>' + badge + '</td>' +
        '<td style="color:var(--muted)">' + rate + '%</td>' +
        '</tr>';
    }).join('');
    container.innerHTML = '<table class="history-table">' +
      '<tr><th>Time</th><th>URL tested</th><th>Total</th><th>Passed</th><th>Result</th><th>Rate</th></tr>' +
      rows + '</table>';
  } catch(e) {
    document.getElementById('historyContainer').innerHTML =
      '<p style="color:var(--muted);font-size:13px">Could not load history.</p>';
  }
}
</script>
</body>
</html>"""


# ── history helpers ───────────────────────────────────────────────────────────

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "run_history.json")

def _load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_history(runs):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(runs[-100:], f, indent=2)


# ── routes ────────────────────────────────────────────────────────────────────

@ui.route("/")
def index():
    return HTML

@ui.route("/history")
def get_history():
    return jsonify(_load_history())

@ui.route("/run", methods=["POST"])
def run_tests():
    import uuid, re
    data    = request.get_json() or {}
    run_id  = str(uuid.uuid4())[:8]
    suite   = data.get("suite", "tests/external")
    api_url = data.get("api_url", "").strip()

    # ── URL validation ────────────────────────────────────────────────────────
    if not re.match(r'^https?://', api_url):
        return jsonify({"error": "Invalid URL. Must start with http:// or https://"}), 400
    host = api_url.split("//")[-1].split("/")[0].split(":")[0]
    if not host:
        return jsonify({"error": "Invalid URL. No host found."}), 400
    if "." not in host and host not in ("localhost", "127.0.0.1", "0.0.0.0"):
        return jsonify({"error": f"Invalid host: '{host}'. Use a real URL like https://reqres.in or http://localhost:5000"}), 400

    _run_status[run_id] = {
        "status": "running",
        "summary": None,
        "report_html": None,
        "log_lines": []
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))

    def execute():
        try:
            json_path = os.path.join(base_dir, "reports", f"results_{run_id}.json")
            os.makedirs(os.path.join(base_dir, "reports"), exist_ok=True)

            env = os.environ.copy()
            env["TARGET_API_URL"]  = api_url
            env["BASE_URL"]        = api_url   # for compatibility
            env["PYTHONIOENCODING"] = "utf-8"

            result = subprocess.run(
                [sys.executable, "-m", "pytest", suite,
                 "--json-report", f"--json-report-file={json_path}",
                 "--override-ini=addopts=",
                 "--override-ini=testpaths=",
                 "-v", "--tb=short", "--no-header"],
                capture_output=True, text=True, timeout=180,
                cwd=base_dir, env=env
            )

            # Parse log lines for live output
            log_lines = []
            for line in (result.stdout + result.stderr).splitlines():
                if line.strip():
                    log_lines.append(line)

            _run_status[run_id]["log_lines"] = log_lines

            summary = {"total": 0, "passed": 0, "failed": 0}

            if os.path.exists(json_path):
                with open(json_path, encoding="utf-8") as f:
                    results = json.load(f)
                summary = results.get("summary", summary)

                # Generate HTML report
                sys.path.insert(0, base_dir)
                from scripts.generate_report import generate_html_report
                out = os.path.join(base_dir, "reports", f"report_{run_id}.html")
                generate_html_report(json_path, out)

                with open(out, encoding="utf-8") as f:
                    html = f.read()

                _run_status[run_id]["report_html"] = html

            # Save to history
            runs = _load_history()
            runs.append({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "api_url":   api_url,
                "suite":     suite,
                "total":     summary.get("total", 0),
                "passed":    summary.get("passed", 0),
                "failed":    summary.get("failed", 0) + summary.get("error", 0),
                "run_id":    run_id,
            })
            _save_history(runs)

            _run_status[run_id].update({
                "status": "done",
                "summary": summary,
            })

        except subprocess.TimeoutExpired:
            _run_status[run_id]["status"] = "error: test run timed out (180s)"
        except Exception as e:
            _run_status[run_id]["status"] = f"error: {e}"

    threading.Thread(target=execute, daemon=True).start()
    return jsonify({"run_id": run_id})


@ui.route("/status/<run_id>")
def status(run_id):
    data = _run_status.get(run_id, {"status": "not_found"})
    # Return and clear log lines so they're only sent once
    out = dict(data)
    if "log_lines" in out:
        _run_status[run_id]["log_lines"] = []
    return jsonify(out)


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    print("\nSmartTestKit Web UI")
    print("Open: http://localhost:8080\n")
    ui.run(port=8080, debug=False, threaded=True)
