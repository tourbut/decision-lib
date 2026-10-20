"""How far can a decision model's probabilities be trusted, and does option order move them?

Two benchmarks on the same metrics:
- sentiment: 200 public NSMC movie reviews. Choice in both option orders vs one Noul,
  as in Raschka's IMDb comparison (#15).
- routing: 40 support tickets, four teams. The Choice is asked in every cyclic order of
  the options; the change rate across orders is the order bias, and L0 (AnyJev, #24)
  averages the orders and divides out the label prior, with no labels needed.

Metrics are plain Python: accuracy, top-label ECE, multi-class Brier, and how many items
a confidence threshold sends to a human.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TypedDict

from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse, Noul

Probs = dict[str, float]

SENTIMENT = {"negative": "부정적인 평가", "positive": "긍정적인 평가"}
SENTIMENT_ASK = "이 영화 리뷰의 감성은?"
POSITIVE = Noul(instructions="이 영화 리뷰는 긍정적인가?")
TEAM_ASK = "이 고객 문의를 어느 팀이 처리해야 하나?"

REVIEW_THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]


class Item(TypedDict):
    text: str
    label: str


def load_nsmc(path: Path) -> list[Item]:
    with path.open(encoding="utf-8") as f:
        rows = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        return [{"text": r["document"], "label": "positive" if r["label"] == "1" else "negative"} for r in rows]


def rotations(labels: list[str]) -> list[list[str]]:
    """Every cyclic order: each label sits in each position exactly once."""
    return [labels[k:] + labels[:k] for k in range(len(labels))]


def ask_choice(
    classifier: Runnable[ClassifierRequest, ClassifierResponse],
    texts: list[str],
    criteria: dict[str, str],
    instructions: str,
    orders: list[list[str]],
) -> list[list[Probs]]:
    """probs[item][order]: one request per (item, order), one question each, so one
    order cannot influence another."""
    questions = [{"q": Choice(instructions=instructions, criteria={k: criteria[k] for k in o})} for o in orders]
    requests = [{"state": {"text": t}, "questions": q} for t in texts for q in questions]
    flat = [r.choices["q"].probabilities for r in classifier.batch(requests)]
    return [flat[i : i + len(orders)] for i in range(0, len(flat), len(orders))]


def ask_positive(classifier: Runnable[ClassifierRequest, ClassifierResponse], texts: list[str]) -> list[Probs]:
    responses = classifier.batch([{"state": {"text": t}, "questions": {"q": POSITIVE}} for t in texts])
    return [{"negative": 1 - r.nouls["q"].noul, "positive": r.nouls["q"].noul} for r in responses]


def top(p: Probs) -> tuple[str, float]:
    label = max(p, key=p.get)
    return label, p[label]


def reliability(probs: list[Probs], labels: list[str], bins: int = 10) -> list[dict]:
    """Top-label confidence buckets: how often the model was right at each confidence."""
    tops = [(top(p)[1], top(p)[0] == y) for p, y in zip(probs, labels)]
    out = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        hits = [(c, ok) for c, ok in tops if lo < c <= hi]
        if hits:
            out.append({"lo": lo, "hi": hi, "n": len(hits), "confidence": sum(c for c, _ in hits) / len(hits),
                        "accuracy": sum(ok for _, ok in hits) / len(hits)})
    return out


def summarize(probs: list[Probs], labels: list[str]) -> dict:
    n = len(labels)
    bins = reliability(probs, labels)
    curve = []
    for t in REVIEW_THRESHOLDS:
        auto = [top(p)[0] == y for p, y in zip(probs, labels) if top(p)[1] >= t]
        curve.append({"threshold": t, "review_rate": 1 - len(auto) / n,
                      "auto_accuracy": sum(auto) / len(auto) if auto else None})
    return {
        "accuracy": sum(top(p)[0] == y for p, y in zip(probs, labels)) / n,
        "ece": sum(b["n"] * abs(b["accuracy"] - b["confidence"]) for b in bins) / n,
        "brier": sum(sum((p.get(k, 0) - (k == y)) ** 2 for k in p) for p, y in zip(probs, labels)) / n,
        "bins": bins,
        "review": curve,
    }


def flips(per_order: list[list[Probs]]) -> list[int]:
    """Indexes of items whose top label changes with the option order."""
    return [i for i, orders in enumerate(per_order) if len({top(p)[0] for p in orders}) > 1]


def position_picks(per_order: list[list[Probs]], orders: list[list[str]]) -> list[float]:
    """Share of answers that landed in each option position. Without bias each is ~1/k."""
    counts = [0] * len(orders[0])
    for item in per_order:
        for p, order in zip(item, orders):
            counts[order.index(top(p)[0])] += 1
    total = sum(counts)
    return [c / total for c in counts]


def l0(per_order: list[list[Probs]]) -> list[Probs]:
    """AnyJev L0: average over cyclic orders, then divide by the mean prediction over the
    whole set (the model's label prior) and renormalize. Uses no labels; assumes the
    true labels are roughly balanced."""
    averaged = [{k: sum(p[k] for p in orders) / len(orders) for k in orders[0]} for orders in per_order]
    prior = {k: sum(p[k] for p in averaged) / len(averaged) for k in averaged[0]}
    out = []
    for p in averaged:
        scaled = {k: p[k] / max(prior[k], 1e-9) for k in p}
        total = sum(scaled.values())
        out.append({k: v / total for k, v in scaled.items()})
    return out
