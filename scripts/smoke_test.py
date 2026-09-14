import json
import urllib.request

BASE = "http://localhost:8000"


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def status_of(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=30) as resp:
            return resp.status
    except Exception as exc:  # noqa: BLE001
        return f"ERR {exc}"


print("index:", status_of("/"))
print("css:", status_of("/static/styles.css"))
print("js:", status_of("/static/app.js"))

print("\n--- reject at gate 1 ---")
r = post("/chat", {"message": "trends"})
r = post("/resume", {"thread_id": r["thread_id"], "decision": {"approved": False}})
print("status:", r["status"], "| cancelled_at:", r.get("cancelled_at"))
print("workspace_id:", r["evidence"]["workspace_id"])

print("\n--- reject at gate 2 ---")
r = post("/chat", {"message": "trends"})
tid = r["thread_id"]
r = post("/resume", {"thread_id": tid, "decision": {"approved": True}})
print("paused at:", r["request"]["type"])
r = post("/resume", {"thread_id": tid, "decision": {"approved": False}})
print("status:", r["status"], "| cancelled_at:", r.get("cancelled_at"))
print("workspace_id:", r["evidence"]["workspace_id"])
print("registration (should be None):", r["evidence"]["registration"])

print("\n--- choose a different outlier, then approve ---")
r = post("/chat", {"message": "trends"})
tid = r["thread_id"]
r = post("/resume", {"thread_id": tid, "decision": {"approved": True, "machine": "NXE3400"}})
print("paused at:", r["request"]["type"])
r = post("/resume", {"thread_id": tid, "decision": {"approved": True}})
print("status:", r["status"])
print("selected:", r["evidence"]["selected_outlier"])
print("anomalous:", r["evidence"]["anomalous_wafers"])
print("findings present:", bool(r.get("findings")))
