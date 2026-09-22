import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import replace

from cachetools import TTLCache

from ..domain import GroupContext, Item, Schedule, SiteUnavailable
from ..infra.disk_cache import DiskCache
from ..infra.html import list_buttons, soup_of
from ..infra.rasp_client import RaspClient
from ..infra.rasp_parser import is_empty_schedule, parse_schedule

log = logging.getLogger(__name__)

class DirectoryService:
    def __init__(self, client: RaspClient, disk: DiskCache, ttl: int):
        self._client = client
        self._disk = disk
        self._ttl = ttl
        self._lock = asyncio.Lock()
        self._exp: dict[str, float] = {}
        self._cache: dict[str, list[Item]] = {}

    def _fresh(self, key: str) -> bool:
        return self._exp.get(key, 0.0) > time.time()

    def _touch(self, key: str) -> None:
        self._exp[key] = time.time() + self._ttl

    async def _fetch(
        self, key: str, fetch_html: Callable[[], Awaitable[str]],
    ) -> list[Item]:
        async with self._lock:
            if self._fresh(key) and key in self._cache:
                return self._cache[key]

        try:
            html = await fetch_html()
            items = [
                Item(target=b["target"], label=b["label"])
                for b in list_buttons(soup_of(html))
            ]
            self._disk.save(
                key, [{"target": i.target, "label": i.label} for i in items],
            )
        except SiteUnavailable:
            cached = self._disk.load(key)
            if cached is None:
                raise
            items = [Item(target=c["target"], label=c["label"]) for c in cached]

        async with self._lock:
            self._cache[key] = items
            self._touch(key)
        return items

    async def _walk(self, ft: str, rest: list[str] | None = None) -> str:
        html = await self._client.enter_groups()
        html = await self._client.click(html, ft)
        for target in (rest or []):
            html = await self._client.click(html, target)
        return html

    async def faculties(self, force: bool = False) -> list[Item]:
        if force:
            async with self._lock:
                self._exp.pop("faculties", None)
        return await self._fetch("faculties", self._client.enter_groups)

    async def specialties(self, ft: str, force: bool = False) -> list[Item]:
        key = f"spec::{ft}"
        if force:
            async with self._lock:
                self._exp.pop(key, None)
        return await self._fetch(key, lambda: self._walk(ft))

    async def courses(self, ft: str, st: str, force: bool = False) -> list[Item]:
        key = f"crs::{ft}::{st}"
        if force:
            async with self._lock:
                self._exp.pop(key, None)
        return await self._fetch(key, lambda: self._walk(ft, [st]))

    async def groups(
        self, ft: str, st: str, kt: str, force: bool = False,
    ) -> list[Item]:
        key = f"grp::{ft}::{st}::{kt}"
        if force:
            async with self._lock:
                self._exp.pop(key, None)
        return await self._fetch(key, lambda: self._walk(ft, [st, kt]))


class ScheduleService:
    def __init__(
        self,
        client: RaspClient,
        disk: DiskCache,
        directory: DirectoryService,
        ttl: int,
        maxsize: int,
    ):
        self._client = client
        self._disk = disk
        self._dir = directory
        self._cache: TTLCache[str, tuple[Schedule | None, bool]] = TTLCache(
            maxsize=maxsize, ttl=ttl,
        )
        self._lock = asyncio.Lock()

    async def get(
        self, ctx: GroupContext, *, force: bool = False,
    ) -> tuple[Schedule | None, bool]:
        key = ctx.gt
        if not force and key in self._cache:
            return self._cache[key]

        async with self._lock:
            if not force and key in self._cache:
                return self._cache[key]

            try:
                html = await self._walk(ctx)
                if is_empty_schedule(html):
                    result: tuple[Schedule | None, bool] = (None, False)
                else:
                    result = (parse_schedule(html), False)
                self._disk.save(f"sched::{key}", html)
            except SiteUnavailable:
                cached = self._disk.load(f"sched::{key}")
                if cached is None:
                    raise
                if is_empty_schedule(cached):
                    result = (None, True)
                else:
                    result = (parse_schedule(cached), True)

            self._cache[key] = result
            return result

    async def _walk(self, ctx: GroupContext) -> str:
        html = await self._client.enter_groups()
        html = await self._client.click(html, ctx.ft)
        html = await self._client.click(html, ctx.st)
        html = await self._client.click(html, ctx.kt)
        return await self._client.click(html, ctx.gt)

    async def re_resolve(self, ctx: GroupContext) -> GroupContext | None:
        try:
            courses = await self._dir.courses(ctx.ft, ctx.st, force=True)
        except SiteUnavailable:
            return None
        for ki, c in enumerate(courses):
            try:
                groups = await self._dir.groups(
                    ctx.ft, ctx.st, c.target, force=True,
                )
            except SiteUnavailable:
                continue
            for gi, g in enumerate(groups):
                if g.label == ctx.gl:
                    return replace(
                        ctx, kt=c.target, gt=g.target, ki=ki, gi=gi,
                    )
        return None
