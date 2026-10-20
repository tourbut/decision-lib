---
title: DEV-014 코드 검색·리뷰 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-014]
summary: "code-judge 샘플의 오프라인 테스트, 실제 모델 측정, 웹 화면 확인 결과"
---

# DEV-014 코드 검색·리뷰 QA

- 대상: `samples/code-judge/`, `web/`의 code-judge 화면.
- 실행기: pytest, `demo.py`, Playwright MCP(Chromium). 모델은 실제 d3-flash.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/code-judge` | 5 passed. 색인 범위(테스트·자기 자신 제외, 메서드 포함), 검색 결과 형식, 키워드 기준선, 파일 단위 분할, 체크리스트 집계 |
| `uv run pytest -q` | `web` | 20 passed |

## 실제 모델 측정

| 항목 | 결과 |
|---|---|
| 코드 찾기 20문항 | 2단계 top-1 17/20·top-3 19/20(1.2초), 한 번에 16/20·20/20(3.8초), 키워드 2/20·6/20 |
| 체크리스트 diff 12개 | 심은 결함 8/8, 잘못 표시 2/52 |

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| "외부 링크를 후보에서 빼는 곳": action-picker의 WebEnv._links 1위, 경로·줄·원문 | 통과 | `codejudge-1440.png` |
| diff 12개 전부: 8/8, 잘못 표시 2 | 통과 | — |
| 모바일 390px: 가로 스크롤 없음(375), 콘솔 오류 0 | 통과 | — |

## 확인 중 고친 결함

- 폴더 단계에 README 소개만 주자 2단계 top-1이 11/20이었다. 선언 이름 목록을 붙여 17/20.
- 결과가 비었을 때 집계가 리스트를 더하다 실패했다.

## 미실행

- 다크 모드, 키보드 전체 조작, 명암비: not_run.
- 실제 PR·SWE-bench 평가: not_run.
