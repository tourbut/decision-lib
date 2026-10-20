"""Offline tests: safe arithmetic, fail-safe directions, plan hints, and a real MCP round
trip with an in-process client."""

from __future__ import annotations

import asyncio
import json

import pytest
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse
from langchain_typesafe.client import TypeSafeAPIConnectionError
from mcp.client.client import Client

import tools
from server import build_server


def response(answers: dict) -> ClassifierResponse:
    return ClassifierResponse.model_validate({"model": "stub", "answers": answers})


def choice(probs: dict[str, float]) -> dict:
    return {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs, "confidence": max(probs.values())}


def down(_):
    raise TypeSafeAPIConnectionError("refused")


def never(_):
    raise AssertionError("no model call expected")


def test_calculate_is_arithmetic_only() -> None:
    assert tools.calculate("(18 + 7) / 5") == 5
    assert tools.calculate("2^10") == 1024
    for bad in ("__import__('os')", "len('a')", "9**999999"):
        with pytest.raises(ValueError):
            tools.calculate(bad)


def test_failures_never_become_a_yes() -> None:
    assert tools.verify(RunnableLambda(down), "c", "e")["recommendation"] == "review"
    assert tools.gate(RunnableLambda(down), "a", "c")["recommendation"] == "review"
    assert tools.approval(RunnableLambda(down), "ls")["decision"] == "ESCALATE"
    assert tools.fastpath(RunnableLambda(down), "1 + 1 은?")["handler"] == "normal_llm"


def test_unsure_approve_escalates_and_every_result_is_advice() -> None:
    unsure = RunnableLambda(lambda _: response({"q": choice({"APPROVE": 0.7, "DENY": 0.1, "ESCALATE": 0.2})}))
    r = tools.approval(unsure, "npm run build")
    assert r["decision"] == "ESCALATE" and r["advisory_only"] and not r["execution_authorized"]


def test_verify_mapping() -> None:
    def stub(supports, contradicts):
        return RunnableLambda(lambda _: response({"q": choice(
            {"supports": supports, "contradicts": contradicts, "says_nothing": 1 - supports - contradicts})}))
    assert tools.verify(stub(0.95, 0.0), "c", "e")["recommendation"] == "pass"
    assert tools.verify(stub(0.05, 0.9), "c", "e")["recommendation"] == "block"


def test_fastpath_skips_the_model_without_candidates_and_answers_locally() -> None:
    assert tools.fastpath(RunnableLambda(never), "리팩터링 계획 세워 줘")["handler"] == "normal_llm"
    sure = RunnableLambda(lambda r: response({
        "handler": choice({"calculator": 0.99, "normal_llm": 0.01}), "alone_calculator": {"type": "noul", "noul": 0.97}}))
    r = tools.fastpath(sure, "123 * 45 는?")
    assert (r["handler"], r["answer"]) == ("calculator", "123 * 45 = 5535")
    unsure = RunnableLambda(lambda r: response({
        "handler": choice({"calculator": 0.99, "normal_llm": 0.01}), "alone_calculator": {"type": "noul", "noul": 0.5}}))
    assert tools.fastpath(unsure, "사과 3 + 4개를 어떻게 나눠?")["handler"] == "normal_llm"


def test_skill_relation_never_merges_a_conflict() -> None:
    probs = {k: 0.0 for k in tools.RELATIONS} | {"conflict": 1.0}
    r = tools.skill_relation(RunnableLambda(lambda _: response({"q": choice(probs)})), "a", "b")
    assert r["relation"] == "conflict" and "합치지 않음" in r["plan"]


def test_mcp_round_trip() -> None:
    stub = RunnableLambda(lambda _: response({"q": choice({"supports": 0.97, "contradicts": 0.01, "says_nothing": 0.02})}))

    async def go():
        async with Client(build_server(stub)) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            result = await client.call_tool("verify", {"claim": "c", "evidence": "e"})
            return names, json.loads(result.content[0].text)

    names, verdict = asyncio.run(go())
    assert names == {"check", "route", "score", "verify", "gate", "approval", "fastpath", "skill_relation"}
    assert verdict["recommendation"] == "pass" and verdict["execution_authorized"] is False
