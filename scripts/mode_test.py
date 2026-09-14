import json
import urllib.request

BASE = "http://localhost:8000"

PROMPTS = [
    "Show me trends and outliers",
    "show me outliers",
    "show me outliers below 80%",
    "show me outliers above 92%",
    "anything more than 10% below normal for each machine",
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
    per_machine = {o["machine"]: len(o["outlier_dates"]) for o in outliers}
    rule = (
        f"{ev.get('direction')} {ev.get('limit_value')}"
        if ev.get("mode") == "absolute"
        else f">{ev.get('baseline_deviation_pct')}% above own baseline"
    )
    print(f"{prompt!r}")
    print(f"   mode={ev.get('mode'):<9} rule={rule:<28} machines={per_machine}")
