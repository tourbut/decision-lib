"""rag-passage-filter: retrieve, classify each passage, optionally generate the answer."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import SAMPLES_DIR, classifier, llm, load

rag = load("rag-passage-filter", "rag")
PASSAGES = rag.load_passages(SAMPLES_DIR / "rag-passage-filter" / "corpus.md")
EXAMPLES = list(load("rag-passage-filter", "demo").QUERIES)

SUMMARY = "검색 문단마다 관련성·근거·전제 충돌·인젝션을 판정해 채택·충돌·제외로 나눈 뒤 답한다."

router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=6, ge=1, le=12)
    generate: bool = True


@router.get("/setup")
def setup() -> dict:
    return {"examples": EXAMPLES, "passages": PASSAGES, "thresholds": rag.THRESHOLDS}


@router.post("/query")
def query(
    body: QueryRequest,
    decision_model: Annotated[object, Depends(classifier)],
    generator: Annotated[object, Depends(llm)],
) -> dict:
    routed = rag.classify(decision_model, body.query, rag.bm25(body.query, PASSAGES, body.top_k))
    answer = None
    if body.generate and routed:
        answer = str(generator.invoke(rag.build_prompt(body.query, routed)).content)
    return {
        "passages": [
            {**p, "route": r, "scores": {k: v.noul for k, v in answers.nouls.items()}}
            for p, answers, r in routed
        ],
        "answer": answer,
        "thresholds": rag.THRESHOLDS,
    }
