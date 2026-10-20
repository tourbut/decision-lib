"""Match the 40-headline feed to five profiles and compare thresholds.

Usage: python demo.py
"""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import TypeSafeClassifier

from feed import HEADLINES, TOPICS
from match import match, picks, precision_recall

load_dotenv(find_dotenv())  # the repo-root .env

THRESHOLDS = [1.0, 1.5, 2.0, 2.5]


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    labels = [h["topics"] for h in HEADLINES]
    out = match(classifier, [h["text"] for h in HEADLINES], TOPICS)
    pairs = len(HEADLINES) * len(TOPICS)
    print(f"{len(HEADLINES)} headlines x {len(TOPICS)} profiles = {pairs} pairs in {out['seconds']:.1f}s "
          f"({out['seconds'] / len(HEADLINES):.2f}s per headline)")
    for t in THRESHOLDS:
        m = precision_recall(picks(out["scores"], t), labels)
        print(f"  score >= {t}: picked {m['picked']:>3} of {m['relevant']} relevant   "
              f"precision {m['precision']:.2f}   recall {m['recall']:.2f}")
    for h, got in zip(HEADLINES, picks(out["scores"])):
        if got != sorted(h["topics"]):
            print(f"  diff at 1.5: want {sorted(h['topics'])} got {got}: {h['text']}")


if __name__ == "__main__":
    main()
