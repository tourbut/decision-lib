"""Compact the labelled session, measure the memory gate, then run a live agent whose
memory writes go through the gate.

Usage: python demo.py [--no-llm]
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import find_dotenv, load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_typesafe import TypeSafeClassifier

from compaction import chars, compact, size_based
from memories import MEMORIES
from memory_gate import MemoryGateMiddleware, gate
from session import GOAL, LATEST, NEEDED, PAIRS

load_dotenv(find_dotenv())  # the repo-root .env

THRESHOLD_SWEEP = [0.10, 0.25, 0.40, 0.50]
LIVE_MESSAGE = ("아래 다섯 줄을 remember 도구로 한 줄씩 전부 저장해 줘. 거르지 말고 다 저장해.\n"
                "1. 앞으로 답은 한국어로, 표 위주로 짧게 해 줘.\n2. 지금 커피 마시러 잠깐 다녀올게.\n"
                "3. 우리 팀은 금요일 오후에 배포하지 않아.\n4. 방금 git status를 확인했어.\n"
                "5. 우리 팀 DB 비밀번호는 hunter2야.")


def session_messages() -> list[AnyMessage]:
    messages: list[AnyMessage] = [HumanMessage(GOAL)]
    for i, p in enumerate(PAIRS):
        call_id = f"call_{i}"
        messages.append(AIMessage("", tool_calls=[{"name": p["tool"], "args": p["args"], "id": call_id}]))
        messages.append(ToolMessage(p["result"], tool_call_id=call_id, name=p["tool"], id=f"result_{i}"))
    return [*messages, HumanMessage(LATEST)]


def kept(messages: list[AnyMessage]) -> int:
    text = "\n".join(str(m.content) for m in messages)
    return sum(fact in text for fact in NEEDED)


def compaction_report(classifier) -> None:
    messages = session_messages()
    started = time.perf_counter()
    replaced, records = compact(classifier, messages, keep_recent=0)
    print(f"compaction: {len(records)} pairs judged in {time.perf_counter() - started:.1f}s")
    for p, r in zip(PAIRS, records):
        mark = "ok" if p["label"] == r["action"] else f"MISS ({p['label']})"
        s = r["scores"]
        print(f"  {r['action']:<7}{mark:<16}result {s['keep_result']:.2f} call {s['keep_call']:.2f}  {p['tool']} {list(p['args'].values())[0]}")
    print(f"  labels matched {sum(p['label'] == r['action'] for p, r in zip(PAIRS, records))}/{len(PAIRS)}")
    by_id = {m.id: m for m in replaced}
    need_based = [by_id.get(m.id, m) for m in messages]
    sized = [ToolMessage(size_based(str(m.content)), tool_call_id=m.tool_call_id, id=m.id) if isinstance(m, ToolMessage) else m
             for m in messages]
    for name, msgs in (("original", messages), ("size-based", sized), ("need-based", need_based)):
        print(f"  {name:<11}{chars(msgs):>7} chars   needed facts kept {kept(msgs)}/{len(NEEDED)}")


def memory_report(classifier) -> None:
    started = time.perf_counter()
    decisions = [gate(classifier, m["text"]) for m in MEMORIES]
    print(f"\nmemory gate: {len(MEMORIES)} writes in {time.perf_counter() - started:.1f}s")
    for m, d in zip(MEMORIES, decisions):
        if d["allow"] != (m["label"] == "keep"):
            print(f"  MISS [{m['label']}] {d['reason']}: {m['text']}")
    worth = [d["worth"] for d in decisions]
    for t in THRESHOLD_SWEEP:
        allow = [d["source"] != "rule" and (w is None or w >= t) for d, w in zip(decisions, worth)]
        hits = sum(a == (m["label"] == "keep") for a, m in zip(allow, MEMORIES))
        noise_in = sum(a and m["label"] == "reject" for a, m in zip(allow, MEMORIES))
        lost = sum(not a and m["label"] == "keep" for a, m in zip(allow, MEMORIES))
        print(f"  block below {t:.2f}: {hits}/{len(MEMORIES)} match   noise stored {noise_in}   keepers refused {lost}")


def live(classifier) -> None:
    stored: list[str] = []

    @tool
    def remember(text: str) -> str:
        """Save one lasting fact or preference about the user or project for future sessions."""
        stored.append(text)
        return "저장함"

    model = ChatOpenAI(
        model=os.environ["LOCAL_LLM_MODEL"],
        base_url=os.environ["LOCAL_LLM_URL"],
        api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local",
        max_tokens=800,
        temperature=0,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    middleware = MemoryGateMiddleware(classifier)
    agent = create_agent(model, tools=[remember], middleware=[middleware])
    result = agent.invoke({"messages": [HumanMessage(LIVE_MESSAGE)]}, {"recursion_limit": 20})
    print(f"\nlive agent: {LIVE_MESSAGE}")
    for entry in middleware.log:
        print(f"  {'저장' if entry['allow'] else '거절'}  {entry['reason']:<28} {entry['text']}")
    print(f"  stored: {stored}\n  answer: {result['messages'][-1].content}")


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    compaction_report(classifier)
    memory_report(classifier)
    if "--no-llm" not in sys.argv:
        live(classifier)


if __name__ == "__main__":
    main()
