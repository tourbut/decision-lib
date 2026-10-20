"""Render every page in pages.py to shots/<id>.png with headless Chrome.

Usage: python render.py [chrome binary]   # default: google-chrome
The PNGs are committed, so this only needs to run after pages.py changes.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from pages import PAGES

STYLE = """<style>body{font-family:'Noto Sans KR',sans-serif;margin:0;background:#f4f6f8;color:#1e2a36}
main{max-width:400px;margin:20px auto;background:#fff;padding:28px;border-radius:10px;box-shadow:0 1px 4px #0002}
h1{font-size:22px} .note{color:#b03a48;font-weight:700} label{display:block;margin:10px 0}
input{display:block;width:100%;padding:8px;margin-top:4px;border:1px solid #bbb;border-radius:6px}
button{margin-top:12px;width:100%;padding:10px;border:0;border-radius:6px;background:#1e2a36;color:#fff}</style>"""


def main(chrome: str) -> None:
    out = Path(__file__).with_name("shots")
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for p in PAGES:
            # No address bar: the model judges only the page; code alone reads the URL.
            html = Path(tmp) / f"{p['id']}.html"
            html.write_text(f"<meta charset='utf-8'>{STYLE}<main>{p['html']}</main>", encoding="utf-8")
            subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--window-size=480,440",
                            f"--screenshot={out / (p['id'] + '.png')}", html.as_uri()], check=True, capture_output=True)
    print(f"{len(PAGES)} screenshots in {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "google-chrome")
