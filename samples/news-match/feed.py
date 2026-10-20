"""A made-up morning feed of 40 headlines and five interest profiles, with the profiles
each headline should go to. Headlines and companies are invented.
"""

from __future__ import annotations

TOPICS = {
    "agents": "AI 에이전트·코딩 에이전트·도구 호출·에이전트 프레임워크 소식",
    "medical_ai": "의료 AI: 진단 보조, 의료 영상, 병원 도입, 의료기기 인허가",
    "chips": "AI 반도체·GPU·HBM·데이터센터 하드웨어",
    "security": "보안 사고·취약점·랜섬웨어·개인정보 유출",
    "open_models": "오픈 가중치 LLM·소형 모델 공개·로컬 실행",
}

HEADLINES = [
    {"text": "오픈소스 코딩 에이전트, 테스트까지 스스로 돌리는 새 버전 공개", "topics": ["agents"]},
    {"text": "대형 병원 3곳, 흉부 엑스레이 판독 보조 AI 정식 도입", "topics": ["medical_ai"]},
    {"text": "차세대 HBM 양산 앞당겨… AI 서버 수요 급증", "topics": ["chips"]},
    {"text": "온라인 쇼핑몰 회원 120만 명 개인정보 유출 확인", "topics": ["security"]},
    {"text": "9B 오픈 가중치 모델, 노트북에서 돌아가는 양자화 버전 배포", "topics": ["open_models"]},
    {"text": "에이전트가 도구 호출 전에 사람 승인을 받는 프레임워크 기능 추가", "topics": ["agents"]},
    {"text": "식약처, 뇌 MRI 분석 AI 소프트웨어 3등급 의료기기 허가", "topics": ["medical_ai"]},
    {"text": "GPU 클라우드 가격 인하 경쟁… 시간당 요금 30% 내려", "topics": ["chips"]},
    {"text": "랜섬웨어 공격으로 지역 병원 진료 시스템 이틀째 마비", "topics": ["security", "medical_ai"]},
    {"text": "병원 전용 소형 언어 모델 공개, 폐쇄망에서 실행", "topics": ["open_models", "medical_ai"]},
    {"text": "코딩 에이전트가 낸 취약한 코드, 공급망 공격 통로 될 수 있어", "topics": ["agents", "security"]},
    {"text": "데이터센터 전력난에 액침 냉각 서버 도입 늘어", "topics": ["chips"]},
    {"text": "오픈 모델로 만든 의료 영상 판독 에이전트 임상 시험 시작", "topics": ["medical_ai", "open_models", "agents"]},
    {"text": "브라우저 확장 프로그램 위장한 악성코드, 기업 계정 탈취", "topics": ["security"]},
    {"text": "1B 이하 소형 모델 벤치마크, 일부는 7B 넘어서", "topics": ["open_models"]},
    {"text": "AI 칩 스타트업, 추론 전용 가속기 시제품 공개", "topics": ["chips"]},
    {"text": "다중 에이전트 협업 프레임워크, 작업 분배 기능 강화", "topics": ["agents"]},
    {"text": "환자 데이터 무단 반출 혐의로 의료 AI 업체 조사", "topics": ["medical_ai", "security"]},
    {"text": "오픈 가중치 모델 라이선스 변경, 상업 이용 허용", "topics": ["open_models"]},
    {"text": "에이전트 메모리 기능 표준화 논의 본격화", "topics": ["agents"]},
    # nothing for any profile
    {"text": "프로야구 정규시즌 우승팀 확정", "topics": []},
    {"text": "가을 단풍 절정 시기, 다음 주 중부 지방", "topics": []},
    {"text": "기준금리 동결… 물가 상승률 둔화", "topics": []},
    {"text": "인기 드라마 시즌2 제작 확정", "topics": []},
    {"text": "전기차 보조금 내년부터 개편", "topics": []},
    {"text": "수도권 아파트 거래량 석 달째 증가", "topics": []},
    {"text": "국제 영화제 개막작 발표", "topics": []},
    {"text": "주말 미세먼지 '나쁨'… 외출 자제 권고", "topics": []},
    {"text": "라면 가격 일제히 인상", "topics": []},
    {"text": "마라톤 대회 교통 통제 안내", "topics": []},
    # near misses: a profile's word appears, but the story is not about it
    {"text": "여행 에이전트 업계, 연휴 항공권 예약 급증", "topics": []},
    {"text": "감자칩 신제품 출시, 매운맛 인기", "topics": []},
    {"text": "보안 요원 채용 박람회 개최", "topics": []},
    {"text": "병원 주차장 증설 공사 시작", "topics": []},
    {"text": "오픈 키친 레스토랑 창업 늘어", "topics": []},
    {"text": "스마트폰 카메라 신기술, 저조도 촬영 개선", "topics": []},
    {"text": "보험 설계 에이전트 수수료 체계 바뀐다", "topics": []},
    {"text": "모델하우스 방문객 주말 몰려", "topics": []},
    {"text": "반도체 업종 주가 하락 마감", "topics": ["chips"]},  # market news, still chips
    {"text": "의료진 번아웃 설문, 응답자 절반이 이직 고려", "topics": []},
]
