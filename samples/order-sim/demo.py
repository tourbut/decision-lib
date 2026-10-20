"""Dry run on 200 synthetic blocks: the decision model against two baselines.
No exchange, no wallet, no orders. Usage: python demo.py
"""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import TypeSafeClassifier

from market import simulate
from trader import always_hold, coin_flip, imbalance_rule, model_policy, run

load_dotenv(find_dotenv())  # the repo-root .env


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    blocks = simulate()
    print(f"dry run: {len(blocks)} synthetic blocks, no real orders")
    for name, policy in (("always hold", always_hold), ("coin flip", coin_flip()), ("imbalance rule", imbalance_rule),
                         ("d3-flash", model_policy(classifier))):
        r = run(blocks, policy)
        hit = "-" if r["hit_rate"] is None else f"{r['hit_rate']:.0%}"
        print(f"  {name:<15} pnl {r['pnl']:+.5f}  trades {r['trades']:>3}  hit {hit:>4}  position {r['position']:+d}  "
              f"counts {r['counts']}  stopped {r['stopped_at']}  p50 {r['p50_seconds'] * 1000:.0f}ms")
    tight = run(blocks, model_policy(classifier), budget=0.05)
    print(f"  d3-flash with a 50ms budget: late {tight['counts']['late']} of {len(blocks) - 1} blocks became hold")


if __name__ == "__main__":
    main()
