"""Rerank the 30 SciFact queries and compare nDCG@10 against BM25.

Usage: python demo.py [N]   # N queries (default all 30); about 15s per query
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import TypeSafeClassifier

from rerank import load, measure, rankings, score

load_dotenv(find_dotenv())  # the repo-root .env


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    queries, docs = load()
    queries = queries[: int(sys.argv[1])] if len(sys.argv) > 1 else queries
    totals: dict[str, dict[str, float]] = {}
    started = time.perf_counter()
    for q in queries:
        results = measure(rankings(q["bm25"], score(classifier, q["text"], q["bm25"], docs)), q["relevant"])
        for name, m in results.items():
            for metric, value in m.items():
                totals.setdefault(name, {}).setdefault(metric, 0.0)
                totals[name][metric] += value / len(queries)
        print(f"  q{q['id']:<5} " + "  ".join(f"{n} {m['ndcg@10']:.2f}" for n, m in results.items()) + f"  {q['text'][:50]}")
    calls = len(queries) * len(queries[0]["bm25"])
    print(f"\n{len(queries)} queries, {calls} requests, {(time.perf_counter() - started) / calls:.2f}s per request")
    for name, m in totals.items():
        print(f"  {name:<16} nDCG@10 {m['ndcg@10']:.4f}   recall@10 {m['recall@10']:.4f}")


if __name__ == "__main__":
    main()
