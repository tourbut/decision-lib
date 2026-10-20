"""Offline tests: scoring plumbing, threshold picks, precision and recall."""

from __future__ import annotations

from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

from feed import HEADLINES, TOPICS
from match import match, picks, precision_recall


def stub(request) -> ClassifierResponse:
    headline = request["state"]["headline"]
    answers = {}
    for name in request["questions"]:
        level = 3.0 if (name == "chips" and "HBM" in headline) else 0.2
        answers[name] = {"type": "score", "score": level, "legend": {str(i): str(i) for i in range(4)},
                         "probabilities": {str(i): 0.25 for i in range(4)}, "confidence": 0.5}
    return ClassifierResponse.model_validate({"model": "stub", "answers": answers})


def test_match_scores_every_pair_and_picks_by_threshold() -> None:
    out = match(RunnableLambda(stub), ["차세대 HBM 양산", "프로야구 우승"], TOPICS)
    assert [set(row) for row in out["scores"]] == [set(TOPICS)] * 2
    assert picks(out["scores"]) == [["chips"], []]


def test_precision_recall() -> None:
    m = precision_recall([["a"], ["b", "c"], []], [["a"], ["b"], ["d"]])
    assert (m["picked"], m["relevant"]) == (3, 3)
    assert m["precision"] == 2 / 3 and m["recall"] == 2 / 3
    assert precision_recall([[]], [[]]) == {"precision": 1.0, "recall": 1.0, "picked": 0, "relevant": 0}


def test_feed() -> None:
    assert len(HEADLINES) == 40 and all(set(h["topics"]) <= set(TOPICS) for h in HEADLINES)
