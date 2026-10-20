"""Offline tests: compaction keeps every row, the memory gate's rules, both middlewares."""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langchain_typesafe import ClassifierResponse
from langchain_typesafe.client import TypeSafeAPIConnectionError

from compaction import DROPPED, SHRUNK_NOTE, CompactionMiddleware, compact, decide, rewrite
from demo import session_messages
from memory_gate import MemoryGateMiddleware, gate
from session import PAIRS


def nouls(**values) -> ClassifierResponse:
    return ClassifierResponse.model_validate(
        {"model": "stub", "answers": {k: {"type": "noul", "noul": v} for k, v in values.items()}})


def by_tool(request) -> ClassifierResponse:
    call = request["state"]["tool_call"]
    if call.startswith("read_file"):
        return nouls(keep_result=0.9, keep_call=0.9)
    if "pytest" in call:
        return nouls(keep_result=0.2, keep_call=0.8)
    return nouls(keep_result=0.1, keep_call=0.1)


def test_decide_and_rewrite() -> None:
    assert decide({"keep_result": 0.6, "keep_call": 0.0}) == "keep"
    assert decide({"keep_result": 0.5, "keep_call": 0.5}) == "shrink"
    assert decide({"keep_result": 0.1, "keep_call": 0.1}) == "drop"
    assert rewrite("x" * 500, "shrink").endswith(SHRUNK_NOTE) and rewrite("short", "shrink") == "short"
    assert rewrite("anything", "drop") == DROPPED


def test_compact_keeps_every_row_and_the_recent_pairs() -> None:
    messages = session_messages()
    replaced, records = compact(RunnableLambda(by_tool), messages, keep_recent=2)
    assert len(records) == len(PAIRS) - 2
    ids = {m.id for m in messages if isinstance(m, ToolMessage)}
    assert {m.id for m in replaced} <= ids  # replacements only, never new or missing rows
    assert all(r["id"] not in {"result_10", "result_11"} for r in records)
    actions = {r["tool"] + str(r["args"]): r["action"] for r in records}
    assert actions["read_file{'path': 'webhook.py'}"] == "keep"


def test_model_down_compacts_nothing() -> None:
    def down(_):
        raise TypeSafeAPIConnectionError("refused")

    assert compact(RunnableLambda(down), session_messages()) == ([], [])


def test_compaction_middleware_edits_in_place_and_skips_done_rows() -> None:
    seen: list[str] = []

    def recording(request):
        seen.append(request["state"]["tool_call"])
        return by_tool(request)

    middleware = CompactionMiddleware(RunnableLambda(recording), budget=1000)
    agent = create_agent(GenericFakeChatModel(messages=iter([AIMessage("고쳤다"), AIMessage("다시 확인")])),
                         tools=[], middleware=[middleware])
    first = agent.invoke({"messages": session_messages()})
    assert len(first["messages"]) == len(session_messages()) + 1  # rows kept, one answer added
    assert any(m.content == DROPPED for m in first["messages"] if isinstance(m, ToolMessage))
    judged = len(seen)
    agent.invoke({"messages": [*first["messages"], HumanMessage("한 번 더")]})
    assert len(seen) - judged == 4  # only the four read_file results kept whole are judged again


def worth(value: float):
    return RunnableLambda(lambda _: nouls(worth=value))


def test_memory_gate_rules() -> None:
    assert gate(worth(0.99), "DB 비밀번호는 hunter2다.")["source"] == "rule"
    assert gate(worth(0.0), "좋아")["allow"] is True  # too short to judge
    assert gate(worth(0.1), "방금 ls를 실행했다.")["allow"] is False
    assert gate(worth(0.3), "사용자는 표를 선호한다.")["allow"] is True

    def down(_):
        raise TypeSafeAPIConnectionError("refused")

    assert gate(RunnableLambda(down), "사용자는 표를 선호한다.")["source"] == "error"


def test_memory_middleware_refuses_noise_only() -> None:
    stored: list[str] = []

    @tool
    def remember(text: str) -> str:
        """Save a fact."""
        stored.append(text)
        return "저장함"

    calls = [{"name": "remember", "args": {"text": t}, "id": str(i)}
             for i, t in enumerate(["사용자는 한국어 답변을 원한다.", "지금 커피 마시러 간다."])]
    model = type("Fake", (GenericFakeChatModel,), {"bind_tools": lambda self, tools, **kw: self})(
        messages=iter([AIMessage("", tool_calls=calls), AIMessage("끝")]))
    judge = RunnableLambda(lambda r: nouls(worth=0.9 if "한국어" in r["state"]["memory_entry"] else 0.05))
    middleware = MemoryGateMiddleware(judge)
    create_agent(model, tools=[remember], middleware=[middleware]).invoke({"messages": [HumanMessage("기억해")]})
    assert stored == ["사용자는 한국어 답변을 원한다."]
    # The two calls run in parallel, so the log order is not fixed.
    assert {e["text"]: e["allow"] for e in middleware.log} == {"사용자는 한국어 답변을 원한다.": True, "지금 커피 마시러 간다.": False}
