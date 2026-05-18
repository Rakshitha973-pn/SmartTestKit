"""
PHASE 4 — NOTIFICATIONS
Send test results to Slack or Email after every CI run.
Run: python notifications/notify.py reports/results.json
"""
import json, sys, os, smtplib, urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def load_results(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def send_slack(results: dict, webhook_url: str):
    """Post a summary message to a Slack channel via webhook."""
    summary = results.get("summary", {})
    passed  = summary.get("passed", 0)
    failed  = summary.get("failed", 0) + summary.get("error", 0)
    total   = summary.get("total", 0)
    dur     = results.get("duration", 0)
    status  = "✅ All tests passed!" if failed == 0 else f"❌ {failed} test(s) failed"
    color   = "#10B981" if failed == 0 else "#EF4444"

    payload = {
        "attachments": [{
            "color": color,
            "blocks": [
                {"type": "header", "text": {"type": "plain_text",
                    "text": f"🧪 SmartTestKit Results — {datetime.now().strftime('%d %b %Y %H:%M')}"}},
                {"type": "section", "text": {"type": "mrkdwn",
                    "text": f"*{status}*\n✓ {passed} passed  ✗ {failed} failed  ⏱ {dur:.1f}s  📊 {total} total"}},
            ]
        }]
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
        print("✓ Slack notification sent")
    except Exception as e:
        print(f"✗ Slack notification failed: {e}")


def send_email(results: dict, smtp_host: str, smtp_port: int,
               sender: str, password: str, recipient: str):
    """Send an HTML email summary of test results."""
    summary = results.get("summary", {})
    passed  = summary.get("passed", 0)
    failed  = summary.get("failed", 0) + summary.get("error", 0)
    total   = summary.get("total", 0)
    subject = f"{'✅' if failed == 0 else '❌'} SmartTestKit — {passed}/{total} tests passed"

    failures_html = ""
    for t in results.get("tests", []):
        if t.get("outcome") in ("failed", "error"):
            name = t.get("nodeid", "").split("::")[-1]
            failures_html += f"<li style='color:#EF4444'>{name}</li>"

    html = f"""
    <html><body style="font-family:sans-serif;background:#0F172A;color:#E2E8F0;padding:24px">
    <h2>🧪 SmartTestKit Test Report</h2>
    <p>{datetime.now().strftime('%d %b %Y at %H:%M')}</p>
    <table style="border-collapse:collapse;margin:16px 0">
      <tr><td style="padding:8px 16px;background:#1E293B;border-radius:8px 0 0 8px">✓ Passed</td>
          <td style="padding:8px 16px;background:#1E293B;color:#10B981;font-weight:bold">{passed}</td></tr>
      <tr><td style="padding:8px 16px;background:#243044">✗ Failed</td>
          <td style="padding:8px 16px;background:#243044;color:#EF4444;font-weight:bold">{failed}</td></tr>
      <tr><td style="padding:8px 16px;background:#1E293B;border-radius:0 0 0 8px">📊 Total</td>
          <td style="padding:8px 16px;background:#1E293B;font-weight:bold">{total}</td></tr>
    </table>
    {"<h3>Failed tests:</h3><ul>" + failures_html + "</ul>" if failures_html else "<p style='color:#10B981'>All tests passed! 🎉</p>"}
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"✓ Email sent to {recipient}")
    except Exception as e:
        print(f"✗ Email failed: {e}")


def main(json_path: str):
    results = load_results(json_path)

    slack_url = os.environ.get("SLACK_WEBHOOK_URL")
    if slack_url:
        send_slack(results, slack_url)
    else:
        print("ℹ SLACK_WEBHOOK_URL not set — skipping Slack")

    smtp_host = os.environ.get("SMTP_HOST")
    if smtp_host:
        send_email(
            results,
            smtp_host=smtp_host,
            smtp_port=int(os.environ.get("SMTP_PORT", 465)),
            sender=os.environ.get("SMTP_SENDER", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
            recipient=os.environ.get("NOTIFY_EMAIL", ""),
        )
    else:
        print("ℹ SMTP_HOST not set — skipping email")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "reports/results.json"
    main(path)
