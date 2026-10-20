---
title: "DEV-015 — effort-router에 shadow·off 모드, 티어 설정 JSON, 비용 추정 추가(#8)"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-015]
summary: "effort-router에 shadow·off 모드, 티어 설정 JSON, 비용 추정 추가(#8)"
attempt: d8786e3f4cec4fa68278a2e69b91cc63
base: 6b3d946cedda449336d2649970f8f627cfa54f7b
subagent_level: lite
test_level: lite
---

# DEV-015 — effort-router에 shadow·off 모드, 티어 설정 JSON, 비용 추정 추가(#8)

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- 남은 이슈 #8(Hermes Jev Skills): shadow 모드 라우터, 로그 기반 비용 추정, 티어 설정 JSON. 기존 effort-router를 확장한다.
- 메모리·검색 항목 선택과 인젝션 판정은 rag-passage-filter·context-gate 샘플이 이미 다룬다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/effort-router/`: mode(on·shadow·off), tiers.json으로 모델 생성, shadow_report, demo --shadow, 테스트 3개 추가(21개), README
- [x] `web/adapters/effort.py`(모드, /shadow), `web/static/views/effort.js`(모드 선택, 비용 추정), `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-015-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 남은 이슈 #8.
- 검증한 것: 샘플 pytest 21, web 20 통과. 실제 모델로 shadow 32턴(think로 응답, 의도 fast 10·think 16·handoff 6, 추정 39% 절감, 실측 think 7,626토큰). 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-015-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 서로 다른 가격의 실제 모델 티어(같은 모델이라 가격 동일).
- lint: SLOP-004는 demo.py의 CLI 출력. 의존성 변경 없음.
- 남은 일: 없음.
