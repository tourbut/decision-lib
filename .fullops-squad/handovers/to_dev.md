---
title: "DEV-013 — P3-3 판정 MCP 도구 샘플(#9 #35 #36 #28 #31 #34)을 웹 화면까지 추가"
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-013]
summary: "P3-3 판정 MCP 도구 샘플(#9 #35 #36 #28 #31 #34)을 웹 화면까지 추가"
attempt: 21a346ea8f0545aca988125dacac7228
base: 98b80c9d368533dd340f96bc57a2112393096bad
subagent_level: lite
test_level: lite
---

# DEV-013 — P3-3 판정 MCP 도구 샘플(#9 #35 #36 #28 #31 #34)을 웹 화면까지 추가

- 작성일: 2026-10-20
- From / To: 사용자 → dev(현재 세션)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위 / 추가 승인이 필요한 행위: 사용자 지시 "순서대로해서 나한테 물어보지말고 끝가지 진행해". 샘플·web 추가, fullops/dev·main push, 이슈 댓글·종료. 독립 리뷰 면제.
- 담당 repo id / 워크트리 절대경로 / 브랜치: decision-lib / /home/shin/workspace/decision-lib-dev / fullops/dev
- 병합 책임자 / 기본 브랜치: dev(현재 세션) / main

## 현재 상황과 확인 근거

- P3-3: #9(jev-mcp), #35(호출형 판단 도구), #36(로컬 백엔드), #28(structured-aux), #31(fastpath), #34(jev-curator).
- MCP Python SDK는 2.x(MCPServer, Client)가 설치된다. 서버는 stdio와 같은 프로세스 연결 둘 다 시험한다.

## 적용 기준과 예외

- 공통 규칙 `.fullops-squad/rules/common/README.md`. 새 샘플은 README mermaid 다이어그램과 web 어댑터·화면을 갖춘다. 독립 리뷰는 면제(waiver).

## 해야 할 일과 파일 소유권

- [x] `samples/judgment-tools/`: tools.py 8개 판정, MCP 서버(stdio), 라벨 세트 3개, stdio 클라이언트 demo, 테스트 7개(MCP 왕복 포함), README 다이어그램 2개
- [x] `web/adapters/judgment.py`(같은 프로세스 MCP 클라이언트), `web/static/views/judgment.js`, `web/pyproject.toml`(mcp 추가), `web/static/style.css`(모바일 가로 넘침 수정), `web/app.py`, `web/static/app.js`, `web/test_app.py`
- [x] 레포 README 표, lint.json 테스트 등록, QA 보고

## 완료 기준과 검증

- 샘플·web pytest 통과, 실제 모델 측정 결과 README 기록, 브라우저 1440px·390px 확인, lint 오류 0.

### UI 작업의 디자인 기준과 검증

- 토큰 정본 `web/static/style.css`의 `:root`, 공용 `web/static/common.js`. 새 색 토큰 없음.

## 갱신할 산출물

없음. QA 보고는 `docs/evaluations/qa-reports/DEV-013-test/`.

## 기대 산출물

샘플 폴더, web 어댑터·화면, QA 보고.

## 제약·협업·후속

- 하위 위임 없음. 외부 전송 없음.

## 완료 보고

- 변경 이유: 우선순위 P3-3 샘플.
- 검증한 것: 샘플 pytest 7, web 19 통과(정적 JS 구문 검사 테스트 추가). 실제 d3-flash로 stdio MCP 경유 fastpath 14/14, approval 10/10, skill_relation 9/10. 브라우저 1440px·390px(13개 샘플 화면 모두 가로 넘침 없음), 콘솔 오류는 의도한 422 하나. 근거 `docs/evaluations/qa-reports/DEV-013-test/report.md`.
- 못 한 것: 다크 모드, 키보드 전체 조작, 명암비. Claude Code·Hermes에 실제로 등록해 쓰기(설정 예시만).
- lint: SLOP-004는 demo.py의 CLI 출력. DEP-001은 새 샘플 pyproject(langchain-typesafe, mcp, python-dotenv). mcp는 MCP 서버·클라이언트에 필요하고 표준 라이브러리 대안이 없다. web에도 mcp를 더했다. web 의존성 변경 없음.
- 남은 일: 없음.
