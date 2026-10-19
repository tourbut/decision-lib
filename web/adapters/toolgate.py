"""tool-call-gate: judge one tool call, run the labelled set, or run the gated agent."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import classifier, llm, load

gate = load("tool-call-gate", "gate")
agent = load("tool-call-gate", "agent")
CASES = load("tool-call-gate", "cases").CASES
TASKS = load("tool-call-gate", "demo").TASKS

SUMMARY = "에이전트의 도구 호출마다 차단 규칙과 d3-flash 판정으로 실행·사람 확인·차단을 정한다."

router = APIRouter()


class CheckRequest(BaseModel):
    task: str = Field(min_length=1, max_length=500)
    tool: str = Field(min_length=1, max_length=50)
    args: dict[str, Annotated[str, Field(max_length=2000)]] = Field(max_length=10)


class AgentRequest(BaseModel):
    task: str = Field(min_length=1, max_length=500)
    approve: bool  # the answer to every "ask" in this run


@router.get("/setup")
def setup() -> dict:
    return {
        "cases": CASES,
        "tasks": TASKS,
        "thresholds": gate.THRESHOLDS,
        "approval_tools": sorted(gate.APPROVAL_TOOLS),
        "tools": [t.name for t in agent.TOOLS],
    }


@router.post("/check")
def check(body: CheckRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return gate.gate(decision_model, body.task, body.tool, body.args)


@router.post("/eval")
def evaluate(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    """All labelled cases, with the rules-only baseline next to each verdict."""
    rows = [
        {**c, **gate.gate(decision_model, c["task"], c["tool"], c["args"]), "rules_only": gate.rules_only(c["tool"], c["args"])}
        for c in CASES
    ]
    return {"rows": rows, "thresholds": gate.THRESHOLDS}


@router.post("/agent")
def run_agent(
    body: AgentRequest,
    decision_model: Annotated[object, Depends(classifier)],
    model: Annotated[object, Depends(llm)],
) -> dict:
    graph, middleware = agent.build_agent(model, decision_model)
    result = agent.run(graph, body.task, lambda payload: body.approve, thread_id=str(uuid.uuid4()))
    return {"calls": list(middleware.log.values()), "answer": str(result["messages"][-1].content)}
