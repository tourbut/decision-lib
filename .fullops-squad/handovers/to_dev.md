---
title: "DEV-008 — P2-3 검색 리랭킹 샘플(#5 #17)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-008]
summary: "P2-3 검색 리랭킹 샘플(#5 #17)을 웹 화면까지 추가"
attempt: 19308627de35410390da61588a74cd33
base: cb81fc2a5117ae227318574efa5ca7ba3e9eff89
subagent_level: lite
test_level: lite
---

# DEV-008 — P2-3 검색 리랭킹 샘플(#5 #17)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- P2-3: #5(검색 리랭킹), #17(결과 관련도 채점). 공개 벤치마크 SciFact(BEIR, CC BY-NC 2.0) 일부를 넣어 nDCG@10으로 잰다.
- 사전 측정: 질의 30개 × 후보 30개에서 BM25 0.692, 관련도 루브릭 0.698. 개선 폭이 작아 RRF 결합을 더했다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/rerank/`: SciFact 부분집합(질의 30, 초록 810), BM25, Score 루브릭 2개, RRF, nDCG·recall, demo, 테스트 5개, README 다이어그램, 데이터 출처·라이선스
- [x] `web/adapters/rerank.py`, `web/static/views/rerank.js`, `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-008-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 우선순위 P2-3 샘플.
- 검증한 것: 샘플 pytest 5, web 13 통과. 실제 d3-flash로 질의 30개 측정(BM25 0.692, 관련도 0.698, 근거 0.681, RRF 0.708, 이상치 0.820). 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-008-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. SciFact 전체 300질의(약 70분), jev-search의 검색 소스·기간 선택(검색 API 없음).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain-typesafe, python-dotenv만). web 의존성 변경 없음.
- 남은 일: 없음.
