"""decision-calibration: order sensitivity for one ticket, or either benchmark."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import classifier, load

bench = load("decision-calibration", "bench")
calib = load("decision-calibration", "calib")
LABELS = load("decision-calibration", "tickets").LABELS

SUMMARY = "선택지 순서를 바꿔 묻고 정확도·ECE·Brier·사람 검토 비율을 재서 판정 확률을 믿어도 되는지 확인한다."

router = APIRouter()


class OneRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class SentimentRequest(BaseModel):
    # 200 reviews x 3 calls is about 70s; the view defaults to fewer.
    limit: int = Field(default=60, ge=10, le=len(bench.NSMC))


@router.get("/setup")
def setup() -> dict:
    return {
        "labels": LABELS,
        "tickets": bench.ROUTING,
        "nsmc_size": len(bench.NSMC),
        "review_thresholds": calib.REVIEW_THRESHOLDS,
    }


@router.post("/one")
def one(body: OneRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    orders = calib.rotations(list(LABELS))
    (per_order,) = calib.ask_choice(decision_model, [body.text], LABELS, calib.TEAM_ASK, orders)
    return {"orders": orders, "probabilities": per_order}


@router.post("/routing")
def routing(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return bench.routing(decision_model, bench.ROUTING)


@router.post("/sentiment")
def sentiment(body: SentimentRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    # nsmc_200.tsv is shuffled, so the first N stay roughly balanced.
    return bench.sentiment(decision_model, bench.NSMC[: body.limit])
