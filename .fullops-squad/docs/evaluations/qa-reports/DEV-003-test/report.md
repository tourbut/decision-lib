---
title: DEV-003 샘플 웹 QA
status: draft
updated: 2026-10-19
owner: dev
tasks: [DEV-003]
summary: 샘플 웹의 오프라인 테스트와 실제 모델 브라우저 확인 결과
---

# DEV-003 샘플 웹 QA

- 대상: `web/`(FastAPI + 정적 HTML/JS), fullops/dev 작업 트리(커밋 전 상태, 기준 `61b2337`).
- 실행기: Playwright MCP(Chromium), 로컬 서버 `uvicorn app:app --port 8300`, 실제 d3-flash와 muse-glimmer-30b.

## 자동 검사

| 명령 | cwd | 결과 |
|---|---|---|
| `uv run pytest -q` | `web` | 5 passed (스텁 모델: 샘플 목록, discovery 실행·재개, 재개 거부 404/409, rag 질의, 모델 연결 실패 502) |
| `uv run pytest -q` | `samples/rag-passage-filter` | 10 passed |
| `uv run pytest -q` | `samples/discovery-review` | 15 passed |

## 브라우저 확인 (실제 모델)

| 항목 | 결과 | 증거 |
|---|---|---|
| rag: 기본 질의 실행, 답변·문단 6개·막대 눈금 표시 (1440px) | 통과 | `rag-results-1440.png` |
| rag: 틀린 전제 질의, 충돌 3개·답변 반박, 다이어그램 렌더 | 통과 | `rag-false-premise-v2.png` |
| discovery: 6페이지 실행, 변호사 검토 3건 대기 | 통과 | `discovery-pending.png` |
| discovery: 결정 입력 후 재개, 6건 처리 완료 | 통과 | `discovery-resumed.png` |
| discovery: 다이어그램 2개 렌더(로컬 mermaid) | 통과 | `discovery-diagrams.png` |
| 모바일 390px: 가로 스크롤 없음(scrollWidth 375), 표 세로 배치 | 통과 | `rag-mobile-v2.png` |
| 다크 모드 토큰 | 통과(시각 확인) | `rag-dark.png` |

## 확인 중 고친 결함

- CDN mermaid가 인증서 오류로 로드 실패 → `static/vendor/`에 mermaid 11.4.1 번들을 두었다.
- 문단 본문이 표 밖으로 넘침, 사이드바 경계선이 화면 높이에서 끊김, 채택 근거 막대가 경고색으로 보임, 모바일에서 문단 열이 46%로 좁음 → CSS 수정 후 재확인.
- 다이어그램 실패 시 원문 대신 `[object HTMLPreElement]` 출력 → 수정(실패 경로는 브라우저에서 재현하지 않음).

## 미실행

- 키보드만으로 전체 조작, 명암비 수치 측정, reduced-motion: not_run. 포커스 링(`:focus-visible`)은 CSS로만 확인했다.
- 모델 서버 중단 상태의 화면 오류 표시: 브라우저 not_run. API 502 응답은 테스트로 확인했다.
