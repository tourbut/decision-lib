"""Offline tests: the host rule, what the model is shown, and the page set."""

from __future__ import annotations

import pytest
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse
from langchain_typesafe.client import TypeSafeAPIConnectionError

from check import SHOTS, ImageClassifier, check, decide, request
from pages import BRANDS, PAGES


def scores(brand: str = "none", password: float = 0.9, p: float = 0.9) -> dict[str, float]:
    s = {f"brand_{b}": (p if b == brand else (1 - p) / len(BRANDS)) for b in [*BRANDS, "none"]}
    return {**s, "password_form": password}


@pytest.mark.parametrize(
    ("url", "s", "label"),
    [
        ("https://login.megabank.co.kr/", scores("MegaBank"), "legit"),
        ("http://megabank-secure-verify.xyz/", scores("MegaBank"), "phishing"),
        ("https://kopay.com.login-check.top/", scores("KoPay"), "phishing"),  # brand host as a prefix only
        ("https://cl0udnest.io/login", scores("Cloudnest"), "phishing"),
        ("https://kopay.com/", scores("KoPay", password=0.2), "other"),
        ("https://unknown.example/", scores("none"), "other"),
        ("https://unknown.example/", scores("KoPay", p=0.4), "other"),  # unsure brand is no brand
    ],
)
def test_decide(url, s, label) -> None:
    assert decide(url, s)[0] == label


def test_model_never_sees_the_url_and_images_go_in_the_array() -> None:
    assert request("text", text="로그인")["state"] == {"page_text": "로그인"}
    image = request("image", image=b"png")
    assert "http" not in str(image["state"]) and image["images"][0].startswith("data:image/png;base64,")
    client = ImageClassifier(model="d3-flash", api_key="local", base_url="http://127.0.0.1:1")
    assert client._payload(image)["images"] == image["images"]
    assert "images" not in client._payload(request("text", text="x"))


def test_check_reports_failure_as_unknown() -> None:
    def down(_):
        raise TypeSafeAPIConnectionError("refused")

    assert check(RunnableLambda(down), "https://kopay.com/", "text", text="x")["label"] == "unknown"


def test_check_end_to_end_with_a_stub() -> None:
    def stub(request) -> ClassifierResponse:
        probs = {**{b: 0.0 for b in BRANDS}, "none": 0.0, "KoPay": 1.0}
        return ClassifierResponse.model_validate({"model": "stub", "answers": {
            "brand": {"type": "choice", "choice": "KoPay", "probabilities": probs, "confidence": 1.0},
            "password_form": {"type": "noul", "noul": 0.95}}})

    v = check(RunnableLambda(stub), "https://pay-verify-center.com/", "text", text="아이디 비밀번호 로그인")
    assert (v["label"], v["brand"], v["host"]) == ("phishing", "KoPay", "pay-verify-center.com")


def test_pages_and_shots() -> None:
    assert len(PAGES) == 16 and all((SHOTS / f"{p['id']}.png").exists() for p in PAGES)
    logo_only = [p for p in PAGES if p["id"].endswith("-logo")]
    assert logo_only and all(b not in p["text"] for p in logo_only for b in BRANDS)
