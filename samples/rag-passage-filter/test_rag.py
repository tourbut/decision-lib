"""Offline tests: routing policy, retrieval, and prompt assembly. No model is called."""

from __future__ import annotations

from pathlib import Path

import pytest
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

from rag import bm25, build_prompt, classify, load_passages, route

PASSAGES = load_passages(Path(__file__).with_name("corpus.md"))


def answers(rel=0.0, evid=0.0, contra=0.0, inject=0.0) -> ClassifierResponse:
    values = {
        "is_relevant": rel,
        "contains_answer_evidence": evid,
        "contradicts_query_premise": contra,
        "contains_prompt_injection": inject,
    }
    return ClassifierResponse.model_validate(
        {"model": "d3-flash", "answers": {k: {"type": "noul", "noul": v} for k, v in values.items()}}
    )


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        (dict(rel=0.99, evid=0.99, inject=0.95), "excluded_injection"),  # injection beats evidence
        (dict(rel=0.99, evid=0.99, contra=0.93), "conflict"),  # contradiction beats evidence
        (dict(rel=0.2, contra=0.93), "conflict"),  # a premise denial need not look relevant
        (dict(rel=0.2, evid=0.9), "excluded_off_topic"),
        (dict(rel=0.99, evid=0.99), "evidence"),
        (dict(rel=0.6, evid=0.3), "excluded_no_evidence"),
        (dict(rel=0.2, contra=0.70), "excluded_off_topic"),  # 0.70 is below the tuned 0.80
    ],
)
def test_route_first_match_wins(scores: dict, expected: str) -> None:
    assert route(answers(**scores)) == expected


def test_corpus_loads_every_section() -> None:
    assert len(PASSAGES) == 12
    assert PASSAGES[0]["id"] == "AUTH-01"
    assert "15분" in PASSAGES[0]["text"]


def test_bm25_ranks_on_topic_first_and_drops_non_matches() -> None:
    hits = bm25("로그아웃하면 리프레시 토큰은 어떻게 되나?", PASSAGES, k=12)
    assert hits[0]["id"] == "AUTH-03"
    assert "OPS-03" not in {p["id"] for p in hits}


def test_prompt_keeps_conflicts_apart_and_drops_excluded_passages() -> None:
    by_id = {p["id"]: p for p in PASSAGES}
    picks = {"AUTH-01": answers(contra=0.93), "AUTH-03": answers(rel=0.99, evid=0.99),
             "FORUM-02": answers(inject=1.0)}
    classifier = RunnableLambda(
        lambda request: next(a for pid, a in picks.items() if by_id[pid]["text"] == request["state"]["passage"])
    )
    routed = classify(classifier, "질문", [by_id[pid] for pid in picks])
    prompt = build_prompt("질문", routed)

    evidence, conflict = prompt.split("채택 근거:")[1].split("충돌 근거:")
    assert "[AUTH-03]" in evidence and "[AUTH-01]" not in evidence
    assert "[AUTH-01]" in conflict
    assert by_id["FORUM-02"]["text"] not in prompt
