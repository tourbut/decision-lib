"""Offline API tests: stub models are injected, so no model server is needed."""

from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse
from langchain_typesafe.client import TypeSafeAPIConnectionError

from adapters import classifier, llm
from app import app


def forever(text: str) -> Iterator[AIMessage]:
    while True:
        yield AIMessage(content=text)


def response(answers: dict) -> ClassifierResponse:
    return ClassifierResponse.model_validate({"model": "d3-flash", "answers": answers})


def discovery_answers(request) -> ClassifierResponse:
    privileged = 0.9 if "counsel" in request["state"]["page"] else 0.01
    return response({
        "responsive": {"type": "score", "score": 2.0, "legend": {0: "n", 1: "m", 2: "y"},
                       "probabilities": {0: 0.0, 1: 0.05, 2: 0.95}, "confidence": 0.95},
        "privileged": {"type": "noul", "noul": privileged},
        "contains_pii": {"type": "noul", "noul": 0.01},
    })


def rag_answers(request) -> ClassifierResponse:
    injection = 1.0 if "AI 시스템" in request["state"]["passage"] else 0.0
    return response({
        "is_relevant": {"type": "noul", "noul": 0.9},
        "contains_answer_evidence": {"type": "noul", "noul": 0.9},
        "contradicts_query_premise": {"type": "noul", "noul": 0.0},
        "contains_prompt_injection": {"type": "noul", "noul": injection},
    })


@pytest.fixture
def client():
    app.dependency_overrides[llm] = lambda: GenericFakeChatModel(messages=forever("15분이다 [AUTH-01]"))
    yield TestClient(app)
    app.dependency_overrides.clear()


def use(answer_fn) -> None:
    app.dependency_overrides[classifier] = lambda: RunnableLambda(answer_fn)


def test_samples_list_includes_readme_diagrams(client) -> None:
    samples = {s["id"]: s for s in client.get("/api/samples").json()}
    assert set(samples) == {"discovery-review", "rag-passage-filter"}
    assert all(s["diagrams"] for s in samples.values())


def test_discovery_pauses_for_attorney_and_resumes(client) -> None:
    use(discovery_answers)
    pages = [{"doc_id": "CLEAN", "page": "Q3 revenue"}, {"doc_id": "PRIV", "page": "counsel advises"}]
    first = client.post("/api/discovery-review/run", json={"protocol": "Q3", "pages": pages}).json()

    assert first["results"] == [{"doc_id": "CLEAN", "decision": "produce"}]
    (pending,) = first["pending"]
    assert pending["doc_id"] == "PRIV" and "page" not in pending
    assert first["scores"]["PRIV"]["privileged"] == 0.9

    resume = {"thread_id": first["thread_id"], "decisions": {pending["id"]: "withhold"}}
    final = client.post("/api/discovery-review/resume", json=resume).json()
    assert {r["doc_id"]: r["decision"] for r in final["results"]} == {"CLEAN": "produce", "PRIV": "withhold"}
    assert final["pending"] == []


def test_discovery_resume_rejects_unknown_runs_and_partial_decisions(client) -> None:
    use(discovery_answers)
    assert client.post("/api/discovery-review/resume",
                       json={"thread_id": "nope", "decisions": {}}).status_code == 404

    pages = [{"doc_id": "PRIV", "page": "counsel advises"}]
    first = client.post("/api/discovery-review/run", json={"protocol": "Q3", "pages": pages}).json()
    wrong = {"thread_id": first["thread_id"], "decisions": {"not-an-interrupt": "produce"}}
    assert client.post("/api/discovery-review/resume", json=wrong).status_code == 409


def test_rag_query_routes_passages_and_answers(client) -> None:
    use(rag_answers)
    data = client.post("/api/rag-passage-filter/query",
                       json={"query": "액세스 토큰 유효기간은 얼마인가?", "top_k": 12}).json()
    routes = {p["id"]: p["route"] for p in data["passages"]}
    assert routes["FORUM-02"] == "excluded_injection"
    assert routes["AUTH-01"] == "evidence"
    assert data["answer"] == "15분이다 [AUTH-01]"

    quiet = client.post("/api/rag-passage-filter/query", json={"query": "토큰", "generate": False}).json()
    assert quiet["answer"] is None


def test_unreachable_decision_model_returns_502_with_reason(client) -> None:
    def down(_request):
        raise TypeSafeAPIConnectionError("connection refused")

    use(down)
    res = client.post("/api/rag-passage-filter/query", json={"query": "토큰"})
    assert res.status_code == 502
    assert "decision 모델" in res.json()["detail"]
