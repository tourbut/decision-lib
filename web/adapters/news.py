"""news-match: score one feed (the sample's or a pasted one) against the interest profiles."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import classifier, load

match_mod = load("news-match", "match")
feed = load("news-match", "feed")

SUMMARY = "헤드라인마다 관심 주제별 점수(0~3)를 매겨, 기준 이상인 주제의 읽을 목록으로 보낸다."

router = APIRouter()


class MatchRequest(BaseModel):
    headlines: list[Annotated[str, Field(min_length=1, max_length=300)]] | None = Field(default=None, max_length=60)


@router.get("/setup")
def setup() -> dict:
    return {"topics": feed.TOPICS, "headlines": feed.HEADLINES, "threshold": match_mod.THRESHOLD}


@router.post("/match")
def match(body: MatchRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    """Without headlines, the sample feed with its labels; otherwise the pasted ones."""
    texts = body.headlines or [h["text"] for h in feed.HEADLINES]
    labels = None if body.headlines else [h["topics"] for h in feed.HEADLINES]
    out = match_mod.match(decision_model, texts, feed.TOPICS)
    return {"headlines": texts, "labels": labels, **out}
