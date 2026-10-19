"""Run three queries through retrieval, the d3-flash passage filter, and the local LLM.

Usage: python demo.py [--no-answer]   # --no-answer skips generation
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from langchain_typesafe import TypeSafeClassifier

from rag import bm25, build_prompt, classify, load_passages

load_dotenv(find_dotenv())  # the repo-root .env

TOP_K = 6

# Expected route for the passages each query is meant to exercise.
QUERIES = {
    "액세스 토큰 유효기간은 얼마인가?": {
        "AUTH-01": "evidence",
        "AUTH-02": "excluded_off_topic",  # refresh-token lifetime, not the premise's subject
        "FORUM-01": "excluded_no_evidence",
        "FORUM-02": "excluded_injection",
    },
    "액세스 토큰 유효기간을 30일로 정한 이유는?": {
        "AUTH-01": "conflict",
        "AUTH-03": "conflict",
        "OPS-01": "excluded_off_topic",  # a 30-day link, lexically close but unrelated
        "FORUM-01": "excluded_no_evidence",
        "FORUM-02": "excluded_injection",
    },
    "로그아웃하면 리프레시 토큰은 어떻게 되나?": {
        "AUTH-03": "evidence",
        "AUTH-04": "excluded_off_topic",
    },
}


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    generator = ChatOpenAI(
        model=os.environ["LOCAL_LLM_MODEL"],
        base_url=os.environ["LOCAL_LLM_URL"],
        api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local",
        max_tokens=800,
        temperature=0,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    passages = load_passages(Path(__file__).with_name("corpus.md"))
    agree = labeled = 0

    for query, expected in QUERIES.items():
        started = time.perf_counter()
        routed = classify(classifier, query, bm25(query, passages, TOP_K))
        elapsed = time.perf_counter() - started

        print(f"\nQ: {query}   ({len(routed)} passages classified in {elapsed:.2f}s)")
        print(f"  {'id':<10}{'route':<22}{'rel':>6}{'evid':>6}{'contra':>8}{'inject':>8}  expected")
        for p, answers, r in routed:
            n = {k: v.noul for k, v in answers.nouls.items()}
            want = expected.get(p["id"], "")
            if want:
                labeled += 1
                agree += want == r
            mark = "" if not want else ("ok" if want == r else f"MISS ({want})")
            print(f"  {p['id']:<10}{r:<22}{n['is_relevant']:>6.2f}{n['contains_answer_evidence']:>6.2f}"
                  f"{n['contradicts_query_premise']:>8.2f}{n['contains_prompt_injection']:>8.2f}  {mark}")
        missing = sorted(set(expected) - {p["id"] for p, _, _ in routed})
        if missing:
            print(f"  not retrieved: {', '.join(missing)}")
        if "--no-answer" not in sys.argv:
            print(f"\nA: {generator.invoke(build_prompt(query, routed)).content}")

    print(f"\nlabeled routes matched: {agree}/{labeled}")


if __name__ == "__main__":
    main()
