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
    assert set(samples) == {
        "discovery-review", "rag-passage-filter", "tool-call-gate", "citation-check", "decision-calibration", "effort-router",
        "completion-check",
    }
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


def gate_answers(request) -> ClassifierResponse:
    risky = "id_rsa" in request["state"]["args"]
    probs = {"allow": 0.05, "ask": 0.05, "block": 0.9} if risky else {"allow": 0.9, "ask": 0.05, "block": 0.05}
    return response({
        "verdict": {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs, "confidence": 0.9},
        "reads_secrets": {"type": "noul", "noul": 0.9 if risky else 0.0},
        "sends_outbound": {"type": "noul", "noul": 0.0},
        "self_advocating": {"type": "noul", "noul": 0.0},
        "blast_radius": {"type": "score", "score": 0.1, "legend": {0: "r", 1: "e", 2: "h"},
                         "probabilities": {0: 0.9, 1: 0.1, 2: 0.0}, "confidence": 0.9},
    })


class ToolCallingFake(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def test_tool_gate_check_uses_rules_then_model(client) -> None:
    use(gate_answers)
    check = lambda command: client.post("/api/tool-call-gate/check",
                                        json={"task": "정리", "tool": "bash", "args": {"command": command}}).json()
    assert check("rm -rf ~")["source"] == "rule"
    assert check("ls")["action"] == "allow"
    assert check("cat ~/.ssh/id_rsa")["action"] == "block"


def test_tool_gate_agent_reports_each_call(client) -> None:
    use(gate_answers)
    calls = [AIMessage(content="", tool_calls=[{"name": "bash", "args": {"command": c}, "id": c}])
             for c in ("ls", "cat ~/.ssh/id_rsa")]
    app.dependency_overrides[llm] = lambda: ToolCallingFake(messages=iter([*calls, AIMessage(content="보고")]))
    data = client.post("/api/tool-call-gate/agent", json={"task": "정리", "approve": False}).json()
    assert [c["action"] for c in data["calls"]] == ["allow", "block"]
    assert data["answer"] == "보고"


def relation_answers(request) -> ClassifierResponse:
    probs = {"supports": 0.05, "contradicts": 0.9, "says_nothing": 0.05}
    return response({"relation": {"type": "choice", "choice": "contradicts", "probabilities": probs, "confidence": 0.7}})


def test_citation_check_matches_strings_before_the_model(client) -> None:
    use(relation_answers)
    citations = [
        {"id": "a", "claim": "c", "quote": "종이 문서는 분쇄한다.", "section": "1"},
        {"id": "b", "claim": "c", "quote": "없는 문장", "section": "1"},
        {"id": "c", "claim": "c", "quote": "", "section": "6"},
    ]
    results = client.post("/api/citation-check/check", json={"citations": citations}).json()["results"]
    assert [(r["verdict"], r["section"], r["needs_review"]) for r in results] == [
        ("contradicted", "5.2", True), ("fabricated", None, False), ("contradicted", "6", True),
    ]


def test_citation_ask_checks_llm_citations(client) -> None:
    from langchain_core.runnables import RunnableLambda as Lambda

    class StructuredFake:
        def with_structured_output(self, schema):
            return Lambda(lambda _prompt: schema(claims=[{"claim": "c", "quote": "없는 문장", "section": "6"}]))

    use(relation_answers)
    app.dependency_overrides[llm] = StructuredFake
    data = client.post("/api/citation-check/ask", json={"question": "유출 시 할 일은?"}).json()
    assert data["citations"][0]["id"] == "c1" and data["results"][0]["verdict"] == "fabricated"


def first_option(request) -> ClassifierResponse:
    question = request["questions"]["q"]
    if question.type == "noul":
        return response({"q": {"type": "noul", "noul": 0.6}})
    labels = list(question.criteria)
    probs = {k: 0.7 if i == 0 else 0.1 for i, k in enumerate(labels)}
    return response({"q": {"type": "choice", "choice": labels[0], "probabilities": probs, "confidence": 0.5}})


def test_calibration_reports_order_bias(client) -> None:
    use(first_option)
    one = client.post("/api/decision-calibration/one", json={"text": "환불해 주세요"}).json()
    assert [max(p, key=p.get) for p in one["probabilities"]] == [o[0] for o in one["orders"]]

    routing = client.post("/api/decision-calibration/routing").json()
    assert routing["flip_rate"] == 1.0 and routing["position_picks"][0] == 1.0
    sentiment = client.post("/api/decision-calibration/sentiment", json={"limit": 10}).json()
    assert sentiment["n"] == 10 and set(sentiment["methods"]) == {"choice", "choice_reversed", "noul"}


def route_answers(request) -> ClassifierResponse:
    hand = "송금" in request["state"]["message"]
    probs = {"fast": 0.05, "think": 0.9, "handoff": 0.05} if not hand else {"fast": 0.0, "think": 0.0, "handoff": 1.0}
    return response({
        "route": {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs, "confidence": 0.8},
        "needs_access": {"type": "noul", "noul": 0.9 if hand else 0.0},
        "high_stakes": {"type": "noul", "noul": 0.0},
    })


def test_effort_router_routes_turns_and_compares(client) -> None:
    from adapters import effort

    use(route_answers)
    app.dependency_overrides[effort.models] = lambda: {
        name: GenericFakeChatModel(messages=forever("정답: 3")) for name in ("fast", "think")
    }
    rows = client.post("/api/effort-router/route").json()["rows"]
    assert {r["route"] for r in rows} == {"think", "handoff"}

    data = client.post("/api/effort-router/turn",
                       json={"text": "strawberry라는 영어 단어에 r이 몇 번 나오나?", "compare": True}).json()
    assert data["routed"]["tried"] == ["think"] and data["routed"]["correct"] is True
    assert data["key"] == "3" and set(data["baselines"]) == {"fast", "think"}

    handoff = client.post("/api/effort-router/turn", json={"text": "송금해 줘"}).json()
    assert handoff["routed"]["tried"] == ["handoff"] and handoff["baselines"] is None


def completion_answers(request) -> ClassifierResponse:
    done = "#52" in request["state"]["final_response"]
    values = {"claims_done": 0.9, "requirements_met": 0.9 if done else 0.2, "needs_tests": 0.1,
              "tests_cover": 0.1, "needs_human": 0.0}
    return response({k: {"type": "noul", "noul": v} for k, v in values.items()})


def test_completion_check_and_gated_agent(client) -> None:
    use(completion_answers)
    one = client.post("/api/completion-check/check", json={
        "task": "노트", "response": "#41만", "tests": {"passed": 1, "failed": 1}}).json()
    assert one["action"] == "steer" and "실패한 테스트 1개" in one["instruction"]

    app.dependency_overrides[llm] = lambda: GenericFakeChatModel(messages=forever("#41, #52 모두"))
    data = client.post("/api/completion-check/agent", json={"task": "노트를 써라", "lazy": True}).json()
    assert [a["action"] for a in data["attempts"]] == ["steer", "pass"] and data["final"] == "#41, #52 모두"
