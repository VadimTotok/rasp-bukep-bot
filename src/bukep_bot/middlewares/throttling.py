import time

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate: float = 1.5):
        super().__init__()
        self._rate = rate
        self._last: dict[int, float] = {}

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)
        now = time.monotonic()
        last = self._last.get(user.id, 0.0)
        if now - last < self._rate:
            if isinstance(event, CallbackQuery):
                await event.answer("Слишком быстро, подождите…", show_alert=False)
            return None
        self._last[user.id] = now
        if len(self._last) > 10_000:
            cutoff = now - 300
            self._last = {u: t for u, t in self._last.items() if t > cutoff}
        return await handler(event, data)
