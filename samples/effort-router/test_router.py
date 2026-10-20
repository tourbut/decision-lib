"""Offline tests: routing policy, the middleware's escalation and handoff, the answer check."""

from __future__ import annotations

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse
from langchain_typesafe.client import TypeSafeAPIConnectionError

from router import build_agent, correct, decide, route_turn, run_turn, shadow_report
from turns import TURNS


def scores(fast=0.0, think=0.0, handoff=0.0, confidence=0.9, access=0.0, stakes=0.0) -> dict[str, float]:
    return {"route_fast": fast, "route_think": think, "route_handoff": handoff, "confidence": confidence,
            "needs_access": access, "high_stakes": stakes}


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        (scores(fast=0.9, access=0.85), "handoff"),  # the access check beats a confident fast
        (scores(think=0.9, stakes=0.9), "handoff"),
        (scores(handoff=0.6, confidence=0.2), "handoff"),  # a model handoff needs no confidence
        (scores(fast=0.6, think=0.4, confidence=0.39), "think"),  # unsure falls back to think
        (scores(fast=0.77, think=0.23, confidence=0.50), "fast"),
        (scores(think=0.9), "think"),
    ],
)
def test_decide_first_match_wins(s, expected) -> None:
    assert decide(s)[0] == expected


def answers(route: str, confidence: float = 0.9) -> ClassifierResponse:
    probs = {k: (0.9 if k == route else 0.05) for k in ("fast", "think", "handoff")}
    return ClassifierResponse.model_validate({"model": "stub", "answers": {
        "route": {"type": "choice", "choice": route, "probabilities": probs, "confidence": confidence},
        "needs_access": {"type": "noul", "noul": 0.0},
        "high_stakes": {"type": "noul", "noul": 0.0},
    }})


def test_override_skips_the_model_and_errors_fall_back_to_think() -> None:
    def never(_):
        raise AssertionError("override must not call the model")

    assert route_turn(RunnableLambda(never), "effort: Handoff 이건 넘겨")["route"] == "handoff"

    def down(_):
        raise TypeSafeAPIConnectionError("refused")

    d = route_turn(RunnableLambda(down), "안녕")
    assert (d["route"], d["source"]) == ("think", "error")


def fake(*replies: AIMessage) -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter(replies))


def reply(text: str, finish: str = "stop", tokens: int = 5) -> AIMessage:
    usage = {"input_tokens": 1, "output_tokens": tokens, "total_tokens": tokens + 1}
    return AIMessage(content=text, response_metadata={"finish_reason": finish}, usage_metadata=usage)


def test_cut_off_fast_answer_climbs_to_think() -> None:
    models = {"fast": fake(reply("12개월이고 그 이유는", "length", 512)), "think": fake(reply("정답: 12", tokens=40))}
    agent, router = build_agent(RunnableLambda(lambda _: answers("fast")), models)
    r = run_turn(agent, router, "1년은 몇 개월?")
    assert r["tried"] == ["fast", "think"] and r["answer"] == "정답: 12"
    assert r["output_tokens"] == 552 and "think로 올림" in r["reason"]


def test_handoff_answers_without_calling_a_model() -> None:
    models = {"fast": fake(), "think": fake()}  # an empty fake raises if called
    agent, router = build_agent(RunnableLambda(lambda _: answers("handoff")), models)
    r = run_turn(agent, router, "송금해 줘")
    assert r["tried"] == ["handoff"] and r["output_tokens"] == 0 and "넘깁니다" in r["answer"]


def test_unsure_route_runs_on_think() -> None:
    models = {"fast": fake(), "think": fake(reply("정답: 3"))}
    agent, router = build_agent(RunnableLambda(lambda _: answers("fast", confidence=0.3)), models)
    assert run_turn(agent, router, "strawberry의 r은?")["tried"] == ["think"]


@pytest.mark.parametrize(
    ("answer", "key", "ok"),
    [
        ("계산하면...\n정답: 12개", "12", True),
        ("대한민국의 수도는 **서울특별시**입니다.", "서울", True),
        ("정답: 400원", "0", False),
        ("정답: $5/12$", "5/12", True),
        ("정답: 15/12", "5/12", False),
        ("정답: −8", "-8", True),
        ("1년은 12개월이에요.", "2", False),
    ],
)
def test_correct(answer: str, key: str, ok: bool) -> None:
    assert correct(answer, key) is ok


def test_turn_labels() -> None:
    assert {t["label"] for t in TURNS} == {"fast", "think", "handoff"} and len(TURNS) == 32


def test_shadow_serves_the_fixed_route_and_logs_the_intended_one() -> None:
    models = {"fast": fake(), "think": fake(reply("정답: 서울"))}
    agent, router = build_agent(RunnableLambda(lambda _: answers("fast")), models, mode="shadow")
    r = run_turn(agent, router, "대한민국의 수도는?")
    assert (r["intended"], r["route"], r["tried"], r["mode"]) == ("fast", "think", ["think"], "shadow")


def test_off_skips_the_router() -> None:
    def never(_):
        raise AssertionError("off must not call the decision model")

    agent, router = build_agent(RunnableLambda(never), {"fast": fake(), "think": fake(reply("안녕"))}, mode="off")
    assert run_turn(agent, router, "안녕")["tried"] == ["think"]


def test_shadow_report_estimates_saving_from_tiers() -> None:
    tiers = {"fast": {"avg_output_tokens": 100, "price_per_1k": 1.0}, "think": {"avg_output_tokens": 400, "price_per_1k": 1.0},
             "handoff": {"avg_output_tokens": 0, "price_per_1k": 0.0}}
    records = [{"intended": i, "output_tokens": 400} for i in ("fast", "think", "handoff", "fast")]
    report = shadow_report(records, tiers)
    assert report["intended"] == {"fast": 2, "think": 1, "handoff": 1}
    assert report["fixed_cost"] == pytest.approx(1.6) and report["routed_cost"] == pytest.approx(0.6)
    assert report["saving"] == pytest.approx(1 - 0.6 / 1.6) and report["measured_fixed_tokens"] == 1600
