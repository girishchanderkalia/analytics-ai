import json
import urllib.request

BASE = "http://localhost:8000"

PROMPTS = [
    "Show me trends and outliers",
    "Show me anything over 5%",
    "Only severe degradation, more than 10 percent below baseline",
    "flag even the small stuff, 1% is enough",
    "show me anything worse than 40%",
]


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


for prompt in PROMPTS:
    r = post("/chat", {"message": prompt})
    ev = r.get("evidence") or {}
    outliers = ev.get("outliers") or []
    points = sum(len(o["outlier_dates"]) for o in outliers)
    print(f"{prompt!r}")
    print(
        f"   threshold={ev.get('threshold_pct')} "
        f"status={r['status']} series={len(outliers)} points={points}"
    )
