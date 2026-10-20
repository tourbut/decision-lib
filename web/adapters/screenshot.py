"""screenshot-check: judge a labelled page or an uploaded screenshot, or measure all pages."""

from __future__ import annotations

import base64
import binascii
import os
from functools import cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import load

check = load("screenshot-check", "check")
PAGES = load("screenshot-check", "pages").PAGES
BY_ID = {p["id"]: p for p in PAGES}
MAX_IMAGE = 3_000_000  # bytes after decoding

SUMMARY = "화면 캡처에서 브랜드와 비밀번호 입력을 판정하고, URL이 그 브랜드의 공식 호스트인지 코드로 확인해 사칭을 찾는다."

router = APIRouter()


@cache
def image_classifier():
    """The sample's classifier that sends images; tests override this dependency."""
    return check.ImageClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )


class CheckRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    page_id: str | None = Field(default=None, max_length=60)
    image_base64: str | None = Field(default=None, max_length=4_100_000)  # an uploaded PNG/JPEG
    mode: str = Field(default="image", pattern="^(image|text)$")


@router.get("/setup")
def setup() -> dict:
    return {"pages": [{k: p[k] for k in ("id", "url", "label", "text")} for p in PAGES], "brands": check.BRANDS}


@router.get("/shot/{page_id}")
def shot(page_id: str) -> FileResponse:
    if page_id not in BY_ID:
        raise HTTPException(404, "없는 페이지다.")
    return FileResponse(check.SHOTS / f"{page_id}.png", media_type="image/png")


@router.post("/check")
def check_one(body: CheckRequest, decision_model: Annotated[object, Depends(image_classifier)]) -> dict:
    page = BY_ID.get(body.page_id or "")
    if body.image_base64:
        try:
            image = base64.b64decode(body.image_base64, validate=True)
        except binascii.Error:
            raise HTTPException(422, "이미지가 base64가 아니다.") from None
        if len(image) > MAX_IMAGE:
            raise HTTPException(413, "이미지는 3MB 이하로 올린다.")
        if not image.startswith((b"\x89PNG", b"\xff\xd8")):
            raise HTTPException(422, "PNG나 JPEG만 받는다.")
        return check.check(decision_model, body.url, "image", image=image)
    if not page:
        raise HTTPException(422, "page_id나 image_base64 중 하나를 보낸다.")
    if body.mode == "text":
        return check.check(decision_model, body.url, "text", text=page["text"])
    return check.check(decision_model, body.url, "image", image=check.shot(page["id"]))


@router.post("/eval")
def evaluate(decision_model: Annotated[object, Depends(image_classifier)]) -> dict:
    rows = []
    for p in PAGES:
        image = check.check(decision_model, p["url"], "image", image=check.shot(p["id"]))
        text = check.check(decision_model, p["url"], "text", text=p["text"])
        rows.append({"id": p["id"], "url": p["url"], "label": p["label"], "image": image, "text": text})
    return {"rows": rows}
