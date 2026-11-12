"""End-to-end smoke test against a running API.

Usage: python smoke_test.py [BASE_URL]   (default http://127.0.0.1:5000)
Runs inside the app container in CI:  docker compose exec -T app python - < ci/smoke_test.py
Exits non-zero with a clear message on the first failed check.
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
STUDENT = {"id": f"CI-{int(time.time())}", "name": "Smoke Test", "course": "DevOps"}


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"null")


def check(name, condition, detail):
    print(f"[{'PASS' if condition else 'FAIL'}] {name}: {detail}")
    if not condition:
        sys.exit(1)


status, body = call("GET", "/health")
check("health", status == 200 and body.get("storage") == "redis", f"{status} {body}")

status, body = call("POST", "/students", STUDENT)
check("add student", status == 201, f"{status} {body}")

status, body = call("POST", "/students", STUDENT)
check("duplicate rejected", status == 409, f"{status} {body}")

status, body = call("GET", f"/students/{STUDENT['id']}")
check("get student", status == 200 and body == STUDENT, f"{status} {body}")

status, body = call("DELETE", f"/students/{STUDENT['id']}")
check("delete student", status == 204, f"{status}")

print("Smoke test passed")
