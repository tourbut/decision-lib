---
title: "DEV-017 — 합성 주문장 dry-run 샘플(#20)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-017]
summary: "합성 주문장 dry-run 샘플(#20)을 웹 화면까지 추가"
attempt: 8dd03c3519ab4843a455f2cdd02e2e81
base: 9fe08a3f0ee7ea3d16ac7d12a3e345c0e310feed
subagent_level: lite
test_level: lite
---

# DEV-017 — 합성 주문장 dry-run 샘플(#20)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- 남은 이슈 #20(jev-trader). 실자금·거래소 연결 없이 합성 주문장으로만 한다.
- 첫 구현은 다음 블록 가격으로 체결해 신호를 버렸고, 스프레드가 신호보다 커 모든 정책이 손해였다. 체결가와 비용을 고쳤다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/order-sim/`: 합성 시장, 정책 4개, 늦은 결정·포지션 한도·손실 한도, 테스트 7개, README 다이어그램
- [x] `web/adapters/order.py`, `web/static/views/order.js`, `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-017-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 남은 이슈 #20.
- 검증한 것: 샘플 pytest 7, web 22 통과. 실제 d3-flash로 200블록 손익 +0.024(적중 70%), 동전 던지기는 손실 한도로 중단, 50ms 예산이면 전부 보류. 브라우저 1440px·390px, 콘솔 오류 0. 근거 `docs/evaluations/qa-reports/DEV-017-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. 실제 시장 데이터(의도적으로 사용 안 함).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain-typesafe, python-dotenv만). web 의존성 변경 없음.
- 남은 일: 없음.
