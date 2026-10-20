"""Memory gate: before an agent writes to long-term memory, ask whether the entry is
worth carrying into future sessions (Hermes jev-memory-gate).

- Secrets (keys, passwords) are refused by a regex, with no model call.
- Very short entries skip the check and pass.
- One Noul question; below BLOCK_BELOW the write is refused. The gate only refuses
  clear noise, so the default threshold is low.
- Only the entry text is sent, never the conversation. If the model is down the
  write passes (fail-open), as in the plugin.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, Literal, TypedDict

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langchain_core.runnables import Runnable
from langchain_typesafe import ClassifierRequest, ClassifierResponse, Noul
from langchain_typesafe.client import TypeSafeError

WORTH = Noul(
    instructions="Is this worth remembering in future sessions with this user or project: a lasting "
    "preference, rule, or fact, rather than a passing status update?"
)

BLOCK_BELOW = 0.25  # the plugin's default
MIN_CHARS = 6
MEMORY_TOOL = "remember"
SECRET = re.compile(r"(?i)\b(sk|ghp|xox[bp])[-_][\w-]{8,}|(password|passwd|비밀번호|api[ _-]?key|토큰)\s*(은|는|이|:|=)\s*\S+")


class Decision(TypedDict):
    allow: bool
    reason: str
    worth: float | None
    source: Literal["rule", "model", "skip", "error"]


def gate(classifier: Runnable[ClassifierRequest, ClassifierResponse], text: str, block_below: float = BLOCK_BELOW) -> Decision:
    if SECRET.search(text):
        return {"allow": False, "reason": "비밀 정보로 보여 저장하지 않는다", "worth": None, "source": "rule"}
    if len(text.strip()) < MIN_CHARS:
        return {"allow": True, "reason": "짧아서 판정 생략", "worth": None, "source": "skip"}
    try:
        worth = classifier.invoke({"state": {"memory_entry": text}, "questions": {"worth": WORTH}}).nouls["worth"].noul
    except TypeSafeError as e:
        return {"allow": True, "reason": f"판정 실패({type(e).__name__}): 그대로 저장", "worth": None, "source": "error"}
    if worth < block_below:
        return {"allow": False, "reason": f"기억할 가치 낮음({worth:.2f} < {block_below})", "worth": worth, "source": "model"}
    return {"allow": True, "reason": f"기억할 가치 있음({worth:.2f})", "worth": worth, "source": "model"}


class MemoryGateMiddleware(AgentMiddleware):
    """Wraps calls to the `remember` tool; every other tool passes through untouched."""

    def __init__(self, classifier, block_below: float = BLOCK_BELOW):
        super().__init__()
        self.classifier = classifier
        self.block_below = block_below
        self.log: list[dict[str, Any]] = []

    def wrap_tool_call(self, request, handler: Callable):
        call = request.tool_call
        if call["name"] != MEMORY_TOOL:
            return handler(request)
        decision = gate(self.classifier, str(call["args"].get("text", "")), self.block_below)
        self.log.append({"text": call["args"].get("text", ""), **decision})
        if decision["allow"]:
            return handler(request)
        return ToolMessage(content=f"저장 거절: {decision['reason']}", tool_call_id=call["id"], name=MEMORY_TOOL)
