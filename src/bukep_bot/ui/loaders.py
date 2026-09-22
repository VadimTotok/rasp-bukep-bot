import asyncio
import contextlib
import time
from collections.abc import Awaitable
from typing import Any

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
)
from aiogram.types import Message

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

async def safe_delete(message: Message) -> None:
    with contextlib.suppress(TelegramBadRequest, TelegramForbiddenError):
        await message.delete()

async def safe_edit(message: Message, text: str, **kwargs) -> None:
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        raise

async def _keep_typing(bot: Bot, chat_id: int, stop: asyncio.Event) -> None:
    while not stop.is_set():
        with contextlib.suppress(Exception):
            await bot.send_chat_action(chat_id, "typing")
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=4.0)

async def run_with_loader(
    target: Message,
    edit: bool,
    work: Awaitable[tuple[str, Any]],
    label: str,
    bot: Bot,
) -> None:
    loader = f"⏳ <b>{label}</b>\n<code>⠋</code>"
    if edit:
        try:
            await target.edit_text(loader, parse_mode="HTML")
            msg = target
        except TelegramBadRequest:
            msg = await target.answer(loader, parse_mode="HTML")
    else:
        msg = await target.answer(loader, parse_mode="HTML")

    stop = asyncio.Event()
    started = time.monotonic()

    async def ticker():
        i = 0
        while not stop.is_set():
            spin = SPINNER[i % len(SPINNER)]
            elapsed = time.monotonic() - started
            with contextlib.suppress(TelegramBadRequest):
                await msg.edit_text(
                    f"⏳ <b>{label}</b>\n<code>{spin}</code> {elapsed:.1f} с",
                    parse_mode="HTML",
                )
            i += 1
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=0.6)

    ticker_task = asyncio.create_task(ticker())
    typing_task = asyncio.create_task(_keep_typing(bot, msg.chat.id, stop))
    try:
        text, kb = await work
    finally:
        stop.set()
        for t in (ticker_task, typing_task):
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t
    with contextlib.suppress(TelegramForbiddenError):
        await safe_edit(msg, text, reply_markup=kb, parse_mode="HTML")
