---
title: DEV-003 — 샘플 테스트 웹 UI와 샘플 README 다이어그램
status: draft
updated: 2026-10-19
owner: dev
tasks: [DEV-003]
summary: 샘플 테스트 웹 UI와 샘플 README 다이어그램
attempt: fab026d7e64e4c4298727a011d18a779
base: 61b2337033aa6cfcbbed40aa411a936cb9afb2ed
subagent_level: lite
test_level: lite
---

# DEV-003 — 샘플 테스트 웹 UI와 샘플 README 다이어그램

- 작성일: 2026-10-19
- From / To: 사용자 / dev 주 담당(직접 작업)
- 상태: done
- 테스트 레벨 / 하위 에이전트 레벨: lite / lite
- 승인된 범위: 레포 루트 `web/` 신규, 샘플 README에 mermaid 다이어그램, 레포 README 갱신 / 추가 승인 행위 없음
- 담당 워크트리 / 브랜치: /home/shin/workspace/decision-lib-dev / fullops/dev, 기본 브랜치 main
- 독립 리뷰: 사용자 결정으로 생략(`review_policy`)

## 대상과 실행 선택 (fullops-frontend)

- 대상: `web/` 단일 페이지. 사용자는 레포 개발자. 주요 행동: 샘플 선택 → 흐름 다이어그램 확인 → 입력 실행 → 판정 확률·임계값·경로 확인. discovery-review는 변호사 결정 입력 후 재개.
- 호스트 / 모델 / effort: claude-code / claude-opus-5-5 / high. 주 스킬 `frontend-design`, 보조 없음. `frontend.py --check`: 디자인 정본 미지정 외 이상 없음. authentication·browser_qa·mcp_connection은 not_run.
- 디자인 정본: 기존 화면 없음. 새 정본은 `web/static/style.css`의 `:root` 토큰 한 곳.
- 방향: 화면의 강조점은 판정 확률 막대에 그린 임계값 눈금 하나다. 경로 색은 의미(채택·충돌/검토·제외·인젝션)에만 쓴다. 크림 배경, 테라코타 강조, 동일 카드 반복, 대문자 라벨, 모노스페이스 데이터 라벨, 외부 폰트 로드는 피한다.
- 상태: 모델 서버 연결 실패 오류, 실행 중, 빈 결과, 모바일 폭(사이드바 → 상단 선택), 다크 모드 토큰, 키보드 포커스.

## 해야 할 일

- [x] 샘플 README에 흐름 mermaid 다이어그램 (discovery-review 2개, rag-passage-filter 1개)
- [x] `web/` FastAPI 백엔드: 샘플 목록·README 다이어그램, discovery 실행/재개, rag 질의
- [x] `web/static/` 화면
- [x] 오프라인 테스트(스텁 모델 주입), lint 명령 등록
- [x] 실제 모델로 브라우저 확인과 캡처, mermaid 렌더 확인

## 완료 기준과 검증

- 오프라인 `pytest` 통과. 실제 d3-flash·로컬 LLM으로 두 샘플을 브라우저에서 끝까지 실행하고, 다이어그램 3개가 렌더된다(Playwright 캡처).

## 완료 보고

- 변경: `web/`(app.py, adapters/, static/, test_app.py, README), 샘플 README 다이어그램, 레포 README, `lint.json`에 `web-test` 등록, `frontend.json` 디자인 정본 `web/static/style.css`.
- 검증: `.fullops-squad/docs/evaluations/qa-reports/DEV-003-test/report.md`. web 5, rag 10, discovery 15 passed. 실제 모델로 두 샘플 브라우저 실행·재개·다이어그램 3개 렌더·모바일·다크 확인.
- 의존성(DEP-001): `web/` 신규 `fastapi`, `uvicorn`(서버), 샘플 런타임 의존성 합집합, 개발용 `pytest`·`httpx`(TestClient). mermaid 11.4.1 번들(MIT, 라이선스 동봉)은 폐쇄망에서 다이어그램을 그리기 위해 vendor로 둔다.
- 미실행: 키보드 전체 조작, 명암비 측정, 모델 중단 시 화면 오류 표시(API 502는 테스트됨).
- 남은 일: 없음.
