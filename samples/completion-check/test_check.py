"""Offline tests: decision policy, fail-open, attempt cap, and the agent middleware loop."""

from __future__ import annotations

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse
from langchain_typesafe.client import TypeSafeAPIConnectionError

from check import MAX_ATTEMPTS, check, decide
from gate import STEER_NAME, build_agent
from transcripts import TRANSCRIPTS

DONE = {"claims_done": 0.95, "requirements_met": 0.95, "needs_tests": 0.9, "tests_cover": 0.9, "needs_human": 0.0}


def evidence(tests=None, attempt=1) -> dict:
    return {"task": "t", "response": "r", "changed": ["a.py"], "tests": tests, "attempt": attempt}


@pytest.mark.parametrize(
    ("overrides", "tests", "attempt", "action"),
    [
        ({}, {"passed": 3, "failed": 0}, 1, "pass"),
        ({}, {"passed": 3, "failed": 1}, 1, "steer"),  # a failing test overrides a happy model
        ({"needs_human": 0.9}, {"passed": 3, "failed": 1}, 1, "halt"),  # a question beats everything
        ({"requirements_met": 0.3}, None, 1, "steer"),
        ({"tests_cover": 0.1}, None, 1, "steer"),
        ({"tests_cover": 0.1, "needs_tests": 0.1}, None, 1, "pass"),  # docs need no tests
        ({"claims_done": 0.1}, None, 1, "steer"),
        ({"requirements_met": 0.3}, None, MAX_ATTEMPTS, "halt"),
        ({}, None, MAX_ATTEMPTS, "pass"),  # the cap only stops unfinished work
    ],
)
def test_decide(overrides, tests, attempt, action) -> None:
    assert decide(evidence(tests, attempt), {**DONE, **overrides})[0] == action


def test_steer_lists_every_gap() -> None:
    action, reasons = decide(evidence({"passed": 1, "failed": 2}), {**DONE, "requirements_met": 0.2, "tests_cover": 0.2})
    assert action == "steer" and len(reasons) == 3 and reasons[0] == "실패한 테스트 2개를 고친다"


def test_decision_model_down_fails_open_except_for_failed_tests() -> None:
    def down(_):
        raise TypeSafeAPIConnectionError("refused")

    assert check(RunnableLambda(down), evidence())["action"] == "pass"
    v = check(RunnableLambda(down), evidence({"passed": 0, "failed": 1}))
    assert (v["action"], v["source"]) == ("steer", "error")
    assert check(RunnableLambda(down), evidence({"passed": 0, "failed": 1}, MAX_ATTEMPTS))["action"] == "pass"


def nouls(**values) -> ClassifierResponse:
    return ClassifierResponse.model_validate(
        {"model": "stub", "answers": {k: {"type": "noul", "noul": v} for k, v in {**DONE, **values}.items()}}
    )


def test_middleware_steers_until_the_answer_is_complete() -> None:
    # The stub says "not done" while the answer lacks '#52'.
    stub = RunnableLambda(lambda r: nouls(requirements_met=0.9 if "#52" in r["state"]["final_response"] else 0.2))
    model = GenericFakeChatModel(messages=iter([AIMessage("#41만 씀. 완료"), AIMessage("#41, #52 모두 씀")]))
    agent, gate = build_agent(model, stub)
    result = agent.invoke({"messages": [HumanMessage("노트를 써라")]})
    assert [e["action"] for e in gate.log] == ["steer", "pass"]
    assert [m.name for m in result["messages"] if isinstance(m, HumanMessage)] == [None, STEER_NAME]
    assert result["messages"][-1].content == "#41, #52 모두 씀"


def test_middleware_halts_at_the_attempt_cap() -> None:
    stub = RunnableLambda(lambda r: nouls(requirements_met=0.1))
    model = GenericFakeChatModel(messages=iter([AIMessage(f"시도 {i}") for i in range(1, 5)]))
    agent, gate = build_agent(model, stub)
    result = agent.invoke({"messages": [HumanMessage("노트를 써라")]})
    assert [e["action"] for e in gate.log] == ["steer", "steer", "halt"]
    assert result["messages"][-1].content.startswith("[사람 확인 필요]")


def test_labels() -> None:
    assert len(TRANSCRIPTS) == 30 and {t["label"] for t in TRANSCRIPTS} == {"pass", "steer", "halt"}
