import re
from urllib.parse import quote

from bs4 import BeautifulSoup

_IIS_RE = re.compile(r"%u([0-9a-fA-F]{4})")
_POSTBACK_A = re.compile(r"__doPostBack\(&#39;([^&]+)&#39;")
_POSTBACK_B = re.compile(r"__doPostBack\('([^']+)'")

def soup_of(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml", multi_valued_attributes=None)
    except Exception:
        return BeautifulSoup(html, "html.parser", multi_valued_attributes=None)

def _s(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return " ".join(str(x) for x in v)
    return str(v)

def fix_iis_url(url: str) -> str:
    return _IIS_RE.sub(lambda m: quote(chr(int(m.group(1), 16)), safe=""), url)

def hidden(soup: BeautifulSoup) -> dict[str, str]:
    return {
        _s(i.get("name")): _s(i.get("value"))
        for i in soup.find_all("input")
        if _s(i.get("type")).lower() == "hidden" and _s(i.get("name"))
    }

def form_action(soup: BeautifulSoup, base: str) -> str:
    form = soup.find("form", id="aspnetForm") or soup.find("form")
    a = _s(form.get("action")) if form else "/Default.aspx?idFil=1000"
    if a.startswith("./"):
        a = a[2:]
    if a.startswith("/"):
        return base + a
    if not a.startswith("http"):
        return base + "/" + a
    return a

def list_buttons(soup: BeautifulSoup) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for a in soup.find_all("a"):
        aid = _s(a.get("id"))
        if not aid.startswith("ctl00_head_"):
            continue
        href = _s(a.get("href"))
        m = _POSTBACK_A.search(href) or _POSTBACK_B.search(href)
        if m:
            out.append({"target": m.group(1), "label": a.get_text(" ", strip=True)})
    return out
