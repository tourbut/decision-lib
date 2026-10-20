"""A made-up coding session (fixing a webhook 500) with twelve tool call/result pairs,
each labelled keep / shrink / drop, and the facts the next step still needs.

keep: the next steps need the full result. shrink: worth remembering the call was made,
but the output can go. drop: neither.
"""

from __future__ import annotations

GOAL = "결제 웹훅이 500을 반환하는 버그를 고쳐라. 원인을 찾고, 고치고, 테스트로 확인한다."
LATEST = "원인은 찾았으니 이제 서명 검증 부분을 고치고 테스트를 다시 돌려 줘."

LOG = "\n".join(
    [f"2026-10-20 09:{m:02d}:11 INFO  GET /health 200 3ms" for m in range(0, 40)]
    + ["2026-10-20 09:41:07 ERROR POST /webhooks/pay 500 KeyError: 'Stripe-Signature' (webhook.py:42)"]
    + [f"2026-10-20 09:{m:02d}:11 INFO  GET /health 200 2ms" for m in range(42, 60)]
)

# Real files are longer than a 200-character head, so the lines that matter sit further down.
WEBHOOK_PY = """import hmac
import logging

from flask import Blueprint, request

from config import WEBHOOK_SECRET
from payments import mark_paid

bp = Blueprint("webhooks", __name__)
log = logging.getLogger(__name__)


def _event(payload: bytes) -> dict:
    import json
    return json.loads(payload or b"{}")


@bp.post("/webhooks/pay")
def handle():
    payload = request.data
    sig = request.headers['Stripe-Signature']  # line 42
    expected = hmac.new(WEBHOOK_SECRET, payload, "sha256").hexdigest()
    if not hmac.compare_digest(sig, expected):
        return "bad signature", 400
    mark_paid(_event(payload)["id"])
    return "ok", 200
"""

TEST_PY = """import hmac

import pytest

from app import create_app
from config import WEBHOOK_SECRET


@pytest.fixture
def client():
    return create_app(testing=True).test_client()


def test_valid_signature(client):
    body = b'{"id": "evt_1"}'
    sig = hmac.new(WEBHOOK_SECRET, body, "sha256").hexdigest()
    assert client.post("/webhooks/pay", data=body, headers={"Stripe-Signature": sig}).status_code == 200


def test_missing_signature_header(client):
    r = client.post('/webhooks/pay', data=b'{}')
    assert r.status_code == 400
"""

PAIRS = [
    {"tool": "bash", "args": {"command": "ls"}, "label": "drop",
     "result": "README.md\napp.py\nwebhook.py\nconfig.py\ntests/\nrequirements.txt\nDockerfile\n.github/"},
    {"tool": "bash", "args": {"command": "pip list"}, "label": "drop",
     "result": "\n".join(f"package-{i} 1.{i}.0" for i in range(60))},
    {"tool": "bash", "args": {"command": "tail -n 60 logs/app.log"}, "label": "shrink", "result": LOG},
    {"tool": "read_file", "args": {"path": "webhook.py"}, "label": "keep", "result": WEBHOOK_PY},
    {"tool": "read_file", "args": {"path": "README.md"}, "label": "drop",
     "result": "# Payments service\n\n사내 결제 서비스. 로컬 실행은 docker compose up.\n" + "설명 문단. " * 80},
    {"tool": "read_file", "args": {"path": "config.py"}, "label": "keep",
     "result": "import os\nWEBHOOK_SECRET = os.environ['WEBHOOK_SECRET'].encode()\nTIMEOUT = 10\n"},
    {"tool": "bash", "args": {"command": "pytest -q tests/test_webhook.py"}, "label": "shrink",
     "result": "F.\n=== FAILURES ===\ntest_missing_signature_header: KeyError: 'Stripe-Signature'\n" + "traceback line\n" * 40
     + "1 failed, 1 passed"},
    {"tool": "bash", "args": {"command": "git log --oneline -5"}, "label": "drop",
     "result": "a1b2c3d docs: README\nb2c3d4e chore: deps\nc3d4e5f feat: webhook\nd4e5f6a init\ne5f6a7b ci"},
    {"tool": "read_file", "args": {"path": "tests/test_webhook.py"}, "label": "keep", "result": TEST_PY},
    {"tool": "bash", "args": {"command": "docker ps"}, "label": "drop",
     "result": "CONTAINER ID   IMAGE   STATUS\n" + "\n".join(f"{i:012x}   svc-{i}   Up 3 days" for i in range(15))},
    {"tool": "web_search", "args": {"query": "flask request.headers KeyError missing header"}, "label": "shrink",
     "result": "1. Flask docs: request.headers.get(name) returns None when missing.\n" + "검색 결과 스니펫. " * 60},
    {"tool": "bash", "args": {"command": "cat Dockerfile"}, "label": "drop",
     "result": "FROM python:3.12-slim\nCOPY . /app\nRUN pip install -r requirements.txt\nCMD python app.py\n"},
]

# Facts the next step (fix line 42, rerun the test) cannot do without.
NEEDED = [
    "request.headers['Stripe-Signature']",  # the line to change
    "WEBHOOK_SECRET = os.environ['WEBHOOK_SECRET'].encode()",
    "assert r.status_code == 400",  # what the fix must return
]
