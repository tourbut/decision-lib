"""many-options: suggest a skill, or pick a time zone through regions; measure either set."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import classifier, load

pick = load("many-options", "pick")
skills = load("many-options", "skills")
zones = load("many-options", "zones")
demo = load("many-options", "demo")
DESCRIPTIONS = {name: desc for name, (_, desc) in skills.SKILLS.items()}
GROUPS = zones.catalog()

SUMMARY = "스킬 24개 중 최대 1개를 추천하고, 255개를 넘는 시간대 448개는 지역을 먼저 골라 두 단계로 고른다."

router = APIRouter()


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


@router.get("/setup")
def setup() -> dict:
    return {
        "skills": skills.SKILLS, "categories": skills.CATEGORIES, "skill_requests": skills.REQUESTS,
        "zone_requests": zones.REQUESTS, "regions": zones.REGIONS,
        "zone_count": sum(len(v) for v in GROUPS.values()), "thresholds": pick.THRESHOLDS,
    }


@router.post("/skill")
def skill(body: TextRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return pick.suggest(decision_model, body.text, DESCRIPTIONS)


@router.post("/skill/eval")
def skill_eval(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    rows = []
    for r in skills.REQUESTS:
        s = pick.suggest(decision_model, r["text"], DESCRIPTIONS)
        rows.append({**r, **s, "stage1_pick": pick.stage1_only(s["stage1"])})
    return {"rows": rows}


@router.post("/zone")
def zone(body: TextRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return pick.hierarchical_choice(decision_model, body.text, GROUPS, zones.REGIONS, demo.ZONE_ASK)


@router.post("/zone/eval")
def zone_eval(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return {"rows": [{**r, **pick.hierarchical_choice(decision_model, r["text"], GROUPS, zones.REGIONS, demo.ZONE_ASK)}
                     for r in zones.REQUESTS]}
