"""Pick the next action from the actions that are valid right now.

Every environment in this sample hands the picker the same thing: a goal, a short
observation, and a dict of candidate actions {id: label}. One decision-model Choice picks
one id, or DONE (the goal is reached) or NONE (no candidate leads anywhere useful).
Plain code owns everything else: which actions exist, executing them, page or state
freshness, the step limit, and an independent check after DONE.

Based on browser-use jev-ultrafast (#1), Agent Desktop / typesafe-computer-use (#19),
and minecraft-agent's System 2 planner plus Jev controller (#18).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse
from langchain_typesafe.client import TypeSafeError

DONE, NONE = "DONE", "NONE"
CONFIDENT = 0.50  # below this the picker holds (NONE) instead of guessing
MAX_STEPS = 12


class Env(Protocol):
    def observe(self, state: Any) -> tuple[str, dict[str, str]]:
        """(observation text, {action id: label}) for the current state."""

    def step(self, state: Any, action: str) -> Any: ...


def pick(
    classifier: Runnable[ClassifierRequest, ClassifierResponse],
    goal: str,
    observation: str,
    candidates: dict[str, str],
) -> tuple[str, dict[str, float]]:
    """One Choice over the valid actions plus DONE and NONE."""
    criteria = {**candidates,
                DONE: "The goal is already reached on the current screen; stop.",
                NONE: "None of these actions moves toward the goal."}
    question = Choice(instructions="Which single action moves closest to the goal right now?", criteria=criteria)
    try:
        answer = classifier.invoke({"state": {"goal": goal, "screen": observation}, "questions": {"action": question}})
    except TypeSafeError:
        return NONE, {}
    probs = answer.choices["action"].probabilities
    best = max(probs, key=probs.get)
    return (best if probs[best] >= CONFIDENT else NONE), probs


def run(
    classifier,
    env: Env,
    goal: str,
    state: Any,
    verify: Callable[[Any], bool],
    max_steps: int = MAX_STEPS,
) -> dict[str, Any]:
    """Loop until DONE, NONE, a repeated state, or the step limit. DONE is not trusted:
    `verify` checks the final state independently."""
    trace = []
    seen = {repr(state)}
    for _ in range(max_steps):
        observation, candidates = env.observe(state)
        action, probs = pick(classifier, goal, observation, candidates)
        trace.append({"observation": observation, "action": action, "label": candidates.get(action, action),
                      "probability": probs.get(action, 0.0)})
        if action in (DONE, NONE):
            break
        state = env.step(state, action)
        if repr(state) in seen:
            trace.append({"observation": "같은 상태로 돌아옴", "action": NONE, "label": "반복 감지로 중단", "probability": 0.0})
            break
        seen.add(repr(state))
    stopped = trace[-1]["action"]
    return {"trace": trace, "stopped": stopped, "state": state, "verified": stopped == DONE and verify(state)}
