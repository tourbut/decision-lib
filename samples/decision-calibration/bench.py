"""The two benchmarks as functions that return plain dicts, shared by demo.py and web/."""

from __future__ import annotations

import time
from pathlib import Path

from langchain_core.runnables import Runnable
from langchain_typesafe import ClassifierRequest, ClassifierResponse

from calib import (
    SENTIMENT,
    SENTIMENT_ASK,
    TEAM_ASK,
    Item,
    ask_choice,
    ask_positive,
    flips,
    l0,
    load_nsmc,
    position_picks,
    rotations,
    summarize,
)
from tickets import LABELS, TICKETS

NSMC = load_nsmc(Path(__file__).with_name("nsmc_200.tsv"))
ROUTING: list[Item] = [{"text": t, "label": y} for t, y in TICKETS]

Classifier = Runnable[ClassifierRequest, ClassifierResponse]


def timed(fn, *args):
    started = time.perf_counter()
    return fn(*args), time.perf_counter() - started


def sentiment(classifier: Classifier, items: list[Item]) -> dict:
    texts, labels = [i["text"] for i in items], [i["label"] for i in items]
    orders = rotations(list(SENTIMENT))
    choice, choice_s = timed(ask_choice, classifier, texts, SENTIMENT, SENTIMENT_ASK, orders)
    noul, noul_s = timed(ask_positive, classifier, texts)
    changed = flips(choice)
    per_call = choice_s / len(items) / len(orders)
    return {
        "n": len(items),
        "methods": {
            "choice": {**summarize([o[0] for o in choice], labels), "seconds_per_call": per_call},
            "choice_reversed": {**summarize([o[1] for o in choice], labels), "seconds_per_call": per_call},
            "noul": {**summarize(noul, labels), "seconds_per_call": noul_s / len(items)},
        },
        "flip_rate": len(changed) / len(items),
        "flipped": [{**items[i], "orders": choice[i]} for i in changed],
    }


def routing(classifier: Classifier, items: list[Item]) -> dict:
    texts, labels = [i["text"] for i in items], [i["label"] for i in items]
    orders = rotations(list(LABELS))
    per_order, seconds = timed(ask_choice, classifier, texts, LABELS, TEAM_ASK, orders)
    changed = flips(per_order)
    return {
        "n": len(items),
        "orders": orders,
        "methods": {
            "first_order": summarize([o[0] for o in per_order], labels),
            "l0": summarize(l0(per_order), labels),
        },
        "flip_rate": len(changed) / len(items),
        "position_picks": position_picks(per_order, orders),
        "seconds_per_call": seconds / len(items) / len(orders),
        "flipped": [{**items[i], "orders": per_order[i]} for i in changed],
        "items": [{**item, "orders": o, "l0": p} for item, o, p in zip(items, per_order, l0(per_order))],
    }
