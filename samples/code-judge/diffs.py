"""Twelve small made-up diffs, some with defects planted on purpose. `defects` lists the
checklist items a careful reviewer would flag; an empty list means the change is clean.
"""

from __future__ import annotations

DIFFS = [
    {"id": "sql-format", "defects": ["injection"], "diff": '''--- a/app/users.py
+++ b/app/users.py
@@ def find_user(db, name):
-    return db.execute("SELECT * FROM users WHERE name = %s", (name,)).fetchone()
+    return db.execute(f"SELECT * FROM users WHERE name = '{name}'").fetchone()
'''},
    {"id": "secret-literal", "defects": ["secret"], "diff": '''--- a/app/payments.py
+++ b/app/payments.py
@@
-STRIPE_KEY = os.environ["STRIPE_KEY"]
+STRIPE_KEY = "sk_live_FAKE0000"
'''},
    {"id": "bare-except", "defects": ["error_handling"], "diff": '''--- a/app/sync.py
+++ b/app/sync.py
@@ def sync_orders(client):
-    orders = client.fetch_orders()
+    try:
+        orders = client.fetch_orders()
+    except Exception:
+        pass
     for order in orders:
         save(order)
'''},
    {"id": "file-leak", "defects": ["resource_leak"], "diff": '''--- a/app/report.py
+++ b/app/report.py
@@ def read_report(path):
-    with open(path) as f:
-        return f.read()
+    f = open(path)
+    data = f.read()
+    return data
'''},
    {"id": "log-password", "defects": ["sensitive_log"], "diff": '''--- a/app/auth.py
+++ b/app/auth.py
@@ def login(username, password):
+    logger.info("login attempt user=%s password=%s", username, password)
     user = authenticate(username, password)
'''},
    {"id": "shell-injection", "defects": ["injection"], "diff": '''--- a/app/tools.py
+++ b/app/tools.py
@@ def ping(host):
-    return subprocess.run(["ping", "-c", "1", host], capture_output=True)
+    return subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True)
'''},
    {"id": "token-in-log-and-swallow", "defects": ["sensitive_log", "error_handling"], "diff": '''--- a/app/api.py
+++ b/app/api.py
@@ def call_api(token, url):
+    print("calling", url, "with token", token)
+    try:
+        return requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=5).json()
+    except Exception:
+        return None
'''},
    # clean changes
    {"id": "param-query", "defects": [], "diff": '''--- a/app/users.py
+++ b/app/users.py
@@ def find_user(db, name):
-    return db.execute(f"SELECT * FROM users WHERE name = '{name}'").fetchone()
+    return db.execute("SELECT * FROM users WHERE name = %s", (name,)).fetchone()
'''},
    {"id": "with-open", "defects": [], "diff": '''--- a/app/report.py
+++ b/app/report.py
@@ def read_report(path):
-    f = open(path)
-    return f.read()
+    with open(path, encoding="utf-8") as f:
+        return f.read()
'''},
    {"id": "specific-except", "defects": [], "diff": '''--- a/app/config.py
+++ b/app/config.py
@@ def load_port(raw):
-    return int(raw)
+    try:
+        return int(raw)
+    except ValueError:
+        raise ConfigError(f"PORT must be a number, got {raw!r}") from None
'''},
    {"id": "env-secret", "defects": [], "diff": '''--- a/app/payments.py
+++ b/app/payments.py
@@
-STRIPE_KEY = "sk_live_FAKE0000"
+STRIPE_KEY = os.environ["STRIPE_KEY"]
'''},
    {"id": "rename-only", "defects": [], "diff": '''--- a/app/cart.py
+++ b/app/cart.py
@@
-def calc(items):
-    return sum(i.price * i.qty for i in items)
+def cart_total(items):
+    return sum(i.price * i.qty for i in items)
'''},
]
