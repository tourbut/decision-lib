"""Thirty made-up support tickets, each labelled three ways as Kev asks in one request:
the team (dept), whether it needs an urgent response, and the customer's frustration
(0 calm, 1 annoyed, 2 angry).
"""

from __future__ import annotations

DEPTS = {"billing": "결제·청구·환불·구독", "technical": "오류·장애·연동·사용법", "sales": "가격·견적·도입 상담",
         "other": "그 밖의 문의"}
FRUSTRATION = ["차분함", "불만이 있음", "매우 화남"]

TICKETS = [
    {"text": "카드 결제가 두 번 됐어요. 하나 환불 부탁드립니다.", "dept": "billing", "urgent": False, "frustration": 1},
    {"text": "또 이중 결제입니다. 이번이 세 번째예요. 당장 환불 안 하면 카드사에 신고합니다!!", "dept": "billing", "urgent": True, "frustration": 2},
    {"text": "세금계산서를 회사명으로 재발행해 주실 수 있을까요?", "dept": "billing", "urgent": False, "frustration": 0},
    {"text": "해지했는데 이번 달에도 요금이 나갔네요. 확인 부탁해요.", "dept": "billing", "urgent": False, "frustration": 1},
    {"text": "오늘 자정까지 결제 안 되면 서비스가 끊긴다는데 카드 등록이 계속 실패해요. 급합니다.", "dept": "billing", "urgent": True, "frustration": 1},
    {"text": "연간 구독으로 바꾸면 할인되나요? 결제는 다음 달에 할게요.", "dept": "billing", "urgent": False, "frustration": 0},
    {"text": "구독 해지하는 버튼이 어디 있나요?", "dept": "billing", "urgent": False, "frustration": 0},
    {"text": "운영 서버 전체가 다운됐습니다. 고객들이 아무것도 못 하고 있어요. 지금 바로 연락 주세요.", "dept": "technical", "urgent": True, "frustration": 2},
    {"text": "로그인하면 흰 화면만 나와요.", "dept": "technical", "urgent": False, "frustration": 1},
    {"text": "API 웹훅이 한 시간째 500을 반환해서 주문이 전부 막혔습니다.", "dept": "technical", "urgent": True, "frustration": 1},
    {"text": "CSV 내보내기 형식을 바꾸는 방법이 궁금합니다.", "dept": "technical", "urgent": False, "frustration": 0},
    {"text": "업데이트 후에 대시보드가 엄청 느려졌어요. 일을 못 하겠네요 정말.", "dept": "technical", "urgent": False, "frustration": 2},
    {"text": "모바일 앱 알림이 가끔 안 와요. 시간 날 때 봐 주세요.", "dept": "technical", "urgent": False, "frustration": 0},
    {"text": "보안 경고: 우리 계정에서 모르는 로그인이 계속 시도되고 있습니다. 즉시 차단이 필요합니다.", "dept": "technical", "urgent": True, "frustration": 1},
    {"text": "슬랙 연동 설정했는데 메시지가 안 와요. 문서대로 했는데요?", "dept": "technical", "urgent": False, "frustration": 1},
    {"text": "100명 규모로 도입하려는데 견적서 받을 수 있을까요?", "dept": "sales", "urgent": False, "frustration": 0},
    {"text": "다음 주 월요일 임원 보고 전에 엔터프라이즈 가격표가 꼭 필요합니다. 오늘 중으로 부탁드려요.", "dept": "sales", "urgent": True, "frustration": 0},
    {"text": "데모 신청했는데 2주째 연락이 없네요. 다른 제품 알아봐야 하나요?", "dept": "sales", "urgent": False, "frustration": 2},
    {"text": "비영리 단체 할인이 있나요?", "dept": "sales", "urgent": False, "frustration": 0},
    {"text": "온프레미스 설치형도 판매하시나요?", "dept": "sales", "urgent": False, "frustration": 0},
    {"text": "영업 담당자가 말한 가격이랑 계약서 가격이 다르네요. 장난하시는 건가요?", "dept": "sales", "urgent": False, "frustration": 2},
    {"text": "경쟁사에서 옮기려는데 데이터 이전도 도와주시나요?", "dept": "sales", "urgent": False, "frustration": 0},
    {"text": "사무실 주소가 바뀌었습니다. 어디에 알리면 되나요?", "dept": "other", "urgent": False, "frustration": 0},
    {"text": "채용 공고 보고 연락드립니다. 지원은 어디로 하나요?", "dept": "other", "urgent": False, "frustration": 0},
    {"text": "담당자분 이름 좀 알려 주세요. 전화를 세 번이나 했는데 아무도 안 받네요.", "dept": "other", "urgent": False, "frustration": 2},
    {"text": "개인정보 삭제를 요청합니다. 법정 기한이 오늘까지입니다.", "dept": "other", "urgent": True, "frustration": 1},
    {"text": "공동 마케팅 제휴를 제안하고 싶습니다.", "dept": "other", "urgent": False, "frustration": 0},
    {"text": "기술 블로그 글을 사내 교육에 써도 될까요?", "dept": "other", "urgent": False, "frustration": 0},
    {"text": "계정 소유자를 퇴사자에서 저로 바꿔 주세요.", "dept": "other", "urgent": False, "frustration": 0},
    {"text": "고객센터 운영 시간이 어떻게 되나요? 답답하네요.", "dept": "other", "urgent": False, "frustration": 1},
]
