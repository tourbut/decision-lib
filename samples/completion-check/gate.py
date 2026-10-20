"""The completion check as LangChain middleware: when the model gives a final answer
(no tool calls), check it; on steer, add the instruction as a new user message and send
the agent back to the model, like a Hermes pre_verify hook returning "continue".

The attempt count lives in the conversation itself (steer messages carry the name
`completion_gate`), so the cap holds without extra state.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langchain_core.messages import AIMessage, HumanMessage

from check import Evidence, check

STEER_NAME = "completion_gate"

# What the harness knows about the run: changed files and test counts. The demo agent
# writes prose, so the default reports neither.
Observe = Callable[[AgentState], tuple[list[str], dict[str, int] | None]]


class CompletionGateMiddleware(AgentMiddleware):
    def __init__(self, classifier, observe: Observe = lambda state: ([], None)):
        super().__init__()
        self.classifier = classifier
        self.observe = observe
        self.log: list[dict[str, Any]] = []

    @hook_config(can_jump_to=["model"])
    def after_model(self, state: AgentState, runtime) -> dict[str, Any] | None:
        last = state["messages"][-1]
        if not isinstance(last, AIMessage) or last.tool_calls:
            return None  # mid-task; only a final answer is a completion claim
        humans = [m for m in state["messages"] if isinstance(m, HumanMessage)]
        changed, tests = self.observe(state)
        evidence: Evidence = {
            "task": str(humans[0].content),
            "response": str(last.content),
            "changed": changed,
            "tests": tests,
            "attempt": 1 + sum(m.name == STEER_NAME for m in humans),
        }
        verdict = check(self.classifier, evidence)
        self.log.append({"attempt": evidence["attempt"], "response": evidence["response"], **verdict})
        if verdict["action"] == "steer":
            return {"messages": [HumanMessage(verdict["instruction"], name=STEER_NAME)], "jump_to": "model"}
        if verdict["action"] == "halt":
            note = "[사람 확인 필요] " + "; ".join(verdict["reasons"])
            return {"messages": [AIMessage(note, name=STEER_NAME)]}
        return None


def build_agent(model, classifier, middleware: list[AgentMiddleware] = ()):
    gate = CompletionGateMiddleware(classifier)
    return create_agent(model, tools=[], middleware=[gate, *middleware]), gate
