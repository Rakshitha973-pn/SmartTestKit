"""
PHASE 4 -- HISTORY TRACKER
Appends every test run result to a history file.
Generates a trend graph showing quality over time.
Run: python scripts/track_history.py reports/results.json
"""
import json, os, sys
from datetime import datetime
from pathlib import Path

HISTORY_FILE = "reports/history.json"


def record_run(results_path: str):
    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)

    summary_data = data.get("summary", {})
    entry = {
        "timestamp": datetime.now().isoformat(),
        "passed":    summary_data.get("passed", 0),
        "failed":    summary_data.get("failed", 0) + summary_data.get("error", 0),
        "total":     summary_data.get("total", 0),
        "duration":  round(data.get("duration", 0), 2),
    }
    entry["pass_rate"] = round(entry["passed"] / entry["total"] * 100, 1) if entry["total"] else 0

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            history = json.load(f)

    history.append(entry)

    Path(HISTORY_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"Run recorded. Total history: {len(history)} runs")
    _generate_trend_html(history)


def _generate_trend_html(history: list):
    if len(history) < 1:
        return

    labels = [h["timestamp"][:10] for h in history]
    rates  = [h["pass_rate"] for h in history]

    w, h, pad = 600, 200, 40
    x_step = (w - 2*pad) / max(len(history)-1, 1)
    points = []
    for i, rate in enumerate(rates):
        x = pad + i * x_step
        y = h - pad - (rate / 100) * (h - 2*pad)
        points.append((x, y))

    polyline = " ".join(f"{x},{y}" for x, y in points)
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="4" fill="#38BDF8"/>'
        for x, y in points
    )
    x_labels = "".join(
        f'<text x="{pad + i*x_step}" y="{h-8}" text-anchor="middle" font-size="9" fill="#64748B">{labels[i]}</text>'
        for i in range(len(labels))
    )

    rows = "".join(
        f"<tr>"
        f"<td>{e['timestamp'][:19].replace('T',' ')}</td>"
        f"<td style='color:#10B981'>{e['passed']}</td>"
        f"<td style='color:{'#EF4444' if e['failed'] else '#10B981'}'>{e['failed']}</td>"
        f"<td style='color:{'#10B981' if e['pass_rate']>=80 else '#EF4444'}'>{e['pass_rate']}%</td>"
        f"<td>{e['duration']}s</td></tr>"
        for e in reversed(history)
    )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>SmartTestKit History</title>
<style>
  body{{font-family:sans-serif;background:#0F172A;color:#E2E8F0;padding:32px}}
  h2{{color:#38BDF8;margin-bottom:24px}}
  table{{border-collapse:collapse;width:100%;background:#1E293B;border-radius:12px;overflow:hidden}}
  th,td{{padding:10px 16px;text-align:left;border-bottom:1px solid #334155;font-size:13px}}
  th{{background:#243044;color:#94A3B8;font-size:11px;text-transform:uppercase;letter-spacing:0.05em}}
</style></head><body>
<h2>SmartTestKit &mdash; Test Quality Trend</h2>
<svg width="100%" viewBox="0 0 {w} {h}" style="background:#1E293B;border-radius:12px;margin-bottom:24px">
  <polyline points="{polyline}" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linejoin="round"/>
  {dots}
  {x_labels}
  <text x="{pad-8}" y="{h-pad}" text-anchor="end" font-size="9" fill="#64748B">0%</text>
  <text x="{pad-8}" y="{pad}" text-anchor="end" font-size="9" fill="#64748B">100%</text>
  <line x1="{pad}" y1="{h - pad - 0.8*(h-2*pad)}" x2="{w-pad}" y2="{h - pad - 0.8*(h-2*pad)}"
        stroke="#334155" stroke-dasharray="4 4" stroke-width="1"/>
  <text x="{w-pad+4}" y="{h - pad - 0.8*(h-2*pad)+4}" font-size="9" fill="#64748B">80%</text>
</svg>
<table>
  <tr><th>Date</th><th>Passed</th><th>Failed</th><th>Pass Rate</th><th>Duration</th></tr>
  {rows}
</table>
</body></html>"""

    out = "reports/history.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Trend graph saved to: {out}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "reports/results.json"
    record_run(path)
