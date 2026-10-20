"""Behaviour-based code search over this repo's samples, as jevgrep does: folder first,
then the declarations inside, judged by the decision model instead of matched by text.

Stage 1: one Choice over the sample folders (each described by its README title line).
Stage 2: one Choice over the functions, classes, and methods of the chosen folder(s),
each shown as name + signature + first docstring line. Results carry path, line, and
the source excerpt; reading and editing them is the calling agent's job.
"""

from __future__ import annotations

import ast
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, TypedDict

from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse

SAMPLES = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", "__pycache__", "code-judge"}
SECOND_FOLDER_BELOW = 0.60  # also search the runner-up folder when the first is unsure
TOP = 3


class Decl(TypedDict):
    id: str  # folder/file.py:Qualified.name
    folder: str
    path: str
    line: int
    summary: str  # what the model reads
    source: str


def _summary(node: ast.AST, qualname: str, source: str) -> str:
    doc = (ast.get_docstring(node) or "").strip().splitlines()
    head = source.splitlines()[0].strip()
    return f"{qualname}: {head}" + (f" — {doc[0]}" if doc else "")


def index(root: Path = SAMPLES) -> dict[str, dict[str, Any]]:
    """{folder: {"about": README title, "decls": [Decl]}} for every sample but this one.
    Tests are left out: they describe behaviour, they do not implement it."""
    folders = {}
    for folder in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in SKIP_DIRS):
        readme = folder / "README.md"
        about = readme.read_text(encoding="utf-8").split("\n\n")[1].strip() if readme.exists() else folder.name
        decls: list[Decl] = []
        for file in sorted(folder.glob("*.py")):
            if file.name.startswith("test_"):
                continue
            text = file.read_text(encoding="utf-8")
            tree = ast.parse(text)

            def walk(nodes, prefix=""):
                for node in nodes:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        qual = f"{prefix}{node.name}"
                        src = ast.get_source_segment(text, node) or ""
                        decls.append({"id": f"{folder.name}/{file.name}:{qual}", "folder": folder.name,
                                      "path": f"samples/{folder.name}/{file.name}", "line": node.lineno,
                                      "summary": _summary(node, qual, src), "source": src})
                        if isinstance(node, ast.ClassDef):
                            walk(node.body, f"{qual}.")
            walk(tree.body)
        folders[folder.name] = {"about": about[:300], "decls": decls}
    return folders


def search(classifier: Runnable[ClassifierRequest, ClassifierResponse], question: str,
           folders: dict[str, dict[str, Any]]) -> dict[str, Any]:
    # The README intro alone lost the folder on 9 of 20 questions; the declaration names
    # tell the model what the code actually contains.
    stage1 = Choice(instructions="Which sample folder most likely contains the code that does this?",
                    criteria={name: f"{f['about']} Declarations: {', '.join(d['id'].split(':')[1] for d in f['decls'])}"[:1500]
                              for name, f in folders.items()})
    fp = classifier.invoke({"state": {"question": question}, "questions": {"q": stage1}}).choices["q"].probabilities
    order = sorted(fp, key=fp.get, reverse=True)
    chosen = order[:2] if fp[order[0]] < SECOND_FOLDER_BELOW else order[:1]

    decls = {d["id"]: d for name in chosen for d in folders[name]["decls"]}
    stage2 = Choice(instructions="Which declaration implements what the question asks about?",
                    criteria={i: d["summary"] for i, d in decls.items()})
    dp = classifier.invoke({"state": {"question": question}, "questions": {"q": stage2}}).choices["q"].probabilities
    hits = sorted(dp, key=dp.get, reverse=True)[:TOP]
    return {"folders": chosen, "folder_probabilities": fp,
            "results": [{**{k: decls[i][k] for k in ("id", "path", "line")}, "probability": dp[i],
                         "excerpt": "\n".join(decls[i]["source"].splitlines()[:12])} for i in hits],
            "chars_sent": sum(len(f["about"]) for f in folders.values()) + sum(len(d["summary"]) for d in decls.values())}


# --- Keyword baseline -----------------------------------------------------------------


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+|[가-힣]+", text.lower())


def keyword_search(question: str, folders: dict[str, dict[str, Any]]) -> list[str]:
    """BM25 over every declaration's source: what a grep-style tool finds from the words."""
    decls = [d for f in folders.values() for d in f["decls"]]
    docs = [Counter(_tokens(d["source"])) for d in decls]
    avg = sum(sum(c.values()) for c in docs) / len(docs)
    df = Counter(t for c in docs for t in c)
    q = set(_tokens(question))

    def bm25(c: Counter) -> float:
        n = sum(c.values())
        return sum(math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5)) * c[t] * 2.2 / (c[t] + 1.2 * (0.25 + 0.75 * n / avg))
                   for t in q if t in c)

    ranked = sorted(zip(decls, docs), key=lambda dc: -bm25(dc[1]))
    return [d["id"] for d, c in ranked[:TOP] if bm25(c) > 0]
