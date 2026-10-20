"""Rerank BM25 candidates with decision-model Score rubrics, and measure nDCG@10.

Each candidate gets one decision-model request with two Score questions:
- relevance: a general 10-level relevance rubric (LambdaDB's native Jev reranking).
- evidence: a task-specific 3-level rubric for SciFact claims: does the abstract report
  findings that support or refute the claim? (the "custom criterion" variant)

A Score answer is the expected level under the model's distribution, so it sorts well
but is not a calibrated probability. Ties keep the BM25 order.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from langchain_core.runnables import Runnable
from langchain_typesafe import ClassifierRequest, ClassifierResponse, Question, Score

from metrics import ndcg, recall

DATA = Path(__file__).with_name("data") / "scifact_30.json"

QUESTIONS: dict[str, Question] = {
    "relevance": Score(
        instructions="How relevant is the document to the query?",
        criteria=[
            "Unrelated topic.",
            "Same broad field only.",
            "Shares a few terms, different subject.",
            "Related subject, different question.",
            "Touches the query's subject in passing.",
            "Discusses the subject but not the specific claim.",
            "Partly addresses the specific claim.",
            "Addresses the claim with indirect evidence.",
            "Directly addresses the claim with evidence.",
            "Directly and fully answers the query.",
        ],
    ),
    "evidence": Score(
        instructions="Does the document report findings that support or refute the claim in the query?",
        criteria=[
            "No: a different topic or no findings about this claim.",
            "Partly: findings on a closely related claim.",
            "Yes: findings that directly support or refute this claim.",
        ],
    ),
}


class Query(TypedDict):
    id: str
    text: str
    relevant: list[str]
    bm25: list[str]  # candidate ids in BM25 order


class Doc(TypedDict):
    title: str
    text: str


def load(path: Path = DATA) -> tuple[list[Query], dict[str, Doc]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["queries"], data["docs"]


def score(
    classifier: Runnable[ClassifierRequest, ClassifierResponse],
    query: str,
    candidates: list[str],
    docs: dict[str, Doc],
) -> list[dict[str, float]]:
    """One request per candidate, both rubrics at once; returns {rubric: expected level}."""
    responses = classifier.batch(
        [{"state": {"query": query, "document": f"{docs[d]['title']}\n{docs[d]['text']}"}, "questions": QUESTIONS}
         for d in candidates]
    )
    return [{name: r.scores[name].score for name in QUESTIONS} for r in responses]


def rank_by(candidates: list[str], values: list[float]) -> list[str]:
    """Highest value first; equal values keep the incoming (BM25) order."""
    order = sorted(range(len(candidates)), key=lambda i: (-values[i], i))
    return [candidates[i] for i in order]


def rrf(*rankings: list[str], k: int = 60) -> list[str]:
    """Reciprocal rank fusion: sum of 1/(k + rank) across rankings."""
    total: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            total[doc] = total.get(doc, 0.0) + 1 / (k + rank + 1)
    return sorted(total, key=lambda d: (-total[d], rankings[0].index(d)))


def rankings(candidates: list[str], scores: list[dict[str, float]]) -> dict[str, list[str]]:
    by_relevance = rank_by(candidates, [s["relevance"] for s in scores])
    return {
        "bm25": candidates,
        "relevance": by_relevance,
        "evidence": rank_by(candidates, [s["evidence"] for s in scores]),
        "bm25+relevance": rrf(candidates, by_relevance),
    }


def measure(ranked: dict[str, list[str]], relevant: list[str]) -> dict[str, dict[str, float]]:
    rel = set(relevant)
    return {name: {"ndcg@10": ndcg(r, rel), "recall@10": recall(r, rel)} for name, r in ranked.items()}
