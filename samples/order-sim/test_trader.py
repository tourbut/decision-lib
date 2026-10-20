"""Offline tests: the market's built-in edge, and every guard rail in the runner."""

from __future__ import annotations

import time

from langchain_core.runnables import RunnableLambda
from langchain_typesafe.client import TypeSafeAPIConnectionError

from market import simulate
from trader import LOSS_LIMIT, MAX_POSITION, always_hold, coin_flip, imbalance_rule, model_policy, run

BLOCKS = simulate()


def test_market_is_seeded_and_has_an_edge() -> None:
    assert simulate() == BLOCKS
    agree = sum((b["imbalance"] > 0) == (n["mid"] > b["mid"]) for b, n in zip(BLOCKS, BLOCKS[1:]))
    assert agree / (len(BLOCKS) - 1) > 0.6  # the imbalance predicts the next move more often than not


def test_hold_does_nothing_and_the_rule_profits() -> None:
    assert run(BLOCKS, always_hold)["pnl"] == 0
    assert run(BLOCKS, imbalance_rule)["pnl"] > 0


def test_position_cap() -> None:
    r = run(BLOCKS, lambda block, position: "buy")
    assert r["position"] <= MAX_POSITION and r["counts"]["position_cap"] > 0


def test_loss_limit_closes_and_stops() -> None:
    worst = run(BLOCKS, lambda block, position: "sell" if block["imbalance"] > 0 else "buy")  # always wrong
    assert worst["stopped_at"] is not None and worst["position"] == 0 and worst["counts"]["after_stop"] > 0
    assert worst["pnl"] < LOSS_LIMIT * 0.5


def test_late_decision_becomes_hold() -> None:
    def slow(block, position):
        time.sleep(0.002)
        return "buy"
    r = run(BLOCKS[:5], slow, budget=0.001)
    assert r["counts"]["late"] == 4 and r["trades"] == 0


def test_model_failure_holds() -> None:
    def down(_):
        raise TypeSafeAPIConnectionError("refused")
    assert run(BLOCKS[:10], model_policy(RunnableLambda(down)))["trades"] == 0


def test_coin_flip_is_seeded() -> None:
    a, b = run(BLOCKS, coin_flip(1)), run(BLOCKS, coin_flip(1))
    assert (a["pnl"], a["counts"]) == (b["pnl"], b["counts"])
