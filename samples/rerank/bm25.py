"""Plain BM25 over English text: lowercase word tokens, a short stopword list."""

from __future__ import annotations

import math
import re
from collections import Counter

STOP = set("a an and are as at be by for from has have in is it its of on or that the to was were with which this these".split())


def tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class BM25:
    def __init__(self, docs: dict[str, str], k1: float = 0.9, b: float = 0.4):
        self.ids = list(docs)
        self.tf = [Counter(tokens(docs[i])) for i in self.ids]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / len(self.len)
        df = Counter(t for c in self.tf for t in c)
        n = len(self.ids)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b = k1, b

    def search(self, query: str, k: int) -> list[str]:
        """Top-k document ids; ties break on id so runs replay identically."""
        q = set(tokens(query))
        scores = []
        for i, (tf, length) in enumerate(zip(self.tf, self.len)):
            s = sum(self.idf[t] * tf[t] * (self.k1 + 1) / (tf[t] + self.k1 * (1 - self.b + self.b * length / self.avg))
                    for t in q if t in tf)
            if s > 0:
                scores.append((-s, self.ids[i]))
        return [i for _, i in sorted(scores)[:k]]
