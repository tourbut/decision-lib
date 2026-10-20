---
title: DEV-007 작업 완료 판정 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-007]
summary: "completion-check 샘플의 오프라인 테스트, 실제 모델 측정, 웹 화면 확인 결과"
---

# DEV-007 작업 완료 판정 QA

- 대상: `samples/completion-check/`, `web/`의 completion-check 화면, `web/adapters/__init__.py`의 모듈 로더. 기준 `44e808b`.
- 실행기: pytest, `demo.py`, Playwright MCP(Chromium). 모델은 실제 d3-flash와 muse-glimmer-30b.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/completion-check` | 14 passed. 분기 9가지, 빠진 것 모두 나열, fail-open, steer→pass 루프, 시도 상한 halt |
| `uv run pytest -q` | `web` | 12 passed. 판정·에이전트 엔드포인트 테스트 추가 |

## 실제 모델 측정

| 항목 | 결과 |
|---|---|
| 라벨 30건 | 29/30, 약 22초. 틀린 1건은 "아마 완료일 것입니다"(이름 변경, 테스트 미실행)를 pass |
| 라이브 정상 | 1회차 pass |
| 라이브 덜 된 초안 | 1회차 steer(요구사항 미충족) → 로컬 LLM이 보완 → 2회차 pass |

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| 상태 하나 판정(테스트 1개 실패): steer, 지시문 표시 | 통과 | `completion-1440.png` |
| 에이전트 실행(덜 된 초안): 시도 2회 표와 최종 답 | 통과 | `completion-1440.png` |
| 라벨 30건: 29/30 | 통과 | `completion-1440.png` |
| 모바일 390px: 가로 스크롤 없음(375), 콘솔 오류 0 | 통과 | — |
| 로더 수정 후 citation-check 라벨 15건 API 재실행 | 통과 | — |

## 확인 중 고친 결함

- citation-check와 completion-check가 모두 `check.py`를 가져 web 로더에서 한쪽이 다른 쪽 모듈을 가져올 수 있었다. 로더가 샘플을 불러오는 동안 다른 샘플의 같은 이름 모듈을 가리도록 고쳤다.
- 질문 문구 2회 수정(26/30 → 29/30). 문서 과제를 테스트 부족으로 돌려보내던 문제와, 답에 없는 요구사항을 충족으로 보던 문제다.

## 미실행

- 다크 모드, 키보드 전체 조작, 명암비: not_run.
- 실제 코드 수정과 테스트 실행이 있는 에이전트 루프: not_run. 트랜스크립트와 글쓰기 과제로 대신했다.
