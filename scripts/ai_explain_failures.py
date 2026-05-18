"""
PHASE 3 — AI FAILURE EXPLAINER
After tests run, reads the JSON results and uses Claude to explain
each failure in plain English + suggest the exact fix.
Run: python scripts/ai_explain_failures.py reports/results.json
"""
import json, sys, os, urllib.request


def explain_failure(test_name: str, error: str) -> str:
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": f"""A pytest test failed. Explain in simple English what went wrong and suggest the exact code fix.

Test name: {test_name}
Error output:
{error[:1500]}

Reply in this format:
WHAT BROKE: (1 sentence, plain English)
WHY IT BROKE: (2-3 sentences explaining the root cause)
HOW TO FIX: (exact code change needed)
"""
        }]
    }
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except Exception as e:
        return f"Could not reach Claude API: {e}"


def main(json_path: str):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    failures = [
        t for t in data.get("tests", [])
        if t.get("outcome") in ("failed", "error")
    ]

    if not failures:
        print("✓ No failures to explain!")
        return

    print(f"\n{'='*60}")
    print(f"  SmartTestKit — AI Failure Explainer ({len(failures)} failures)")
    print(f"{'='*60}\n")

    for t in failures:
        name = t.get("nodeid", "unknown")
        call = t.get("call", {}) or {}
        error = call.get("longrepr", "No error detail available")

        print(f"❌ FAILED: {name.split('::')[-1]}")
        print(f"   File:   {name}")
        print()

        explanation = explain_failure(name, error)
        for line in explanation.splitlines():
            print(f"   {line}")
        print(f"\n{'─'*60}\n")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "reports/results.json"
    main(path)
