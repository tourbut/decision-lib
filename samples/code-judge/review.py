"""Checklist code review, as jev-review does: split a diff into per-file hunks and ask a
fixed set of yes/no questions about each hunk, all hunks in parallel. The output is the
checklist itself, not review prose; a person reads it and decides.

Questions are about what the change adds. A hunk that removes a problem is clean.
"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.runnables import Runnable
from langchain_typesafe import ClassifierRequest, ClassifierResponse, Noul

CHECKLIST = {
    "injection": "Does the added code build a SQL query or shell command by inserting a variable into a string, "
                 "instead of passing parameters?",
    "secret": "Does the added code put a password, API key, or token directly in the source as a literal?",
    "error_handling": "Does the added code catch an exception and silently ignore it or return a placeholder, "
                      "hiding the failure?",
    "resource_leak": "Does the added code open a file, connection, or socket without closing it or using a with block?",
    "sensitive_log": "Does the added code write a password, token, or other secret to a log or to standard output?",
}
FLAG_AT = 0.60


def hunks(diff: str) -> list[str]:
    """One chunk per file (`--- a/…` header to the next); small diffs stay whole."""
    parts = re.split(r"(?m)^(?=--- )", diff)
    return [p for p in parts if p.strip()]


def review(classifier: Runnable[ClassifierRequest, ClassifierResponse], diff: str) -> dict[str, Any]:
    questions = {k: Noul(instructions=v) for k, v in CHECKLIST.items()}
    chunks = hunks(diff)
    responses = classifier.batch([{"state": {"diff": chunk}, "questions": questions} for chunk in chunks])
    # A finding anywhere in the diff counts once; keep the strongest hunk's score.
    scores = {k: max(r.nouls[k].noul for r in responses) for k in CHECKLIST}
    return {"flags": sorted(k for k, p in scores.items() if p >= FLAG_AT), "scores": scores, "hunks": len(chunks)}
