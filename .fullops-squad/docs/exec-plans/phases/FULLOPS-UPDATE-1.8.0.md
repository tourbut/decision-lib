---
title: FullOps 1.8.0 업데이트 적용 기록
status: draft
updated: 2026-10-21
owner: dev
summary: decision-lib 레포에 FullOps 1.7.1·1.8.0 릴리스를 적용한 판정·변경·검증 기록
---

# FullOps 1.8.0 업데이트 적용 기록

## 버전

| 항목 | 값 |
|---|---|
| 업데이트 전 레포 적용 버전(`plugin_version`) | 1.7.0 |
| 이 세션이 쓰던 패키지 | 1.7.0(세션 시작 시 로드) |
| 업데이트 전 실제 설치 버전 | 1.8.0. Claude Code 플러그인이 2026-10-20 23:23(UTC)에 이미 1.8.0으로 갱신돼 있었다(호스트 자동 업데이트로 보임). 적용 기준은 레포 적용 버전 1.7.0 |
| 대상 버전 | 1.8.0(`claude plugin update` 결과 최신) |
| hook 런타임 | `~/.fullops-squad/runtime/fullops-squad/current.json` = 1.8.0 |

## 설치·의존성

- `claude plugin marketplace update fullops-squad`, `claude plugin update fullops-squad@fullops-squad`: 이미 최신(1.8.0).
- `scripts/deps.py --host claude-code`: 완료(ponytail 5.3.2, mattpocock-skills 1.3.1 최신 확인, 공통 스킬 갱신).
- `scripts/deps.py --check --host claude-code`: 호스트 의존성 검증 완료.
- `frontend.json`의 선택 도구(`tools`)는 비어 있어 추가 설치 없음.
- `setup.py --repo . --dry-run --roles dev`: 생성 예정 0개.

## 릴리스별 판정

| 릴리스 | 항목 | 판정 | 근거·변경 |
|---|---|---|---|
| 1.7.1 | deps 실행·검사 | 적용 | 위 설치·의존성 절 |
| 1.7.1 | 레포 파일 변경 | 해당 없음 | 릴리스가 "레포 파일 변경 없음"으로 명시. 스킬 절차 변경(reload 안내, non-FF 병합 검증)은 새 스킬을 읽으면 적용 |
| 1.8.0 | 1. deps 실행·검사 | 적용 | 위와 같음 |
| 1.8.0 | 2. 핸드오버 템플릿 추가 문장 | 적용 | `.fullops-squad/handovers/_TEMPLATE.md`를 1.8.0 템플릿으로 교체. 기존 파일은 이전 템플릿 원본 그대로여서 통합할 사용자 수정이 없었다 |
| 1.8.0 | 3. 진행 중 과제 패킷 재생성 | 해당 없음 | 진행 중 과제 없음(DEV-018 완료). 이 레포는 탐색 패킷을 쓰지 않았다 |
| 1.8.0 | 4. 증거 커밋 범위 | 적용 | `rules/common/testing.md`에 증거 범위 문단 추가, `rules/common/README.md` 규칙 묶음 `fullops-common-0.3.4`, `.fullops-squad/.gitignore`에 `docs/evaluations/qa-reports/**/raw/` 추가. 이미 커밋된 과거 캡처는 지우지 않았다(이력 보존) |

## 검증

- `lint.py --repo . --from fa4af9d`(1.8.0 lint): 첫 실행에서 이 기록의 front matter 형식(DOC-003) 1건이 나와 `deliverables.py --stamp`로 고쳤다. 고친 뒤 오류 0.
- 레포 코드·테스트 변경 없음.

## 보류

- 없음. 과거 QA 캡처를 `raw/`로 옮겨 용량을 줄이는 일은 릴리스가 별도 과제로 두었다. 이 레포의 `qa-reports/` 캡처는 판정 항목이 링크하는 파일 위주라 지금 하지 않는다.

## 다음 단계

- Claude Code: 사용자가 `/reload-plugins`를 실행해 로드 오류가 없으면 같은 세션에서 이어 간다. 그렇지 않으면 새 세션에서 진행한다.
