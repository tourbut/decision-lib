"""rerank: rerank one SciFact query (or a typed claim) and show both orders."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import classifier, load

rr = load("rerank", "rerank")
bm25 = load("rerank", "bm25")
QUERIES, DOCS = rr.load()
BY_ID = {q["id"]: q for q in QUERIES}
INDEX = bm25.BM25({i: d["title"] + " " + d["text"] for i, d in DOCS.items()})

SUMMARY = "BM25 후보를 d3-flash Score 루브릭으로 다시 채점해 순서를 바꾸고 SciFact 정답으로 nDCG@10을 잰다."

router = APIRouter()


class RerankRequest(BaseModel):
    query_id: str | None = Field(default=None, max_length=10)
    text: str | None = Field(default=None, max_length=500)  # a typed claim, searched over the subset
    depth: int = Field(default=20, ge=5, le=30)


@router.get("/setup")
def setup() -> dict:
    return {"queries": QUERIES, "docs": len(DOCS)}


@router.post("/query")
def query(body: RerankRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    if body.query_id:
        if body.query_id not in BY_ID:
            raise HTTPException(404, "없는 질의 ID다.")
        q = BY_ID[body.query_id]
        text, candidates, relevant = q["text"], q["bm25"][: body.depth], q["relevant"]
    elif body.text and body.text.strip():
        text, candidates, relevant = body.text, INDEX.search(body.text, body.depth), []
    else:
        raise HTTPException(422, "질의 ID나 문장 중 하나를 보낸다.")
    if not candidates:
        return {"text": text, "rows": [], "rankings": {}, "metrics": None}
    scores = rr.score(decision_model, text, candidates, DOCS)
    ranked = rr.rankings(candidates, scores)
    rows = [{"id": d, **DOCS[d], **s, "relevant": d in relevant} for d, s in zip(candidates, scores)]
    return {"text": text, "rows": rows, "rankings": ranked, "metrics": rr.measure(ranked, relevant) if relevant else None}
