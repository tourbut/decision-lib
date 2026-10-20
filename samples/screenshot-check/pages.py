"""Sixteen made-up web pages: the URL, the visible text a crawler extracts, an HTML body
rendered to shots/<id>.png, and a label. All brands and domains are fictional.

Several phishing pages draw the brand only as a logo image (here: an inline SVG that
the text extractor does not read), as phishing kits do to slip past text scanners. A
text-only check cannot see the brand on those; a screenshot can.
"""

from __future__ import annotations

# The brand registry: which hosts may legitimately ask for each brand's password.
BRANDS = {
    "MegaBank": ["megabank.co.kr", "login.megabank.co.kr"],
    "KoPay": ["kopay.com", "auth.kopay.com"],
    "Cloudnest": ["cloudnest.io", "id.cloudnest.io"],
    "ShopMall": ["shopmall.kr"],
}

COLORS = {"MegaBank": "#0b4a8b", "KoPay": "#f2b705", "Cloudnest": "#5b3cc4", "ShopMall": "#e4572e"}


def logo(brand: str) -> str:
    """The brand as an image: SVG text is drawn, not extracted."""
    return (f'<svg width="260" height="56"><rect width="260" height="56" rx="8" fill="{COLORS[brand]}"/>'
            f'<text x="20" y="38" font-size="28" font-family="sans-serif" font-weight="700" fill="#fff">{brand}</text></svg>')


def login(brand: str, *, title: str = "로그인", note: str = "", logo_only: bool = False) -> tuple[str, str]:
    """(html, extracted text). With logo_only the brand name appears nowhere in the text."""
    heading = "" if logo_only else f"<h1>{brand} {title}</h1>"
    html = (f"{logo(brand)}{heading}<p class='note'>{note}</p>"
            "<form><label>아이디<input></label><label>비밀번호<input type='password'></label><button>로그인</button></form>")
    text = " ".join(filter(None, [None if logo_only else f"{brand} {title}", note, "아이디 비밀번호 로그인"]))
    return html, text


def article(brand: str, headline: str, body: str) -> tuple[str, str]:
    html = f"{logo(brand)}<h1>{headline}</h1><p>{body}</p>"
    return html, f"{headline} {body}"


def page(id_: str, url: str, label: str, content: tuple[str, str]) -> dict:
    html, text = content
    return {"id": id_, "url": url, "label": label, "html": html, "text": text}


PAGES = [
    # legit: the brand's login on the brand's own host
    page("legit-megabank", "https://login.megabank.co.kr/", "legit", login("MegaBank")),
    page("legit-kopay", "https://auth.kopay.com/signin", "legit", login("KoPay")),
    page("legit-cloudnest", "https://id.cloudnest.io/login", "legit", login("Cloudnest", logo_only=True)),
    page("legit-shopmall", "https://shopmall.kr/member/login", "legit", login("ShopMall")),
    # phishing: a brand's login on someone else's host
    page("phish-megabank-urgent", "http://megabank-secure-verify.xyz/", "phishing",
         login("MegaBank", note="계정이 24시간 안에 정지됩니다. 지금 본인 확인을 완료하세요.")),
    page("phish-kopay-sub", "https://kopay.com.login-check.top/", "phishing", login("KoPay")),
    page("phish-cloudnest-zero", "https://cl0udnest.io/login", "phishing", login("Cloudnest")),
    page("phish-shopmall-refund", "http://shopmall-refund.kr-event.net/", "phishing",
         login("ShopMall", title="환불 신청", note="환불을 받으려면 로그인하세요.")),
    page("phish-megabank-logo", "https://secure-banking-portal.top/", "phishing", login("MegaBank", logo_only=True)),
    page("phish-kopay-logo", "https://pay-verify-center.com/", "phishing", login("KoPay", logo_only=True)),
    page("phish-cloudnest-logo", "https://docs-share-view.net/open", "phishing",
         login("Cloudnest", note="공유 문서를 보려면 로그인하세요.", logo_only=True)),
    page("phish-shopmall-logo", "http://delivery-check.kr-info.org/", "phishing",
         login("ShopMall", note="배송 주소 확인이 필요합니다.", logo_only=True)),
    # other: no password form, even on odd hosts
    page("other-news", "https://megabank-news.blogspot.example/", "other",
         article("MegaBank", "MegaBank 3분기 실적 발표", "순이익이 지난해보다 4% 늘었다.")),
    page("other-docs", "https://docs.kopay.com/api", "other",
         article("KoPay", "KoPay 결제 API 문서", "결제 요청은 POST /v1/payments로 보낸다.")),
    page("other-coupon", "http://shopmall-coupon.event-hub.net/", "other",
         article("ShopMall", "ShopMall 가을 쿠폰 모음", "쿠폰 코드는 매장 앱에서 확인한다.")),
    page("other-parked", "https://cloudnest-login.net/", "other",
         ("<h1>This domain is for sale</h1><p>Contact the owner.</p>", "This domain is for sale Contact the owner.")),
]
