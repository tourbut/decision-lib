"""Effort router: before a turn, decide how much model the turn needs.

Three routes for one local model:
- fast: reasoning off, short budget. Facts, chat, short rewrites.
- think: reasoning on. Arithmetic, counting, puzzles, anything a quick answer gets wrong.
- handoff: no answer from here. Live or private data, real-world actions, or a binding
  legal, medical, or financial call go to a person or a larger system.

One decision-model request per turn picks the route; plain code adds the rest:
1. "effort: fast|think|handoff" written in the message wins, with no model call.
2. Access or high-stakes checks force handoff even when the route says otherwise.
3. Confidence below CONFIDENT keeps the safe default (think), as in jev-effort-router.
4. A fast or think answer that comes back empty or cut off moves one route up and
   retries in the same turn (effortless-hermes raises effort on the next turn instead).

Wired into a LangChain agent as middleware. ModelRouterMiddleware from
langchain-typesafe picks a model the same way, but builds its own classifier from the
environment and has no threshold or fallback, so this sample keeps its own.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any, Literal, TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, AgentState, ModelRequest, ModelResponse
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse, Noul, Question
from langchain_typesafe.client import TypeSafeError
from typing_extensions import NotRequired

Route = Literal["fast", "think", "handoff"]
LADDER: list[Route] = ["fast", "think", "handoff"]
DEFAULT: Route = "think"

QUESTIONS: dict[str, Question] = {
    "route": Choice(
        instructions="Which path should handle this user message in a local assistant without tools or internet?",
        criteria={
            "fast": "One-step answer, small talk, or a short rewrite. No calculation or reasoning chain.",
            "think": "Needs several reasoning steps: arithmetic, counting, puzzles, logic, or planning, "
            "where a quick answer is easy to get wrong.",
            "handoff": "Needs live or private data, real-world actions, or a binding legal, medical, or "
            "financial decision. A person or a system with access must take over.",
        },
    ),
    "needs_access": Noul(
        instructions="Does this request need live data, private files, account access, or an action in the real world?"
    ),
    "high_stakes": Noul(instructions="Would a wrong answer cause legal, medical, or financial harm?"),
}

THRESHOLDS = {"access_handoff": 0.80, "stakes_handoff": 0.80, "confident": 0.50}

OVERRIDE = re.compile(r"\beffort:\s*(fast|think|handoff)\b", re.I)

SYSTEM = "한국어로 간결하게 답한다. 답이 하나로 정해지는 질문이면 마지막 줄에 '정답: <값>'을 적는다."


class Decision(TypedDict):
    route: Route
    reason: str
    source: Literal["override", "model", "error"]
    scores: dict[str, float]


def decide(s: dict[str, float]) -> tuple[Route, str]:
    """First match wins: the safety handoffs, then the model's own handoff, then the
    confidence fallback, then the chosen route."""
    t = THRESHOLDS
    if s["needs_access"] >= t["access_handoff"]:
        return "handoff", "외부 데이터·계정·실제 행동 필요"
    if s["high_stakes"] >= t["stakes_handoff"]:
        return "handoff", "틀리면 법률·의료·금전 피해"
    route = max(LADDER, key=lambda r: s[f"route_{r}"])
    if route == "handoff":
        return "handoff", "모델 판정: 이관"
    if s["confidence"] < t["confident"]:
        return DEFAULT, f"판정이 불확실해 기본값({DEFAULT})"
    return route, "모델 판정"


def route_turn(classifier: Runnable[ClassifierRequest, ClassifierResponse], text: str) -> Decision:
    if m := OVERRIDE.search(text):
        return {"route": m.group(1).lower(), "reason": "메시지에 직접 지정", "source": "override", "scores": {}}
    try:
        answers = classifier.invoke({"state": {"message": text}, "questions": QUESTIONS})
    except TypeSafeError as e:
        return {"route": DEFAULT, "reason": f"판정 실패: {type(e).__name__}", "source": "error", "scores": {}}
    choice = answers.choices["route"]
    s = {f"route_{k}": p for k, p in choice.probabilities.items()}
    s.update({"confidence": choice.confidence, **{k: a.noul for k, a in answers.nouls.items()}})
    route, reason = decide(s)
    return {"route": route, "reason": reason, "source": "model", "scores": s}


def incomplete(message: AIMessage) -> bool:
    """Empty, or stopped by the token budget rather than by the model."""
    return not str(message.content).strip() or message.response_metadata.get("finish_reason") == "length"


class _State(AgentState):
    route: NotRequired[Decision]


class EffortRouterMiddleware(AgentMiddleware[_State]):
    """Routes once per run (before_agent), then serves every model call of the run from
    the routed model, climbing LADDER when an answer comes back incomplete. `log` keeps
    one record per run for reports: the decision, the routes tried, tokens, seconds.

    mode="on" serves the routed model. mode="shadow" asks the router and records what it
    would have chosen (`intended`) but always serves `fixed`, so a team can watch the
    router before trusting it (Hermes Jev Skills). mode="off" skips the router."""

    state_schema = _State

    def __init__(self, classifier: Runnable[ClassifierRequest, ClassifierResponse], models: dict[str, BaseChatModel],
                 mode: Literal["on", "shadow", "off"] = "on", fixed: Route = DEFAULT):
        super().__init__()
        self.classifier = classifier
        self.models = models
        self.mode = mode
        self.fixed = fixed
        self.log: list[dict[str, Any]] = []

    def before_agent(self, state: _State, runtime) -> dict[str, Decision]:
        text = next(m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)).content
        if self.mode == "off":
            decision: Decision = {"route": self.fixed, "reason": "라우터 꺼짐", "source": "override", "scores": {}}
        else:
            decision = route_turn(self.classifier, str(text))
        intended = decision["route"]
        if self.mode == "shadow":
            decision = {**decision, "route": self.fixed, "reason": f"shadow: {intended} 판정만 기록, {self.fixed}로 응답"}
        self.log.append({**decision, "intended": intended, "mode": self.mode, "tried": [], "output_tokens": 0, "seconds": 0.0})
        return {"route": decision}

    def wrap_model_call(self, request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]):
        record = self.log[-1]
        route = request.state["route"]["route"]
        started = time.perf_counter()
        try:
            while route != "handoff":
                record["tried"].append(route)
                response = handler(request.override(model=self.models[route]))
                message = response.result[-1]
                record["output_tokens"] += (message.usage_metadata or {}).get("output_tokens", 0)
                if not incomplete(message):
                    return response
                route = LADDER[LADDER.index(route) + 1]
                record["reason"] += f" → 답이 비거나 잘려 {route}로 올림"
            record["tried"].append("handoff")
            return AIMessage(content=f"이 요청은 여기서 답하지 않고 담당자나 상위 시스템으로 넘깁니다. 사유: {record['reason']}")
        finally:
            record["seconds"] += time.perf_counter() - started


def build_agent(classifier, models: dict[str, BaseChatModel], mode: Literal["on", "shadow", "off"] = "on"):
    router = EffortRouterMiddleware(classifier, models, mode=mode)
    return create_agent(models["fast"], tools=[], system_prompt=SYSTEM, middleware=[router]), router


def shadow_report(records: list[dict[str, Any]], tiers: dict[str, dict[str, Any]], fixed: Route = DEFAULT) -> dict[str, Any]:
    """From a shadow log, what routing would have cost against always serving `fixed`.
    Costs use each tier's average output tokens and price from tiers.json, so this is an
    estimate; the measured tokens of the fixed model are reported next to it."""
    def cost(route: str) -> float:
        tier = tiers[route]
        return tier["avg_output_tokens"] * tier["price_per_1k"] / 1000

    intended = [r["intended"] for r in records]
    fixed_cost, routed_cost = cost(fixed) * len(records), sum(cost(r) for r in intended)
    return {
        "turns": len(records),
        "intended": {route: intended.count(route) for route in LADDER},
        "fixed_cost": fixed_cost,
        "routed_cost": routed_cost,
        "saving": 1 - routed_cost / fixed_cost if fixed_cost else 0.0,
        "measured_fixed_tokens": sum(r["output_tokens"] for r in records),
    }


def run_turn(agent, router: EffortRouterMiddleware, text: str) -> dict[str, Any]:
    result = agent.invoke({"messages": [HumanMessage(text)]})
    return {**router.log[-1], "answer": str(result["messages"][-1].content)}


ANSWER_LINE = re.compile(r"정답\s*[:：]\s*(.+)")


def correct(answer: str, key: str) -> bool:
    """The key appears as a whole value in the last '정답:' line, or in the last line when
    a short reply skipped that line ('서울특별시입니다' has 서울, '400원' does not have 0)."""
    found = ANSWER_LINE.findall(answer)
    lines = answer.strip().splitlines()
    text = found[-1] if found else (lines[-1] if lines else "")
    text = re.sub(r"[*`$]", "", text).replace("−", "-").lower()
    return re.search(rf"(?<![\w./-]){re.escape(key.lower())}(?![\d./])", text) is not None
