---
title: DEV-018 로컬 판정 방법 비교 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-018]
summary: "local-judges 샘플의 오프라인 테스트, 실제 모델 측정, 웹 화면 확인 결과"
---

# DEV-018 로컬 판정 방법 비교 QA

- 대상: `samples/local-judges/`, `web/`의 local-judges 화면.
- 실행기: pytest, `demo.py`, Playwright MCP(Chromium). 모델은 실제 d3-flash와 muse-glimmer-30b.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/local-judges` | 5 passed. 템플릿 토큰 건너뛰고 글자 확률 정규화, JSON 파싱, d3 매핑, 나이브 베이즈, AUC |
| `uv run pytest -q` | `web` | 23 passed |

## 실제 모델 측정 (문의 30건)

| 방법 | 팀 | 긴급(0.5) | 긴급 AUC | 불만도 | 문의당 |
|---|---|---|---|---|---|
| d3-flash | 29 | 17 | 0.94 | 23 | 0.37초 |
| LLM 확률 읽기 | 25~26 | 9 | 0.76 | 24 | 0.37초 |
| LLM JSON | 23 | 20 | — | 24 | 0.51초 |
| 나이브 베이즈 | 13 | 19 | 0.80 | 18 | 0.00초 |

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| 문의 하나 네 방법 판정, 확률 막대 | 통과 | — |
| 30건 전부: 위 표와 같은 값 | 통과 | `judges-1440.png` |
| 모바일 390px: 가로 스크롤 없음, 콘솔 오류 0 | 통과 | — |

## 확인 중 고친 결함

- 로컬 LLM의 첫 출력 토큰이 `<|message|>`라 첫 위치만 읽으면 확률이 없었다. 선택지 글자가 처음 나오는 위치를 읽는다.
- 긴급 0.5 기준 정답 수만으로는 순위 품질을 알 수 없어 AUC를 더했다.

## 미실행

- 다크 모드, 키보드 전체 조작, 명암비: not_run.
- LoRA 미세조정, Kev·Jevlike 가중치 실행: not_run.
