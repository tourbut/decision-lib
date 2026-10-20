"""A made-up intranet help site as static HTML, and an environment that turns the current
page into candidate actions the way jev-ultrafast turns DOM into a candidate table.

Only links inside ALLOWED_HOST become candidates; an external link is never offered, so
the picker cannot leave the site whatever the page text says.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

ALLOWED_HOST = "help.corp.example"
START = "https://help.corp.example/"


def page(title: str, body: str, links: list[tuple[str, str]]) -> str:
    items = "".join(f'<li><a href="{href}">{text}</a></li>' for href, text in links)
    return f"<html><head><title>{title}</title></head><body><h1>{title}</h1><p>{body}</p><ul>{items}</ul></body></html>"


SITE = {
    "/": page("사내 도움말", "무엇을 도와드릴까요? 분야를 고르세요.", [
        ("/it", "IT 지원"), ("/hr", "인사·급여"), ("/office", "총무·시설"),
        ("https://partner-portal.example/login", "협력사 포털(외부)"),
    ]),
    "/it": page("IT 지원", "계정, 네트워크, 장비 문제를 안내합니다.", [
        ("/it/account", "계정·비밀번호"), ("/it/network", "네트워크·VPN"), ("/it/device", "노트북·모니터 신청"), ("/", "처음으로"),
    ]),
    "/it/account": page("계정·비밀번호", "비밀번호를 잊었거나 계정이 잠긴 경우의 절차입니다.", [
        ("/it/account/reset", "비밀번호 재설정 방법"), ("/it/account/mfa", "2단계 인증 기기 변경"), ("/it", "IT 지원으로"),
    ]),
    "/it/account/reset": page("비밀번호 재설정 방법", "사내 포털 로그인 화면의 '비밀번호 찾기'를 누르고 사번으로 인증합니다.", [("/it/account", "뒤로")]),
    "/it/account/mfa": page("2단계 인증 기기 변경", "새 휴대폰으로 바꿨다면 보안팀에 기기 초기화를 요청합니다.", [("/it/account", "뒤로")]),
    "/it/network": page("네트워크·VPN", "사내망과 재택 접속 문제를 안내합니다.", [
        ("/it/network/vpn-error", "VPN 접속 오류 해결"), ("/it/network/wifi", "사무실 와이파이 비밀번호"), ("/it", "IT 지원으로"),
    ]),
    "/it/network/vpn-error": page("VPN 접속 오류 해결", "오류 809는 공유기 설정 문제입니다. 오류 691은 비밀번호 만료입니다.", [("/it/network", "뒤로")]),
    "/it/network/wifi": page("사무실 와이파이 비밀번호", "층별 안내 데스크 게시판에서 확인합니다.", [("/it/network", "뒤로")]),
    "/it/device": page("노트북·모니터 신청", "장비 신청은 전자결재의 'IT 장비 요청서'로 합니다.", [("/it", "IT 지원으로")]),
    "/hr": page("인사·급여", "휴가, 급여, 증명서 발급을 안내합니다.", [
        ("/hr/leave", "연차 신청 방법"), ("/hr/certificate", "재직증명서 발급"), ("/", "처음으로"),
    ]),
    "/hr/leave": page("연차 신청 방법", "전자결재에서 휴가 신청서를 올리고 팀장 승인을 받습니다.", [("/hr", "뒤로")]),
    "/hr/certificate": page("재직증명서 발급", "인사 포털의 증명서 메뉴에서 바로 출력합니다.", [("/hr", "뒤로")]),
    "/office": page("총무·시설", "회의실, 주차, 택배를 안내합니다.", [
        ("/office/parking", "주차 등록"), ("/office/room", "회의실 예약"), ("/", "처음으로"),
    ]),
    "/office/parking": page("주차 등록", "차량 번호를 총무팀 양식으로 등록합니다.", [("/office", "뒤로")]),
    "/office/room": page("회의실 예약", "캘린더에서 회의실을 자원으로 추가해 예약합니다.", [("/office", "뒤로")]),
}


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title, self.text, self.links = "", [], []
        self._in, self._href = None, None

    def handle_starttag(self, tag, attrs):
        self._in = tag
        if tag == "a":
            self._href = dict(attrs).get("href")

    def handle_endtag(self, tag):
        self._in = None
        if tag == "a":
            self._href = None

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if self._in == "title":
            self.title = data
        elif self._href is not None:
            self.links.append((self._href, data))
        else:
            self.text.append(data)


def parse(html: str) -> _Parser:
    parser = _Parser()
    parser.feed(html)
    return parser


class WebEnv:
    """State is the current URL. Candidates are in-site links, keyed by a short id."""

    def _links(self, url: str) -> tuple[_Parser, list[tuple[str, str]]]:
        doc = parse(SITE[urlparse(url).path or "/"])
        inside = []
        for href, text in doc.links:
            target = urljoin(url, href)
            if urlparse(target).hostname == ALLOWED_HOST and (urlparse(target).path or "/") in SITE:
                inside.append((target, text))
        return doc, inside

    def observe(self, url: str) -> tuple[str, dict[str, str]]:
        doc, links = self._links(url)
        candidates = {f"link_{i}": f"{text} ({urlparse(target).path})" for i, (target, text) in enumerate(links)}
        return f"제목: {doc.title}\n본문: {' '.join(doc.text[1:])}", candidates

    def step(self, url: str, action: str) -> str:
        return self._links(url)[1][int(action.split("_")[1])][0]


def title_of(url: str) -> str:
    return parse(SITE[urlparse(url).path or "/"]).title


GOALS = [
    {"goal": "VPN 접속할 때 오류 809가 나. 해결 방법 문서를 찾아 줘.", "expect": "VPN 접속 오류 해결"},
    {"goal": "비밀번호를 잊어버렸어. 재설정하는 방법을 알려 주는 페이지로 가 줘.", "expect": "비밀번호 재설정 방법"},
    {"goal": "재직증명서 발급 방법 페이지", "expect": "재직증명서 발급"},
    {"goal": "새 휴대폰으로 바꿔서 2단계 인증이 안 돼.", "expect": "2단계 인증 기기 변경"},
    {"goal": "다음 주 회의실 예약하는 법", "expect": "회의실 예약"},
    {"goal": "모니터 하나 더 신청하고 싶어.", "expect": "노트북·모니터 신청"},
    {"goal": "주차 등록은 어디서 해?", "expect": "주차 등록"},
    {"goal": "이번 달 급여명세서 PDF를 내려받아 줘.", "expect": None},  # not on this site: should stop with NONE
]
