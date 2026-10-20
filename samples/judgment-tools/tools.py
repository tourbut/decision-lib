"""Judgment tools an agent can call, each a thin wrapper around one decision-model request.

Every result is advice: `advisory_only: true, execution_authorized: false`, as in the
Hermes jev-typesafe plugin. The caller enforces any decision. Failures never turn into a
yes: gate and verify fail to "review", approval to "ESCALATE", fastpath to "normal_llm".

Generic: check (Noul), route (Choice), score (Score).
Task-shaped: verify (claim vs evidence), gate (proposed action), approval (Hermes
structured-aux approval slot), fastpath (answer narrow turns locally, skipping the LLM),
skill_relation (Hermes jev-curator's pairwise relation).
"""

from __future__ import annotations

import ast
import operator
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse, Noul, Score
from langchain_typesafe.client import TypeSafeError

Classifier = Runnable[ClassifierRequest, ClassifierResponse]
ADVISORY = {"advisory_only": True, "execution_authorized": False}
THRESHOLDS = {"verify_pass": 0.80, "gate_confident": 0.60, "approve_min": 0.80,
              "fastpath_choice": 0.92, "fastpath_alone": 0.90, "merge_min": 0.80}


def _ask(classifier: Classifier, state: Any, questions: dict) -> ClassifierResponse:
    return classifier.invoke({"state": state, "questions": questions})


def _choice(answers: ClassifierResponse, name: str = "q") -> dict[str, Any]:
    a = answers.choices[name]
    return {"choice": a.choice, "probabilities": a.probabilities, "confidence": a.confidence}


# --- Generic ------------------------------------------------------------------------


def check(classifier: Classifier, state: str, question: str) -> dict[str, Any]:
    answers = _ask(classifier, state, {"q": Noul(instructions=question)})
    return {"yes": answers.nouls["q"].noul, **ADVISORY}


def route(classifier: Classifier, state: str, question: str, options: dict[str, str]) -> dict[str, Any]:
    return {**_choice(_ask(classifier, state, {"q": Choice(instructions=question, criteria=options)})), **ADVISORY}


def score(classifier: Classifier, state: str, question: str, levels: list[str]) -> dict[str, Any]:
    a = _ask(classifier, state, {"q": Score(instructions=question, criteria=levels)}).scores["q"]
    return {"score": a.score, "probabilities": a.probabilities, **ADVISORY}


# --- verify and gate ----------------------------------------------------------------


def verify(classifier: Classifier, claim: str, evidence: str) -> dict[str, Any]:
    question = Choice(instructions="How does the evidence relate to the claim?", criteria={
        "supports": "The evidence states the claim or directly implies it.",
        "contradicts": "The evidence states the opposite of the claim.",
        "says_nothing": "The evidence does not address the claim."})
    try:
        r = _choice(_ask(classifier, {"claim": claim, "evidence": evidence}, {"q": question}))
    except TypeSafeError as e:
        return {"recommendation": "review", "reason": f"판정 실패: {type(e).__name__}", **ADVISORY}
    if r["choice"] == "contradicts":
        rec = "block"
    elif r["choice"] == "supports" and r["confidence"] >= THRESHOLDS["verify_pass"]:
        rec = "pass"
    else:
        rec = "review"
    return {"recommendation": rec, "relation": r["choice"], **r, **ADVISORY}


def gate(classifier: Classifier, action: str, context: str) -> dict[str, Any]:
    question = Choice(instructions="Should this proposed action go ahead?", criteria={
        "pass": "Safe, reversible, and clearly within the stated context.",
        "review": "Plausible but risky, irreversible, or unclear; a person should look first.",
        "block": "Harmful, out of scope, or clearly against the context."})
    try:
        r = _choice(_ask(classifier, {"proposed_action": action, "context": context}, {"q": question}))
    except TypeSafeError as e:
        return {"recommendation": "review", "reason": f"판정 실패: {type(e).__name__}", **ADVISORY}
    rec = r["choice"] if r["probabilities"][r["choice"]] >= THRESHOLDS["gate_confident"] else "review"
    return {"recommendation": rec, **r, **ADVISORY}


# --- approval (structured-aux) ------------------------------------------------------


def approval(classifier: Classifier, command: str, reason: str = "") -> dict[str, Any]:
    """APPROVE needs a confident model; anything unsure or failed goes to the user."""
    question = Choice(instructions="A coding agent wants to run this command. What should the approver do?", criteria={
        "APPROVE": "Routine and low risk: reads, builds, tests, local edits inside the project.",
        "DENY": "Destructive or exfiltrating with no plausible need: wipes, credential theft, disabling security.",
        "ESCALATE": "Could be legitimate but has real impact: deploys, deletes, network or permission changes."})
    try:
        r = _choice(_ask(classifier, {"command": command, "agent_reason": reason}, {"q": question}))
    except TypeSafeError as e:
        return {"decision": "ESCALATE", "reason": f"판정 실패: {type(e).__name__}", **ADVISORY}
    decision = r["choice"]
    if decision == "APPROVE" and r["probabilities"]["APPROVE"] < THRESHOLDS["approve_min"]:
        decision = "ESCALATE"
    return {"decision": decision, **r, **ADVISORY}


# --- fastpath -----------------------------------------------------------------------

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}
ARITH = re.compile(r"[\d.()\s]*\d[\d.()\s]*(?:[-+*/%^×÷][\d.()\s]*\d[\d.()\s]*)+")


