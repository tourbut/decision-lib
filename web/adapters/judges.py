"""local-judges: the same three judgments from four local methods, for one ticket or all."""

from __future__ import annotations

import os
import time
from functools import cache
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from openai import OpenAI
from pydantic import BaseModel, Field

from . import classifier, load

judges = load("local-judges", "judges")
TICKETS = load("local-judges", "tickets").TICKETS

SUMMARY = "같은 판정(팀·긴급·불만도)을 d3-flash, LLM 확률 직접 읽기, LLM JSON, 소량 라벨 분류기로 내고 비교한다."

router = APIRouter()


@cache
def chat_client() -> tuple[OpenAI, str]:
    """The raw OpenAI client for logprobs; tests override this dependency."""
    return OpenAI(base_url=os.environ["LOCAL_LLM_URL"], api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local"), \
        os.environ["LOCAL_LLM_MODEL"]


class OneRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


def run_all(decision_model, llm: tuple[OpenAI, str], text: str, train: list[dict]) -> dict[str, Any]:
    client, model = llm
    methods = {"d3-flash": lambda: judges.d3(decision_model, text),
               "LLM 확률 읽기": lambda: judges.llm_read(client, model, text),
               "LLM JSON": lambda: judges.llm_json(client, model, text),
               "소량 라벨 NB": lambda: judges.few_label(train, text)}
    out = {}
    for name, call in methods.items():
        started = time.perf_counter()
        judgment = call()
        out[name] = {"judgment": judgment, "answers": judges.answers(judgment), "seconds": time.perf_counter() - started}
    return out


@router.get("/setup")
def setup() -> dict:
    return {"tickets": TICKETS}


@router.post("/one")
def one(body: OneRequest, decision_model: Annotated[object, Depends(classifier)],
        llm: Annotated[tuple, Depends(chat_client)]) -> dict:
    train = [t for t in TICKETS if t["text"] != body.text]
    return {"methods": run_all(decision_model, llm, body.text, train),
            "label": next((t for t in TICKETS if t["text"] == body.text), None)}


@router.post("/eval")
def evaluate(decision_model: Annotated[object, Depends(classifier)], llm: Annotated[tuple, Depends(chat_client)]) -> dict:
    rows = [run_all(decision_model, llm, t["text"], TICKETS[:i] + TICKETS[i + 1:]) for i, t in enumerate(TICKETS)]
    summary = {}
    for name in rows[0]:
        right = {f: sum(r[name]["answers"][f] == t[f] for r, t in zip(rows, TICKETS)) for f in ("dept", "urgent", "frustration")}
        urgent = [r[name]["judgment"]["urgent"] for r in rows]
        summary[name] = {**right, "seconds": sum(r[name]["seconds"] for r in rows) / len(rows),
                         "urgent_auc": None if isinstance(urgent[0], bool) else judges.auc(urgent, [t["urgent"] for t in TICKETS])}
    return {"summary": summary, "n": len(TICKETS), "always_not_urgent": sum(not t["urgent"] for t in TICKETS)}
