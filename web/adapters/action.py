"""action-picker: run one goal in one environment, or every goal of an environment."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import classifier, load

agent = load("action-picker", "agent")
web_env = load("action-picker", "web_env")
desktop_env = load("action-picker", "desktop_env")
grid_env = load("action-picker", "grid_env")
demo = load("action-picker", "demo")

SUMMARY = "지금 가능한 행동만 후보로 주고 d3-flash가 다음 행동 하나(또는 완료·보류)를 고른다. 웹·설정 앱·격자 세계."

router = APIRouter()

GRID_GOAL = "열쇠를 주워 잠긴 문을 열고 출구(E)에 도착하라. 출구에 서면 끝이다."


def cases(env: str) -> list[dict]:
    """Every goal of an environment as (goal, env object, start state, check, impossible)."""
    if env == "web":
        return [{"goal": g["goal"], "env": web_env.WebEnv(), "start": web_env.START, "impossible": g["expect"] is None,
                 "verify": lambda url, want=g["expect"]: want is not None and web_env.title_of(url) == want,
                 "limit": agent.MAX_STEPS} for g in web_env.GOALS]
    if env == "desktop":
        return [{"goal": g["goal"], "env": desktop_env.DesktopEnv(), "start": desktop_env.START, "impossible": g["expect"] is None,
                 "verify": lambda s, want=g["expect"]: want is not None and s.get(want[0]) == want[1],
                 "limit": agent.MAX_STEPS} for g in desktop_env.GOALS]
    mode = env.split(":")[1]
    return [{"goal": f"{GRID_GOAL} ({name})", "map": name, "env": grid_env.GridEnv(mode), "start": grid_env.start(name),
             "impossible": False, "verify": grid_env.at_exit, "limit": demo.GRID_STEPS} for name in grid_env.MAPS]


ENVS = {"web": "사내 도움말 웹", "desktop": "설정 앱(dry run)", "grid:macro": "격자: 높은 수준 행동",
        "grid:distance": "격자: 한 칸 이동 + 걸음 수", "grid:offset": "격자: 한 칸 이동 + 직선 위치"}


class RunRequest(BaseModel):
    env: str = Field(pattern="^(web|desktop|grid:(macro|distance|offset))$")
    index: int | None = Field(default=None, ge=0, le=20)  # None: every goal


def run_case(decision_model, c: dict) -> dict:
    r = agent.run(decision_model, c["env"], c["goal"], c["start"], c["verify"], max_steps=c["limit"])
    ok = r["stopped"] == agent.NONE if c["impossible"] else r["verified"]
    extra = {"moves": c["env"].moves, "replans": c["env"].replans} if hasattr(c["env"], "replans") else {}
    if hasattr(c["env"], "log"):
        extra["dry_run"] = c["env"].log
    if "map" in c:
        extra["map"] = grid_env.MAPS[c["map"]]
        extra["shortest"] = grid_env.optimal_steps(c["map"])
    return {"goal": c["goal"], "trace": r["trace"], "stopped": r["stopped"], "verified": r["verified"],
            "impossible": c["impossible"], "ok": ok, **extra}


@router.get("/setup")
def setup() -> dict:
    return {"envs": ENVS, "goals": {k: [c["goal"] for c in cases(k)] for k in ENVS}, "confident": agent.CONFIDENT}


@router.post("/run")
def run(body: RunRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    all_cases = cases(body.env)
    if body.index is not None:
        if body.index >= len(all_cases):
            raise HTTPException(404, "없는 목표다.")
        all_cases = [all_cases[body.index]]
    return {"runs": [run_case(decision_model, c) for c in all_cases]}
