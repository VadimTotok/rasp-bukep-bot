import asyncio
import logging
import socket

import aiohttp

from ..domain import SiteUnavailable
from .html import fix_iis_url, form_action, hidden, soup_of

log = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_START_PATH = "/Default.aspx?idFil=1000"

class RaspClient:
    def __init__(
        self,
        base_url: str,
        *,
        verify_ssl: bool = True,
        timeout: float = 15.0,
        retries: int = 3,
    ):
        self._base = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._retries = retries
        self._ssl: bool = verify_ssl
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        connector = aiohttp.TCPConnector(
            family=socket.AF_INET,
            ssl=self._ssl,
            limit=20,
        )
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self._timeout,
            headers={"User-Agent": _UA},
        )

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def _request(self, method: str, url: str, data: dict | None = None) -> str:
        if self._session is None:
            raise RuntimeError("RaspClient.start() не вызван")
        last_err: Exception | None = None
        for attempt in range(1, self._retries + 1):
            try:
                async with self._session.request(method, url, data=data) as r:
                    if r.status >= 400:
                        raise SiteUnavailable(f"{method} {url} -> {r.status}")
                    return await r.text()
            except SiteUnavailable:
                raise
            except Exception as e:
                last_err = e
                log.warning("%s %s attempt %d/%d: %s",
                            method, url, attempt, self._retries, e)
                if attempt < self._retries:
                    await asyncio.sleep(2.0 * attempt)
        raise SiteUnavailable(str(last_err))

    async def enter_groups(self) -> str:
        html = await self._request("GET", self._base + _START_PATH)
        data = hidden(soup_of(html))
        data["ctl00$head$1"] = "Группы"
        return await self._request("POST", self._base + _START_PATH, data)

    async def click(self, html: str, target: str) -> str:
        soup = soup_of(html)
        url = fix_iis_url(form_action(soup, self._base))
        data = hidden(soup)
        data["__EVENTTARGET"] = target
        data["__EVENTARGUMENT"] = ""
        return await self._request("POST", url, data)
