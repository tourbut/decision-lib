"""Offline tests: metrics, ordering, fusion, and the vendored subset."""

from __future__ import annotations

import math

import pytest
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

from metrics import ndcg, recall
from rerank import QUESTIONS, load, measure, rank_by, rankings, rrf, score


def test_ndcg_and_recall() -> None:
    assert ndcg(["a", "b"], {"a"}) == 1.0
    assert ndcg(["x", "a"], {"a"}) == pytest.approx(1 / math.log2(3))
    assert ndcg(["x"], set()) == 0.0
    assert recall(["a", "x", "b"], {"a", "b", "c"}, k=2) == pytest.approx(1 / 3)


def test_rank_by_keeps_bm25_order_on_ties() -> None:
    assert rank_by(["a", "b", "c"], [1.0, 2.0, 1.0]) == ["b", "a", "c"]


def test_rrf_rewards_agreement() -> None:
    assert rrf(["a", "b", "c"], ["b", "a", "c"])[2] == "c"
    assert rrf(["a", "b", "c"], ["c", "b", "a"]) == ["a", "c", "b"]  # a and c tie; the first ranking breaks it


def test_subset_is_consistent() -> None:
    queries, docs = load()
    assert len(queries) == 30 and all(len(q["bm25"]) == 30 for q in queries)
    assert all(d in docs for q in queries for d in q["bm25"])


def levels(request) -> ClassifierResponse:
    good = "relevant" in request["state"]["document"]
    def answer(n: int, level: float) -> dict:
        return {"type": "score", "score": level, "legend": {str(i): str(i) for i in range(n)},
                "probabilities": {str(i): 1.0 if i == round(level) else 0.0 for i in range(n)}, "confidence": 0.9}
    return ClassifierResponse.model_validate({"model": "stub", "answers": {
        "relevance": answer(10, 9 if good else 1), "evidence": answer(3, 2 if good else 0)}})


def test_rerank_moves_the_relevant_doc_up() -> None:
    docs = {"a": {"title": "a", "text": "noise"}, "b": {"title": "b", "text": "noise"}, "c": {"title": "c", "text": "relevant"}}
    scores = score(RunnableLambda(levels), "claim", ["a", "b", "c"], docs)
    ranked = rankings(["a", "b", "c"], scores)
    assert ranked["relevance"][0] == "c" and ranked["evidence"][0] == "c" and ranked["bm25"][0] == "a"
    m = measure(ranked, ["c"])
    assert m["relevance"]["ndcg@10"] == 1.0 and m["bm25"]["ndcg@10"] < 1.0
    assert set(QUESTIONS) == {"relevance", "evidence"}
