"""Labelled citations against source.md: six accurate, six planted failures, and three
borderline claims that d3-flash judged correctly but below AUTO_ACCEPT on 2026-10-20.

Each citation is what an LLM attaches to one claim in a report: the claim, the quote it
rests on (None for a claim that only names a section), and the section it cites.
`label` is the verdict a careful reviewer would give.
"""

from __future__ import annotations

CITATIONS = [
    {
        "id": "db_approval",
        "claim": "개인정보 DB에 접근하려면 팀장 승인이 필요하다.",
        "quote": "개인정보가 담긴 데이터베이스에 접근하려면 소속 팀장의 승인을 받아야 한다.",
        "section": "3.1",
        "label": "verified",
    },
    {
        "id": "log_retention",
        "claim": "개인정보 접근 기록은 1년간 남는다.",
        "quote": "개인정보 조회·수정·내려받기 기록은 1년 동안 보관한다.",
        "section": "3.2",
        "label": "verified",
    },
    {
        "id": "aes_at_rest",
        "claim": "저장된 개인정보는 AES-256으로 암호화된다.",
        "quote": "개인정보는 저장할 때 AES-256으로 암호화한다.",
        "section": "4.1",
        "label": "verified",
    },
    {
        "id": "ssn_marketing",
        "claim": "마케팅 목적으로 주민등록번호를 모으는 일은 없다.",
        # Wraps across two lines in source.md; normalize() must still find it.
        "quote": "주민등록번호는 법령이 요구하는 경우에만 수집하며, 마케팅 목적으로는 어떤 경우에도 수집하지 않는다.",
        "section": "2.1",
        "label": "verified",
    },
    {
        "id": "breach_report",
        "claim": "유출을 안 직원은 하루 안에 CISO에게 알려야 한다.",
        "quote": "개인정보 유출을 알게 된 직원은 24시간 안에 정보보호최고책임자(CISO)에게 보고한다.",
        "section": "6",
        "label": "verified",
    },
    {
        "id": "payment_records",
        "claim": "탈퇴한 고객의 결제 기록은 5년간 보관된다.",
        "quote": None,
        "section": "5.1",
        "label": "verified",
    },
    {
        "id": "logs_forever",
        "claim": "접근 기록은 감사 대비를 위해 영구 보관한다.",
        "quote": "모든 접근 기록은 감사에 대비해 영구 보관한다.",
        "section": "3.2",
        "label": "fabricated",  # no such sentence anywhere
    },
    {
        "id": "breach_48h",
        "claim": "유출 보고 기한은 48시간이다.",
        "quote": "개인정보 유출을 알게 된 직원은 48시간 안에 정보보호최고책임자(CISO)에게 보고한다.",
        "section": "6",
        "label": "fabricated",  # one number changed from the real sentence
    },
    {
        "id": "cloud_ok",
        "claim": "개인정보는 보안팀 승인 없이도 외부 클라우드에 저장할 수 있다.",
        "quote": "보안팀이 사전에 검토하고 승인한 저장소에는 암호화한 상태로 저장할 수 있다.",
        "section": "4.2",
        "label": "contradicted",  # the exception clause, read as the rule
    },
    {
        "id": "delete_immediately",
        "claim": "회원이 탈퇴하면 결제 기록을 포함한 모든 개인정보를 즉시 파기한다.",
        "quote": "고객 개인정보는 회원 탈퇴 후 30일 안에 파기한다.",
        "section": "5.1",
        "label": "contradicted",
    },
    {
        "id": "mobile_mdm",
        "claim": "개인정보를 다루는 직원의 휴대폰에는 MDM 설치가 의무다.",
        "quote": "개인정보가 담긴 데이터베이스에 접근하려면 소속 팀장의 승인을 받아야 한다.",
        "section": "3.1",
        "label": "unsupported",  # real quote, unrelated claim
    },
    {
        "id": "breach_fine",
        "claim": "유출 보고를 늦춘 직원은 징계 대상이다.",
        "quote": None,
        "section": "6",
        "label": "unsupported",
    },
    # Borderline: a vague or overstated claim. These exercise the human review queue.
    {
        "id": "password_safe",
        "claim": "고객 비밀번호는 안전하게 보관된다.",
        "quote": "비밀번호는 복호화할 수 없는 단방향 해시로만 저장한다.",
        "section": "4.1",
        "label": "verified",
    },
    {
        "id": "realtime_watch",
        "claim": "보안팀은 모든 개인정보 조회를 실시간으로 감시한다.",
        "quote": "보안팀은 매월 접근 기록을 검토해 업무와 무관한 조회를 찾는다.",
        "section": "3.2",
        "label": "contradicted",
    },
    {
        "id": "any_cloud_encrypted",
        "claim": "개인정보는 암호화하면 어떤 외부 클라우드에도 저장할 수 있다.",
        "quote": "보안팀이 사전에 검토하고 승인한 저장소에는 암호화한 상태로 저장할 수 있다.",
        "section": "4.2",
        "label": "contradicted",
    },
]
