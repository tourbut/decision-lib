---
title: DEV-016 뉴스 매칭 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-016]
summary: "news-match 샘플의 오프라인 테스트, 실제 모델 측정, 웹 화면 확인 결과"
---

# DEV-016 뉴스 매칭 QA

- 대상: `samples/news-match/`, `web/`의 news-match 화면.
- 실행기: pytest, `demo.py`, Playwright MCP(Chromium). 모델은 실제 d3-flash.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/news-match` | 3 passed |
| `uv run pytest -q` | `web` | 21 passed |

## 실제 모델 측정

| 기준 | 정밀도 | 재현율 |
|---|---|---|
| 1.0 | 0.89 | 0.93 |
| 1.5 | 1.00 | 0.93 |
| 2.0 | 1.00 | 0.81 |

200쌍(헤드라인 40 × 주제 5)에 약 28초.

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| 예시 피드: 기준 1.5 정밀도 1.00·재현율 0.93, 기준 2로 바꾸면 다시 판정 없이 0.81 | 통과 | `news-1440.png` |
| 붙여넣은 헤드라인 2개: 라벨 없이 고른 쌍만 표시 | 통과 | — |
| 모바일 390px: 가로 스크롤 없음, 콘솔 오류 0 | 통과 | — |

## 미실행

- 다크 모드, 키보드 전체 조작, 명암비: not_run.
