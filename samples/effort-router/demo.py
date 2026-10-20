"""Route the 32 labelled turns, then compare answers: always fast, always think, routed.

Usage: python demo.py [--route-only | --shadow] ["메시지"]   # a message runs just that turn
       --shadow serves every turn from think and logs what the router would have done
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_typesafe import TypeSafeClassifier

from router import SYSTEM, build_agent, correct, route_turn, run_turn, shadow_report
from turns import TURNS

load_dotenv(find_dotenv())  # the repo-root .env


TIERS = json.loads(Path(__file__).with_name("tiers.json").read_text(encoding="utf-8"))


def local_models() -> dict[str, ChatOpenAI]:
    """One chat model per tier in tiers.json. fast has a short budget on purpose: a long
    answer is cut off and climbs to think."""
    def model(tier: dict) -> ChatOpenAI:
        return ChatOpenAI(
            model=os.environ["LOCAL_LLM_MODEL"],  # tiers.json names the model for the record; .env says where it runs
            base_url=os.environ["LOCAL_LLM_URL"],
            api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local",
            max_tokens=tier["max_tokens"],
            temperature=0,
            extra_body={"chat_template_kwargs": {"enable_thinking": tier["thinking"]}},
        )

    return {name: model(TIERS[name]) for name in ("fast", "think")}


def direct(model: ChatOpenAI, text: str) -> tuple[str, int, float]:
    started = time.perf_counter()
    message = model.invoke([SystemMessage(SYSTEM), HumanMessage(text)])
    return str(message.content), (message.usage_metadata or {}).get("output_tokens", 0), time.perf_counter() - started


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    models = local_models()
    agent, router = build_agent(classifier, models)
    messages = [a for a in sys.argv[1:] if not a.startswith("--")]
    if messages:
        for text in messages:
            r = run_turn(agent, router, text)
            print(f"[{'→'.join(r['tried'])}] {r['reason']} ({r['output_tokens']} tokens, {r['seconds']:.1f}s)\n{r['answer']}\n")
        return

    if "--shadow" in sys.argv:
        agent, router = build_agent(classifier, models, mode="shadow")
        for t in TURNS:
            run_turn(agent, router, t["text"])
        report = shadow_report(router.log, TIERS)
        print(f"shadow: {report['turns']} turns served by think, router intended {report['intended']}")
        print(f"  estimated cost: always think {report['fixed_cost']:.2f}, routed {report['routed_cost']:.2f} "
              f"({report['saving']:.0%} less); think actually used {report['measured_fixed_tokens']} output tokens")
        return

    started = time.perf_counter()
    decisions = [route_turn(classifier, t["text"]) for t in TURNS]
    print(f"routing {len(TURNS)} turns took {time.perf_counter() - started:.1f}s")
    for t, d in zip(TURNS, decisions):
        mark = "ok" if d["route"] == t["label"] else f"MISS ({t['label']})"
        print(f"  {d['route']:<8}{mark:<16}{d['reason']:<24}{t['text'][:40]}")
    print(f"  routes matched: {sum(d['route'] == t['label'] for t, d in zip(TURNS, decisions))}/{len(TURNS)}")
    if "--route-only" in sys.argv:
        return

    keyed = [t for t in TURNS if t["answer"]]
    totals = {name: [0, 0, 0.0] for name in ("always fast", "always think", "routed")}  # right, tokens, seconds
    for t in keyed:
        rows = {"always fast": direct(models["fast"], t["text"]), "always think": direct(models["think"], t["text"])}
        r = run_turn(agent, router, t["text"])
        rows["routed"] = (r["answer"], r["output_tokens"], r["seconds"])
        marks = []
        for name, (answer, tokens, seconds) in rows.items():
            ok = correct(answer, t["answer"])
            totals[name][0] += ok
            totals[name][1] += tokens
            totals[name][2] += seconds
            marks.append("O" if ok else "X")
        print(f"  {' '.join(marks)}  routed={'→'.join(r['tried']):<12}{t['text'][:40]}")
    print(f"\n{len(keyed)} turns with an answer key (columns: always fast, always think, routed)")
    for name, (right, tokens, seconds) in totals.items():
        print(f"  {name:<14}{right:>3}/{len(keyed)} right  {tokens:>6} output tokens  {seconds:6.1f}s")


if __name__ == "__main__":
    main()
