---
title: DEV-008 검색 리랭킹 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-008]
summary: "rerank 샘플의 오프라인 테스트, SciFact 측정, 웹 화면 확인 결과"
---

# DEV-008 검색 리랭킹 QA

- 대상: `samples/rerank/`, `web/`의 rerank 화면. 기준 `cb81fc2`.
- 실행기: pytest, 측정 스크립트(질의 30개 × 후보 30개), Playwright MCP(Chromium). 모델은 실제 d3-flash.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/rerank` | 5 passed. nDCG·recall, 동점 시 BM25 순서, RRF, 부분집합 일관성, 재정렬 |
| `uv run pytest -q` | `web` | 13 passed. 질의 ID·직접 쓴 주장·없는 ID 404 |

## 실제 모델 측정

| 항목 | 결과 |
|---|---|
| BM25 구현 검증(SciFact 테스트 300개) | nDCG@10 0.660(BEIR 보고 0.665) |
| 질의 30개, 후보 30개, 900요청 | BM25 0.692, 관련도 0.698, 근거 0.681, BM25+관련도 RRF 0.708, 이상적 재정렬 0.820. 요청 1건 약 0.49초 |

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| SciFact 질의(PIN1, 후보 20): BM25 0.631 → 관련도 1.000, 정답·오답 배지와 막대 | 통과 | `rerank-1440.png` |
| 직접 쓴 주장(비타민 D, 후보 10): 라벨 없음 안내, 재정렬 목록 | 통과 | — |
| 모바일 390px: 가로 스크롤 없음(375), 콘솔 오류 0 | 통과 | — |

## 미실행

- 다크 모드, 키보드 전체 조작, 명암비: not_run.
- SciFact 전체 300질의 재정렬: not_run(약 70분 예상). 30개는 작은 표본이다.
