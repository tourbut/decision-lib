"""Offline tests: the index, the two-stage search plumbing, hunks, and the checklist."""

from __future__ import annotations

from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

from diffs import DIFFS
from questions import QUESTIONS
from review import CHECKLIST, hunks, review
from search import index, keyword_search, search

FOLDERS = index()


def test_index_covers_samples_but_not_tests_or_itself() -> None:
    ids = {d["id"] for f in FOLDERS.values() for d in f["decls"]}
    assert "code-judge" not in FOLDERS and not any("/test_" in i for i in ids)
    assert all(a in ids for q in QUESTIONS for a in q["answers"])
    assert "screenshot-check/check.py:ImageClassifier._payload" in ids  # methods are indexed too


def pick(target_folder: str, target_decl: str):
    def answer(request) -> ClassifierResponse:
        labels = list(request["questions"]["q"].criteria)
        want = target_folder if target_folder in labels else target_decl
        probs = {k: (0.9 if k == want else 0.1 / (len(labels) - 1)) for k in labels}
        return ClassifierResponse.model_validate({"model": "stub", "answers": {
            "q": {"type": "choice", "choice": want, "probabilities": probs, "confidence": 0.9}}})
    return RunnableLambda(answer)


def test_search_returns_path_line_and_excerpt() -> None:
    out = search(pick("rerank", "rerank/rerank.py:rrf"), "순위 합치기", FOLDERS)
    top = out["results"][0]
    assert out["folders"] == ["rerank"] and top["id"] == "rerank/rerank.py:rrf"
    assert top["path"] == "samples/rerank/rerank.py" and top["line"] > 0 and top["excerpt"].startswith("def rrf")


def test_keyword_baseline_matches_words_only() -> None:
    assert any(i.startswith("rerank/metrics.py") for i in keyword_search("ndcg recall", FOLDERS))


def test_hunks_split_per_file() -> None:
    two = DIFFS[0]["diff"] + DIFFS[1]["diff"]
    assert len(hunks(two)) == 2 and len(hunks(DIFFS[0]["diff"])) == 1


def test_review_flags_the_strongest_hunk() -> None:
    def answer(request) -> ClassifierResponse:
        secret = "sk_live" in request["state"]["diff"]
        return ClassifierResponse.model_validate({"model": "stub", "answers": {
            k: {"type": "noul", "noul": 0.95 if (k == "secret" and secret) else 0.05} for k in CHECKLIST}})
    out = review(RunnableLambda(answer), DIFFS[0]["diff"] + DIFFS[1]["diff"])
    assert out["flags"] == ["secret"] and out["hunks"] == 2
