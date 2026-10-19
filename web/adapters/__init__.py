"""Shared plumbing for sample adapters: import sample modules by path, build models."""

from __future__ import annotations

import importlib.util
import os
import sys
from functools import cache
from pathlib import Path
from types import ModuleType

from langchain_openai import ChatOpenAI
from langchain_typesafe import TypeSafeClassifier

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"


def load(sample: str, module: str) -> ModuleType:
    """Import `samples/<sample>/<module>.py` under a unique name; samples reuse names
    like `demo` and `corpus`, so plain sys.path imports would collide."""
    name = f"sample_{sample.replace('-', '_')}_{module}"
    if name in sys.modules:
        return sys.modules[name]
    folder = SAMPLES_DIR / sample
    spec = importlib.util.spec_from_file_location(name, folder / f"{module}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    sys.path.insert(0, str(folder))  # the sample's own sibling imports (e.g. `from corpus import`)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(folder))
    return mod


@cache
def classifier() -> TypeSafeClassifier:
    return TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )


@cache
def llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ["LOCAL_LLM_MODEL"],
        base_url=os.environ["LOCAL_LLM_URL"],
        api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local",
        max_tokens=2000,
        temperature=0,
        # The local model reasons by default; samples need only the final text.
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
