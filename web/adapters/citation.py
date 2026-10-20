"""citation-check: check labelled or edited citations, or a cited answer from the local LLM."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import SAMPLES_DIR, classifier, llm, load

check = load("citation-check", "check")
CITATIONS = load("citation-check", "citations").CITATIONS
QUESTIONS = load("citation-check", "demo").QUESTIONS
SECTIONS = check.load_sections(SAMPLES_DIR / "citation-check" / "source.md")

SUMMARY = "인용문 실재는 문자열로, 주장과 문맥의 관계는 d3-flash Choice로 확인해 4가지로 판정한다."

router = APIRouter()


class CitationIn(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    claim: str = Field(min_length=1, max_length=500)
    quote: str | None = Field(default=None, max_length=1000)
    section: str = Field(max_length=20)


class CheckRequest(BaseModel):
    citations: list[CitationIn] = Field(min_length=1, max_length=20)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)


@router.get("/setup")
def setup() -> dict:
    return {"citations": CITATIONS, "sections": SECTIONS, "questions": QUESTIONS, "auto_accept": check.AUTO_ACCEPT}


@router.post("/check")
def check_citations(body: CheckRequest, decision_model: Annotated[object, Depends(classifier)]) -> dict:
    citations = [c.model_dump() for c in body.citations]
    for c in citations:
        c["quote"] = c["quote"] or None  # an empty box means "no quote, section only"
    return {"results": check.check_all(decision_model, SECTIONS, citations)}


@router.post("/eval")
def evaluate(decision_model: Annotated[object, Depends(classifier)]) -> dict:
    """Every labelled citation with its result; the view compares verdict and label."""
    return {"results": check.check_all(decision_model, SECTIONS, CITATIONS)}


@router.post("/ask")
def ask(
    body: AskRequest,
    decision_model: Annotated[object, Depends(classifier)],
    model: Annotated[object, Depends(llm)],
) -> dict:
    citations = check.generate(model, SECTIONS, body.question)
    return {"citations": citations, "results": check.check_all(decision_model, SECTIONS, citations)}
