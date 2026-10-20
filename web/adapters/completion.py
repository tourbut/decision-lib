"""completion-check: check one edited snapshot, the labelled set, or run the gated agent."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from . import classifier, llm, load

check = load("completion-check", "check")
gate = load("completion-check", "gate")
demo = load("completion-check", "demo")
TRANSCRIPTS = load("completion-check", "transcripts").TRANSCRIPTS

SUMMARY = "에이전트의 완료 주장을 요구사항·테스트·사람 개입 필요로 판정해 통과·되돌림·중단을 정한다."

router = APIRouter()


class Tests(BaseModel):
    passed: int = Field(ge=0, le=100000)
    failed: int = Field(ge=0, le=100000)


class CheckRequest(BaseModel):
    task: str = Field(min_length=1, max_length=2000)
    response: str = Field(min_length=1, max_length=4000)
    changed: list[Annotated[str, Field(max_length=200)]] = Field(default_factory=list, max_length=50)
    tests: Tests | None = None
    attempt: int = Field(default=1, ge=1, le=10)


class AgentRequest(BaseModel):
    task: str = Field(min_length=1, max_length=2000)
    lazy: bool = False  # replace the first answer with the canned half-done draft


@router.get("/setup")
def setup() -> dict:
    return {"transcripts": TRANSCRIPTS, "thresholds": check.THRESHOLDS, "max_attempts": check.MAX_ATTEMPTS,
            "task": demo.TASK}


@router.post("/check")
def check_one(body: CheckRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return check.check(decision_model, body.model_dump())


@router.post("/eval")
def evaluate(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return {"rows": [{**t, **check.check(decision_model, t)} for t in TRANSCRIPTS]}


@router.post("/agent")
def run_agent(
    body: AgentRequest,
    decision_model: Annotated[object, Depends(classifier)],
    model: Annotated[object, Depends(llm)],
) -> dict:
    agent, middleware = gate.build_agent(model, decision_model, [demo.LazyFirstDraft()] if body.lazy else [])
    result = agent.invoke({"messages": [HumanMessage(body.task)]}, {"recursion_limit": 20})
    return {"attempts": middleware.log, "final": str(result["messages"][-1].content)}
