import asyncio
import logging
import sys

from .bot import build_bot, build_dispatcher, setup_services
from .config import load_config

async def _run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("bukep_bot")

    cfg = load_config()
    dp = build_dispatcher()
    bot = build_bot(cfg)
    services = await setup_services(cfg, dp)

    log.info("bot started, data_dir=%s", cfg.data_dir)
    try:
        await dp.start_polling(bot)
    finally:
        log.info("shutting down…")
        await services["client"].close()
        await services["storage"].close()
        await bot.session.close()

def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
