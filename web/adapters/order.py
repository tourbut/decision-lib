"""order-sim: dry-run the policies on a synthetic order book. No exchange, no orders."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import classifier, load

market = load("order-sim", "market")
trader = load("order-sim", "trader")

SUMMARY = "합성 주문장에서 블록마다 매수·매도·보류를 고르는 dry run. 늦은 결정·포지션 한도·손실 한도는 코드가 막는다."

router = APIRouter()


class RunRequest(BaseModel):
    blocks: int = Field(default=100, ge=20, le=300)
    seed: int = Field(default=7, ge=0, le=10000)
    budget_ms: int = Field(default=300, ge=10, le=2000)


@router.get("/setup")
def setup() -> dict:
    return {"max_position": trader.MAX_POSITION, "loss_limit": trader.LOSS_LIMIT, "budget_ms": int(trader.BUDGET_SECONDS * 1000)}


@router.post("/run")
def run(body: RunRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    blocks = market.simulate(body.blocks, body.seed)
    budget = body.budget_ms / 1000
    policies = {"always hold": trader.always_hold, "coin flip": trader.coin_flip(body.seed),
                "imbalance rule": trader.imbalance_rule, "d3-flash": trader.model_policy(decision_model)}
    return {"results": {name: trader.run(blocks, p, budget) for name, p in policies.items()}, "blocks": body.blocks}
