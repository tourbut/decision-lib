---
title: "DEV-005 — P1-2 인용 검증 샘플(#4)과 P1-3 판정 보정·순서 편향 샘플(#15 #24)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-005]
summary: "P1-2 인용 검증 샘플(#4)과 P1-3 판정 보정·순서 편향 샘플(#15 #24)을 웹 화면까지 추가"
attempt: abee2cb98bdb4fc7901c6b1f73286375
base: 5b8c2109adf3fdc7a17d9bbd1bf37ff01d76c6bf
subagent_level: lite
test_level: lite
---

# DEV-005 — P1-2 인용 검증 샘플(#4)과 P1-3 판정 보정·순서 편향 샘플(#15 #24)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 샘플 2개와 web 어댑터·화면 추가, fullops/dev·main push, 이슈 #4·#15·#24 댓글·종료. 독립 리뷰는 사용자가 이 레포 전체에 면제했다.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- 사용자 요청 "다음 예제들 구현해": 우선순위 P1-2(#4 인용 검증), P1-3(#15 대량 분류 보정, #24 순서 편향)를 이어서 만든다.
- 기존 샘플 3개(discovery-review, rag-passage-filter, tool-call-gate)와 web/ 구조(adapters/, static/views/)를 따른다.
- d3-flash 사전 확인: Choice 1문항 요청 약 0.13초. NSMC 60건에서 선택지 순서를 바꿔도 판정이 바뀐 건이 없었다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 사용자 지시로 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다.
- 예외: 독립 리뷰 면제(waiver). NSMC는 CC0 공개 데이터라 200건만 레포에 넣는다.

## 해야 할 일과 파일 소유권

- [x] `samples/citation-check/`: 출처 문서, 라벨 인용 12건, 문자열 검사 → Choice → 4상태, 사람 검토 큐, 로컬 LLM 답변 인용 검사, 테스트, README 다이어그램
- [x] `samples/decision-calibration/`: NSMC 200건 Choice(두 순서)·Noul 정확도·ECE·Brier·검토 비율, 문의 라우팅 40건 순환 치환 변경률과 L0 보정, 테스트, README 다이어그램
- [x] `web/adapters/`, `web/static/views/`, `web/app.py`, `web/test_app.py`
- [x] 레포 README 표, `.fullops-squad/lint/lint.json` 테스트 등록, QA 보고

## 완료 기준과 검증

- 두 샘플 pytest와 web pytest 통과, 실제 d3-flash·로컬 LLM으로 demo 실행 결과를 README에 기록.
- 브라우저(데스크톱·390px)에서 두 화면을 실제 모델로 실행하고 콘솔 오류 0.
- lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 디자인 문서 / 테마·토큰 정본 경로: `web/static/style.css`의 `:root` 토큰
- 재사용할 공용 컴포넌트 경로: `web/static/common.js`(h, api, meter, badge, runBusy), 기존 `table.results`, `.meters`
- 디자인 lint: `lint.py --repo . --from <base>`, DESIGN 경고 0 유지
- 테마: 새 색 토큰을 추가하지 않는다. 다크 모드는 기존 토큰 경로를 그대로 쓴다.

## 갱신할 산출물

없음(샘플 레포, 산출물 문서 체계 미사용). QA 보고만 `docs/evaluations/qa-reports/DEV-005-test/`에 남긴다.

## 기대 산출물

두 샘플 폴더, web 어댑터·화면, QA 보고, 이 지시서의 완료 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음(모델은 로컬). IMDb 25,000건 재현은 범위 밖.

## 완료 보고

- 브랜치 / SHA: fullops/dev / b109f72 (feat: 인용 검증·판정 보정 샘플 추가)
- 변경 이유: 사용자 요청 "다음 예제들 구현해"에 따라 P1-2(#4)와 P1-3(#15 #24) 샘플을 추가했다.
- 검증한 것: 샘플 pytest 6+6, web 10 통과. 실제 d3-flash로 citation-check 15/15, NSMC 200건과 문의 40건 측정. 브라우저 1440px·390px에서 두 화면을 실제 모델로 실행, 콘솔 오류 0. 근거는 `docs/evaluations/qa-reports/DEV-005-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비 측정. 화면에서 NSMC 200건 전체 실행(40건만 확인). IMDb 25,000건 재현은 범위 밖.
- lint: 오류 0. SLOP-004는 demo.py의 CLI 출력이다. LINT-001은 새 샘플 테스트 2개 등록이다.
- DEP-001: 새 샘플 pyproject 2개. citation-check는 기존 샘플과 같은 langchain-typesafe, langchain-openai(LLM 답변 생성), python-dotenv. decision-calibration은 langchain-typesafe, python-dotenv만 쓴다. 지표 계산은 표준 라이브러리로 했다. web 의존성 변경 없음.
- SIZE-002: 샘플 2개를 코드·데이터(NSMC 200줄 포함)·README·웹 화면과 함께 한 번에 추가했다. 샘플마다 독립 폴더라 나눠도 리뷰 단위가 바뀌지 않는다.
- 남은 일: 주소창 해시만 바꾸면 화면이 바뀌지 않는 기존 동작(범위 밖). L0 효과는 40건에서 1건 차이라 일반화하지 않는다.
