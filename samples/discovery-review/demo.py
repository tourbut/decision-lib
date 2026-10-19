"""Run the synthetic corpus through the review graph on local models.

Classification uses the local d3-flash decision model (`DECISION_*` in `.env`).
Redaction uses the local chat model (`LOCAL_LLM_*`), so only pages that need it touch
a generative model. Escalated pages are resumed with scripted attorney decisions, or
asked on the terminal with `--ask`.

Usage: python demo.py [--ask]
"""

from __future__ import annotations

import os
import sys
import time
from collections import Counter

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from langchain_typesafe import TypeSafeClassifier
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.types import Command

from corpus import PAGES, PROTOCOL
from review import build_review_graph

load_dotenv(find_dotenv())  # the repo-root .env

# What the reviewing attorney decides for each escalated page in this scripted demo.
ATTORNEY_DECISIONS = {"ARC-000401": "withhold", "ARC-000455": "produce", "ARC-000508": "produce"}


def build():
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    redaction_model = ChatOpenAI(
        model=os.environ["LOCAL_LLM_MODEL"],
        base_url=os.environ["LOCAL_LLM_URL"],
        api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local",
        max_tokens=2000,
        temperature=0,
        # The local model reasons by default; redaction needs only the rewritten text.
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    # Checkpoints restore only the types the graph stores, not arbitrary classes.
    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[("langchain_typesafe.types", "ClassifierResponse")]
    )
    checkpointer = InMemorySaver(serde=serde)
    return build_review_graph(classifier, redaction_model, checkpointer)


def attorney(value: dict, ask: bool) -> str:
    if not ask:
        return ATTORNEY_DECISIONS.get(value["doc_id"], "withhold")
    while (answer := input(f"  {value} -> produce/withhold? ").strip()) not in ("produce", "withhold"):
        pass
    return answer


def review_batch(graph, pages: list[dict], ask: bool) -> tuple[list[dict], dict]:
    config = {"configurable": {"thread_id": "demo-batch-1"}}
    payload = [{"doc_id": p["doc_id"], "page": p["page"], "protocol": PROTOCOL} for p in pages]
    state = graph.invoke({"pages": payload, "results": []}, config)

    escalated = {}
    while state.get("__interrupt__"):
        resume = {}
        for intr in state["__interrupt__"]:
            decision = attorney(intr.value, ask)
            escalated[intr.value["doc_id"]] = (intr.value, decision)
            resume[intr.id] = decision
        state = graph.invoke(Command(resume=resume), config)
    return state["results"], escalated


def main() -> None:
    graph = build()
    started = time.perf_counter()
    results, escalated = review_batch(graph, PAGES, ask="--ask" in sys.argv)
    elapsed = time.perf_counter() - started

    by_id = {r["doc_id"]: r for r in results}
    print(f"\n{'doc_id':<14}{'expected branch':<18}{'decision':<12}notes")
    print("-" * 74)
    for p in PAGES:
        r = by_id.get(p["doc_id"], {})
        notes = []
        if r.get("redacted"):
            notes.append("redacted")
        if p["doc_id"] in escalated:
            value, decision = escalated[p["doc_id"]]
            notes.append(f"attorney -> {decision} (privileged={value['privileged']:.2f}, "
                         f"responsive={value['responsive_score']:.2f}/"
                         f"{value['responsive_confidence']:.2f})")
        print(f"{p['doc_id']:<14}{p['expect']:<18}{r.get('decision', '<missing>'):<12}"
              f"{', '.join(notes)}")

    print("\nAGGREGATION")
    print("-" * 74)
    for decision, n in sorted(Counter(r["decision"] for r in results).items()):
        print(f"  {decision:<12}{n}")
    print(f"  {'TOTAL':<12}{len(results)} pages in {elapsed:.2f}s")
    for r in results:
        if r.get("redacted"):
            print(f"\n[{r['doc_id']} redacted]\n{r['page']}")


if __name__ == "__main__":
    main()
