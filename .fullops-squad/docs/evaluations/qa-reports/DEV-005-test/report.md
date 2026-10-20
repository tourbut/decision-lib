---
title: DEV-005 인용 검증·판정 보정 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-005]
summary: "citation-check, decision-calibration 샘플의 오프라인 테스트, 실제 모델 측정, 웹 화면 확인 결과"
---

# DEV-005 인용 검증·판정 보정 QA

- 대상: `samples/citation-check/`, `samples/decision-calibration/`, `web/`의 두 화면. fullops/dev 작업 트리(기준 `fd0b2f2`).
- 실행기: pytest, 각 `demo.py`, Playwright MCP(Chromium). 로컬 서버는 `uvicorn app:app --port 8300`이다. 모델은 실제 d3-flash와 muse-glimmer-30b를 썼다.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/citation-check` | 6 passed. 줄바꿈을 넘는 인용, 다른 절에 있는 인용, 모델 호출 없는 fabricated, 절 번호만 있는 주장, 0.8 경계, LLM 절 번호 정리 |
| `uv run pytest -q` | `samples/decision-calibration` | 6 passed. 데이터 균형, 순환 순서, 정확도·ECE·Brier 계산값, 변경률·위치 비율, L0의 사전확률 제거, 첫 선택지만 고르는 스텁 |
| `uv run pytest -q` | `web` | 10 passed. 새 엔드포인트 테스트 3개 추가 |

## 실제 모델 측정

| 항목 | 결과 |
|---|---|
| citation-check 라벨 15건 | 15/15 일치, 모델 호출 13건 약 2초, 사람 검토 큐 3건(애매한 주장, 확신도 0.61~0.76) |
| citation-check 로컬 LLM 답변 3개 | 인용 7건 모두 출처에 있었고 verified |
| decision-calibration NSMC 200건 | Choice 86.5%/87.5%(순서 반대), Noul 87.0%. ECE 0.070/0.078/0.042. 순서를 바꿔 판정이 바뀐 리뷰 2건(1.0%) |
| decision-calibration 문의 40건 × 4순서 | 첫 순서 95.0%, L0 97.5%. 순서에 따라 바뀐 문의 3건(7.5%). 위치별 선택 비율 23~26% |

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| citation-check: 인용 하나 검사(예외 조항 인용 → contradicted 0.97), LLM 답변 검사, 라벨 15건 | 통과 | `citation-1440.png` |
| decision-calibration: 문의 하나 4순서(technical/sales가 순서에 따라 바뀜), 라우팅 40건, NSMC 40건 | 통과 | `calibration-1440.png` |
| 모바일 390px: 두 화면 가로 스크롤 없음(scrollWidth 375), 다이어그램 SVG 렌더, 콘솔 오류 0 | 통과 | `calibration-mobile.png` |

## 확인 중 고친 결함

- 로컬 LLM이 절 번호를 "6 유출 대응"처럼 제목까지 적어, 화면에 "인용문은 §6에 있음"이 잘못 표시됐다. `generate()`가 절 번호만 남기게 고치고 테스트에 넣었다.
- 라우팅 결과에서 지표 표와 순서별 판정 표가 붙어 구분되지 않았다. 사이에 제목 문장을 넣었다.

## 미실행

- 다크 모드: not_run. 새 색 토큰을 추가하지 않았다.
- 키보드만으로 전체 조작, 명암비 측정: not_run.
- 화면에서 NSMC 200건 전체: not_run(40건만). 200건은 `demo.py`로 측정했다.
- 주소창에서 해시만 바꿔 샘플을 옮기면 화면이 바뀌지 않는다. 기존 동작이며 이번 범위 밖이다. 왼쪽 목록으로 옮기면 된다.
