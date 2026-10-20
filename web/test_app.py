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
        "completion-check", "rerank", "context-gate", "screenshot-check", "many-options", "action-picker", "judgment-tools",
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


def rerank_answers(request) -> ClassifierResponse:
    level = 9.0 if request["state"]["document"].startswith("Relevant") else 1.0
    def answer(n: int, value: float) -> dict:
        return {"type": "score", "score": min(value, n - 1), "legend": {str(i): str(i) for i in range(n)},
                "probabilities": {str(i): 1.0 / n for i in range(n)}, "confidence": 0.5}
    return response({"relevance": answer(10, level), "evidence": answer(3, level)})


def test_rerank_query_and_typed_claim(client) -> None:
    from adapters import rerank

    use(rerank_answers)
    q = rerank.QUERIES[0]
    data = client.post("/api/rerank/query", json={"query_id": q["id"], "depth": 5}).json()
    assert data["rankings"]["bm25"] == q["bm25"][:5] and set(data["metrics"]) >= {"bm25", "relevance"}
    typed = client.post("/api/rerank/query", json={"text": "vitamin D reduces fracture risk", "depth": 5}).json()
    assert typed["metrics"] is None and len(typed["rows"]) <= 5
    assert client.post("/api/rerank/query", json={"query_id": "nope"}).status_code == 404


def context_answers(request) -> ClassifierResponse:
    state = request["state"]
    if "memory_entry" in state:
        return response({"worth": {"type": "noul", "noul": 0.9 if "한국어" in state["memory_entry"] else 0.05}})
    need = 0.9 if state["tool_call"].startswith("read_file") else 0.1
    return response({"keep_result": {"type": "noul", "noul": need}, "keep_call": {"type": "noul", "noul": 0.1}})


def test_context_gate_compaction_and_memory(client) -> None:
    use(context_answers)
    data = client.post("/api/context-gate/compact").json()
    assert len(data["rows"]) == 12 and data["totals"]["need_based"]["chars"] < data["totals"]["original"]["chars"]
    assert data["totals"]["need_based"]["facts"] == 3

    assert client.post("/api/context-gate/memory/check", json={"text": "DB 비밀번호는 hunter2다"}).json()["source"] == "rule"
    rows = client.post("/api/context-gate/memory/eval").json()["rows"]
    assert len(rows) == 30 and any(not r["allow"] for r in rows)

    calls = [{"name": "remember", "args": {"text": "답은 한국어로"}, "id": "m1"}]
    app.dependency_overrides[llm] = lambda: ToolCallingFake(messages=iter([AIMessage("", tool_calls=calls), AIMessage("저장함")]))
    agent = client.post("/api/context-gate/memory/agent", json={"message": "기억해"}).json()
    assert agent["stored"] == ["답은 한국어로"] and agent["log"][0]["allow"] is True


def brand_answers(request) -> ClassifierResponse:
    seen = "images" in request  # only the image path sends the screenshot
    probs = {"MegaBank": 0.95 if seen else 0.0, "KoPay": 0.0, "Cloudnest": 0.0, "ShopMall": 0.0, "none": 0.05 if seen else 1.0}
    return response({
        "brand": {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs, "confidence": 0.9},
        "password_form": {"type": "noul", "noul": 0.95},
    })


def test_screenshot_check_image_text_and_upload(client) -> None:
    from adapters import screenshot

    app.dependency_overrides[screenshot.image_classifier] = lambda: RunnableLambda(brand_answers)
    url = "https://secure-banking-portal.top/"
    image = client.post("/api/screenshot-check/check", json={"url": url, "page_id": "phish-megabank-logo"}).json()
    text = client.post("/api/screenshot-check/check", json={"url": url, "page_id": "phish-megabank-logo", "mode": "text"}).json()
    assert (image["label"], text["label"]) == ("phishing", "other")

    import base64
    png = base64.b64encode((screenshot.check.SHOTS / "legit-megabank.png").read_bytes()).decode()
    legit = client.post("/api/screenshot-check/check", json={"url": "https://login.megabank.co.kr/", "image_base64": png}).json()
    assert legit["label"] == "legit"
    bad = client.post("/api/screenshot-check/check", json={"url": url, "image_base64": base64.b64encode(b"GIF89a").decode()})
    assert bad.status_code == 422
    assert client.get("/api/screenshot-check/shot/nope").status_code == 404
    assert len(client.post("/api/screenshot-check/eval").json()["rows"]) == 16


