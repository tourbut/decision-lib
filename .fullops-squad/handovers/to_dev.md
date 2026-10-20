---
title: "DEV-011 — P3-1 스킬 추천·255개 초과 계층 선택 샘플(#2 #14)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-011]
summary: "P3-1 스킬 추천·255개 초과 계층 선택 샘플(#2 #14)을 웹 화면까지 추가"
attempt: 04dae3ef18894fd5b2ae5ff5efdf1d85
base: 482f33ce07ac66adc12f79a1f00b0ad820eabf9a
subagent_level: lite
test_level: lite
---

# DEV-011 — P3-1 스킬 추천·255개 초과 계층 선택 샘플(#2 #14)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- P3-1: #2(스킬 추천), #14(255개 초과 계층 분류). d3-flash는 Choice 선택지 256개부터 422를 돌려준다(직접 확인).
- 255개 초과 예제는 표준 라이브러리 zoneinfo의 IANA 시간대 448개로 만든다(내려받기 없음).

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/many-options/`(DEV-010 커밋에 섞인 `skill-picker/skills.py`를 옮김): 스킬 24개·요청 40개, 1단계 순위 → 상위 3개 재검토, 시간대 448개 지역→시간대 2단계, 테스트 6개, README 다이어그램
- [x] `web/adapters/many.py`, `web/static/views/many.js`, `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-011-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 우선순위 P3-1 샘플.
- 검증한 것: 샘플 pytest 6, web 16 통과. 실제 d3-flash로 스킬 39/40(1단계만도 39/40), 시간대 39/40, 448개 한 번에 묻기는 422. 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-011-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 국세청 서식 같은 실제 공공 서식 PDF 분류(시간대 카탈로그로 같은 패턴을 대신).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain-typesafe, python-dotenv만). web 의존성 변경 없음.
- 남은 일: 없음.
