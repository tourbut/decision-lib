"""Tests for the e-discovery review graph.

Routing tests drive a stub classifier so each policy branch is exercised
deterministically. One integration test drives a real `TypeSafeClassifier` over
`httpx2.MockTransport` to prove the request/response wiring, with no network or key.
"""

from __future__ import annotations

import json
from typing import Any, Iterator

import httpx2
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse, TypeSafeClassifier
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from review import build_review_graph

PROTOCOL = "Matter 24-CV-118: all documents concerning Q3 revenue recognition."


def make_answers(
    *,
    responsive: float,
    confidence: float,
    privileged: float,
    pii: float,
) -> ClassifierResponse:
    """Build a `ClassifierResponse` with the shape the graph reads."""
    return ClassifierResponse.model_validate(
        {
            "model": "jev-latest",
            "answers": {
                "responsive": {
                    "type": "score",
                    "score": responsive,
                    "legend": {0: "not", 1: "maybe", 2: "yes"},
                    "probabilities": {0: 0.1, 1: 0.2, 2: 0.7},
                    "confidence": confidence,
                },
                "privileged": {"type": "noul", "noul": privileged},
                "contains_pii": {"type": "noul", "noul": pii},
            },
        }
    )


def stub_classifier(response: ClassifierResponse, residual_pii: float = 0.0):
    """A classifier stand-in: one canned page response, and `residual_pii` for the
    post-redaction check (whose state is the redacted text, not the page dict)."""
    residual = ClassifierResponse.model_validate(
        {"model": "d3-flash", "answers": {"contains_pii": {"type": "noul", "noul": residual_pii}}}
    )
    return RunnableLambda(
        lambda request: residual if isinstance(request["state"], str) else response
    )


def redactor(text: str = "Contact [REDACTED] at [REDACTED].") -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter_forever(text))


def iter_forever(text: str) -> Iterator[AIMessage]:
    while True:
        yield AIMessage(content=text)


def run_batch(classifier, pages: list[dict], model=None) -> tuple[Any, Any, str]:
    graph = build_review_graph(
        classifier=classifier,
        redaction_model=model or redactor(),
        checkpointer=InMemorySaver(),
    )
    thread = "thread-1"
    config = {"configurable": {"thread_id": thread}}
    state = graph.invoke({"pages": pages, "results": []}, config)
    return graph, state, thread


PAGE = {"doc_id": "DOC-001", "page": "Q3 revenue figures.", "protocol": PROTOCOL}


# --- Routing ------------------------------------------------------------------------


def test_clean_responsive_page_is_produced() -> None:
    answers = make_answers(responsive=2.0, confidence=0.95, privileged=0.01, pii=0.02)
    _, state, _ = run_batch(stub_classifier(answers), [PAGE])
    assert state["results"] == [{"doc_id": "DOC-001", "decision": "produce"}]


def test_non_responsive_page_is_withheld() -> None:
    answers = make_answers(responsive=0.1, confidence=0.95, privileged=0.01, pii=0.02)
    _, state, _ = run_batch(stub_classifier(answers), [PAGE])
    assert state["results"] == [{"doc_id": "DOC-001", "decision": "withhold"}]


def test_fractional_score_just_under_threshold_is_withheld() -> None:
    """`score` is an expected value, so 0.49 must withhold -- not equal zero."""
    answers = make_answers(responsive=0.49, confidence=0.95, privileged=0.01, pii=0.02)
    _, state, _ = run_batch(stub_classifier(answers), [PAGE])
    assert state["results"][0]["decision"] == "withhold"


def test_pii_page_is_redacted_before_production() -> None:
    answers = make_answers(responsive=2.0, confidence=0.95, privileged=0.01, pii=0.91)
    _, state, _ = run_batch(stub_classifier(answers), [PAGE])
    (result,) = state["results"]
    assert result["decision"] == "produce"
    assert result["redacted"] is True
    assert result["page"] == "Contact [REDACTED] at [REDACTED]."


def test_redaction_output_replaces_the_original_page_text() -> None:
    """The produced page must not carry the original characters through."""
    secret = "SSN 123-45-6789"
    page = {"doc_id": "DOC-PII", "page": secret, "protocol": PROTOCOL}
    answers = make_answers(responsive=2.0, confidence=0.95, privileged=0.01, pii=0.99)
    _, state, _ = run_batch(stub_classifier(answers), [page])
    assert secret not in state["results"][0]["page"]


def test_redaction_that_leaves_pii_escalates_instead_of_producing() -> None:
    """The decision model re-checks the redacted text; residual PII is never produced."""
    answers = make_answers(responsive=2.0, confidence=0.95, privileged=0.01, pii=0.99)
    graph, state, thread = run_batch(stub_classifier(answers, residual_pii=0.9), [PAGE])
    assert state["results"] == []
    (pending,) = state["__interrupt__"]
    assert pending.value["residual_pii"] == 0.9

    final = graph.invoke(
        Command(resume={pending.id: "withhold"}), {"configurable": {"thread_id": thread}}
    )
    assert final["results"] == [{"doc_id": "DOC-001", "decision": "withhold"}]


