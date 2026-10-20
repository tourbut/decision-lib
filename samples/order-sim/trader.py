"""Per-block buy / sell / hold decisions on the synthetic book, with the guard rails in code.

DRY RUN ONLY. There is no exchange, no wallet, and no order is sent anywhere. The
decision model only picks a direction; code owns everything that limits damage:

- a decision slower than the block's budget becomes hold (jev-trader holds when late);
- the position stays within ±MAX_POSITION units;
- once the running loss passes LOSS_LIMIT, the position is closed and trading stops for
  the rest of the run;
- an order fills at this block's mid price plus half the spread (a taker fill), and the
  position is marked at each next block's mid.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any, Literal

from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse
from langchain_typesafe.client import TypeSafeError

from market import Block

Side = Literal["buy", "sell", "hold"]
MAX_POSITION = 3
LOSS_LIMIT = -0.05  # in price units over the whole run
BUDGET_SECONDS = 0.30  # the block's decision window

QUESTION = Choice(
    instructions="Given this order book snapshot, which side is the next mid-price move more likely to favour?",
    criteria={
        "buy": "Bids outweigh asks or recent moves point up: the price is more likely to rise.",
        "sell": "Asks outweigh bids or recent moves point down: the price is more likely to fall.",
        "hold": "No clear edge either way.",
    },
)


def observe(block: Block, position: int) -> dict[str, Any]:
    return {"bid_depth": block["bid_depth"], "ask_depth": block["ask_depth"], "imbalance": block["imbalance"],
            "spread": block["spread"], "last_moves": block["last_moves"], "position": position}


def model_policy(classifier: Runnable[ClassifierRequest, ClassifierResponse]) -> Callable[[Block, int], Side]:
    def decide(block: Block, position: int) -> Side:
        try:
            answer = classifier.invoke({"state": observe(block, position), "questions": {"side": QUESTION}})
        except TypeSafeError:
            return "hold"
        return answer.choices["side"].choice
    return decide


def imbalance_rule(block: Block, position: int) -> Side:
    """The baseline that knows how the market was built."""
    if block["imbalance"] > 0.2:
        return "buy"
    if block["imbalance"] < -0.2:
        return "sell"
    return "hold"


def always_hold(block: Block, position: int) -> Side:
    return "hold"


def coin_flip(seed: int = 0) -> Callable[[Block, int], Side]:
    rng = random.Random(seed)
    return lambda block, position: rng.choice(["buy", "sell", "hold"])


def run(blocks: list[Block], policy: Callable[[Block, int], Side], budget: float = BUDGET_SECONDS) -> dict[str, Any]:
    position, cash, stopped_at = 0, 0.0, None
    counts = {"buy": 0, "sell": 0, "hold": 0, "late": 0, "position_cap": 0, "after_stop": 0}
    seconds, right, traded = [], 0, 0
    for block, nxt in zip(blocks, blocks[1:]):
        if stopped_at is not None:
            counts["after_stop"] += 1
            continue
        started = time.perf_counter()
        side = policy(block, position)
        took = time.perf_counter() - started
        seconds.append(took)
        if took > budget:
            side = "late"
        if side == "buy" and position >= MAX_POSITION or side == "sell" and position <= -MAX_POSITION:
            counts["position_cap"] += 1
            side = "hold"
        counts[side] += 1
        if side in ("buy", "sell"):
            step = 1 if side == "buy" else -1
            price = block["mid"] + step * block["spread"] / 2  # cross half the spread
            position += step
            cash -= step * price
            traded += 1
            right += (nxt["mid"] > block["mid"]) == (side == "buy")
        pnl = cash + position * nxt["mid"]
        if pnl < LOSS_LIMIT:
            cash += position * nxt["mid"] - abs(position) * nxt["spread"] / 2  # close at the next mid, pay the spread
            position, stopped_at = 0, nxt["n"]
    final = cash + position * blocks[-1]["mid"]
    return {"pnl": round(final, 5), "position": position, "counts": counts, "stopped_at": stopped_at,
            "hit_rate": right / traded if traded else None, "trades": traded,
            "p50_seconds": sorted(seconds)[len(seconds) // 2] if seconds else 0.0}
