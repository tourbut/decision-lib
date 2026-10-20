---
title: "DEV-012 — P3-2 다음 행동 선택 샘플(#1 #19 #18)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-012]
summary: "P3-2 다음 행동 선택 샘플(#1 #19 #18)을 웹 화면까지 추가"
attempt: 3ca53a9cd4954b7ea774d8d29a26c480
base: 691217ffc71d449d1f83aa56c16ed4b365dbe069
subagent_level: lite
test_level: lite
---

# DEV-012 — P3-2 다음 행동 선택 샘플(#1 #19 #18)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- P3-2: #1(브라우저 다음 행동), #19(데스크톱 조작), #18(플래너 + 컨트롤러).
- 실제 브라우저·OS 조작 없이 정적 HTML, 접근성 트리 모의, 텍스트 격자로 같은 고르기 함수를 시험한다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/action-picker/`: 공통 pick·run, 웹 15쪽, 설정 앱, 격자 3지도·3가지 후보 방식·stage guard, 테스트 7개, README 다이어그램
- [x] `web/adapters/action.py`, `web/static/views/action.js`, `web/static/style.css`(지도·실행 블록), `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-012-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 우선순위 P3-2 샘플.
- 검증한 것: 샘플 pytest 7, web 17 통과. 실제 d3-flash로 웹 7/8, 설정 앱 6/6, 격자 높은 수준 행동 3/3(최단 경로), 한 칸 이동 0/3. 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-012-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 실제 브라우저(Playwright)·OS 조작, 입력 문자열 생성(TYPE_TEXT).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain-typesafe, python-dotenv만). web 의존성 변경 없음.
- 남은 일: 없음.
