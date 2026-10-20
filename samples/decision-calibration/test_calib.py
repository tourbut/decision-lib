"""Offline tests for the metrics, the order rotation, and L0. No model is called."""

from __future__ import annotations

from collections import Counter

import pytest
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

from bench import NSMC, ROUTING, routing
from calib import ask_choice, flips, l0, position_picks, rotations, summarize
from tickets import LABELS


def test_datasets_are_balanced() -> None:
    assert Counter(i["label"] for i in NSMC) == {"negative": 100, "positive": 100}
    assert Counter(i["label"] for i in ROUTING) == {k: 10 for k in LABELS}


def test_rotations_put_every_label_in_every_position() -> None:
    orders = rotations(["a", "b", "c"])
    assert orders == [["a", "b", "c"], ["b", "c", "a"], ["c", "a", "b"]]
    assert all(sorted(o[i] for o in orders) == ["a", "b", "c"] for i in range(3))


def test_summarize_known_numbers() -> None:
    probs = [{"a": 0.9, "b": 0.1}, {"a": 0.6, "b": 0.4}, {"a": 0.3, "b": 0.7}, {"a": 0.8, "b": 0.2}]
    m = summarize(probs, ["a", "b", "b", "a"])  # second item is wrong
    assert m["accuracy"] == 0.75
    assert m["brier"] == pytest.approx((0.02 + 0.72 + 0.18 + 0.08) / 4)
    # buckets: 0.6 wrong, 0.7 right, 0.8 right, 0.9 right
    assert m["ece"] == pytest.approx((0.6 + 0.3 + 0.2 + 0.1) / 4)
    at = {r["threshold"]: r for r in m["review"]}
    assert at[0.7] == {"threshold": 0.7, "review_rate": 0.25, "auto_accuracy": 1.0}
    assert at[0.95]["auto_accuracy"] is None


def test_flips_and_position_picks() -> None:
    orders = rotations(["x", "y"])
    first_wins = [{"x": 0.6, "y": 0.4}, {"x": 0.4, "y": 0.6}]  # always the first option
    stable = [{"x": 0.9, "y": 0.1}, {"x": 0.8, "y": 0.2}]
    assert flips([stable, first_wins]) == [1]
    assert position_picks([first_wins], orders) == [1.0, 0.0]


def test_l0_removes_a_label_prior() -> None:
    # The model leans to "x" by 0.2 everywhere; true labels are balanced.
    leaning = [[{"x": 0.7, "y": 0.3}], [{"x": 0.45, "y": 0.55}], [{"x": 0.65, "y": 0.35}], [{"x": 0.4, "y": 0.6}]]
    fixed = l0(leaning)
    assert all(sum(p.values()) == pytest.approx(1) for p in fixed)
    assert sum(p["x"] for p in fixed) / len(fixed) == pytest.approx(0.5, abs=0.02)
    assert max(fixed[0], key=fixed[0].get) == "x" and max(fixed[1], key=fixed[1].get) == "y"


def first_option_model(request) -> ClassifierResponse:
    """Always picks whichever option is listed first: the worst possible order bias."""
    labels = list(request["questions"]["q"].criteria)
    probs = {k: (0.7 if i == 0 else 0.3 / (len(labels) - 1)) for i, k in enumerate(labels)}
    answer = {"type": "choice", "choice": labels[0], "probabilities": probs, "confidence": 0.5}
    return ClassifierResponse.model_validate({"model": "stub", "answers": {"q": answer}})


def test_ask_choice_sends_each_order_and_routing_reports_the_bias() -> None:
    stub = RunnableLambda(first_option_model)
    (item,) = ask_choice(stub, ["t"], LABELS, "q", rotations(list(LABELS)))
    assert [max(p, key=p.get) for p in item] == list(LABELS)

    r = routing(stub, ROUTING[:8])
    assert r["flip_rate"] == 1.0 and r["position_picks"] == [1.0, 0.0, 0.0, 0.0]
    # Averaged over orders the stub says nothing, so every label ties at 0.25.
    assert r["items"][0]["l0"] == pytest.approx({k: 0.25 for k in LABELS})
