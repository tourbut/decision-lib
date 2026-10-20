"""Measure skill suggestion (one pass vs shortlist review) and the hierarchical time-zone
choice over the full IANA catalog.

Usage: python demo.py [--skills-only | --zones-only]
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import TypeSafeClassifier

from pick import hierarchical_choice, stage1_only, suggest
from skills import REQUESTS as SKILL_REQUESTS
from skills import SKILLS
from zones import REGIONS, catalog
from zones import REQUESTS as ZONE_REQUESTS

load_dotenv(find_dotenv())  # the repo-root .env

ZONE_ASK = "Which IANA time zone should a scheduler use for this place?"


def tally(name: str, pairs: list[tuple[str | None, str | None]]) -> None:
    hits = sum(want == got for want, got in pairs)
    wrong = sum(got is not None and got != want for want, got in pairs)  # a skill the reviewer would not suggest
    refused = sum(got is None and want is not None for want, got in pairs)
    print(f"  {name:<18}{hits}/{len(pairs)} match   wrong suggestion {wrong}   missed {refused}")


def skills_report(classifier) -> None:
    descriptions = {name: desc for name, (_, desc) in SKILLS.items()}
    started = time.perf_counter()
    results = [suggest(classifier, r["text"], descriptions) for r in SKILL_REQUESTS]
    print(f"skill suggestion: {len(SKILL_REQUESTS)} requests in {time.perf_counter() - started:.1f}s (2 requests each)")
    for r, s in zip(SKILL_REQUESTS, results):
        if stage1_only(s["stage1"]) != (None if r["label"] == "none" else r["label"]):
            print(f"  stage 1 alone: want {r['label']}, got {stage1_only(s['stage1'])}: {r['text']}")
        want = None if r["label"] == "none" else r["label"]
        if s["skill"] != want:
            fits = {k: round(v, 2) for k, v in s["fits"].items()}
            print(f"  MISS want {r['label']}, got {s['skill']} ({s['reason']}; stage1 {stage1_only(s['stage1'])} {fits}): {r['text']}")
    labels = [None if r["label"] == "none" else r["label"] for r in SKILL_REQUESTS]
    tally("stage 1 only", list(zip(labels, [stage1_only(s["stage1"]) for s in results])))
    tally("shortlist review", list(zip(labels, [s["skill"] for s in results])))


def zones_report(classifier) -> None:
    groups = catalog()
    total = sum(len(v) for v in groups.values())
    started = time.perf_counter()
    results = [hierarchical_choice(classifier, r["text"], groups, REGIONS, ZONE_ASK) for r in ZONE_REQUESTS]
    seconds = time.perf_counter() - started
    print(f"\ntime zones: {total} options in {len(groups)} regions, {len(ZONE_REQUESTS)} requests in {seconds:.1f}s")
    for r, z in zip(ZONE_REQUESTS, results):
        if z["choice"] != r["label"]:
            print(f"  MISS want {r['label']}, got {z['choice']} (regions {z['groups']}): {r['text']}")
    region_hits = sum(r["label"].split("/")[0] in z["groups"] for r, z in zip(ZONE_REQUESTS, results))
    hits = sum(z["choice"] == r["label"] for r, z in zip(ZONE_REQUESTS, results))
    print(f"  region right {region_hits}/{len(ZONE_REQUESTS)}   zone right {hits}/{len(ZONE_REQUESTS)}   "
          f"second region asked {sum(len(z['groups']) > 1 for z in results)}")


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    if "--zones-only" not in sys.argv:
        skills_report(classifier)
    if "--skills-only" not in sys.argv:
        zones_report(classifier)


if __name__ == "__main__":
    main()
