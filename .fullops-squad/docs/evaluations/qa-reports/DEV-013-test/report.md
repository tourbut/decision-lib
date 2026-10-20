---
title: DEV-013 판정 MCP 도구 QA
status: draft
updated: 2026-10-20
owner: dev
tasks: [DEV-013]
summary: "judgment-tools 샘플의 오프라인 테스트, MCP 경유 실제 모델 측정, 웹 화면 확인 결과"
---

# DEV-013 판정 MCP 도구 QA

- 대상: `samples/judgment-tools/`, `web/`의 judgment-tools 화면과 공통 스타일.
- 실행기: pytest, `demo.py`(stdio MCP 클라이언트), Playwright MCP(Chromium). 모델은 실제 d3-flash.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `samples/judgment-tools` | 7 passed. 산술만 계산, 실패 시 review·ESCALATE·normal_llm, 불확실한 APPROVE, verify 매핑, fastpath 후보 없음·단락·미달, 충돌 미병합, 같은 프로세스 MCP 왕복 |
| `uv run pytest -q` | `web` | 19 passed. MCP 경유 호출·잘못된 인자 422·측정, 정적 JS 모듈 구문 검사(node) |

## 실제 모델 측정 (stdio MCP 경유)

| 도구 | 결과 |
|---|---|
| fastpath 14턴 | 14/14(로컬 답 8개, 비슷한 턴 6개 normal_llm) |
| approval 10명령 | 10/10 |
| skill_relation 10쌍 | 9/10(Word 보고서 vs docx 작성·수정을 a_subset_of_b로) |

## 브라우저 확인

| 항목 | 결과 | 증거 |
|---|---|---|
| 도구 8개를 예시 인자로 호출, 권고 배지와 JSON | 통과 | `judgment-1440.png` |
| 잘못된 인자: 422와 검증 메시지 표시 | 통과 | — |
| 측정 3개: 14/14, 10/10, 9/10 | 통과 | — |
| 모바일 390px: 13개 샘플 화면 모두 가로 넘침 없음 | 통과(수정 후) | — |

## 확인 중 고친 결함

- fastpath의 "고정된 답으로 다 답할 수 있나" 질문이 감사 인사도 0.83에 머물러 8/14였다. "오직 X만 묻나"로 바꿔 14/14.
- 계산식 추출이 여는 괄호를 놓쳤다.
- MCP 클라이언트 컨텍스트 안에서 HTTPException을 던지면 ExceptionGroup으로 감싸져 500이 됐다. 컨텍스트를 닫은 뒤 던진다.
- judgment.js의 괄호 하나가 남아 화면 전체가 빈 채로 떴다. node로 정적 JS를 구문 검사하는 web 테스트를 추가했다.
- 모바일에서 샘플이 13개가 되자 가로 목록의 최소 폭이 페이지를 넓혔다(`grid-template-columns: minmax(0, 1fr)`). 가운뎃점으로만 이어진 요약 문장도 줄바꿈되게 했다.

## 미실행

- 다크 모드, 키보드 전체 조작, 명암비: not_run.
- Claude Code·Hermes에 실제 등록: not_run(설정 예시만).
