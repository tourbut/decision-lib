"""A made-up catalog of 24 agent skills in 6 categories, and 40 labelled requests.

`label` is the one skill a careful reviewer would suggest, or "none" when no skill
fits or the request needs none. Some requests are near misses on purpose (a Mastodon
post when only an X skill exists), the failure the TypeSafe cookbook reports.
"""

from __future__ import annotations

CATEGORIES = {
    "docs": "문서·파일 만들기와 변환",
    "data": "데이터 분석과 시각화",
    "code": "코드 작성·검토·테스트",
    "ops": "배포·인프라·모니터링",
    "comms": "메일·메신저·SNS로 보내기",
    "web": "웹 검색·수집·브라우저 조작",
}

SKILLS = {
    "pdf-tools": ("docs", "PDF를 합치기·나누기·텍스트 추출·양식 채우기"),
    "docx-writer": ("docs", "Word(.docx) 보고서·계약서 작성과 수정, 변경 추적"),
    "slide-maker": ("docs", "발표 슬라이드(.pptx) 만들기"),
    "md-to-html": ("docs", "마크다운 문서를 HTML 페이지로 변환"),
    "csv-analyst": ("data", "CSV·엑셀 표를 읽어 집계·통계 요약"),
    "chart-builder": ("data", "숫자 데이터로 막대·선·산점도 차트 그리기"),
    "sql-runner": ("data", "사내 DB에 읽기 전용 SQL 질의 실행"),
    "forecast": ("data", "시계열 데이터로 다음 기간 수요 예측"),
    "code-review": ("code", "변경된 코드의 버그·보안 문제 검토"),
    "test-writer": ("code", "함수에 대한 단위 테스트 작성"),
    "refactor": ("code", "동작을 유지하며 코드 구조 정리"),
    "regex-helper": ("code", "정규식 작성과 설명"),
    "docker-deploy": ("ops", "Docker 이미지 빌드와 컨테이너 배포"),
    "k8s-status": ("ops", "쿠버네티스 파드·배포 상태 조회"),
    "log-search": ("ops", "서버 로그에서 오류 검색과 요약"),
    "cert-renew": ("ops", "TLS 인증서 만료 확인과 갱신"),
    "gmail-send": ("comms", "Gmail로 메일 작성·발송"),
    "slack-post": ("comms", "Slack 채널에 메시지 게시"),
    "x-post": ("comms", "X(트위터)에 글 게시"),
    "calendar-invite": ("comms", "Google 캘린더 일정 만들기와 초대"),
    "web-search": ("web", "웹 검색 결과 요약"),
    "page-scraper": ("web", "웹 페이지 본문·표 수집"),
    "browser-auto": ("web", "브라우저로 로그인·클릭·양식 입력 자동화"),
    "translate": ("web", "문서·문장 번역(한·영·일)"),
}

REQUESTS = [
    {"text": "이 세 PDF를 하나로 합쳐 줘.", "label": "pdf-tools"},
    {"text": "스캔한 신청서 PDF에서 이름 칸을 채워 줘.", "label": "pdf-tools"},
    {"text": "계약서 초안을 docx로 만들고 수정 내역이 보이게 해 줘.", "label": "docx-writer"},
    {"text": "분기 실적 발표용 슬라이드 10장 만들어 줘.", "label": "slide-maker"},
    {"text": "README.md를 사내 위키에 올릴 HTML로 바꿔 줘.", "label": "md-to-html"},
    {"text": "sales.csv에서 지역별 매출 합계 좀 내 줘.", "label": "csv-analyst"},
    {"text": "월별 가입자 수를 선 그래프로 그려 줘.", "label": "chart-builder"},
    {"text": "어제 가입한 사용자 수를 DB에서 세어 줘.", "label": "sql-runner"},
    {"text": "지난 2년 판매량으로 다음 달 수요를 예측해 줘.", "label": "forecast"},
    {"text": "이 PR 변경분에 보안 문제 없는지 봐 줘.", "label": "code-review"},
    {"text": "parse_date 함수 테스트 코드 좀 써 줘.", "label": "test-writer"},
    {"text": "500줄짜리 함수를 동작 그대로 작게 나눠 줘.", "label": "refactor"},
    {"text": "이메일 주소를 검사하는 정규식 만들어 줘.", "label": "regex-helper"},
    {"text": "이 Dockerfile로 이미지 빌드해서 스테이징에 띄워 줘.", "label": "docker-deploy"},
    {"text": "운영 클러스터 파드 중 재시작 반복하는 거 있어?", "label": "k8s-status"},
    {"text": "오늘 새벽 결제 서버 500 에러 로그 찾아서 요약해 줘.", "label": "log-search"},
    {"text": "api.example.com 인증서 언제 만료돼? 곧이면 갱신해 줘.", "label": "cert-renew"},
    {"text": "팀장님께 휴가 신청 메일 보내 줘.", "label": "gmail-send"},
    {"text": "#release 채널에 배포 완료 공지 올려 줘.", "label": "slack-post"},
    {"text": "신제품 출시 소식을 트위터에 올려 줘.", "label": "x-post"},
    {"text": "다음 주 화요일 3시에 디자인 리뷰 회의 잡고 세 명 초대해 줘.", "label": "calendar-invite"},
    {"text": "최근 LLM 추론 비용 동향을 검색해서 정리해 줘.", "label": "web-search"},
    {"text": "경쟁사 가격표 페이지의 표를 가져와 줘.", "label": "page-scraper"},
    {"text": "관리자 페이지에 로그인해서 공지 등록 폼을 채워 줘.", "label": "browser-auto"},
    {"text": "이 일본어 매뉴얼을 한국어로 옮겨 줘.", "label": "translate"},
    {"text": "엑셀 매출표를 읽고 그래프로 보여 줘.", "label": "chart-builder"},
    {"text": "로그에서 타임아웃 패턴을 잡는 정규식이 필요해.", "label": "regex-helper"},
    {"text": "회의록을 Word 문서로 정리해 줘.", "label": "docx-writer"},
    # none: no skill needed, or no skill fits
    {"text": "파이썬에서 리스트와 튜플 차이가 뭐야?", "label": "none"},
    {"text": "고마워, 오늘 도움 많이 됐어.", "label": "none"},
    {"text": "이 문장 맞춤법만 봐 줘: 됬다고 했잖아.", "label": "none"},
    {"text": "마스토돈에 출시 소식 올려 줘.", "label": "none"},  # only an X skill exists
    {"text": "디스코드 서버에 공지 올려 줘.", "label": "none"},
    {"text": "AWS Lambda 함수 배포해 줘.", "label": "none"},  # docker-deploy is not Lambda
    {"text": "피그마 시안을 PNG로 내보내 줘.", "label": "none"},
    {"text": "오늘 점심 메뉴 추천해 줘.", "label": "none"},
    {"text": "재귀가 뭔지 쉽게 설명해 줘.", "label": "none"},
    {"text": "노션 페이지에 회의록 올려 줘.", "label": "none"},
    {"text": "이 함수 이름 더 좋은 거 있을까? get_d", "label": "none"},
    {"text": "카카오톡으로 고객에게 알림 보내 줘.", "label": "none"},
]
