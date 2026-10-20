"""Rebuild data/scifact_30.json from the full BEIR SciFact download.

Usage: python build_subset.py <path to unzipped scifact/>
Download: https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip

Keeps 30 random test queries (seed 0), each query's BM25 top 30 over the full corpus
(5,183 abstracts), and only the abstracts those lists need, cut to 1,200 characters.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from bm25 import BM25

QUERIES, DEPTH, CHARS = 30, 30, 1200


def main(folder: Path) -> None:
    corpus = {}
    for line in (folder / "corpus.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        corpus[d["_id"]] = {"title": d["title"], "text": d["text"]}
    queries = {(q := json.loads(line))["_id"]: q["text"] for line in (folder / "queries.jsonl").open(encoding="utf-8")}
    relevant: dict[str, set[str]] = {}
    for line in (folder / "qrels" / "test.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        qid, did, _ = line.split("\t")
        relevant.setdefault(qid, set()).add(did)

    index = BM25({i: d["title"] + " " + d["text"] for i, d in corpus.items()})
    qids = sorted(relevant, key=int)
    random.Random(0).shuffle(qids)
    out = {"queries": [], "docs": {}}
    for qid in qids[:QUERIES]:
        candidates = index.search(queries[qid], DEPTH)
        out["queries"].append({"id": qid, "text": queries[qid], "relevant": sorted(relevant[qid]), "bm25": candidates})
        for did in candidates:
            out["docs"][did] = {"title": corpus[did]["title"], "text": corpus[did]["text"][:CHARS]}
    path = Path(__file__).with_name("data") / "scifact_30.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(out['queries'])} queries, {len(out['docs'])} abstracts -> {path}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
