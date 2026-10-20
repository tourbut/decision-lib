"""nDCG@k and recall@k with binary relevance, as BEIR scores SciFact."""

from __future__ import annotations

import math


def ndcg(ranked: list[str], relevant: set[str], k: int = 10) -> float:
    dcg = sum(1 / math.log2(i + 2) for i, d in enumerate(ranked[:k]) if d in relevant)
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(relevant))))
    return dcg / ideal if ideal else 0.0


def recall(ranked: list[str], relevant: set[str], k: int = 10) -> float:
    return len(set(ranked[:k]) & relevant) / len(relevant) if relevant else 0.0
