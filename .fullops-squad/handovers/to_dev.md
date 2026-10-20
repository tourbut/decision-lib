---
title: "DEV-009 — P2-4 필요도 기반 압축·메모리 저장 판정 샘플(#11 #32 #33)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-009]
summary: "P2-4 필요도 기반 압축·메모리 저장 판정 샘플(#11 #32 #33)을 웹 화면까지 추가"
attempt: cd0969b3abbd483d9cc719f8435bbc95
base: bdea23e492a46201a6167f9c641bed188358dbf4
subagent_level: lite
test_level: lite
---

# DEV-009 — P2-4 필요도 기반 압축·메모리 저장 판정 샘플(#11 #32 #33)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- P2-4: #11(점수 기반 압축), #32(jev-compaction), #33(jev-memory-gate).
- 압축은 LangChain 메시지(ToolMessage)를 같은 id로 바꿔 행 수를 지킨다. 메모리는 remember 도구 호출을 감싼다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/context-gate/`: 세션 12쌍·필요 사실 3개, keep/shrink/drop 판정과 미들웨어, 메모리 30건·비밀 정규식·임계값 비교·미들웨어, 라이브 에이전트, 테스트 6개, README 다이어그램
- [x] `web/adapters/context.py`, `web/static/views/context.js`, `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-009-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 우선순위 P2-4 샘플.
- 검증한 것: 샘플 pytest 6, web 14 통과. 실제 모델로 압축 라벨 10/12(필요도 1,986자·사실 3/3, 크기 기반 2,253자·사실 1/3), 메모리 29/30, 라이브 에이전트 5건 중 3건 거절. 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-009-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 토큰 단위 측정(글자 수로 대신).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain, langchain-typesafe, langchain-openai, python-dotenv, 기존 샘플과 같은 구성). web 의존성 변경 없음.
- 남은 일: 없음.
