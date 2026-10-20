"""Choosing among many options with a decision model.

1. Skill suggestion (TypeSafe cookbook): one Choice ranks every skill plus "none"; the
   top 3 skills are then reviewed with their full descriptions, and at most one is
   suggested. A suggestion is a hint for the agent, not permission to run it.
2. Hierarchical choice: d3-flash rejects a Choice with more than 255 options (HTTP 422),
   and a 255-option Choice already takes about 2 seconds. Pick the group first, then the
   option inside it (tax-doc-classifier splits 261 IRS forms the same way).
"""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import Runnable
from langchain_typesafe import Choice, ClassifierRequest, ClassifierResponse, Noul

MAX_OPTIONS = 255
SHORTLIST = 3
THRESHOLDS = {"fit": 0.60, "second_group": 0.60}

Classifier = Runnable[ClassifierRequest, ClassifierResponse]


def ranked(probabilities: dict[str, float]) -> list[str]:
    return sorted(probabilities, key=probabilities.get, reverse=True)


# --- 1. Skill suggestion ------------------------------------------------------------


def suggest(classifier: Classifier, text: str, skills: dict[str, str]) -> dict[str, Any]:
    """{"skill": name or None, "reason", "stage1": probabilities, "shortlist", "fits"}.

    Stage 1 ranks every skill plus "none"; if "none" wins, stop there. Otherwise the top
    three are reviewed with their full descriptions, and the best fit is suggested only
    if it clears the threshold (the cookbook's Mastodon-to-X failure is a low fit)."""
    rank = Choice(
        instructions="Which skill would an assistant use to carry out this request?",
        criteria={**skills, "none": "No skill is needed, or none of the listed skills fits."},
    )
    stage1 = classifier.invoke({"state": {"request": text}, "questions": {"skill": rank}}).choices["skill"].probabilities
    if ranked(stage1)[0] == "none":
        return {"skill": None, "reason": "1단계: 맞는 스킬 없음", "stage1": stage1, "shortlist": [], "fits": {}}

    shortlist = [s for s in ranked(stage1) if s != "none"][:SHORTLIST]
    review = {
        f"fit_{i}": Noul(instructions=f"Would the skill '{name}' ({skills[name]}) do exactly what the request asks, "
                         "on the same service, product, or file format?")
        for i, name in enumerate(shortlist)
    }
    answers = classifier.invoke({"state": {"request": text}, "questions": review}).nouls
    fits = {name: answers[f"fit_{i}"].noul for i, name in enumerate(shortlist)}
    best = max(fits, key=fits.get)
    if fits[best] < THRESHOLDS["fit"]:
        return {"skill": None, "reason": f"2단계: 후보 {len(shortlist)}개 모두 정확히 맞지 않음",
                "stage1": stage1, "shortlist": shortlist, "fits": fits}
    return {"skill": best, "reason": "2단계 재검토 통과", "stage1": stage1, "shortlist": shortlist, "fits": fits}


def stage1_only(stage1: dict[str, float]) -> str | None:
    """Baseline: trust the ranking alone."""
    top = ranked(stage1)[0]
    return None if top == "none" else top


# --- 2. Hierarchical choice ---------------------------------------------------------


def flat_choice(classifier: Classifier, text: str, instructions: str, options: dict[str, Any]) -> dict[str, float]:
    if len(options) > MAX_OPTIONS:
        raise ValueError(f"선택지 {len(options)}개는 한 번에 물을 수 없다(최대 {MAX_OPTIONS}).")
    question = Choice(instructions=instructions, criteria=options)
    return classifier.invoke({"state": {"request": text}, "questions": {"q": question}}).choices["q"].probabilities


def hierarchical_choice(
    classifier: Classifier,
    text: str,
    groups: dict[str, list[str]],
    group_descriptions: dict[str, str],
    instructions: str,
) -> dict[str, Any]:
    """Group first, then the option inside it. If the top group is unsure, the second
    group's options join the second step too, as long as they still fit in one Choice."""
    group_p = flat_choice(classifier, text, f"{instructions} First, which group?",
                          {g: group_descriptions[g] for g in groups})
    order = ranked(group_p)
    chosen = [order[0]]
    if group_p[order[0]] < THRESHOLDS["second_group"] and len(order) > 1:
        if len(groups[order[0]]) + len(groups[order[1]]) <= MAX_OPTIONS:
            chosen.append(order[1])
    options = {o: None for g in chosen for o in groups[g]}
    option_p = flat_choice(classifier, text, instructions, options)
    choice = ranked(option_p)[0]
    return {"choice": choice, "groups": chosen, "group_probabilities": group_p,
            "probability": option_p[choice], "options_asked": len(options)}
