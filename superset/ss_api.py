import json, os, requests
BASE = "http://localhost:8088"
class Superset:
    def __init__(self):
        self.s = requests.Session()
        r = self.s.post(f"{BASE}/api/v1/security/login", json={"username": os.environ["SUPERSET_ADMIN_USER"],
            "password": os.environ["SUPERSET_ADMIN_PASSWORD"], "provider": "db", "refresh": True}); r.raise_for_status()
        self.s.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
        self.s.headers.update({"X-CSRFToken": self.s.get(f"{BASE}/api/v1/security/csrf_token/").json()["result"], "Referer": BASE})
    def get(self, path, **params):
        r = self.s.get(f"{BASE}/api/v1/{path}", params={"q": json.dumps(params)} if params else None); r.raise_for_status(); return r.json()
    def post(self, path, body):
        r = self.s.post(f"{BASE}/api/v1/{path}", json=body)
        if not r.ok: raise RuntimeError(f"POST {path} → {r.status_code}: {r.text[:500]}")
        return r.json()
    def put(self, path, body):
        r = self.s.put(f"{BASE}/api/v1/{path}", json=body)
        if not r.ok: raise RuntimeError(f"PUT {path} → {r.status_code}: {r.text[:500]}")
        return r.json()
