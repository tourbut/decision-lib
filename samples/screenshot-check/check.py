"""Screenshot check: is this login page impersonating a brand?

The decision model looks at the page (a screenshot, or only its extracted text for the
baseline) and answers two questions: which brand the page presents itself as, and whether
it asks for a password. Plain code then checks the
URL's host against the brand registry, which the model never decides:

- no password form → other
- password form, no recognizable brand → other (an unbranded login is not impersonation)
- password form + brand + host in the brand's registry → legit
- password form + brand + any other host → phishing

Based on Cloudflare Clef's rendered-page domain classification (#22) and the Decision 3.0
multimodal guardrail examples (#26).

The local /v1/systemone server reads images from a top-level `images` array. An image
put inside `state` (as a LangChain image block) is serialized as base64 text: requests
took 15-30 seconds, the answers ignored the picture, and the server was restarted
during that run. ImageClassifier adds the array.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Literal, TypedDict
from urllib.parse import urlparse

from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse, Noul, Question, TypeSafeClassifier
from langchain_typesafe.client import TypeSafeError

from pages import BRANDS

Label = Literal["legit", "phishing", "other", "unknown"]
Mode = Literal["image", "text"]
SHOTS = Path(__file__).with_name("shots")

QUESTIONS: dict[str, Question] = {
    "brand": Choice(
        instructions="Whose logo or company name appears on this page?",
        criteria={**{b: f"The {b} logo or name appears." for b in BRANDS}, "none": "None of these companies appears."},
    ),
    "password_form": Noul(instructions="Does the page ask the visitor to type a password?"),
}

THRESHOLDS = {"password_form": 0.50, "brand_min": 0.50}


class Verdict(TypedDict):
    label: Label
    reason: str
    brand: str | None
    host: str
    scores: dict[str, float]


class ImageClassifier(TypeSafeClassifier):
    """TypeSafeClassifier that also sends `request["images"]` (data URLs) as the server's
    top-level `images` array.

    shortcut: overrides the private _payload of langchain-typesafe 0.0.1a3 (pinned);
    drop this class once the client accepts images itself."""

    def _payload(self, request):
        payload = super()._payload(request)
        if request.get("images"):
            payload["images"] = request["images"]
        return payload


def request(mode: Mode, text: str = "", image: bytes | None = None) -> dict:
    """The model never sees the URL: given a lookalike host it named the brand from the
    address alone. The image mode sends only the screenshot; the text mode, what a
    crawler would extract."""
    if mode == "text":
        return {"state": {"page_text": text}, "questions": QUESTIONS}
    data = "data:image/png;base64," + base64.b64encode(image).decode()
    return {"state": "A screenshot of a web page is attached.", "questions": QUESTIONS, "images": [data]}


def decide(url: str, s: dict[str, float]) -> tuple[Label, str, str | None]:
    host = urlparse(url).hostname or ""
    if s["password_form"] < THRESHOLDS["password_form"]:
        return "other", "비밀번호 입력 없음", None
    brand = max([*BRANDS, "none"], key=lambda b: s[f"brand_{b}"])
    if brand == "none" or s[f"brand_{brand}"] < THRESHOLDS["brand_min"]:
        return "other", "알아볼 수 있는 브랜드 없음", None
    if host in BRANDS[brand]:
        return "legit", f"{brand} 공식 호스트", brand
    return "phishing", f"{brand} 로그인인데 공식 호스트가 아님({host})", brand


def check(
    classifier: Runnable[ClassifierRequest, ClassifierResponse],
    url: str,
    mode: Mode,
    text: str = "",
    image: bytes | None = None,
) -> Verdict:
    host = urlparse(url).hostname or ""
    try:
        answers = classifier.invoke(request(mode, text, image))
    except TypeSafeError as e:
        return {"label": "unknown", "reason": f"판정 실패: {type(e).__name__}", "brand": None, "host": host, "scores": {}}
    s = {f"brand_{k}": p for k, p in answers.choices["brand"].probabilities.items()}
    s.update({k: a.noul for k, a in answers.nouls.items()})
    label, reason, brand = decide(url, s)
    return {"label": label, "reason": reason, "brand": brand, "host": host, "scores": s}


def shot(page_id: str) -> bytes:
    return (SHOTS / f"{page_id}.png").read_bytes()
