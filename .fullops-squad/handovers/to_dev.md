---
title: "DEV-007 — P2-2 작업 완료 판정 샘플(#10 #37)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-007]
summary: "P2-2 작업 완료 판정 샘플(#10 #37)을 웹 화면까지 추가"
attempt: 0fa8463694d641558b99f9d4aec32fe2
base: 44e808bb363b9dc0d75400ab852046bbea6ff195
subagent_level: lite
test_level: lite
---

# DEV-007 — P2-2 작업 완료 판정 샘플(#10 #37)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- P2-2: #10(Foreman), #37(pre_verify 완료 판정). 실제 코드 실행 대신 하네스가 넘기는 변경 파일·테스트 결과를 입력으로 둔다.
- 기존 샘플의 web 로더가 샘플 간 같은 모듈 이름(check.py)을 구분하지 못해 함께 고친다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/completion-check/`: 라벨 30건, Noul 5개 판정, pass·steer·halt, 시도 상한, fail-open, after_model 미들웨어, 라이브 demo, 테스트 14개, README 다이어그램
- [x] `web/adapters/completion.py`, `web/static/views/completion.js`, `web/adapters/__init__.py`(모듈 이름 충돌), `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-007-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 우선순위 P2-2 샘플.
- 검증한 것: 샘플 pytest 14, web 12 통과. 실제 d3-flash로 라벨 30건 29/30, 라이브 에이전트 정상 1회 pass·덜 된 초안 steer→pass. 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-007-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 실제 코드 수정·테스트 실행 루프(트랜스크립트로 대신).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain, langchain-typesafe, langchain-openai, python-dotenv, 기존 샘플과 같은 구성). web 의존성 변경 없음.
- 남은 일: 없음.
