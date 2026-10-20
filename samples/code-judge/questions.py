"""Twenty behaviour questions about this repo's samples, written in Korean the way a
developer would ask, each with the declaration(s) that answer it. The code is in
English, so the words rarely match: that is the point of searching by behaviour.
"""

from __future__ import annotations

QUESTIONS = [
    {"q": "키나 토큰 같은 비밀값을 가려서 모델에 보내는 곳은?", "answers": ["tool-call-gate/gate.py:mask"]},
    {"q": "인용문이 출처 문서에 그대로 있는지 찾는 함수", "answers": ["citation-check/check.py:find_quote"]},
    {"q": "선택지 순서를 돌려 가며 모든 순서를 만드는 부분", "answers": ["decision-calibration/calib.py:rotations"]},
    {"q": "라벨 없이 사전확률을 나눠서 보정하는 코드", "answers": ["decision-calibration/calib.py:l0"]},
    {"q": "모델 답이 비었거나 토큰 한도에서 잘렸는지 판단", "answers": ["effort-router/router.py:incomplete"]},
    {"q": "판정이 불확실하면 추론 켜는 경로로 보내는 규칙", "answers": ["effort-router/router.py:decide"]},
    {"q": "테스트가 실패했으면 무조건 되돌려 보내는 판단", "answers": ["completion-check/check.py:decide"]},
    {"q": "오래된 도구 결과를 같은 id로 바꿔서 행 수를 지키는 곳", "answers": ["context-gate/compaction.py:compact",
                                                                  "context-gate/compaction.py:CompactionMiddleware.before_model"]},
    {"q": "메모리에 저장하기 전에 비밀번호 같은 걸 거르는 게이트", "answers": ["context-gate/memory_gate.py:gate"]},
    {"q": "검색 결과 두 순위를 역순위 합으로 합치는 함수", "answers": ["rerank/rerank.py:rrf"]},
    {"q": "nDCG를 계산하는 함수", "answers": ["rerank/metrics.py:ndcg"]},
    {"q": "이미지를 서버가 읽는 images 배열에 붙여서 보내는 부분", "answers": ["screenshot-check/check.py:ImageClassifier._payload"]},
    {"q": "로그인 페이지가 브랜드 공식 호스트인지 확인하는 판단", "answers": ["screenshot-check/check.py:decide"]},
    {"q": "IANA 시간대를 지역별로 묶는 코드", "answers": ["many-options/zones.py:catalog"]},
    {"q": "선택지가 255개를 넘으면 그룹 먼저 고르는 함수", "answers": ["many-options/pick.py:hierarchical_choice"]},
    {"q": "외부 링크를 후보에서 빼고 사이트 안 링크만 남기는 곳", "answers": ["action-picker/web_env.py:WebEnv._links"]},
    {"q": "같은 상태로 돌아오면 반복으로 보고 멈추는 루프", "answers": ["action-picker/agent.py:run"]},
    {"q": "산술식만 안전하게 계산하고 함수 호출은 거부하는 계산기", "answers": ["judgment-tools/tools.py:calculate"]},
    {"q": "검색 문단 BM25로 상위 k개 뽑기", "answers": ["rag-passage-filter/rag.py:bm25", "rerank/bm25.py:BM25.search"]},
    {"q": "도구 호출을 사람 승인 대기로 멈추는 미들웨어", "answers": ["tool-call-gate/agent.py:GateMiddleware.wrap_tool_call",
                                                          "tool-call-gate/agent.py:GateMiddleware"]},
]
