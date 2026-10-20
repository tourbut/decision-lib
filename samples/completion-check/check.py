"""Completion check: when a coding agent says it is done, is it?

Facts the harness already knows are settled in code: failing tests always send the
turn back, and a third failed attempt stops the loop. The decision model reads the
task, the final response, the changed files, and the test summary, and answers four
Noul questions. Code turns them into one of:

- pass: accept the turn.
- steer: send it back with an instruction listing every gap that was found.
- halt: stop and bring in a person (the agent asked for a decision, or keeps failing).

If the decision model is down the check fails open (pass, unless tests failed), so a
broken supervisor never traps the agent in a loop. Based on Foreman (#10) and the
Hermes pre_verify hook proposal (#37).
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langchain_core.runnables import Runnable
from langchain_typesafe import ClassifierRequest, ClassifierResponse, Noul, Question
from langchain_typesafe.client import TypeSafeError

Action = Literal["pass", "steer", "halt"]

MAX_ATTEMPTS = 3

QUESTIONS: dict[str, Question] = {
    "claims_done": Noul(instructions="Does the response say the task is finished?"),
    "requirements_met": Noul(
        instructions="Does the response state that each requirement listed in the task is done? "
        "A requirement the response does not mention, or leaves as TODO or for later, counts as not done."
    ),
    "needs_tests": Noul(instructions="Does the task change code behavior, or ask for tests?"),
    "tests_cover": Noul(
        instructions="Did the harness run tests that would catch a mistake in this change, "
        "including tests the task asked to add?"
    ),
    "needs_human": Noul(
        instructions="Does the response ask a person for a decision, permission, access, or information "
        "before the work can continue?"
    ),
}

THRESHOLDS = {"needs_human": 0.70, "requirements_met": 0.60, "needs_tests": 0.50, "tests_cover": 0.60, "claims_done": 0.50}


class Evidence(TypedDict):
    task: str
    response: str
    changed: list[str]
    tests: dict[str, int] | None  # {"passed": n, "failed": m} from the harness, None if not run
    attempt: int


class Verdict(TypedDict):
    action: Action
    reasons: list[str]
    instruction: str | None  # what to tell the agent on steer
    source: Literal["model", "error"]
    scores: dict[str, float]


def test_summary(tests: dict[str, int] | None) -> str:
    return "실행 안 함" if tests is None else f"통과 {tests['passed']}, 실패 {tests['failed']}"


def decide(evidence: Evidence, s: dict[str, float]) -> tuple[Action, list[str]]:
    """A request for a person stops everything; otherwise every gap is collected so the
    steer instruction covers all of them at once."""
    t = THRESHOLDS
    if s["needs_human"] >= t["needs_human"]:
        return "halt", ["사람의 결정·권한·정보가 필요하다"]
    gaps = []
    if evidence["tests"] and evidence["tests"]["failed"]:
        gaps.append(f"실패한 테스트 {evidence['tests']['failed']}개를 고친다")
    if s["requirements_met"] < t["requirements_met"]:
        gaps.append("과제의 요구사항 중 빠진 것을 마저 구현한다")
    if s["needs_tests"] >= t["needs_tests"] and s["tests_cover"] < t["tests_cover"]:
        gaps.append("요청한 동작을 확인하는 테스트를 추가하고 실제로 실행한다")
    if s["claims_done"] < t["claims_done"] and not gaps:
        gaps.append("작업을 끝까지 진행한다")
    if not gaps:
        return "pass", ["완료 주장과 증거가 맞는다"]
    if evidence["attempt"] >= MAX_ATTEMPTS:
        return "halt", [f"시도 {evidence['attempt']}회에도 미완료", *gaps]
    return "steer", gaps


def request(evidence: Evidence) -> ClassifierRequest:
    state = {
        "task": evidence["task"],
        "final_response": evidence["response"],
        "changed_files": ", ".join(evidence["changed"]) or "없음",
        "tests_run_by_harness": test_summary(evidence["tests"]),
    }
    return {"state": state, "questions": QUESTIONS}


def check(classifier: Runnable[ClassifierRequest, ClassifierResponse], evidence: Evidence) -> Verdict:
    try:
        s = {k: a.noul for k, a in classifier.invoke(request(evidence)).nouls.items()}
    except TypeSafeError as e:
        failed = bool(evidence["tests"] and evidence["tests"]["failed"])
        action: Action = "steer" if failed and evidence["attempt"] < MAX_ATTEMPTS else "pass"
        reason = f"판정 실패({type(e).__name__}): " + ("테스트 실패만 반영" if failed else "그대로 통과(fail-open)")
        return {"action": action, "reasons": [reason], "instruction": "실패한 테스트를 고친다." if action == "steer" else None,
                "source": "error", "scores": {}}
    action, reasons = decide(evidence, s)
    instruction = "아직 끝나지 않았다. " + " ".join(f"{i}. {r}." for i, r in enumerate(reasons, 1)) if action == "steer" else None
    return {"action": action, "reasons": reasons, "instruction": instruction, "source": "model", "scores": s}
