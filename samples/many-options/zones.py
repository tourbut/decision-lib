"""More than 255 options: every IANA time zone in the standard library, grouped by region,
and 40 requests labelled with the zone a scheduler should use.

The catalog comes from `zoneinfo.available_timezones()`, so it needs no download. Legacy
aliases and `Etc/*` offsets are left out; the rest is still far past d3-flash's limit of
255 options per Choice.
"""

from __future__ import annotations

import zoneinfo
from collections import defaultdict

REGIONS = {
    "Africa": "아프리카",
    "America": "남북아메리카(미국·캐나다·중남미)",
    "Antarctica": "남극 기지",
    "Arctic": "북극",
    "Asia": "아시아·중동",
    "Atlantic": "대서양 섬",
    "Australia": "호주",
    "Europe": "유럽",
    "Indian": "인도양 섬",
    "Pacific": "태평양 섬·뉴질랜드",
}


def catalog() -> dict[str, list[str]]:
    zones: dict[str, list[str]] = defaultdict(list)
    for name in sorted(zoneinfo.available_timezones()):
        region = name.split("/", 1)[0]
        if region in REGIONS:
            zones[region].append(name)
    return dict(zones)


REQUESTS = [
    {"text": "부산 지사와 회의 잡을 때 어느 시간대야?", "label": "Asia/Seoul"},
    {"text": "도쿄 고객사 미팅", "label": "Asia/Tokyo"},
    {"text": "상하이 공장 교대 시간 맞추기", "label": "Asia/Shanghai"},
    {"text": "타이베이 협력사와 통화", "label": "Asia/Taipei"},
    {"text": "싱가포르 데이터센터 점검 시각", "label": "Asia/Singapore"},
    {"text": "뭄바이 개발팀 스탠드업", "label": "Asia/Kolkata"},
    {"text": "두바이 박람회 일정", "label": "Asia/Dubai"},
    {"text": "방콕 출장 중 화상회의", "label": "Asia/Bangkok"},
    {"text": "자카르타 물류센터 마감 시간", "label": "Asia/Jakarta"},
    {"text": "호찌민 지사 급여 지급일 공지", "label": "Asia/Ho_Chi_Minh"},
    {"text": "런던 본사 이사회", "label": "Europe/London"},
    {"text": "파리 디자인 스튜디오와 리뷰", "label": "Europe/Paris"},
    {"text": "베를린 파트너와 계약 서명", "label": "Europe/Berlin"},
    {"text": "마드리드 세일즈 콜", "label": "Europe/Madrid"},
    {"text": "이스탄불 행사 시작 시각", "label": "Europe/Istanbul"},
    {"text": "모스크바 사무소 업무 시간", "label": "Europe/Moscow"},
    {"text": "헬싱키 개발자 밋업", "label": "Europe/Helsinki"},
    {"text": "뉴욕 증시 개장 시각 알림", "label": "America/New_York"},
    {"text": "샌프란시스코 투자자 미팅", "label": "America/Los_Angeles"},
    {"text": "시카고 물류 파트너 통화", "label": "America/Chicago"},
    {"text": "덴버 지사 온보딩", "label": "America/Denver"},
    {"text": "피닉스 데이터센터 작업 창", "label": "America/Phoenix"},
    {"text": "토론토 채용 인터뷰", "label": "America/Toronto"},
    {"text": "밴쿠버 게임 스튜디오와 회의", "label": "America/Vancouver"},
    {"text": "멕시코시티 공급사 협의", "label": "America/Mexico_City"},
    {"text": "상파울루 마케팅 팀 주간 회의", "label": "America/Sao_Paulo"},
    {"text": "부에노스아이레스 고객 지원 교대", "label": "America/Argentina/Buenos_Aires"},
    {"text": "앵커리지 현장 팀 점검", "label": "America/Anchorage"},
    {"text": "호놀룰루 리조트 예약 확인", "label": "Pacific/Honolulu"},
    {"text": "시드니 오피스 분기 회의", "label": "Australia/Sydney"},
    {"text": "퍼스 광산 현장 보고", "label": "Australia/Perth"},
    {"text": "오클랜드 파트너사 데모", "label": "Pacific/Auckland"},
    {"text": "카이로 현지 법인 회의", "label": "Africa/Cairo"},
    {"text": "나이로비 모바일 결제 팀 통화", "label": "Africa/Nairobi"},
    {"text": "요하네스버그 지사 결산", "label": "Africa/Johannesburg"},
    {"text": "라고스 스타트업 미팅", "label": "Africa/Lagos"},
    {"text": "레이캬비크 데이터센터 이전 일정", "label": "Atlantic/Reykjavik"},
    {"text": "몰디브 리조트 체크인 시간", "label": "Indian/Maldives"},
    {"text": "남극 맥머도 기지와 위성 통화", "label": "Antarctica/McMurdo"},
    {"text": "카트만두 트레킹 파트너 연락", "label": "Asia/Kathmandu"},
]
