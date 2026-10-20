"""Measure the check on the 30 labelled transcripts, then run the gated agent live.

Usage: python demo.py [--eval-only]
"""

from __future__ import annotations

import os
import sys
import time
from collections import Counter

from dotenv import find_dotenv, load_dotenv
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_typesafe import TypeSafeClassifier

from check import check
from gate import build_agent
from transcripts import TRANSCRIPTS

load_dotenv(find_dotenv())  # the repo-root .env

TASK = """아래 변경 목록으로 릴리스 노트를 써라.
요구: (1) 세 변경을 모두 포함한다. (2) 항목마다 이슈 번호를 붙인다. (3) 마지막에 '업그레이드 주의' 절을 둔다.

변경 목록:
- #41 로그인 시 이메일 대소문자를 구분하지 않게 고침
- #45 사용자 목록 API에 페이지네이션 추가(size 최대 100)
- #52 설정 상수 TIMEOUT을 REQUEST_TIMEOUT으로 이름 변경(설정 파일 수정 필요)"""

# A worker that claims victory early, so the live run shows a steer. Only the first
# answer is canned; after the gate's instruction the real local LLM continues.
LAZY_DRAFT = "릴리스 노트를 작성했습니다.\n\n- 로그인 이메일 대소문자 문제 수정\n- 사용자 목록 페이지네이션 추가\n\n완료했습니다."


class LazyFirstDraft(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        if len(request.messages) == 1:
            return AIMessage(LAZY_DRAFT)
        return handler(request)


def evaluate(classifier) -> None:
    started = time.perf_counter()
    verdicts = [check(classifier, t) for t in TRANSCRIPTS]
    print(f"{len(TRANSCRIPTS)} transcripts checked in {time.perf_counter() - started:.1f}s")
    for t, v in zip(TRANSCRIPTS, verdicts):
        if v["action"] != t["label"]:
            print(f"  MISS {t['label']}->{v['action']} ({'; '.join(v['reasons'])}): {t['response'][:60]}")
    hits = sum(t["label"] == v["action"] for t, v in zip(TRANSCRIPTS, verdicts))
    print(f"  matched {hits}/{len(TRANSCRIPTS)}  labels {dict(Counter(t['label'] for t in TRANSCRIPTS))}")
    early = [v for t, v in zip(TRANSCRIPTS, verdicts) if t["label"] != "pass" and "완료" in t["response"]]
    print(f"  completion claims that were not done: {len(early)}, accepted as pass: {sum(v['action'] == 'pass' for v in early)}")


def main() -> None:
    classifier = TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )
    evaluate(classifier)
    if "--eval-only" in sys.argv:
        return
    model = ChatOpenAI(
        model=os.environ["LOCAL_LLM_MODEL"],
        base_url=os.environ["LOCAL_LLM_URL"],
        api_key=os.environ.get("LOCAL_LLM_API_KEY") or "local",
        max_tokens=1500,
        temperature=0,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    for name, extra in (("honest worker", []), ("lazy first draft", [LazyFirstDraft()])):
        agent, gate = build_agent(model, classifier, extra)
        result = agent.invoke({"messages": [HumanMessage(TASK)]}, {"recursion_limit": 20})
        print(f"\n== {name}")
        for entry in gate.log:
            print(f"  attempt {entry['attempt']}: {entry['action']} — {'; '.join(entry['reasons'])}")
        print(str(result["messages"][-1].content))


if __name__ == "__main__":
    main()