def first_listed(request) -> ClassifierResponse:
    """Picks the first option of every Choice and calls every Noul a fit."""
    answers = {}
    for name, q in request["questions"].items():
        if q.type == "choice":
            labels = list(q.criteria)
            probs = {k: (0.9 if i == 0 else 0.1 / (len(labels) - 1)) for i, k in enumerate(labels)}
            answers[name] = {"type": "choice", "choice": labels[0], "probabilities": probs, "confidence": 0.9}
        else:
            answers[name] = {"type": "noul", "noul": 0.9}
    return response(answers)


def test_many_options_skill_and_zone(client) -> None:
    use(first_listed)
    skill = client.post("/api/many-options/skill", json={"text": "PDF 합쳐 줘"}).json()
    assert skill["skill"] == "pdf-tools" and len(skill["shortlist"]) == 3
    zone = client.post("/api/many-options/zone", json={"text": "카이로"}).json()
    assert zone["groups"] == ["Africa"] and zone["choice"].startswith("Africa/")
    assert len(client.post("/api/many-options/zone/eval").json()["rows"]) == 40


def macro_first(request) -> ClassifierResponse:
    """Walks the grid's macro plan; anything else is done at once."""
    labels = list(request["questions"]["action"].criteria)
    order = ["pick_key", "open_door", "goto_K", "goto_D", "goto_E", "DONE"]
    want = next(a for a in order if a in labels)
    probs = {k: (0.9 if k == want else 0.1 / (len(labels) - 1)) for k in labels}
    return response({"action": {"type": "choice", "choice": want, "probabilities": probs, "confidence": 0.9}})


def test_action_picker_runs_grid_and_reports(client) -> None:
    use(macro_first)
    runs = client.post("/api/action-picker/run", json={"env": "grid:macro"}).json()["runs"]
    assert [r["ok"] for r in runs] == [True, True, True]
    assert all(r["moves"] + 2 == r["shortest"] for r in runs)
    web = client.post("/api/action-picker/run", json={"env": "web", "index": 7}).json()["runs"][0]
    assert web["impossible"] and web["stopped"] == "DONE" and not web["ok"]  # DONE on a goal the site lacks fails
    assert client.post("/api/action-picker/run", json={"env": "shell"}).status_code == 422


def approve_everything(request) -> ClassifierResponse:
    q = next(iter(request["questions"].values()))
    labels = list(q.criteria)
    probs = {k: (0.9 if i == 0 else 0.1 / (len(labels) - 1)) for i, k in enumerate(labels)}
    return response({name: {"type": "choice", "choice": labels[0], "probabilities": probs, "confidence": 0.9}
                     for name in request["questions"]})


def test_judgment_tools_over_mcp(client) -> None:
    use(approve_everything)
    setup = client.get("/api/judgment-tools/setup").json()
    assert len(setup["tools"]) == 8 and setup["sets"]["approval"] == 10
    r = client.post("/api/judgment-tools/call", json={"tool": "approval", "arguments": {"command": "ls"}}).json()
    assert r["decision"] == "APPROVE" and r["execution_authorized"] is False
    bad = client.post("/api/judgment-tools/call", json={"tool": "approval", "arguments": {"wrong": "x"}})
    assert bad.status_code == 422
    rows = client.post("/api/judgment-tools/eval", json={"tool": "approval"}).json()["rows"]
    assert len(rows) == 10


def test_static_modules_parse(tmp_path) -> None:
    """A syntax error in one view module blanks the whole page; node catches it offline."""
    import shutil
    import subprocess
    from pathlib import Path

    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    for js in Path("static").rglob("*.js"):
        if "vendor" in js.parts:
            continue
        copy = tmp_path / (js.stem + ".mjs")  # .mjs: parse as an ES module
        copy.write_text(js.read_text(encoding="utf-8"), encoding="utf-8")
        result = subprocess.run([node, "--check", str(copy)], capture_output=True, text=True)
        assert result.returncode == 0, f"{js}: {result.stderr}"
