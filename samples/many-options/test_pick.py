"""Offline tests: the option limit, the group step, and the shortlist review."""

from __future__ import annotations

import pytest
from langchain_core.runnables import RunnableLambda
from langchain_typesafe import ClassifierResponse

from pick import MAX_OPTIONS, flat_choice, hierarchical_choice, suggest
from skills import REQUESTS, SKILLS
from zones import REGIONS, catalog


def choice(probs: dict[str, float]) -> dict:
    return {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs, "confidence": 0.9}


def response(answers: dict) -> ClassifierResponse:
    return ClassifierResponse.model_validate({"model": "stub", "answers": answers})


def test_catalog_is_past_the_limit_and_every_label_exists() -> None:
    groups = catalog()
    zones = {z for v in groups.values() for z in v}
    assert len(zones) > MAX_OPTIONS and all(len(v) <= MAX_OPTIONS for v in groups.values())
    assert set(groups) <= set(REGIONS)
    from zones import REQUESTS as ZONE_REQUESTS
    assert all(r["label"] in zones for r in ZONE_REQUESTS)


def test_flat_choice_refuses_too_many_options() -> None:
    with pytest.raises(ValueError):
        flat_choice(RunnableLambda(lambda _: None), "x", "q", {str(i): None for i in range(MAX_OPTIONS + 1)})


def groups_then(probs_by_step: list[dict[str, float]], seen: list):
    steps = iter(probs_by_step)

    def answer(request) -> ClassifierResponse:
        seen.append(list(request["questions"]["q"].criteria))
        return response({"q": choice(next(steps))})

    return RunnableLambda(answer)


def test_hierarchical_choice_asks_group_then_option() -> None:
    groups = {"A": ["A/x", "A/y"], "B": ["B/z"]}
    seen: list = []
    out = hierarchical_choice(groups_then([{"A": 0.9, "B": 0.1}, {"A/x": 0.2, "A/y": 0.8}], seen), "t", groups,
                              {"A": "a", "B": "b"}, "q")
    assert out["choice"] == "A/y" and out["groups"] == ["A"] and seen[1] == ["A/x", "A/y"]


def test_unsure_group_adds_the_runner_up() -> None:
    groups = {"A": ["A/x"], "B": ["B/z"]}
    seen: list = []
    out = hierarchical_choice(groups_then([{"A": 0.55, "B": 0.45}, {"A/x": 0.3, "B/z": 0.7}], seen), "t", groups,
                              {"A": "a", "B": "b"}, "q")
    assert out["groups"] == ["A", "B"] and out["choice"] == "B/z"


def skill_stub(stage1_top: str, fits: dict[int, float]):
    def answer(request) -> ClassifierResponse:
        questions = request["questions"]
        if "skill" in questions:
            labels = list(questions["skill"].criteria)
            return response({"skill": choice({k: (0.8 if k == stage1_top else 0.2 / len(labels)) for k in labels})})
        return response({k: {"type": "noul", "noul": fits.get(int(k.split("_")[1]), 0.0)} for k in questions})

    return RunnableLambda(answer)


def test_suggest_stops_on_none_and_needs_a_good_fit() -> None:
    skills = {name: desc for name, (_, desc) in SKILLS.items()}
    assert suggest(skill_stub("none", {}), "고마워", skills)["skill"] is None
    low = suggest(skill_stub("x-post", {0: 0.3}), "마스토돈에 올려 줘", skills)
    assert low["skill"] is None and low["shortlist"][0] == "x-post"
    # The review may promote the second candidate over stage 1's top pick.
    promoted = suggest(skill_stub("x-post", {0: 0.2, 1: 0.9}), "요청", skills)
    assert promoted["skill"] == promoted["shortlist"][1]


def test_labels() -> None:
    assert len(REQUESTS) == 40 and {r["label"] for r in REQUESTS} - {"none"} <= set(SKILLS)
