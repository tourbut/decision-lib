"""Sample workbench: run every sample in `samples/` from a browser.

Each sample keeps its own code; this app imports it by path and injects the models,
so tests can swap in stubs. Adding a sample means one adapter module in `adapters/`
and one view module in `static/views/`.

Run: uv run uvicorn app:app --port 8300
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_typesafe.client import TypeSafeError
from openai import APIError as LLMError

from adapters import (
    SAMPLES_DIR,
    action,
    calibration,
    citation,
    codejudge,
    completion,
    context,
    discovery,
    effort,
    judges,
    judgment,
    many,
    news,
    order,
    rag,
    rerank,
    screenshot,
    toolgate,
)

load_dotenv(find_dotenv())  # the repo-root .env

STATIC = Path(__file__).with_name("static")
ADAPTERS = {
    "discovery-review": discovery,
    "rag-passage-filter": rag,
    "tool-call-gate": toolgate,
    "citation-check": citation,
    "decision-calibration": calibration,
    "effort-router": effort,
    "completion-check": completion,
    "rerank": rerank,
    "context-gate": context,
    "screenshot-check": screenshot,
    "many-options": many,
    "action-picker": action,
    "judgment-tools": judgment,
    "code-judge": codejudge,
    "news-match": news,
    "order-sim": order,
    "local-judges": judges,
}

app = FastAPI(title="decision-lib samples")
app.include_router(discovery.router, prefix="/api/discovery-review")
app.include_router(rag.router, prefix="/api/rag-passage-filter")
app.include_router(toolgate.router, prefix="/api/tool-call-gate")
app.include_router(citation.router, prefix="/api/citation-check")
app.include_router(calibration.router, prefix="/api/decision-calibration")
app.include_router(effort.router, prefix="/api/effort-router")
app.include_router(completion.router, prefix="/api/completion-check")
app.include_router(rerank.router, prefix="/api/rerank")
app.include_router(context.router, prefix="/api/context-gate")
app.include_router(screenshot.router, prefix="/api/screenshot-check")
app.include_router(many.router, prefix="/api/many-options")
app.include_router(action.router, prefix="/api/action-picker")
app.include_router(judgment.router, prefix="/api/judgment-tools")
app.include_router(codejudge.router, prefix="/api/code-judge")
app.include_router(news.router, prefix="/api/news-match")
app.include_router(order.router, prefix="/api/order-sim")
app.include_router(judges.router, prefix="/api/local-judges")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.middleware("http")
async def revalidate(request: Request, call_next):
    # A dev workbench: always revalidate (ETag) so edited static files show on reload.
    response = await call_next(request)
    response.headers.setdefault("Cache-Control", "no-cache")
    return response


@app.exception_handler(TypeSafeError)
@app.exception_handler(LLMError)
async def model_unreachable(_request: Request, error: Exception) -> JSONResponse:
    # Model servers are external; say which one failed instead of a bare 500.
    which = "로컬 LLM" if isinstance(error, LLMError) else "decision 모델"
    detail = f"{which} 호출에 실패했다: {type(error).__name__}. .env의 접속 정보와 서버 상태를 확인한다."
    return JSONResponse(status_code=502, content={"detail": detail})


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/samples")
def samples() -> list[dict]:
    """Sample list with the title, summary, and mermaid diagrams from each README."""
    out = []
    for sample_id, adapter in ADAPTERS.items():
        readme = (SAMPLES_DIR / sample_id / "README.md").read_text(encoding="utf-8")
        out.append(
            {
                "id": sample_id,
                "title": readme.splitlines()[0].lstrip("# ").strip(),
                "summary": adapter.SUMMARY,
                "diagrams": re.findall(r"```mermaid\n(.*?)```", readme, re.S),
            }
        )
    return out


@app.get("/api/models")
def models() -> dict:
    return {
        "decision": os.environ.get("DECISION_MODEL", "d3-flash"),
        "decision_url": os.environ.get("DECISION_BASE_URL", ""),
        "llm": os.environ.get("LOCAL_LLM_MODEL", ""),
    }
