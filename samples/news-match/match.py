"""Match a feed of headlines to interest profiles, as newsjack matches headlines to brands.

One decision-model request per headline asks a Score per profile ("how much would a
reader with this interest want this?", 0-3). A headline goes to every profile whose
score clears the threshold, so one story can reach several readers and most reach none.
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.runnables import Runnable
from langchain_typesafe import ClassifierRequest, ClassifierResponse, Score

LEVELS = [
    "Not about this interest at all, even if a word overlaps.",
    "Touches the interest in passing.",
    "Clearly about the interest.",
    "Central news for this interest; the reader would want it first.",
]
THRESHOLD = 1.5


def questions(topics: dict[str, str]) -> dict[str, Score]:
    return {name: Score(instructions=f"How much would a reader interested in '{desc}' want this headline?", criteria=LEVELS)
            for name, desc in topics.items()}


def match(classifier: Runnable[ClassifierRequest, ClassifierResponse], headlines: list[str],
          topics: dict[str, str]) -> dict[str, Any]:
    """Scores for every (headline, profile) pair, all headlines in one batch."""
    started = time.perf_counter()
    responses = classifier.batch([{"state": {"headline": h}, "questions": questions(topics)} for h in headlines])
    scores = [{name: r.scores[name].score for name in topics} for r in responses]
    return {"scores": scores, "seconds": time.perf_counter() - started}


def picks(scores: list[dict[str, float]], threshold: float = THRESHOLD) -> list[list[str]]:
    return [sorted(t for t, s in row.items() if s >= threshold) for row in scores]


def precision_recall(predicted: list[list[str]], labels: list[list[str]]) -> dict[str, float]:
    pairs_pred = {(i, t) for i, ts in enumerate(predicted) for t in ts}
    pairs_true = {(i, t) for i, ts in enumerate(labels) for t in ts}
    hit = len(pairs_pred & pairs_true)
    return {"precision": hit / len(pairs_pred) if pairs_pred else 1.0, "recall": hit / len(pairs_true) if pairs_true else 1.0,
            "picked": len(pairs_pred), "relevant": len(pairs_true)}
