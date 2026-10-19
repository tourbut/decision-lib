---
title: "DEV-002 — RAG 검색 문단 필터 샘플 (d3-flash, 이슈 #3)"
status: draft
updated: 2026-10-19
owner: dev
tasks: [DEV-002]
summary: "RAG 검색 문단 필터 샘플 (d3-flash, 이슈 #3)"
attempt: 7bb20e5e5ccf4978b6b234df33025723
base: 0de3d8f919ee7b30216ccf1f3f133d33837e16ce
subagent_level: lite
test_level: lite
---

# DEV-002 — RAG 검색 문단 필터 샘플 (d3-flash, 이슈 #3)

- 작성일: 2026-10-19
- From / To: 사용자 / dev 주 담당(직접 작업)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위: `samples/rag-passage-filter/` 신규, 레포 README 샘플 표, lint 테스트 명령 등록 / 추가 승인 행위 없음
- 담당 워크트리 / 브랜치: /home/shin/workspace/decision-lib-dev / fullops/dev, 기본 브랜치 main
- 독립 리뷰: 사용자 결정으로 생략(`review_policy`)

## 현재 상황과 확인 근거

- 기준 SHA `0de3d8f`. 원천: 이슈 #3, https://docs.typesafe.ai/cookbooks/classifying_rag_passages (질문 4개·임계값·라우팅 순서).
- d3-flash가 한국어 문단에서 4개 noul을 의미 있게 판정함을 사전 확인했다.

## 해야 할 일

- [x] 한국어 가상 코퍼스(`corpus.md`, 12문단)와 BM25(글자 bigram)
- [x] 문단별 noul 4개 → 순서 고정 라우팅, 채택/충돌 블록 분리 프롬프트
- [x] `demo.py` 질의 3개 실측, 오프라인 `test_rag.py`
- [x] README, 레포 README 샘플 표, `lint.json` 테스트 명령

## 완료 기준과 검증

- `uv run pytest -q`: 10 passed(오프라인).
- `uv run python demo.py`: 라벨 11/11 일치. 틀린 전제 질의는 채택 0·충돌 3, 답변이 전제를 반박. 인젝션 문단 FORUM-02는 1.00으로 제외.
- 충돌 임계값을 0.70→0.80으로 조정(AUTH-02 오분류 0.70, 진짜 충돌 0.92+). README에 근거 기록.
- UI 작업 없음.

## 완료 보고

- 의존성(DEP-001): 신규 샘플 전용 `langchain-typesafe==0.0.1a3`, `langchain-openai`, `python-dotenv`, 개발용 `pytest`. BM25는 표준 라이브러리로 직접 구현해 의존성을 추가하지 않았다.
- 남은 일: 없음. 이슈 #4(인용 검증)는 범위 밖.
