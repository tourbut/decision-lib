"""Forty made-up support tickets, ten per team. About a third are deliberately ambiguous
(a payment page that errors, a pricing question inside a bug report), which is where
option order is most likely to tip the answer. Labels follow the policy in LABELS.
"""

from __future__ import annotations

LABELS = {
    "billing": "결제, 청구서, 환불, 구독 변경·해지",
    "technical": "제품 오류, 장애, 연동 실패, 사용법 문제",
    "sales": "가격 문의, 견적, 도입 상담, 요금제 업그레이드 상담",
    "other": "계정 정보 변경, 채용, 제휴, 위에 해당하지 않는 문의",
}

TICKETS = [
    # billing
    ("카드 결제가 두 번 됐어요. 하나 환불해 주세요.", "billing"),
    ("이번 달 청구서 금액이 지난달보다 2배 많습니다. 내역 확인 부탁드립니다.", "billing"),
    ("연간 구독을 월간으로 바꾸고 싶어요.", "billing"),
    ("해지했는데 다음 달에도 요금이 빠져나갔어요.", "billing"),
    ("세금계산서를 회사 이름으로 다시 발행해 주세요.", "billing"),
    ("결제 수단을 법인카드로 바꾸려는데 어디서 하나요?", "billing"),
    ("결제 버튼을 눌렀는데 오류가 나더니 돈은 빠져나갔어요. 환불해 주세요.", "billing"),
    ("무료 체험이 끝났는데 자동으로 결제됐네요. 취소할 수 있나요?", "billing"),
    ("쿠폰을 적용했는데 할인이 안 된 금액으로 청구됐습니다.", "billing"),
    ("팀원 3명을 뺐는데 요금이 그대로예요.", "billing"),
    # technical
    ("로그인하면 하얀 화면만 나와요.", "technical"),
    ("API 연동 후 웹훅이 계속 500을 반환합니다.", "technical"),
    ("CSV 내보내기를 누르면 파일이 비어 있어요.", "technical"),
    ("모바일 앱이 실행하자마자 꺼집니다. iOS 18입니다.", "technical"),
    ("슬랙 알림 연동을 설정했는데 메시지가 안 와요.", "technical"),
    ("결제 내역 페이지가 계속 로딩만 돌아요.", "technical"),
    ("대시보드 그래프 숫자가 원본 데이터와 다릅니다.", "technical"),
    ("SSO로 로그인하면 권한 오류가 납니다. 엔터프라이즈 요금제 쓰고 있어요.", "technical"),
    ("파일 업로드가 50MB에서 멈춥니다. 요금제 한도 문제인가요?", "technical"),
    ("비밀번호 재설정 메일이 오지 않아요.", "technical"),
    # sales
    ("50명 팀이 쓰려면 엔터프라이즈 요금이 얼마인가요?", "sales"),
    ("온프레미스 설치형도 판매하시나요?", "sales"),
    ("공공기관인데 조달 견적서를 받을 수 있을까요?", "sales"),
    ("경쟁사 제품에서 옮기려는데 데모를 볼 수 있나요?", "sales"),
    ("비영리 단체 할인이 있나요?", "sales"),
    ("지금 프로 요금제인데 엔터프라이즈로 올리면 뭐가 달라지나요?", "sales"),
    ("연간 계약하면 할인율이 어떻게 되나요?", "sales"),
    ("SSO 기능이 필요한데 어떤 요금제를 사야 하나요?", "sales"),
    ("리셀러로 제품을 팔고 싶은데 가격 정책을 알려 주세요.", "sales"),
    ("100명 이상이면 사용자당 단가를 조정해 주시나요?", "sales"),
    # other
    ("사무실 주소가 바뀌었는데 어디에 알려야 하나요?", "other"),
    ("채용 공고에 지원하려면 어디로 연락하나요?", "other"),
    ("기술 블로그 글을 저희 사내 교육에 인용해도 될까요?", "other"),
    ("계정 이메일을 개인 메일에서 회사 메일로 바꾸고 싶어요.", "other"),
    ("공동 마케팅 제휴를 제안드리고 싶습니다.", "other"),
    ("담당 매니저가 바뀌었다고 들었는데 새 연락처를 알 수 있을까요?", "other"),
    ("서비스 이용약관 개정 내용을 어디서 보나요?", "other"),
    ("행사 부스 후원 문의드립니다.", "other"),
    ("계정 소유자를 퇴사한 직원에서 저로 옮겨 주세요.", "other"),
    ("고객센터 운영 시간이 어떻게 되나요?", "other"),
]
