"""Measure code search (two-stage, flat, keyword) on 20 questions about this repo, and
the review checklist on 12 diffs with planted defects.

Usage: python demo.py [search|review]
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import Choice, TypeSafeClassifier

from diffs import DIFFS
from questions import QUESTIONS
from review import CHECKLIST, review
from search import index, keyword_search, search

load_dotenv(find_dotenv())  # the repo-root .env


def flat_search(classifier, question: str, folders: dict) -> list[str]:
    """Every declaration in one Choice (fits here: about 215 of them, limit 255)."""
    decls = {d["id"]: d["summary"] for f in folders.values() for d in f["decls"]}
    q = Choice(instructions="Which declaration implements what the question asks about?", criteria=decls)
    p = classifier.invoke({"state": {"question": question}, "questions": {"q": q}}).choices["q"].probabilities
    return sorted(p, key=p.get, reverse=True)[:3]


def search_report(classifier) -> None:
    folders = index()
    total = sum(len(f["decls"]) for f in folders.values())
    print(f"code search: {len(folders)} folders, {total} declarations, {len(QUESTIONS)} questions")
    rows = {"two-stage": [], "flat": [], "keyword": []}
    seconds = {"two-stage": 0.0, "flat": 0.0}
    for item in QUESTIONS:
        started = time.perf_counter()
        two = [r["id"] for r in search(classifier, item["q"], folders)["results"]]
        seconds["two-stage"] += time.perf_counter() - started
        started = time.perf_counter()
        flat = flat_search(classifier, item["q"], folders)
        seconds["flat"] += time.perf_counter() - started
        kw = keyword_search(item["q"], folders)
        for name, got in (("two-stage", two), ("flat", flat), ("keyword", kw)):
            rows[name].append((bool(got) and got[0] in item["answers"], any(g in item["answers"] for g in got)))
        if two[0] not in item["answers"]:
            print(f"  two-stage miss: {item['q']} -> {two[0]} (want {item['answers'][0]})")
    for name, r in rows.items():
        t = f"  {seconds[name] / len(QUESTIONS):.2f}s/question" if name in seconds else ""
        print(f"  {name:<10} top-1 {sum(a for a, _ in r)}/{len(r)}   top-3 {sum(b for _, b in r)}/{len(r)}{t}")


def review_report(classifier) -> None:
    started = time.perf_counter()
    results = [review(classifier, d["diff"]) for d in DIFFS]
    print(f"\nreview: {len(DIFFS)} diffs x {len(CHECKLIST)} questions in {time.perf_counter() - started:.1f}s")
    caught = planted = false_flags = 0
    for d, r in zip(DIFFS, results):
        want, got = set(d["defects"]), set(r["flags"])
        caught += len(want & got)
        planted += len(want)
        false_flags += len(got - want)
        mark = "ok" if want == got else f"want {sorted(want)}"
        print(f"  {d['id']:<26} flags {sorted(got)}  {mark}")
    print(f"  planted defects caught {caught}/{planted}   false flags {false_flags} (of {len(DIFFS) * len(CHECKLIST) - planted} clean checks)")


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
        timeout=120,  # a ~215-option Choice takes a couple of seconds
    )
    chosen = sys.argv[1:] or ["search", "review"]
    if "search" in chosen:
        search_report(classifier)
    if "review" in chosen:
        review_report(classifier)


if __name__ == "__main__":
    main()
