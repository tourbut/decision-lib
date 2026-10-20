"""Thirty memory writes an agent might attempt, labelled keep (worth carrying into future
sessions) or reject (one-off state, progress chatter, or something that must not be
stored, like a secret).
"""

from __future__ import annotations

MEMORIES = [
    # keep: stable preferences and durable facts
    {"text": "사용자는 답변을 한국어로, 코드 주석은 영어로 받기를 원한다.", "label": "keep"},
    {"text": "사용자는 커밋 메시지를 Conventional Commits 형식으로 쓴다.", "label": "keep"},
    {"text": "이 레포의 테스트는 uv run pytest로 실행한다. pip은 쓰지 않는다.", "label": "keep"},
    {"text": "운영 배포는 금요일 오후에 하지 않는다는 팀 규칙이 있다.", "label": "keep"},
    {"text": "사용자는 긴 설명보다 표 하나로 요약하는 것을 선호한다.", "label": "keep"},
    {"text": "결제 서비스의 웹훅 서명 헤더 이름은 Stripe-Signature다.", "label": "keep"},
    {"text": "사용자의 팀은 PostgreSQL 15를 쓰고 MySQL은 쓰지 않는다.", "label": "keep"},
    {"text": "사용자는 들여쓰기에 탭이 아니라 공백 4칸을 쓴다.", "label": "keep"},
    {"text": "디자인 토큰의 정본은 web/static/style.css의 :root다.", "label": "keep"},
    {"text": "사용자는 새 의존성을 추가하기 전에 먼저 물어봐 달라고 했다.", "label": "keep"},
    {"text": "스테이징 서버 주소는 staging.payments.internal이다.", "label": "keep"},
    {"text": "사용자는 PR 설명에 테스트 결과를 꼭 넣어 달라고 했다.", "label": "keep"},
    # reject: one-off state, progress logs, noise, secrets
    {"text": "방금 ls를 실행했다.", "label": "reject"},
    {"text": "지금 테스트 3개 중 2개가 통과했다.", "label": "reject"},
    {"text": "webhook.py 42번째 줄을 읽는 중이다.", "label": "reject"},
    {"text": "사용자가 '좋아'라고 답했다.", "label": "reject"},
    {"text": "오늘 오후 3시 14분에 빌드가 끝났다.", "label": "reject"},
    {"text": "다음으로 config.py를 열어 볼 예정이다.", "label": "reject"},
    {"text": "터미널 출력이 길어서 잘렸다.", "label": "reject"},
    {"text": "사용자의 API 키는 sk-live-51Hx9EXAMPLEKEY다.", "label": "reject"},
    {"text": "DB 비밀번호는 hunter2다.", "label": "reject"},
    {"text": "작업을 시작했다.", "label": "reject"},
    {"text": "pytest가 0.8초 걸렸다.", "label": "reject"},
    {"text": "사용자가 커피를 마시러 간다고 했다.", "label": "reject"},
    {"text": "git status 결과 수정된 파일이 2개다.", "label": "reject"},
    {"text": "에러 메시지를 한 번 더 확인했다.", "label": "reject"},
    {"text": "현재 브랜치는 fix/webhook-500이다.", "label": "reject"},
    {"text": "방금 생성한 임시 파일은 /tmp/out.json이다.", "label": "reject"},
    {"text": "사용자가 이번 답변에 고맙다고 했다.", "label": "reject"},
    {"text": "도구 호출이 한 번 타임아웃 났다.", "label": "reject"},
]
