"""A synthetic order book, one snapshot per block. Nothing here touches a real market.

By construction the next mid-price move follows the book imbalance
(next_move = imbalance * tick + noise with sd 0.3 tick), and the spread is a tenth of a
tick, so a reader of the imbalance has an edge after costs and a coin flip has none.
That makes it possible to check whether the decision model reads the signal at all; it
says nothing about real markets.
"""

from __future__ import annotations

import random
from typing import TypedDict


class Block(TypedDict):
    n: int
    mid: float
    spread: float
    bid_depth: float
    ask_depth: float
    imbalance: float  # (bid - ask) / (bid + ask), -1..1
    last_moves: list[float]  # last five mid-price changes, oldest first


def simulate(blocks: int = 200, seed: int = 7, tick: float = 0.01, start: float = 1.0) -> list[Block]:
    rng = random.Random(seed)
    mid, moves, out = start, [0.0] * 5, []
    for n in range(blocks):
        bid = rng.uniform(50, 150)
        ask = rng.uniform(50, 150)
        imbalance = (bid - ask) / (bid + ask)
        out.append({"n": n, "mid": round(mid, 5), "spread": round(tick * 0.1 * rng.choice([1, 1, 2]), 5),
                    "bid_depth": round(bid, 1), "ask_depth": round(ask, 1), "imbalance": round(imbalance, 3),
                    "last_moves": [round(m, 5) for m in moves[-5:]]})
        move = imbalance * tick + rng.gauss(0, tick * 0.3)
        mid += move
        moves.append(move)
    return out
