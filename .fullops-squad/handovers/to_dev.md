---
title: "DEV-010 — P2-5 화면 캡처 기반 사칭 로그인 판정 샘플(#22 #26)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-010]
summary: "P2-5 화면 캡처 기반 사칭 로그인 판정 샘플(#22 #26)을 웹 화면까지 추가"
attempt: 0c68879491454beba4fe006b3dfc9d6c
base: ab1d8d89fda3522a78ad8850fc92bd34aab59655
subagent_level: lite
test_level: lite
---

# DEV-010 — P2-5 화면 캡처 기반 사칭 로그인 판정 샘플(#22 #26)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- P2-5: #22(Clef 멀티모달), #26(Decision 3.0 멀티모달 가드레일). d3-flash는 이미지 입력을 받는다(/v1/models modalities).
- 로컬 서버는 요청 최상위 images 배열에서 이미지를 읽는다. langchain-typesafe는 이를 보내지 않아 하위 클래스로 덧붙인다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/screenshot-check/`: 가상 페이지 16개와 캡처, 브랜드·비밀번호 판정 + 호스트 등록 목록, ImageClassifier, 화면·텍스트 비교 demo, render.py, 테스트 11개, README 다이어그램
- [x] `web/adapters/screenshot.py`, `web/static/views/screenshot.js`, `web/static/style.css`(캡처 미리보기), `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-010-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 우선순위 P2-5 샘플.
- 검증한 것: 샘플 pytest 11, web 15 통과. 실제 d3-flash로 화면 16/16(사칭 8/8), 텍스트만 11/16(사칭 4/8). 브라우저 1440px·390px, 업로드·URL 변경 판정, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-010-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 실제 피싱 페이지 캡처(가상 페이지로 대신). 측정 중 d3-flash 컨테이너가 외부에서 재시작됨(원인 미확정).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain-typesafe, python-dotenv만). PNG 16개(240KB) 추가. web 의존성 변경 없음.
- 남은 일: 없음.
