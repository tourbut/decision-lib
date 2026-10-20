"""Run both benchmarks against the decision model in .env and print the comparison.

Usage: python demo.py [--sentiment-only | --routing-only]
"""

from __future__ import annotations

import os
import sys

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import TypeSafeClassifier

from bench import NSMC, ROUTING, routing, sentiment

load_dotenv(find_dotenv())  # the repo-root .env


def row(name: str, m: dict) -> None:
    review = {r["threshold"]: r for r in m["review"]}[0.9]
    auto = "-" if review["auto_accuracy"] is None else f"{review['auto_accuracy']:.1%}"
    print(f"  {name:<16}{m['accuracy']:>8.1%}{m['ece']:>8.3f}{m['brier']:>8.3f}"
          f"{review['review_rate']:>12.1%}{auto:>10}")


def header() -> None:
    print(f"  {'':<16}{'acc':>8}{'ECE':>8}{'Brier':>8}{'review@0.9':>12}{'auto acc':>10}")


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    if "--routing-only" not in sys.argv:
        s = sentiment(classifier, NSMC)
        print(f"sentiment: NSMC {s['n']} reviews")
        header()
        for name, m in s["methods"].items():
            row(name, m)
        print(f"  decision changed when options swapped: {s['flip_rate']:.1%}")
        print("  " + ", ".join(f"{k} {m['seconds_per_call']:.2f}s/call" for k, m in s["methods"].items()))
        for f in s["flipped"]:
            print(f"    flip [{f['label']}] {f['text'][:60]}  {[round(p['positive'], 2) for p in f['orders']]}")
    if "--sentiment-only" not in sys.argv:
        r = routing(classifier, ROUTING)
        print(f"\nrouting: {r['n']} tickets x {len(r['orders'])} cyclic option orders")
        header()
        for name, m in r["methods"].items():
            row(name, m)
        print(f"  decision changed across orders: {r['flip_rate']:.1%}, {r['seconds_per_call']:.2f}s/call")
        print("  answers by option position: " + ", ".join(f"{i + 1}: {p:.1%}" for i, p in enumerate(r["position_picks"])))
        for f in r["flipped"]:
            picks = [max(p, key=p.get) for p in f["orders"]]
            print(f"    flip [{f['label']}] {f['text'][:50]}  {picks}")
        for item in r["items"]:
            first, after = max(item["orders"][0], key=item["orders"][0].get), max(item["l0"], key=item["l0"].get)
            if first != after:
                print(f"    L0 changed [{item['label']}] {first} -> {after}: {item['text'][:50]}")


if __name__ == "__main__":
    main()
