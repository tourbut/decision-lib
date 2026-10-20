"""code-judge: search this repo's samples by behaviour, or run the review checklist on a diff."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import classifier, load

search_mod = load("code-judge", "search")
review_mod = load("code-judge", "review")
QUESTIONS = load("code-judge", "questions").QUESTIONS
DIFFS = load("code-judge", "diffs").DIFFS

LABELS = {"injection": "주입", "secret": "비밀 하드코딩", "error_handling": "오류 삼킴",
          "resource_leak": "자원 누수", "sensitive_log": "민감 정보 로그"}

SUMMARY = "질문으로 이 레포의 샘플 코드를 폴더 → 선언 순서로 찾고, diff는 체크리스트 5개로 판정한다."

router = APIRouter()


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)


class ReviewRequest(BaseModel):
    diff: str = Field(min_length=1, max_length=20000)


@router.get("/setup")
def setup() -> dict:
    folders = search_mod.index()
    return {"questions": QUESTIONS, "diffs": DIFFS, "checklist": review_mod.CHECKLIST, "labels": LABELS, "flag_at": review_mod.FLAG_AT,
            "folders": len(folders), "decls": sum(len(f["decls"]) for f in folders.values())}


@router.post("/search")
def search(body: SearchRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    folders = search_mod.index()  # rebuilt per call: the samples change while you work
    out = search_mod.search(decision_model, body.question, folders)
    return {**out, "keyword": search_mod.keyword_search(body.question, folders)}


@router.post("/review")
def review(body: ReviewRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return review_mod.review(decision_model, body.diff)


@router.post("/review/eval")
def review_eval(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    return {"rows": [{**d, **review_mod.review(decision_model, d["diff"])} for d in DIFFS]}
