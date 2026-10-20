"""effort-router: route the labelled turns, or run one turn (optionally next to the baselines)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import classifier, load

router_mod = load("effort-router", "router")
demo = load("effort-router", "demo")
TURNS = load("effort-router", "turns").TURNS
KEYS = {t["text"]: t["answer"] for t in TURNS}

SUMMARY = "턴마다 d3-flash가 추론 끔(fast)·추론 켬(think)·이관(handoff)을 정하고, 답이 잘리면 한 단계 올린다."

router = APIRouter()


def models() -> dict:
    """fast and think variants of the local LLM; tests override this dependency."""
    return demo.local_models()


class TurnRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    compare: bool = False  # also answer with always-fast and always-think


@router.get("/setup")
def setup() -> dict:
    return {"turns": TURNS, "thresholds": router_mod.THRESHOLDS}


@router.post("/route")
def route_all(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return {"rows": [{**t, **router_mod.route_turn(decision_model, t["text"])} for t in TURNS]}


@router.post("/turn")
def turn(
    body: TurnRequest,
    decision_model: Annotated[object, Depends(classifier)],
    llms: Annotated[dict, Depends(models)],
) -> dict:
    agent, middleware = router_mod.build_agent(decision_model, llms)
    routed = router_mod.run_turn(agent, middleware, body.text)
    key = KEYS.get(body.text)
    out = {"routed": routed, "key": key, "baselines": None}
    if body.compare:
        out["baselines"] = {
            name: dict(zip(("answer", "output_tokens", "seconds"), demo.direct(llms[name], body.text)))
            for name in ("fast", "think")
        }
    if key:
        out["routed"]["correct"] = router_mod.correct(routed["answer"], key)
        for b in (out["baselines"] or {}).values():
            b["correct"] = router_mod.correct(b["answer"], key)
    return out
