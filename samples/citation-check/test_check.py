"""Offline tests: string match, verdict mapping, review queue. No model is called."""

from __future__ import annotations

from pathlib import Path

from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

from check import AUTO_ACCEPT, CitedAnswer, check_all, find_quote, generate, load_sections
from citations import CITATIONS

SECTIONS = load_sections(Path(__file__).with_name("source.md"))


def relation(supports: float, contradicts: float, says_nothing: float, confidence: float) -> ClassifierResponse:
    probs = {"supports": supports, "contradicts": contradicts, "says_nothing": says_nothing}
    answer = {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs, "confidence": confidence}
    return ClassifierResponse.model_validate({"model": "d3-flash", "answers": {"relation": answer}})


def recording(answer: ClassifierResponse, seen: list) -> RunnableLambda:
    return RunnableLambda(lambda request: seen.append(request["state"]) or answer)


def test_sections_and_quote_across_line_wrap() -> None:
    assert list(SECTIONS)[:3] == ["1", "2.1", "2.2"] and len(SECTIONS) == 10
    ssn = next(c for c in CITATIONS if c["id"] == "ssn_marketing")
    assert find_quote(SECTIONS, ssn["quote"]) == "2.1"


def test_quote_found_in_other_section_is_read_there() -> None:
    quote = "퇴사자의 권한은 퇴사 당일에 회수한다."
    assert find_quote(SECTIONS, quote) == "3.1"
    seen: list = []
    (r,) = check_all(recording(relation(0.9, 0.05, 0.05, 0.9), seen), SECTIONS,
                     [{"id": "x", "claim": "c", "quote": quote, "section": "6"}])
    assert r["section"] == "3.1" and "퇴사 당일" in seen[0]["section"]


def test_missing_quote_is_fabricated_without_a_model_call() -> None:
    seen: list = []
    planted = [c for c in CITATIONS if c["label"] == "fabricated"]
    results = check_all(recording(relation(1, 0, 0, 1), seen), SECTIONS, planted)
    assert [r["verdict"] for r in results] == ["fabricated", "fabricated"]
    assert seen == [] and not any(r["needs_review"] for r in results)


def test_claim_without_quote_reads_cited_section_and_unknown_section_is_fabricated() -> None:
    seen: list = []
    citations = [
        {"id": "a", "claim": "c", "quote": None, "section": "5.1"},
        {"id": "b", "claim": "c", "quote": None, "section": "9.9"},
    ]
    a, b = check_all(recording(relation(0.1, 0.1, 0.8, 0.9), seen), SECTIONS, citations)
    assert (a["verdict"], a["section"]) == ("unsupported", "5.1") and len(seen) == 1
    assert b["verdict"] == "fabricated"


def test_low_confidence_goes_to_review_and_order_is_kept() -> None:
    answers = iter([relation(0.1, 0.85, 0.05, AUTO_ACCEPT - 0.01), relation(0.95, 0, 0.05, AUTO_ACCEPT)])
    classifier = RunnableLambda(lambda request: next(answers))
    citations = [c for c in CITATIONS if c["id"] in {"cloud_ok", "logs_forever", "db_approval"}]
    results = check_all(classifier, SECTIONS, citations)
    assert [(r["id"], r["verdict"], r["needs_review"]) for r in results] == [
        ("db_approval", "contradicted", True),
        ("logs_forever", "fabricated", False),
        ("cloud_ok", "verified", False),
    ]


def test_generate_numbers_llm_claims() -> None:
    class Stub:
        def with_structured_output(self, schema):
            assert schema is CitedAnswer
            return RunnableLambda(lambda prompt: CitedAnswer(claims=[{"claim": "c", "quote": "q", "section": "6 유출 대응"}]))

    assert generate(Stub(), SECTIONS, "질문") == [{"id": "c1", "claim": "c", "quote": "q", "section": "6"}]
