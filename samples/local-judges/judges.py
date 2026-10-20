"""Four ways to get the same three judgments (team, urgent, frustration) for a ticket,
all local:

1. d3: the decision model, three typed questions in one /v1/systemone request (Kev's
   "several questions over one shared context").
2. llm_read: the local chat LLM, one prompt per question with lettered options, reading
   the probability of each letter from the first answer token's logprobs (the SemIf /
   OpenJev idea). No text is parsed.
3. llm_json: the same LLM writes one JSON object with all three answers, parsed from
   text. No probabilities.
4. few_label: no model; a character-bigram naive Bayes trained on the other labelled
   tickets (leave one out), standing in for "a few hundred labels" adaptation.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from typing import Any

from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse, Noul, Score
from openai import OpenAI

from tickets import DEPTS, FRUSTRATION

Judgment = dict[str, Any]  # {"dept": {label: p}, "urgent": p or bool, "frustration": {level: p} or int}

QUESTIONS = {
    "dept": Choice(instructions="Which team should handle this support ticket?", criteria=DEPTS),
    "urgent": Noul(instructions="Does this ticket need a response within hours, not days?"),
    "frustration": Score(instructions="How frustrated is the customer?", criteria=FRUSTRATION),
}


def d3(classifier: Runnable[ClassifierRequest, ClassifierResponse], text: str) -> Judgment:
    r = classifier.invoke({"state": {"ticket": text}, "questions": QUESTIONS})
    return {"dept": r.choices["dept"].probabilities, "urgent": r.nouls["urgent"].noul,
            "frustration": {int(k): v for k, v in r.scores["frustration"].probabilities.items()}}


# --- the chat LLM, read from logprobs -------------------------------------------------

LETTERS = "ABCD"
PROMPTS = {
    "dept": ("이 고객 문의를 처리할 팀은?", list(DEPTS)),
    "urgent": ("이 문의는 며칠이 아니라 몇 시간 안에 답해야 하는가?", ["예", "아니오"]),
    "frustration": ("고객은 얼마나 화가 났는가?", FRUSTRATION),
}


def _ask_letters(client: OpenAI, model: str, text: str, question: str, options: list[str]) -> dict[str, float]:
    lines = "\n".join(f"{LETTERS[i]}) {o}" for i, o in enumerate(options))
    prompt = f'고객 문의: "{text}"\n{question}\n{lines}\n글자 하나로만 답하라.'
    r = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], max_tokens=4, temperature=0,
        logprobs=True, top_logprobs=20, extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    letters = LETTERS[: len(options)]
    # The first answer token comes after any chat-template marker such as <|message|>.
    for position in r.choices[0].logprobs.content:
        if position.token.strip() in letters:
            p = {t.token.strip(): math.exp(t.logprob) for t in position.top_logprobs if t.token.strip() in letters}
            total = sum(p.values())
            return {options[letters.index(k)]: v / total for k, v in p.items()}
    raise ValueError(f"no answer letter in {[c.token for c in r.choices[0].logprobs.content]}")


def llm_read(client: OpenAI, model: str, text: str) -> Judgment:
    dept = _ask_letters(client, model, text, *PROMPTS["dept"])
    urgent = _ask_letters(client, model, text, *PROMPTS["urgent"])
    frustration = _ask_letters(client, model, text, *PROMPTS["frustration"])
    return {"dept": dept, "urgent": urgent.get("예", 0.0),
            "frustration": {FRUSTRATION.index(k): v for k, v in frustration.items()}}


# --- the chat LLM, written as JSON ----------------------------------------------------

JSON_PROMPT = """고객 문의: "{text}"
다음 JSON 하나만 출력하라. 다른 글은 쓰지 마라.
{{"dept": "billing|technical|sales|other", "urgent": true|false, "frustration": 0|1|2}}
dept는 처리할 팀, urgent는 몇 시간 안에 답해야 하는지, frustration은 0 차분함·1 불만·2 매우 화남이다."""


def llm_json(client: OpenAI, model: str, text: str) -> Judgment:
    r = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": JSON_PROMPT.format(text=text)}], max_tokens=80,
        temperature=0, extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    data = json.loads(re.search(r"\{.*\}", r.choices[0].message.content, re.S).group(0))
    return {"dept": data["dept"], "urgent": bool(data["urgent"]), "frustration": int(data["frustration"])}


# --- a few labels, no model -----------------------------------------------------------


def _grams(text: str) -> list[str]:
    s = re.sub(r"\s+", " ", text)
    return [s[i : i + 2] for i in range(len(s) - 1)]


def naive_bayes(train: list[tuple[str, Any]], text: str) -> dict[Any, float]:
    """Multinomial naive Bayes over character bigrams with add-one smoothing."""
    classes = Counter(y for _, y in train)
    counts = {y: Counter() for y in classes}
    for x, y in train:
        counts[y].update(_grams(x))
    vocab = {g for c in counts.values() for g in c}
    scores = {}
    for y in classes:
        total = sum(counts[y].values()) + len(vocab)
        scores[y] = math.log(classes[y] / len(train)) + sum(math.log((counts[y][g] + 1) / total) for g in _grams(text))
    top = max(scores.values())
    z = sum(math.exp(s - top) for s in scores.values())
    return {y: math.exp(s - top) / z for y, s in scores.items()}


def few_label(train: list[dict], text: str) -> Judgment:
    urgent = naive_bayes([(t["text"], t["urgent"]) for t in train], text)
    return {"dept": naive_bayes([(t["text"], t["dept"]) for t in train], text), "urgent": urgent.get(True, 0.0),
            "frustration": naive_bayes([(t["text"], t["frustration"]) for t in train], text)}


# --- scoring ----------------------------------------------------------------------------


def top(value: Any) -> Any:
    return max(value, key=value.get) if isinstance(value, dict) else value


def answers(j: Judgment) -> dict[str, Any]:
    """Collapse a judgment to one answer per question."""
    urgent = j["urgent"] if isinstance(j["urgent"], bool) else j["urgent"] >= 0.5
    return {"dept": top(j["dept"]), "urgent": urgent, "frustration": top(j["frustration"])}


def auc(scores: list[float], labels: list[bool]) -> float:
    """Chance that a random positive outranks a random negative (ties count half)."""
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))
