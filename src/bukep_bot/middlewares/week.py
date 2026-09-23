from datetime import date
from typing import Literal

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from ..domain import current_week_type


class WeekTypeMiddleware(BaseMiddleware):
    def __init__(self, semester_start: date | None, first_week: str):
        super().__init__()
        self._start = semester_start
        self._first = first_week

    async def __call__(self, handler, event: TelegramObject, data: dict):
        week: Literal["numerator", "denominator"] | None = current_week_type(
            self._start, self._first,
        )
        data["week_type"] = week
        return await handler(event, data)