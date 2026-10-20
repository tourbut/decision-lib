"""Run the four judges on the 30 tickets and compare accuracy and time per ticket.

Usage: python demo.py
"""

from __future__ import annotations

import os
import time

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import TypeSafeClassifier
from openai import OpenAI

from judges import answers, auc, d3, few_label, llm_json, llm_read
from tickets import TICKETS

load_dotenv(find_dotenv())  # the repo-root .env

FIELDS = ("dept", "urgent", "frustration")


def judges() -> dict:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    client = OpenAI(base_url=os.environ["LOCAL_LLM_URL"], api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local")
    model = os.environ["LOCAL_LLM_MODEL"]
    return {
        "d3-flash": lambda i, t: d3(classifier, t),
        "LLM logprobs": lambda i, t: llm_read(client, model, t),
        "LLM JSON": lambda i, t: llm_json(client, model, t),
        "few-label NB": lambda i, t: few_label(TICKETS[:i] + TICKETS[i + 1:], t),
    }


def main() -> None:
    print(f"{len(TICKETS)} tickets, 3 questions each")
    for name, judge in judges().items():
        started, right, urgent_p = time.perf_counter(), {f: 0 for f in FIELDS}, []
        for i, ticket in enumerate(TICKETS):
            judgment = judge(i, ticket["text"])
            got = answers(judgment)
            urgent_p.append(judgment["urgent"])
            for f in FIELDS:
                right[f] += got[f] == ticket[f]
        per = (time.perf_counter() - started) / len(TICKETS)
        ranked = "" if isinstance(urgent_p[0], bool) else f"   urgent AUC {auc(urgent_p, [t['urgent'] for t in TICKETS]):.2f}"
        print(f"  {name:<14}" + "  ".join(f"{f} {right[f]:>2}/{len(TICKETS)}" for f in FIELDS) + f"   {per:.2f}s/ticket{ranked}")
    print(f"  (answering 'not urgent' every time: {sum(not t['urgent'] for t in TICKETS)}/{len(TICKETS)})")


if __name__ == "__main__":
    main()
