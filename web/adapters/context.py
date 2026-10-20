"""context-gate: compact the labelled session, judge memory writes, or run the gated agent."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from . import classifier, llm, load

compaction = load("context-gate", "compaction")
memory_gate = load("context-gate", "memory_gate")
demo = load("context-gate", "demo")
session = load("context-gate", "session")
MEMORIES = load("context-gate", "memories").MEMORIES

SUMMARY = "오래된 도구 결과는 필요도로 유지·축소·삭제하고, 메모리 쓰기는 기억할 가치를 판정해 거른다."

router = APIRouter()


class MemoryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


@router.get("/setup")
def setup() -> dict:
    return {
        "goal": session.GOAL, "latest": session.LATEST, "pairs": session.PAIRS, "needed": session.NEEDED,
        "memories": MEMORIES, "live_message": demo.LIVE_MESSAGE,
        "thresholds": {**compaction.THRESHOLDS, "block_below": memory_gate.BLOCK_BELOW},
    }


@router.post("/compact")
def compact(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    messages = demo.session_messages()
    replaced, records = compaction.compact(decision_model, messages, keep_recent=0)
    by_id = {m.id: m for m in replaced}
    need = [by_id.get(m.id, m) for m in messages]
    size = [ToolMessage(compaction.size_based(str(m.content)), tool_call_id=m.tool_call_id, id=m.id)
            if isinstance(m, ToolMessage) else m for m in messages]
    totals = {name: {"chars": compaction.chars(msgs), "facts": demo.kept(msgs)}
              for name, msgs in (("original", messages), ("size_based", size), ("need_based", need))}
    original = {m.id: m for m in messages if isinstance(m, ToolMessage)}
    rows = [{**p, **r, "after": str(by_id.get(r["id"], original[r["id"]]).content)} for p, r in zip(session.PAIRS, records)]
    return {"rows": rows, "totals": totals}


@router.post("/memory/check")
def memory_check(body: MemoryRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return memory_gate.gate(decision_model, body.text)


@router.post("/memory/eval")
def memory_eval(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return {"rows": [{**m, **memory_gate.gate(decision_model, m["text"])} for m in MEMORIES]}


@router.post("/memory/agent")
def memory_agent(
    body: AgentRequest,
    decision_model: Annotated[object, Depends(classifier)],
    model: Annotated[object, Depends(llm)],
) -> dict:
    stored: list[str] = []

    @tool
    def remember(text: str) -> str:
        """Save one lasting fact or preference about the user or project for future sessions."""
        stored.append(text)
        return "저장함"

    middleware = memory_gate.MemoryGateMiddleware(decision_model)
    agent = create_agent(model, tools=[remember], middleware=[middleware])
    result = agent.invoke({"messages": [HumanMessage(body.message)]}, {"recursion_limit": 20})
    return {"log": middleware.log, "stored": stored, "answer": str(result["messages"][-1].content)}
