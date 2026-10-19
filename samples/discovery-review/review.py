"""Page-level e-discovery review built on LangGraph and a decision model.

Each page is classified once against the review protocol, then routed by plain Python
to exactly one disposition: attorney review, redaction, production, or withholding.
Pages that are redacted are classified again, and any residual personal information
sends them to attorney review instead of production.

Dependencies (classifier, redaction model, checkpointer) are injected by
`build_review_graph` so the graph can be exercised without network access.

Adapted from https://gist.github.com/sydney-runkle/a632ba4ea0b2b72501dfa4b6ab2a7d8a
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_typesafe import (
    ClassifierRequest,
    ClassifierResponse,
    Noul,
    NoulCriteria,
    Question,
    Score,
)
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, interrupt

Disposition = Literal["produce", "withhold", "attorney_review"]

# --- Review policy -----------------------------------------------------------------

PII_QUESTION = Noul(
    instructions=(
        "Does this page contain personal information such as contact details, "
        "account numbers, or health information?"
    ),
)

QUESTIONS: dict[str, Question] = {
    "responsive": Score(
        instructions=(
            "How relevant is this page to the matter described in the review protocol?"
        ),
        criteria=[
            "Not responsive: unrelated to the matter.",
            "Possibly responsive: touches on the matter indirectly.",
            "Responsive: directly concerns the matter.",
        ],
    ),
    "privileged": Noul(
        instructions=(
            "Was this page written by or to a lawyer, or does it convey a lawyer's "
            "legal advice? Answer no for ordinary business, finance, or accounting "
            "discussion, even when the subject is litigation-sensitive."
        ),
        criteria=NoulCriteria(
            true=(
                "A named attorney is the author or recipient, or the text relays "
                "legal advice or litigation strategy."
            ),
            false=(
                "Business, finance, operations, or accounting content with no "
                "attorney involved -- including discussion of restatements, audits, "
                "or regulatory exposure."
            ),
        ),
    ),
    "contains_pii": PII_QUESTION,
}

# Producing a privileged page is far costlier than an unnecessary attorney review, so
# the bar for escalation is deliberately low.
PRIVILEGE_ESCALATION_THRESHOLD = 0.2
PII_REDACTION_THRESHOLD = 0.5
# A redacted page that still looks like it holds PII must not be produced unchecked.
RESIDUAL_PII_THRESHOLD = 0.5
# `Score.score` is an expected value over the rubric, not a discrete level, so
# responsiveness is read as bands: below 0.5 is decisively not responsive, above
# 1.5 is decisively responsive, and the span between is the ambiguous middle.
NOT_RESPONSIVE_THRESHOLD = 0.5
RESPONSIVE_THRESHOLD = 1.5
# Confidence on a Score question measures how concentrated the rubric distribution
# is. A page sitting between two levels scores low confidence even when the model is
# perfectly clear it is responsive, so confidence only gates the decisive bands.
RESPONSIVE_CONFIDENCE_THRESHOLD = 0.7

REDACTION_PROMPT = (
    "Return the page text with every piece of personal information replaced by the "
    "literal token [REDACTED]. Remove the underlying characters; do not mask, "
    "abbreviate, or summarize them. Preserve all other text exactly. Output only the "
    "page text.\n\nPAGE:\n"
)


class PageState(TypedDict, total=False):
    """State for one page moving through review."""

    doc_id: str
    page: str
    protocol: str
    answers: ClassifierResponse
    residual_pii: float
    results: Annotated[list[dict], operator.add]


class BatchState(TypedDict):
    """State for a batch of pages fanned out to the page subgraph."""

    pages: list[dict]
    results: Annotated[list[dict], operator.add]


def build_review_graph(
    classifier: Runnable[ClassifierRequest, ClassifierResponse],
    redaction_model: BaseChatModel,
    checkpointer: BaseCheckpointSaver,
) -> Runnable:
    """Compile the batch review graph.

    Args:
        classifier: Decision-model classifier (or any runnable with the same contract).
        redaction_model: Chat model used only for pages that need redaction.
        checkpointer: Persistence backing the human-in-the-loop interrupts.

    Returns:
        Compiled graph accepting `BatchState` and returning accumulated results.
    """

    def classify(state: PageState) -> dict:
        # The protocol travels with the page so every question sees the matter.
        response = classifier.invoke(
            {
                "state": {"protocol": state["protocol"], "page": state["page"]},
                "questions": QUESTIONS,
            }
        )
        return {"answers": response}

    def route(state: PageState) -> Disposition | Literal["redact"]:
        answers = state["answers"]
        privileged = answers.nouls["privileged"].noul
        responsive = answers.scores["responsive"]

        if privileged > PRIVILEGE_ESCALATION_THRESHOLD:
            return "attorney_review"
        if responsive.score < NOT_RESPONSIVE_THRESHOLD:
            return "withhold"
        if (
            responsive.score < RESPONSIVE_THRESHOLD
            or responsive.confidence < RESPONSIVE_CONFIDENCE_THRESHOLD
        ):
            return "attorney_review"
        if answers.nouls["contains_pii"].noul > PII_REDACTION_THRESHOLD:
            return "redact"
        return "produce"

    def attorney_review(state: PageState) -> dict:
        answers = state["answers"]
        # Send the reviewer scores and the document ID only -- never the page text,
        # which would copy privileged content into the checkpoint's interrupt payload.
        decision: Disposition = interrupt(
            {
                "doc_id": state["doc_id"],
                "privileged": answers.nouls["privileged"].noul,
                "responsive_score": answers.scores["responsive"].score,
                "responsive_confidence": answers.scores["responsive"].confidence,
                "residual_pii": state.get("residual_pii"),
            }
        )
        return {"results": [{"doc_id": state["doc_id"], "decision": decision}]}

    def redact(state: PageState) -> dict:
        # Only pages that actually need redaction ever reach a generative model.
        redacted = str(redaction_model.invoke(REDACTION_PROMPT + state["page"]).content)
        check = classifier.invoke(
            {"state": redacted, "questions": {"contains_pii": PII_QUESTION}}
        )
        residual = check.nouls["contains_pii"].noul
        if residual > RESIDUAL_PII_THRESHOLD:
            return {"residual_pii": residual}
        result = {"doc_id": state["doc_id"], "decision": "produce", "page": redacted}
        return {"residual_pii": residual, "results": [{**result, "redacted": True}]}

    def after_redact(state: PageState) -> Literal["attorney_review", "__end__"]:
        if state["residual_pii"] > RESIDUAL_PII_THRESHOLD:
            return "attorney_review"
        return END

    def label(decision: Disposition):
        def _label(state: PageState) -> dict:
            return {"results": [{"doc_id": state["doc_id"], "decision": decision}]}

        return _label

    page = StateGraph(PageState)
    page.add_node("classify", classify)
    page.add_node("attorney_review", attorney_review)
    page.add_node("redact", redact)
    page.add_node("produce", label("produce"))
    page.add_node("withhold", label("withhold"))
    page.add_edge(START, "classify")
    page.add_conditional_edges(
        "classify", route, ["attorney_review", "redact", "produce", "withhold"]
    )
    page.add_conditional_edges("redact", after_redact, ["attorney_review", END])
    for node in ("attorney_review", "produce", "withhold"):
        page.add_edge(node, END)

    def fan_out(state: BatchState) -> list[Send]:
        return [Send("review_page", p) for p in state["pages"]]

    batch = StateGraph(BatchState)
    batch.add_node("review_page", page.compile())
    batch.add_conditional_edges(START, fan_out, ["review_page"])
    batch.add_edge("review_page", END)
    return batch.compile(checkpointer=checkpointer)
