---
title: DEV-010 화면 캡처 사칭 판정 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-010]
summary: "screenshot-check 샘플의 오프라인 테스트, 실제 모델 측정, 웹 화면 확인 결과"
---

# DEV-010 화면 캡처 사칭 판정 QA

- 대상: `samples/screenshot-check/`, `web/`의 screenshot-check 화면.
- 실행기: pytest, `demo.py`, Playwright MCP(Chromium). 모델은 실제 d3-flash(이미지 입력).

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/screenshot-check` | 11 passed. 호스트 규칙 7가지, 모델에 URL 미전달, images 배열 전송, 판정 실패, 페이지·캡처 일관성 |
| `uv run pytest -q` | `web` | 15 passed. 화면·텍스트·업로드·잘못된 이미지 422·없는 캡처 404·측정 |

## 실제 모델 측정

| 항목 | 결과 |
|---|---|
| 화면 캡처 16페이지 | 16/16, 사칭 8/8, 페이지당 약 0.44초 |
| 추출 텍스트 16페이지 | 11/16, 사칭 4/8(로고로만 브랜드를 넣은 4건 놓침) |

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| 로고만 있는 사칭 페이지: 텍스트로는 other, 화면으로는 phishing | 통과 | — |
| 업로드한 캡처 + 바꾼 URL(megabank.co.kr.verify-login.top): phishing | 통과 | `screenshot-1440.png` |
| 16페이지 측정: 화면 16/16, 텍스트 11/16 | 통과 | `screenshot-1440.png` |
| 모바일 390px: 가로 스크롤 없음(375), 콘솔 오류 0 | 통과 | — |

## 확인 중 고친 결함

- 이미지를 `state` 안의 LangChain 이미지 블록으로 보냈더니 base64가 텍스트로 처리돼 요청이 15~30초 걸리고 답이 그림과 무관했다. 서버 문서대로 최상위 `images` 배열로 보내게 고쳤다(요청 약 0.4초).
- 주소창이 찍힌 캡처와 URL을 함께 보내자 판매 중 도메인 페이지를 주소만 보고 브랜드 로그인으로 판정했다. 모델에는 화면만 보내고 호스트 판단은 코드로 옮겼다.
- 업로드한 캡처를 고른 뒤에도 예시 페이지의 추출 텍스트가 보여 헷갈렸다. 안내 문구로 바꿨다.

## 사고 기록

- 잘못된 방식(state 안 base64)으로 이미지 요청을 보내던 중 `dgx-decision-d3-flash` 컨테이너가 stop(신호 15 → 9) 후 start됐다. docker 재시작 정책은 no이고 감시 스크립트는 찾지 못했다. 원인은 확정하지 못했다. 약 2분 뒤 healthy로 돌아왔다.

## 미실행

- 다크 모드, 키보드 전체 조작, 명암비: not_run.
- 실제 피싱 페이지 캡처: not_run(가상 페이지).
