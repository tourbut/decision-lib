---
title: "DEV-016 — 뉴스 헤드라인-관심 주제 매칭 샘플(#16)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-016]
summary: "뉴스 헤드라인-관심 주제 매칭 샘플(#16)을 웹 화면까지 추가"
attempt: 50429cdce03c40119832dc09576b2469
base: 1513910c6ee2fb0bdfcdacab1fec65cb5595976d
subagent_level: lite
test_level: lite
---

# DEV-016 — 뉴스 헤드라인-관심 주제 매칭 샘플(#16)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- 남은 이슈 #16(newsjack).
- 외부 RSS 대신 가상 헤드라인 40개로 측정한다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/news-match/`: 헤드라인 40개·주제 5개, 주제별 Score, 기준별 정밀도·재현율, 테스트 3개, README 다이어그램
- [x] `web/adapters/news.py`, `web/static/views/news.js`(기준 바꾸면 다시 판정 없이 갱신, 헤드라인 붙여넣기), `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-016-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 남은 이슈 #16.
- 검증한 것: 샘플 pytest 3, web 21 통과. 실제 d3-flash로 기준 1.5 정밀도 1.00·재현율 0.93(200쌍 약 28초). 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-016-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 실제 RSS 피드.
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain-typesafe, python-dotenv만). web 의존성 변경 없음.
- 남은 일: 없음.
