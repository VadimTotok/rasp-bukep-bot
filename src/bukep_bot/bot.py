import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .config import (
    CACHE_MAXSIZE,
    HTTP_RETRIES,
    HTTP_TIMEOUT,
    RASP_BASE_URL,
    RASP_VERIFY_SSL,
    SCHEDULE_TTL,
    THROTTLE_RATE,
    TREE_TTL,
    Config,
)
from .handlers import bells, favorites, help, navigation, schedule, start
from .infra.disk_cache import DiskCache
from .infra.rasp_client import RaspClient
from .infra.storage import Storage
from .middlewares.throttling import ThrottlingMiddleware
from .services.favorites import FavoritesService
from .services.rasp import DirectoryService, ScheduleService

log = logging.getLogger(__name__)

def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    throttling = ThrottlingMiddleware(rate=THROTTLE_RATE)
    dp.message.middleware(throttling)
    dp.callback_query.middleware(throttling)

    dp.include_router(start.router)
    dp.include_router(navigation.router)
    dp.include_router(schedule.router)
    dp.include_router(favorites.router)
    dp.include_router(bells.router)
    dp.include_router(help.router)
    return dp

def build_bot(cfg: Config) -> Bot:
    return Bot(
        token=cfg.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

async def setup_services(cfg: Config, dp: Dispatcher) -> dict:
    client = RaspClient(
        RASP_BASE_URL,
        verify_ssl=RASP_VERIFY_SSL,
        timeout=HTTP_TIMEOUT,
        retries=HTTP_RETRIES,
    )
    await client.start()

    disk = DiskCache(cfg.data_dir / "cache")
    storage = Storage(cfg.data_dir / "favorites.db")
    await storage.start()

    directory = DirectoryService(client, disk, ttl=TREE_TTL)
    schedule_svc = ScheduleService(
        client, disk, directory,
        ttl=SCHEDULE_TTL, maxsize=CACHE_MAXSIZE,
    )
    favorites_svc = FavoritesService(storage)

    dp.workflow_data.update({
        "directory": directory,
        "schedule_svc": schedule_svc,
        "favorites": favorites_svc,
        "client": client,
        "storage": storage,
    })
    return dp.workflow_data
