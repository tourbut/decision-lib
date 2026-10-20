"""Offline tests: logprob reading, JSON parsing, the few-label baseline, and AUC."""

from __future__ import annotations

import math
from types import SimpleNamespace as NS

import pytest
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

from judges import answers, auc, d3, few_label, llm_json, llm_read, naive_bayes
from tickets import DEPTS, TICKETS


class FakeLLM:
    """OpenAI-shaped client: letter answers come with a chat-template token first."""

    def __init__(self, letter_probs: dict[str, float] | None = None, content: str = ""):
        self.letter_probs, self.content = letter_probs or {}, content
        self.chat = NS(completions=NS(create=self.create))

    def create(self, **kwargs):
        tops = [NS(token=k, logprob=math.log(v)) for k, v in self.letter_probs.items()]
        positions = [NS(token="<|message|>", top_logprobs=[NS(token="<|message|>", logprob=0.0)]),
                     NS(token=max(self.letter_probs, key=self.letter_probs.get) if tops else "", top_logprobs=tops)]
        return NS(choices=[NS(message=NS(content=self.content), logprobs=NS(content=positions))])


def test_llm_read_skips_template_tokens_and_renormalizes() -> None:
    j = llm_read(FakeLLM({"A": 0.6, "B": 0.2, "x": 0.2}), "m", "결제가 두 번 됐어요")
    assert j["dept"] == pytest.approx({"billing": 0.75, "technical": 0.25})
    assert j["urgent"] == pytest.approx(0.75)  # A = 예
    assert answers(j)["dept"] == "billing"


def test_llm_json_parses_the_object_out_of_text() -> None:
    j = llm_json(FakeLLM(content='답: {"dept": "sales", "urgent": true, "frustration": 2}'), "m", "t")
    assert answers(j) == {"dept": "sales", "urgent": True, "frustration": 2}


def test_d3_maps_three_answers() -> None:
    def stub(request) -> ClassifierResponse:
        probs = {k: (0.9 if k == "technical" else 0.1 / 3) for k in DEPTS}
        return ClassifierResponse.model_validate({"model": "stub", "answers": {
            "dept": {"type": "choice", "choice": "technical", "probabilities": probs, "confidence": 0.9},
            "urgent": {"type": "noul", "noul": 0.95},
            "frustration": {"type": "score", "score": 1.8, "legend": {"0": "a", "1": "b", "2": "c"},
                            "probabilities": {"0": 0.05, "1": 0.1, "2": 0.85}, "confidence": 0.8}}})
    assert answers(d3(RunnableLambda(stub), "서버 다운")) == {"dept": "technical", "urgent": True, "frustration": 2}


def test_naive_bayes_and_few_label() -> None:
    p = naive_bayes([("결제 환불", "billing"), ("서버 오류", "technical")], "환불 결제")
    assert max(p, key=p.get) == "billing" and sum(p.values()) == pytest.approx(1)
    assert set(answers(few_label(TICKETS[1:], TICKETS[0]["text"]))) == {"dept", "urgent", "frustration"}


def test_auc() -> None:
    assert auc([0.9, 0.8, 0.1], [True, True, False]) == 1.0
    assert auc([0.1, 0.9], [True, False]) == 0.0
    assert auc([0.5, 0.5], [True, False]) == 0.5
