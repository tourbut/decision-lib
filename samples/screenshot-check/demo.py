"""Check the 16 labelled pages twice: from the screenshot, and from extracted text only.

Usage: python demo.py [--image-only]
"""

from __future__ import annotations

import os
import sys
import time
from collections import Counter

from dotenv import find_dotenv, load_dotenv

from check import ImageClassifier, check, shot
from pages import PAGES

load_dotenv(find_dotenv())  # the repo-root .env


def run(classifier, mode: str) -> list[dict]:
    started = time.perf_counter()
    verdicts = [check(classifier, p["url"], mode, text=p["text"], image=shot(p["id"]) if mode == "image" else None)
                for p in PAGES]
    seconds = time.perf_counter() - started
    print(f"\n{mode}: {len(PAGES)} pages in {seconds:.1f}s ({seconds / len(PAGES):.2f}s each)")
    for p, v in zip(PAGES, verdicts):
        mark = "ok" if v["label"] == p["label"] else f"MISS ({p['label']})"
        s = v["scores"]
        print(f"  {v['label']:<9}{mark:<16}pw {s.get('password_form', 0):.2f}  brand {v['brand'] or '-':<10}{p['id']}")
    hits = sum(v["label"] == p["label"] for p, v in zip(PAGES, verdicts))
    phishing = [v["label"] for p, v in zip(PAGES, verdicts) if p["label"] == "phishing"]
    print(f"  matched {hits}/{len(PAGES)}   phishing caught {phishing.count('phishing')}/{len(phishing)}   "
          f"{dict(Counter(v['label'] for v in verdicts))}")
    return verdicts


def main() -> None:
    classifier = ImageClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    run(classifier, "image")
    if "--image-only" not in sys.argv:
        run(classifier, "text")


if __name__ == "__main__":
    main()
