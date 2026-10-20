---
title: DEV-015 라우터 shadow 모드 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-015]
summary: "effort-router shadow·off 모드와 비용 추정의 테스트, 실제 모델 측정, 웹 화면 확인 결과"
---

# DEV-015 라우터 shadow 모드 QA

- 대상: `samples/effort-router/`(mode, tiers.json, shadow_report), `web/`의 effort-router 화면.
- 실행기: pytest, `demo.py --shadow`, Playwright MCP(Chromium). 모델은 실제 d3-flash와 muse-glimmer-30b.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/effort-router` | 21 passed. shadow는 고정 경로로 응답하고 의도를 기록, off는 판정 모델을 부르지 않음, 비용 추정 계산 |
| `uv run pytest -q` | `web` | 20 passed. shadow 턴, /shadow 추정 |

## 실제 모델 측정

| 항목 | 결과 |
|---|---|
| shadow 32턴 | 모두 think로 응답, 라우터 의도 fast 10·think 16·handoff 6 |
| 비용 추정(tiers.json) | 항상 think 6.59 → 라우팅 4.03, 39% 절감 추정. think 실측 출력 7,626토큰 |

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| shadow 모드 한 턴: "라우팅(shadow, 의도: fast)", 경로 think | 통과 | `effort-shadow-1440.png` |
| shadow 비용 추정 버튼: 의도 분포와 39% 절감 | 통과 | — |
| 모바일 390px: 가로 스크롤 없음, 콘솔 오류 0 | 통과 | — |

## 미실행

- 다크 모드, 키보드 전체 조작, 명암비: not_run.
