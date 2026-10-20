"""Compaction by need instead of size: decide per old tool result whether to keep it,
shrink it to a stub, or empty it.

For each tool call/result pair older than the KEEP_RECENT most recent, one decision-model
request asks two Noul questions (as Hermes jev-compaction does): is the call itself worth
remembering, and will the next steps need the full result?

- keep_result ≥ 0.6: keep the result word for word.
- else keep_call ≥ 0.5: keep the call, cut the result to its head plus a rerun note.
- else: empty the result.

Rows are never removed: every ToolMessage keeps its id and tool_call_id, so the model's
tool-call pairing stays valid (jev-compaction crashed on a shorter list). User turns and
assistant text are never touched. If the decision model is down nothing is compacted.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.runnables import Runnable
from langchain_typesafe import ClassifierRequest, ClassifierResponse, Noul, Question
from langchain_typesafe.client import TypeSafeError

Action = Literal["keep", "shrink", "drop"]

QUESTIONS: dict[str, Question] = {
    "keep_result": Noul(
        instructions="Will the next steps toward the goal need this tool result's full text, "
        "for example code to edit, a config value, or a test to satisfy?"
    ),
    "keep_call": Noul(instructions="Is it useful to remember that this call was made and roughly what it found?"),
}

THRESHOLDS = {"keep_result": 0.60, "keep_call": 0.50}
KEEP_RECENT = 2
HEAD = 200
SHRUNK_NOTE = "\n[이하 생략: 필요하면 같은 호출을 다시 실행한다]"
DROPPED = "[결과 삭제됨: 다음 단계에 필요하지 않다고 판정]"
STATE_CHARS = 1500  # the model sees the head of a long result; enough to tell what it is


def decide(s: dict[str, float]) -> Action:
    if s["keep_result"] >= THRESHOLDS["keep_result"]:
        return "keep"
    if s["keep_call"] >= THRESHOLDS["keep_call"]:
        return "shrink"
    return "drop"


def rewrite(text: str, action: Action) -> str:
    if action == "keep":
        return text
    if action == "shrink":
        return text if len(text) <= HEAD else text[:HEAD] + SHRUNK_NOTE
    return DROPPED


def size_based(text: str) -> str:
    """The baseline most harnesses use: cut every old result to its head, needed or not."""
    return text if len(text) <= HEAD else text[:HEAD] + SHRUNK_NOTE


def tool_pairs(messages: list[AnyMessage]) -> list[tuple[dict[str, Any], ToolMessage]]:
    calls = {c["id"]: c for m in messages if isinstance(m, AIMessage) for c in m.tool_calls}
    return [(calls[m.tool_call_id], m) for m in messages if isinstance(m, ToolMessage) and m.tool_call_id in calls]


def judge(
    classifier: Runnable[ClassifierRequest, ClassifierResponse],
    messages: list[AnyMessage],
    keep_recent: int = KEEP_RECENT,
) -> list[dict[str, Any]]:
    """One record per old pair: the tool message id, the scores, and the action."""
    humans = [str(m.content) for m in messages if isinstance(m, HumanMessage)]
    pairs = tool_pairs(messages)
    old = pairs[: len(pairs) - keep_recent]
    # Already-compacted results are not judged again on the next pass.
    old = [(c, r) for c, r in old if r.content != DROPPED and not str(r.content).endswith(SHRUNK_NOTE)]
    responses = classifier.batch([
        {"state": {"goal": humans[0], "latest_request": humans[-1],
                   "tool_call": f"{call['name']} {json.dumps(call['args'], ensure_ascii=False)}",
                   "result": str(result.content)[:STATE_CHARS]},
         "questions": QUESTIONS}
        for call, result in old
    ])
    records = []
    for (call, result), r in zip(old, responses):
        s = {k: a.noul for k, a in r.nouls.items()}
        records.append({"id": result.id, "tool": call["name"], "args": call["args"], "scores": s, "action": decide(s)})
    return records


def compact(
    classifier, messages: list[AnyMessage], keep_recent: int = KEEP_RECENT
) -> tuple[list[ToolMessage], list[dict[str, Any]]]:
    """Replacement ToolMessages (same ids) plus the per-pair records. A model failure
    returns no replacements: an unjudged context is kept whole rather than guessed at."""
    try:
        records = judge(classifier, messages, keep_recent)
    except TypeSafeError:
        return [], []
    by_id = {m.id: m for m in messages if isinstance(m, ToolMessage)}
    replaced = []
    for rec in records:
        old = by_id[rec["id"]]
        new = rewrite(str(old.content), rec["action"])
        if new != old.content:
            replaced.append(ToolMessage(content=new, id=old.id, tool_call_id=old.tool_call_id, name=old.name))
    return replaced, records


def chars(messages: list[AnyMessage]) -> int:
    return sum(len(str(m.content)) for m in messages)


class CompactionMiddleware(AgentMiddleware):
    """Before a model call, compact once the context passes `budget` characters. The
    replacements reuse the old ids, so the add_messages reducer edits them in place."""

    def __init__(self, classifier, budget: int = 6000):
        super().__init__()
        self.classifier = classifier
        self.budget = budget
        self.log: list[dict[str, Any]] = []

    def before_model(self, state: AgentState, runtime) -> dict[str, Any] | None:
        if chars(state["messages"]) <= self.budget:
            return None
        replaced, records = compact(self.classifier, state["messages"])
        self.log.append({"before": chars(state["messages"]), "records": records})
        return {"messages": replaced} if replaced else None
