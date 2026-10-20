---
title: "DEV-006 — P2-1 턴별 추론 강도·이관 라우터 샘플(#7 #21 #29 #30)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-006]
summary: "P2-1 턴별 추론 강도·이관 라우터 샘플(#7 #21 #29 #30)을 웹 화면까지 추가"
attempt: f1b761a7b3a446759d804555e1527f88
base: a1e157d079814124259cfd3864fa0d3bbdcd7702
subagent_level: lite
test_level: lite
---

# DEV-006 — P2-1 턴별 추론 강도·이관 라우터 샘플(#7 #21 #29 #30)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- P2-1: #7(남은 라우터), #21, #29, #30. 로컬 LLM은 muse-glimmer-30b 하나뿐이라 상위 모델 이관은 넘김 안내로 대신한다.
- 사전 측정: 추론 끔이면 회문 세기·저울 퍼즐·할인 함정을 틀렸고, 추론 켬은 16/16이었다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/effort-router/`: 턴 32개 라벨, d3-flash 경로 판정, 안전 이관·확신도 폴백·잘림 시 상향, LangChain 미들웨어, 비교 demo, 테스트 18개, README 다이어그램
- [x] `web/adapters/effort.py`, `web/static/views/effort.js`, `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-006-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 우선순위 P2-1 샘플.
- 검증한 것: 샘플 pytest 18, web 11 통과. 실제 모델로 경로 판정 32/32, 정답 있는 23턴에서 항상 fast 21, 항상 think 23, 라우팅 23(토큰 4,036 vs 4,738). 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-006-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 실제 상위 모델 이관(로컬에 없음).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain, langchain-typesafe, langchain-openai, python-dotenv, 기존 샘플과 같은 구성). web 의존성 변경 없음.
- 남은 일: 없음.
