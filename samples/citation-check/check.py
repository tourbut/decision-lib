"""Citation check: is the quote in the source, and does its section back the claim?

1. A plain string match looks for the quote. A quote that is not there is fabricated,
   and no model is called.
2. One Choice question reads the section that holds the quote (or the cited section,
   for a claim with no quote) and says whether it supports, contradicts, or says
   nothing about the claim.
3. Confidence below AUTO_ACCEPT sends the verdict to a human review queue.

"verified" describes the claim against this source only. It says nothing about whether
the source itself is true or current.

Adapted from https://docs.typesafe.ai/cookbooks/citation_check
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse, Question
from pydantic import BaseModel, Field

Verdict = Literal["verified", "contradicted", "unsupported", "fabricated"]

AUTO_ACCEPT = 0.8  # the cookbook's starting point; lower it as trust in the model grows

QUESTIONS: dict[str, Question] = {
    "relation": Choice(
        instructions="How does the section relate to the claim?",
        criteria={
            "supports": "The section states the claim or directly implies that it is true",
            "contradicts": "The section states the opposite of the claim or implies it is false",
            "says_nothing": "The section does not address what the claim asserts, either way",
        },
    ),
}

RELATION_TO_VERDICT: dict[str, Verdict] = {
    "supports": "verified",
    "contradicts": "contradicted",
    "says_nothing": "unsupported",
}


class Citation(TypedDict):
    id: str
    claim: str
    quote: str | None
    section: str


class Result(TypedDict):
    id: str
    verdict: Verdict
    confidence: float | None  # None for fabricated: the string match decided it
    probabilities: dict[str, float]
    section: str | None  # where the quote was found, or the cited section
    needs_review: bool


def load_sections(path: Path) -> dict[str, str]:
    """`## <number> <title>` headings split the source into sections keyed by number."""
    sections = re.split(r"^## ", path.read_text(encoding="utf-8"), flags=re.M)[1:]
    return {s.split(maxsplit=1)[0]: "## " + s.strip() for s in sections}


def normalize(text: str) -> str:
    """Collapse whitespace and fold curly quotes, so a quote matches across line wraps."""
    table = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})
    return re.sub(r"\s+", " ", text.translate(table)).strip()


def find_quote(sections: dict[str, str], quote: str) -> str | None:
    """Number of the first section holding the quote verbatim, or None."""
    needle = normalize(quote)
    return next((n for n, text in sections.items() if needle and needle in normalize(text)), None)


def locate(sections: dict[str, str], citation: Citation) -> str | None:
    """The section the model should read; None means the quote is fabricated. An unknown
    cited section with no quote is also None: there is nothing to check against."""
    if citation["quote"]:
        return find_quote(sections, citation["quote"])
    return citation["section"] if citation["section"] in sections else None


def to_result(citation: Citation, section: str, answers: ClassifierResponse) -> Result:
    relation = answers.choices["relation"]
    return {
        "id": citation["id"],
        "verdict": RELATION_TO_VERDICT[relation.choice],
        "confidence": relation.confidence,
        "probabilities": relation.probabilities,
        "section": section,
        "needs_review": relation.confidence < AUTO_ACCEPT,
    }


def check_all(
    classifier: Runnable[ClassifierRequest, ClassifierResponse],
    sections: dict[str, str],
    citations: list[Citation],
) -> list[Result]:
    """String match for every citation, then one model request per surviving one."""
    found = {c["id"]: locate(sections, c) for c in citations}
    to_ask = [c for c in citations if found[c["id"]]]
    responses = classifier.batch(
        [{"state": {"claim": c["claim"], "section": sections[found[c["id"]]]}, "questions": QUESTIONS} for c in to_ask]
    )
    answers = iter(responses)
    return [
        to_result(c, found[c["id"]], next(answers))
        if found[c["id"]]
        else {"id": c["id"], "verdict": "fabricated", "confidence": None, "probabilities": {},
              "section": None, "needs_review": False}
        for c in citations
    ]


# --- An LLM writes the cited answer this sample checks -------------------------------


class CitedClaim(BaseModel):
    claim: str = Field(description="한 문장짜리 주장")
    quote: str = Field(description="주장의 근거가 된 출처 문장. 원문 그대로 옮긴다")
    section: str = Field(description="인용한 절 번호, 예: 3.1")


class CitedAnswer(BaseModel):
    claims: list[CitedClaim] = Field(min_length=1, max_length=6)


ANSWER_PROMPT = """아래 출처 문서만 근거로 질문에 답하라. 답을 주장 여러 개로 나누고, 주장마다 근거 문장을
출처에서 그대로 옮겨 quote에, 그 절 번호를 section에 적는다.

질문: {question}

출처 문서:
{source}"""


def generate(llm: BaseChatModel, sections: dict[str, str], question: str) -> list[Citation]:
    """The local LLM answers with citations; ids are assigned here so results line up."""
    answer = llm.with_structured_output(CitedAnswer).invoke(
        ANSWER_PROMPT.format(question=question, source="\n\n".join(sections.values()))
    )
    # The LLM sometimes writes "6 유출 대응"; keep only the number so it matches section keys.
    return [{"id": f"c{i}", **c.model_dump(), "section": c.section.strip().split(" ")[0]}
            for i, c in enumerate(answer.claims, 1)]
