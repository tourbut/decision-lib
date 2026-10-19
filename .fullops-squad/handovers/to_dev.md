---
title: "DEV-004 — 도구 호출 게이트 샘플 (allow/ask/block, 이슈 #7 #6 #27 #38)"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-004]
summary: "도구 호출 게이트 샘플 (allow/ask/block, 이슈 #7 #6 #27 #38)"
attempt: d3ca59519a7a46d78d715a2963355aaa
base: 0b284f4c431c83e7972e3d755561bef657ea4b7e
subagent_level: lite
test_level: lite
---

# DEV-004 — 도구 호출 게이트 샘플 (allow/ask/block, 이슈 #7 #6 #27 #38)

- 작성일: 2026-10-20
- From / To: 사용자 / dev 주 담당(직접 작업)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위: `samples/tool-call-gate/` 신규, `web/` 어댑터·화면, 레포 README 샘플 표, lint 테스트 명령 등록 / 추가 승인 행위 없음
- 담당 워크트리 / 브랜치: /home/shin/workspace/decision-lib-dev / fullops/dev, 기본 브랜치 main
- 독립 리뷰: 사용자 결정으로 생략(`review_policy`)

## 현재 상황과 확인 근거

- 기준 SHA `0b284f4`. 사용자가 이슈 우선순위의 P1-1을 "사례대로 phase 진행"으로 승인했다.
- 원천: 이슈 #7, #6, #27, #38. langchain-typesafe 0.0.1a3의 `AutoModeMiddleware` 소스를 확인했다. 이 미들웨어는 차단만 하고 사람 확인은 하지 않는다. langchain 1.4.6의 `AgentMiddleware.wrap_tool_call`도 확인했다.

## 해야 할 일

- [x] `gate.py`: 차단 규칙, 비밀 마스킹, d3-flash 질문 5개(verdict Choice, Noul 3개, Score 1개), 순서가 고정된 분기
- [x] `cases.py`: 라벨 50건(allow 18, ask 15, block 17). `demo.py`: 규칙만 쓸 때와 비교, 에이전트 과제 3개
- [x] `agent.py`: `GateMiddleware`(ask는 `interrupt()`), dry-run 도구, 가짜 README에 키 발송 단계 포함
- [x] 오프라인 `test_gate.py`, README(mermaid 2개), 레포 README, `lint.json`
- [x] `web/adapters/toolgate.py`(setup/check/eval/agent), `app.js` 화면, 웹 테스트 2개

## 완료 기준과 검증

- 오프라인 pytest: 샘플 26, web 7 통과.
- 실제 모델: 라벨 50건에서 규칙만 26/50, 규칙 + d3-flash 48/50. block 라벨이 실행된 건수는 9에서 0으로 줄었다. 에이전트는 키 조회를 차단했다.
- 브라우저: 세 기능, 다이어그램 2개, 모바일 390px를 확인했다.

## 완료 보고

- 변경: `samples/tool-call-gate/`(gate, cases, agent, demo, test_gate, README), `web/adapters/toolgate.py`, `web/app.py`, `web/static/app.js`, `web/static/`(공용 도구는 `common.js`, 샘플별 화면은 `views/*.js`로 분리. `style.css`에 select 스타일 추가), `web/test_app.py`, `web/pyproject.toml`, 레포 README, `lint.json`.
- 검증: `.fullops-squad/docs/evaluations/qa-reports/DEV-004-test/report.md`.
- 설계 판단: 처음 쓴 `task_aligned` Noul은 d3-flash가 관련성과 위험을 섞어 판단해 38/50에 그쳤다. 그래서 jev-approvals처럼 verdict Choice와 보조 질문, 코드 규칙을 조합하는 구조로 바꿨다. 과정은 README에 기록했다.
- 의존성(DEP-001): 샘플은 `langchain`(create_agent, 미들웨어), `langchain-typesafe==0.0.1a3`, `langchain-openai`, `python-dotenv`를 쓰고 개발용으로 `pytest`를 쓴다. web에는 샘플 import를 위해 `langchain`을 추가했다. 표준 라이브러리로는 대체할 수 없다.
- lint: SIZE-001(`app.js` 375줄)은 분할로 해소했다. SIZE-002(추가 900줄 이상)는 샘플 1개와 웹 화면 1개를 함께 추가해 생겼다. 독립 샘플 단위라 나누지 않았다. SLOP-004는 `demo.py`의 CLI 출력이라 유지했다.
- 미실행: 다크 모드, 키보드 전체 조작, 명암비 측정.
- 남은 일: 없음. #7의 모델 라우터 항목은 P2(#21 묶음)로 남는다.
