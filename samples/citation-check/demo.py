"""Check the labelled citations, then have the local LLM answer a question with citations
and check those too.

Usage: python demo.py [--no-llm] ["질문"]
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from langchain_typesafe import TypeSafeClassifier

from check import check_all, generate, load_sections
from citations import CITATIONS

load_dotenv(find_dotenv())  # the repo-root .env

QUESTIONS = [
    "개인정보 유출이 생기면 무엇을 언제까지 해야 하나?",
    "탈퇴한 고객의 정보는 어떻게 처리하나?",
]


def show(citations: list[dict], results: list[dict]) -> None:
    print(f"  {'id':<20}{'verdict':<14}{'conf':>6}  section  expected")
    for c, r in zip(citations, results):
        conf = "" if r["confidence"] is None else f"{r['confidence']:.2f}"
        want = c.get("label")
        mark = "" if want is None else ("ok" if want == r["verdict"] else f"MISS ({want})")
        review = " [사람 검토]" if r["needs_review"] else ""
        print(f"  {c['id']:<20}{r['verdict']:<14}{conf:>6}  {r['section'] or '-':<8} {mark}{review}")


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    sections = load_sections(Path(__file__).with_name("source.md"))

    started = time.perf_counter()
    results = check_all(classifier, sections, CITATIONS)
    print(f"labelled citations ({time.perf_counter() - started:.1f}s)")
    show(CITATIONS, results)
    hits = sum(c["label"] == r["verdict"] for c, r in zip(CITATIONS, results))
    print(f"  matched {hits}/{len(CITATIONS)}, review queue {sum(r['needs_review'] for r in results)}")

    if "--no-llm" in sys.argv:
        return
    llm = ChatOpenAI(
        model=os.environ["LOCAL_LLM_MODEL"],
        base_url=os.environ["LOCAL_LLM_URL"],
        api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local",
        max_tokens=1500,
        temperature=0,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    for question in [a for a in sys.argv[1:] if not a.startswith("--")] or QUESTIONS:
        citations = generate(llm, sections, question)
        print(f"\nQ: {question}")
        for c in citations:
            print(f"  {c['id']}: {c['claim']}  «{c['quote']}» §{c['section']}")
        show(citations, check_all(classifier, sections, citations))


if __name__ == "__main__":
    main()