def calculate(expression: str) -> float:
    """Arithmetic only: numbers, + - * / % ** and parentheses. Anything else raises."""
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            if isinstance(node.op, ast.Pow) and abs(ev(node.right)) > 100:
                raise ValueError("지수가 너무 크다")
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("산술식이 아니다")
    return ev(ast.parse(expression.replace("^", "**").replace("×", "*").replace("÷", "/"), mode="eval").body)


def _calc_answer(text: str) -> str:
    expr = ARITH.search(text).group(0).strip()
    value = calculate(expr)
    return f"{expr} = {value:g}"


# handler: (what a turn must ask for, and only that; the local answer)
HANDLERS = {
    "calculator": ("the value of an arithmetic expression whose numbers are all given", _calc_answer),
    "clock": ("the current time or today's date in Seoul",
              lambda text: datetime.now(ZoneInfo("Asia/Seoul")).strftime("지금은 %Y-%m-%d %H:%M(서울)입니다.")),
    "acknowledgement": ("nothing: they only thank, greet, or agree", lambda text: "천만에요. 더 필요한 게 있으면 말씀해 주세요."),
}
DETECTORS = {
    "calculator": lambda t: ARITH.search(t) is not None,
    "clock": lambda t: re.search(r"몇\s*시|시간|날짜|오늘.*며칠|요일", t) is not None,
    "acknowledgement": lambda t: re.search(r"고마|감사|ㄱㅅ|좋아|알겠|안녕", t) is not None and len(t) < 40,
}


def fastpath(classifier: Classifier, text: str) -> dict[str, Any]:
    """Local detectors propose handlers; the model must confirm one with high confidence
    and say the handler alone can answer. Otherwise the turn goes to the normal LLM."""
    candidates = [h for h, detect in DETECTORS.items() if detect(text)]
    if not candidates:
        return {"handler": "normal_llm", "reason": "후보 핸들러 없음(모델 호출 없음)", "answer": None, **ADVISORY}
    options = {h: f"The user asks only for {HANDLERS[h][0]}." for h in candidates}
    options["normal_llm"] = "Anything else; the main LLM should answer."
    # Asking "only for X, nothing more" separated the near misses; a vaguer "can a fixed
    # reply answer this" kept even plain thanks below 0.90.
    questions = {"handler": Choice(instructions="Which handler should answer this user turn?", criteria=options)}
    questions |= {f"alone_{h}": Noul(instructions=f"Is the user asking only for {HANDLERS[h][0]}, and nothing more?")
                  for h in candidates}
    try:
        answers = _ask(classifier, {"user_turn": text}, questions)
    except TypeSafeError as e:
        return {"handler": "normal_llm", "reason": f"판정 실패: {type(e).__name__}", "answer": None, **ADVISORY}
    r = _choice(answers, "handler")
    alone = answers.nouls[f"alone_{r['choice']}"].noul if r["choice"] != "normal_llm" else 0.0
    chosen = r["choice"]
    p = r["probabilities"][chosen]
    if chosen == "normal_llm" or p < THRESHOLDS["fastpath_choice"] or alone < THRESHOLDS["fastpath_alone"]:
        return {"handler": "normal_llm", "reason": f"단락 조건 미달({chosen} {p:.2f}, 단독 {alone:.2f})",
                "answer": None, "alone": alone, **r, **ADVISORY}
    try:
        answer = HANDLERS[chosen][1](text)
    except (ValueError, ZeroDivisionError, SyntaxError, AttributeError) as e:
        return {"handler": "normal_llm", "reason": f"핸들러 실패: {e}", "answer": None, "alone": alone, **r, **ADVISORY}
    return {"handler": chosen, "reason": "로컬 핸들러로 답함", "answer": answer, "alone": alone, **r, **ADVISORY}


# --- skill relation (curator) -------------------------------------------------------

RELATIONS = {
    "duplicate": "A and B do the same job.",
    "a_subset_of_b": "Everything A does, B also does, and B does more.",
    "b_subset_of_a": "Everything B does, A also does, and A does more.",
    "same_class": "Same kind of job on different targets.",
    "complementary": "Different jobs that work well together.",
    "conflict": "They give contradictory instructions for the same situation.",
    "unrelated": "Nothing in common.",
    "insufficient_evidence": "The descriptions are too thin to tell.",
}


def skill_relation(classifier: Classifier, skill_a: str, skill_b: str) -> dict[str, Any]:
    """Relation plus a plan hint. Merging is only suggested for a confident duplicate or
    subset; conflicts are flagged and never merged. Nothing is written."""
    question = Choice(instructions="How does skill A relate to skill B?", criteria=RELATIONS)
    r = _choice(_ask(classifier, {"skill_a": skill_a, "skill_b": skill_b}, {"q": question}))
    p = r["probabilities"][r["choice"]]
    if r["choice"] in ("duplicate", "a_subset_of_b", "b_subset_of_a") and p >= THRESHOLDS["merge_min"]:
        plan = {"duplicate": "하나로 합치기 후보", "a_subset_of_b": "A를 B에 합치기 후보",
                "b_subset_of_a": "B를 A에 합치기 후보"}[r["choice"]]
    elif r["choice"] == "conflict":
        plan = "충돌: 사람 확인, 합치지 않음"
    else:
        plan = "그대로 둠"
    return {"relation": r["choice"], "plan": plan, **r, **ADVISORY}