@pytest.mark.parametrize(
    ("privileged", "confidence"),
    [(0.25, 0.95), (0.01, 0.5)],
    ids=["privilege_above_threshold", "low_responsive_confidence"],
)
def test_uncertain_pages_escalate_to_attorney_review(
    privileged: float, confidence: float
) -> None:
    answers = make_answers(
        responsive=2.0, confidence=confidence, privileged=privileged, pii=0.0
    )
    _, state, _ = run_batch(stub_classifier(answers), [PAGE])
    assert state["results"] == []
    assert state["__interrupt__"]


def test_privilege_escalation_wins_over_pii_redaction() -> None:
    """A likely-privileged page must never be routed into the redact-and-produce path."""
    answers = make_answers(responsive=2.0, confidence=0.99, privileged=0.9, pii=0.99)
    _, state, _ = run_batch(stub_classifier(answers), [PAGE])
    assert state["results"] == []
    assert state["__interrupt__"]


def test_interrupt_payload_excludes_page_text() -> None:
    secret = "Privileged: counsel advises settlement."
    page = {"doc_id": "DOC-PRIV", "page": secret, "protocol": PROTOCOL}
    answers = make_answers(responsive=2.0, confidence=0.99, privileged=0.9, pii=0.0)
    _, state, _ = run_batch(stub_classifier(answers), [page])
    payload = state["__interrupt__"][0].value
    assert secret not in json.dumps(payload)
    assert payload["doc_id"] == "DOC-PRIV"


# --- Human-in-the-loop resume -------------------------------------------------------


def test_attorney_decision_resumes_and_records_result() -> None:
    answers = make_answers(responsive=2.0, confidence=0.99, privileged=0.9, pii=0.0)
    graph, state, thread = run_batch(stub_classifier(answers), [PAGE])
    config = {"configurable": {"thread_id": thread}}

    interrupt_id = state["__interrupt__"][0].id
    final = graph.invoke(Command(resume={interrupt_id: "withhold"}), config)

    assert final["results"] == [{"doc_id": "DOC-001", "decision": "withhold"}]


def test_batch_fans_out_and_resumes_only_escalated_pages() -> None:
    """Auto-decided pages finish in the first pass; only escalations wait."""
    pages = [
        {"doc_id": "CLEAN", "page": "Q3 revenue.", "protocol": PROTOCOL},
        {"doc_id": "PRIV", "page": "Counsel advises.", "protocol": PROTOCOL},
    ]

    def classify(request) -> ClassifierResponse:
        page_text = request["state"]["page"]
        if "Counsel" in page_text:
            return make_answers(
                responsive=2.0, confidence=0.99, privileged=0.9, pii=0.0
            )
        return make_answers(responsive=2.0, confidence=0.99, privileged=0.0, pii=0.0)

    graph, state, thread = run_batch(RunnableLambda(classify), pages)
    config = {"configurable": {"thread_id": thread}}

    assert state["results"] == [{"doc_id": "CLEAN", "decision": "produce"}]
    assert len(state["__interrupt__"]) == 1

    interrupt_id = state["__interrupt__"][0].id
    final = graph.invoke(Command(resume={interrupt_id: "produce"}), config)

    decisions = {r["doc_id"]: r["decision"] for r in final["results"]}
    assert decisions == {"CLEAN": "produce", "PRIV": "produce"}


# --- Real classifier over a mock transport ------------------------------------------


def test_graph_drives_a_real_typesafe_classifier_over_mock_transport() -> None:
    """Exercises the genuine request payload and response parsing, without network."""
    captured: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx2.Response(
            200,
            json={
                "model": "jev-latest",
                "answers": {
                    "responsive": {
                        "type": "score",
                        "score": 2.0,
                        "legend": {"0": "not", "1": "maybe", "2": "yes"},
                        "probabilities": {"0": 0.01, "1": 0.04, "2": 0.95},
                        "confidence": 0.93,
                    },
                    "privileged": {"type": "noul", "noul": 0.02},
                    "contains_pii": {"type": "noul", "noul": 0.03},
                },
                "usage": {"input_tokens": 120, "output_tokens": 8},
            },
        )

    classifier = TypeSafeClassifier(
        api_key="test-key",
        client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )
    _, state, _ = run_batch(classifier, [PAGE])

    assert state["results"] == [{"doc_id": "DOC-001", "decision": "produce"}]
    assert captured["url"].endswith("/v1/systemone")
    assert captured["body"]["model"] == "jev-latest"
    assert captured["body"]["state"] == {
        "protocol": PROTOCOL,
        "page": "Q3 revenue figures.",
    }
    assert set(captured["body"]["questions"]) == {
        "responsive",
        "privileged",
        "contains_pii",
    }
    assert captured["body"]["questions"]["responsive"]["type"] == "score"
    assert captured["body"]["questions"]["privileged"]["type"] == "noul"


def test_ambiguous_middle_band_escalates_despite_high_confidence() -> None:
    """A page between rubric levels is escalated even when confidence is high."""
    answers = make_answers(responsive=1.2, confidence=0.98, privileged=0.01, pii=0.0)
    _, state, _ = run_batch(stub_classifier(answers), [PAGE])
    assert state["results"] == []
    assert state["__interrupt__"]


def test_decisive_score_survives_mediocre_confidence() -> None:
    """Confidence must not veto a decisively non-responsive score."""
    answers = make_answers(responsive=0.07, confidence=0.55, privileged=0.01, pii=0.0)
    _, state, _ = run_batch(stub_classifier(answers), [PAGE])
    assert state["results"][0]["decision"] == "withhold"
