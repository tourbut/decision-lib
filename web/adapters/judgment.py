"""judgment-tools: call any tool through a real (in-process) MCP client, or measure the sets."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from mcp.client.client import Client
from pydantic import BaseModel, Field

from . import classifier, load

server_mod = load("judgment-tools", "server")
cases = load("judgment-tools", "cases")

SUMMARY = "판정을 MCP 도구 8개(check, route, score, verify, gate, approval, fastpath, skill_relation)로 노출한다. 결과는 모두 권고다."

router = APIRouter()

EXAMPLES = {
    "approval": {"command": "kubectl rollout restart deployment/payments -n prod"},
    "fastpath": {"text": "(18 + 7) / 5 계산해 줘"},
    "verify": {"claim": "액세스 토큰은 1시간 유효하다", "evidence": "사내 API의 액세스 토큰 유효기간은 15분이다."},
    "gate": {"action": "운영 DB에서 users 테이블 삭제", "context": "로그인 버그를 고치는 과제"},
    "skill_relation": {"skill_a": "PDF를 합치거나 나눈다.", "skill_b": "PDF 합치기·나누기·텍스트 추출·양식 채우기"},
    "check": {"state": "배포 후 오류율이 5배 늘었다", "question": "Should the deploy be rolled back?"},
    "route": {"state": "결제가 두 번 됐어요", "question": "Which team?", "options": {"billing": "결제", "technical": "오류", "sales": "구매 상담"}},
    "score": {"state": "앱이 하루 종일 안 열려요. 너무 화나요.", "question": "How frustrated is the customer?",
              "levels": ["calm", "annoyed", "angry"]},
}
SETS = {"fastpath": (cases.FASTPATH, lambda c: {"text": c["text"]}, "handler"),
        "approval": (cases.APPROVAL, lambda c: {"command": c["command"]}, "decision"),
        "skill_relation": (cases.RELATIONS, lambda c: {"skill_a": c["a"], "skill_b": c["b"]}, "relation")}


class CallRequest(BaseModel):
    tool: str = Field(pattern="^(check|route|score|verify|gate|approval|fastpath|skill_relation)$")
    arguments: dict[str, Any] = Field(max_length=5)


class EvalRequest(BaseModel):
    tool: str = Field(pattern="^(fastpath|approval|skill_relation)$")


async def _call(client: Client, tool: str, arguments: dict) -> dict | str:
    """The parsed result, or the error text. Raising inside the client's context would
    surface as an ExceptionGroup, so callers raise after the context closes."""
    result = await client.call_tool(tool, arguments)
    return result.content[0].text if result.is_error else json.loads(result.content[0].text)


@router.get("/setup")
async def setup(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    async with Client(server_mod.build_server(decision_model)) as client:
        listed = await client.list_tools()
    return {"tools": [{"name": t.name, "description": t.description} for t in listed.tools], "examples": EXAMPLES,
            "sets": {k: len(v[0]) for k, v in SETS.items()}}


@router.post("/call")
async def call(body: CallRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    async with Client(server_mod.build_server(decision_model)) as client:
        result = await _call(client, body.tool, body.arguments)
    if isinstance(result, str):
        raise HTTPException(422, result)
    return result


@router.post("/eval")
async def evaluate(body: EvalRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    items, args, field = SETS[body.tool]
    async with Client(server_mod.build_server(decision_model)) as client:
        rows = [{"input": args(c), "label": c["label"], "result": await _call(client, body.tool, args(c))} for c in items]
    if any(isinstance(r["result"], str) for r in rows):
        raise HTTPException(502, next(r["result"] for r in rows if isinstance(r["result"], str)))
    return {"rows": rows, "field": field}
