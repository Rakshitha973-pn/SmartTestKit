"""
PHASE 2 -- HTML REPORT GENERATOR
Parses pytest JSON output and builds a beautiful dashboard HTML report.
Run: python scripts/generate_report.py
"""
import json, os, sys
from datetime import datetime
from pathlib import Path


def generate_html_report(json_path="reports/results.json", out_path="reports/report.html"):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    summary  = data.get("summary", {})
    tests    = data.get("tests", [])
    total    = summary.get("total", 0)
    passed   = summary.get("passed", 0)
    failed   = summary.get("failed", 0)
    errors   = summary.get("error", 0)
    duration = data.get("duration", 0)
    pass_pct = round((passed / total * 100) if total else 0, 1)

    categories = {
        "unit": [], "integration": [], "security": [],
        "performance": [], "regression": [], "other": []
    }
    for t in tests:
        node, placed = t.get("nodeid", ""), False
        for cat in ("unit", "integration", "security", "performance", "regression"):
            if cat in node:
                categories[cat].append(t)
                placed = True
                break
        if not placed:
            categories["other"].append(t)

    cat_colors = {
        "unit": "#3B82F6", "integration": "#10B981", "security": "#EF4444",
        "performance": "#F59E0B", "regression": "#8B5CF6", "other": "#6B7280"
    }
    # Use HTML entities instead of emoji -- works on all Windows encodings
    cat_icons = {
        "unit": "&#x1F9E9;", "integration": "&#x1F517;", "security": "&#x1F6E1;",
        "performance": "&#x26A1;", "regression": "&#x1F501;", "other": "&#x1F4CB;"
    }

    rows_html = ""
    for cat, tlist in categories.items():
        if not tlist:
            continue
        c_pass = sum(1 for t in tlist if t.get("outcome") == "passed")
        c_fail = len(tlist) - c_pass
        color  = cat_colors[cat]
        rows_html += f"""
        <div class="cat-section" style="border-left:4px solid {color}">
          <div class="cat-header">
            <span class="cat-icon">{cat_icons[cat]}</span>
            <span class="cat-name">{cat.upper()} TESTS</span>
            <span class="cat-count">{len(tlist)} tests</span>
            <span class="cat-pass" style="color:{color}">&#10003; {c_pass} passed</span>
            {"<span class='cat-fail'>&#10007; " + str(c_fail) + " failed</span>" if c_fail else ""}
          </div><div class="test-list">"""
        for t in tlist:
            outcome  = t.get("outcome", "unknown")
            name     = t.get("nodeid", "").split("::")[-1]
            dur      = t.get("duration", 0)
            icon     = "&#10003;" if outcome == "passed" else "&#10007;"
            cls      = "pass" if outcome == "passed" else "fail"
            call     = t.get("call", {})
            longrepr = (call.get("longrepr", "") if call else "")[:500]
            details  = f'<div class="error-detail"><pre>{longrepr}</pre></div>' if longrepr else ""
            rows_html += f"""
            <div class="test-row {cls}">
              <span class="test-icon">{icon}</span>
              <span class="test-name">{name}</span>
              <span class="test-dur">{dur*1000:.0f}ms</span>
            </div>{details}"""
        rows_html += "</div></div>"

    gate_color = "#10B981" if pass_pct >= 80 else "#EF4444"
    gate_mark  = "&#10003;" if pass_pct >= 80 else "&#10007; (below 80% gate)"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SmartTestKit Report</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0F172A;color:#E2E8F0;min-height:100vh}}
  .topbar{{background:#1E293B;border-bottom:1px solid #334155;padding:16px 32px;display:flex;align-items:center;gap:12px}}
  .logo{{font-size:20px;font-weight:700;color:#38BDF8}}
  .subtitle{{font-size:13px;color:#94A3B8}}
  .container{{max-width:1100px;margin:0 auto;padding:32px 20px}}
  .summary-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:32px}}
  .summary-card{{background:#1E293B;border-radius:12px;padding:20px;border:1px solid #334155;text-align:center}}
  .summary-card .num{{font-size:36px;font-weight:700;line-height:1}}
  .summary-card .label{{font-size:13px;color:#94A3B8;margin-top:4px}}
  .num-pass{{color:#10B981}} .num-fail{{color:#EF4444}} .num-total{{color:#38BDF8}} .num-dur{{color:#F59E0B}}
  .progress-section{{background:#1E293B;border-radius:12px;padding:20px 24px;margin-bottom:24px;border:1px solid #334155}}
  .progress-label{{display:flex;justify-content:space-between;font-size:14px;margin-bottom:8px}}
  .progress-bar{{background:#0F172A;border-radius:999px;height:16px;overflow:hidden}}
  .progress-fill{{height:100%;border-radius:999px;background:linear-gradient(90deg,#10B981,#38BDF8)}}
  .cat-section{{background:#1E293B;border-radius:12px;margin-bottom:16px;overflow:hidden;border:1px solid #334155}}
  .cat-header{{display:flex;align-items:center;gap:12px;padding:14px 20px;background:#243044;flex-wrap:wrap}}
  .cat-icon{{font-size:18px}} .cat-name{{font-weight:600;font-size:13px;letter-spacing:0.05em}}
  .cat-count{{font-size:12px;color:#64748B;margin-left:auto}}
  .cat-pass{{font-size:13px;font-weight:500}} .cat-fail{{font-size:13px;font-weight:500;color:#EF4444}}
  .test-list{{padding:4px 0}}
  .test-row{{display:flex;align-items:center;gap:10px;padding:8px 20px;border-bottom:1px solid #1A2539;font-size:13px}}
  .test-row:last-child{{border-bottom:none}}
  .test-row.pass .test-icon{{color:#10B981;font-weight:700}}
  .test-row.fail .test-icon{{color:#EF4444;font-weight:700}}
  .test-name{{flex:1;color:#CBD5E1;font-family:'SF Mono',monospace;font-size:12px}}
  .test-dur{{font-size:11px;color:#475569}}
  .error-detail{{background:#1a0a0a;border-left:3px solid #EF4444;margin:0 20px 8px;border-radius:0 4px 4px 0;padding:10px}}
  .error-detail pre{{font-size:11px;color:#FCA5A5;white-space:pre-wrap}}
  .footer{{text-align:center;color:#475569;font-size:12px;margin-top:40px;padding:20px}}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <div class="logo">SmartTestKit</div>
    <div class="subtitle">Report generated {datetime.now().strftime('%d %b %Y at %H:%M:%S')}</div>
  </div>
</div>
<div class="container">
  <div class="summary-grid">
    <div class="summary-card"><div class="num num-total">{total}</div><div class="label">Total Tests</div></div>
    <div class="summary-card"><div class="num num-pass">{passed}</div><div class="label">Passed</div></div>
    <div class="summary-card"><div class="num num-fail">{failed + errors}</div><div class="label">Failed</div></div>
    <div class="summary-card"><div class="num num-dur">{duration:.1f}s</div><div class="label">Duration</div></div>
  </div>
  <div class="progress-section">
    <div class="progress-label">
      <span>Coverage Gate (pass rate)</span>
      <span style="color:{gate_color}">{pass_pct}% {gate_mark}</span>
    </div>
    <div class="progress-bar"><div class="progress-fill" style="width:{pass_pct}%"></div></div>
  </div>
  {rows_html}
  <div class="footer">SmartTestKit &mdash; Automated API Testing Framework &nbsp;|&nbsp; {datetime.now().year}</div>
</div>
</body>
</html>"""

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report saved to: {out_path}")
    return out_path


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "reports/results.json"
    generate_html_report(json_path)
