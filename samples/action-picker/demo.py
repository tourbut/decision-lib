"""Run the picker in all three environments and report success, steps, and stops.

Usage: python demo.py [web|desktop|grid ...]   # default: all three
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import TypeSafeClassifier

import desktop_env
import grid_env
import web_env
from agent import DONE, NONE, run

load_dotenv(find_dotenv())  # the repo-root .env

GRID_STEPS = 40


def web_cases():
    for g in web_env.GOALS:
        verify = (lambda url, want=g["expect"]: want is not None and web_env.title_of(url) == want)
        yield g["goal"], web_env.WebEnv(), web_env.START, verify, g["expect"] is None, 12


def desktop_cases():
    for g in desktop_env.GOALS:
        want = g["expect"]
        verify = (lambda s, want=want: want is not None and s.get(want[0]) == want[1])
        yield g["goal"], desktop_env.DesktopEnv(), desktop_env.START, verify, want is None, 12


def grid_cases(hints: str):
    goal = "열쇠를 주워 잠긴 문을 열고 출구(E)에 도착하라. 출구에 서면 끝이다."
    for name in grid_env.MAPS:
        yield f"{goal} ({name})", grid_env.GridEnv(hints), grid_env.start(name), grid_env.at_exit, False, GRID_STEPS


def report(name: str, cases, classifier) -> None:
    started, rows = time.perf_counter(), []
    for goal, env, state, verify, impossible, limit in cases:
        r = run(classifier, env, goal, state, verify, max_steps=limit)
        steps = sum(t["action"] not in (DONE, NONE) for t in r["trace"])
        ok = r["stopped"] == NONE if impossible else r["verified"]
        rows.append(ok)
        extra = f" moves {env.moves} replans {len(env.replans)}" if hasattr(env, "replans") else ""
        print(f"  {'ok  ' if ok else 'FAIL'} {r['stopped']:<5} steps {steps:>2}{extra}  {goal[:46]}")
        if not ok:
            for t in r["trace"]:
                print(f"         {t['action']:<10} {t['probability']:.2f} {t['label']}")
    print(f"  {name}: {sum(rows)}/{len(rows)} in {time.perf_counter() - started:.1f}s")


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    chosen = sys.argv[1:] or ["web", "desktop", "grid"]
    runs = (("web", web_cases()), ("desktop", desktop_cases()),
            ("grid", grid_cases("offset")), ("grid+distance", grid_cases("distance")),
            ("grid+macro", grid_cases("macro")))
    for name, cases in runs:
        if name.split("+")[0] in chosen:
            print(f"\n{name}")
            report(name, cases, classifier)
    for name in grid_env.MAPS:
        print(f"  shortest route {name}: {grid_env.optimal_steps(name)} actions (moves + pick + open)") if "grid" in chosen else None


if __name__ == "__main__":
    main()
