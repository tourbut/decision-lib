"""discovery-review: run a page batch, pause on attorney review, resume with decisions."""

from __future__ import annotations

import uuid
from collections import OrderedDict
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.types import Command
from pydantic import BaseModel, Field

from . import classifier, llm, load

review = load("discovery-review", "review")
corpus = load("discovery-review", "corpus")

SUMMARY = "페이지마다 관련성·특권·개인정보를 판정해 제출·보류·레드랙션·변호사 검토로 보낸다."
MAX_RUNS = 50  # shortcut: runs live in process memory, oldest dropped; use a DB checkpointer to keep them

router = APIRouter()
runs: OrderedDict[str, dict] = OrderedDict()


class Page(BaseModel):
    doc_id: str = Field(min_length=1, max_length=40)
    page: str = Field(min_length=1, max_length=6000)


class RunRequest(BaseModel):
    protocol: str = Field(min_length=1, max_length=2000)
    pages: list[Page] = Field(min_length=1, max_length=20)


class ResumeRequest(BaseModel):
    thread_id: str
    decisions: dict[str, Literal["produce", "withhold"]]


def thresholds() -> dict:
    return {
        "privileged": review.PRIVILEGE_ESCALATION_THRESHOLD,
        "contains_pii": review.PII_REDACTION_THRESHOLD,
        "residual_pii": review.RESIDUAL_PII_THRESHOLD,
        "not_responsive": review.NOT_RESPONSIVE_THRESHOLD,
        "responsive": review.RESPONSIVE_THRESHOLD,
        "responsive_confidence": review.RESPONSIVE_CONFIDENCE_THRESHOLD,
    }


@router.get("/setup")
def setup() -> dict:
    return {
        "protocol": corpus.PROTOCOL,
        "pages": [{"doc_id": p["doc_id"], "page": p["page"], "expect": p["expect"]} for p in corpus.PAGES],
        "thresholds": thresholds(),
    }


def report(thread_id: str, state: dict) -> dict:
    run = runs[thread_id]
    return {
        "thread_id": thread_id,
        "results": state.get("results", []),
        "pending": [{"id": i.id, **i.value} for i in state.get("__interrupt__", [])],
        "scores": run["scores"],
        "thresholds": thresholds(),
    }


@router.post("/run")
def run(
    body: RunRequest,
    decision_model: Annotated[object, Depends(classifier)],
    redaction_model: Annotated[object, Depends(llm)],
) -> dict:
    by_text = {p.page: p.doc_id for p in body.pages}
    scores: dict[str, dict] = {}

    def recording(request):
        response = decision_model.invoke(request)
        state = request["state"]
        if isinstance(state, dict):  # the page classification, not the post-redaction check
            responsive = response.scores["responsive"]
            scores[by_text[state["page"]]] = {
                "privileged": response.nouls["privileged"].noul,
                "contains_pii": response.nouls["contains_pii"].noul,
                "responsive": responsive.score,
                "responsive_confidence": responsive.confidence,
            }
        return response

    # Checkpoints restore only the types the graph stores, not arbitrary classes.
    serde = JsonPlusSerializer(allowed_msgpack_modules=[("langchain_typesafe.types", "ClassifierResponse")])
    graph = review.build_review_graph(
        RunnableLambda(recording), redaction_model, InMemorySaver(serde=serde)
    )
    thread_id = uuid.uuid4().hex
    runs[thread_id] = {"graph": graph, "scores": scores}
    while len(runs) > MAX_RUNS:
        runs.popitem(last=False)

    payload = [{**p.model_dump(), "protocol": body.protocol} for p in body.pages]
    state = graph.invoke({"pages": payload, "results": []}, {"configurable": {"thread_id": thread_id}})
    return report(thread_id, state)


@router.post("/resume")
def resume(body: ResumeRequest) -> dict:
    run = runs.get(body.thread_id)
    if run is None:
        raise HTTPException(404, "실행 기록이 없다. 서버가 재시작됐거나 오래된 실행이다. 다시 실행한다.")
    config = {"configurable": {"thread_id": body.thread_id}}
    pending = {i.id for i in run["graph"].get_state(config).interrupts}
    if not pending or set(body.decisions) != pending:
        raise HTTPException(409, "대기 중인 모든 페이지에 결정을 하나씩 보내야 한다.")
    state = run["graph"].invoke(Command(resume=body.decisions), config)
    return report(body.thread_id, state)
