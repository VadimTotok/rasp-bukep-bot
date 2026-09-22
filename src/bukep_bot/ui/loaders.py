import asyncio
import time
from typing import Any, Awaitable

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest, TelegramForbiddenError,
)
from aiogram.types import Message

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

async def safe_delete(message: Message) -> None:
    try:
        await message.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        pass

async def safe_edit(message: Message, text: str, **kwargs) -> None:
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        raise

async def _keep_typing(bot: Bot, chat_id: int, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await bot.send_chat_action(chat_id, "typing")
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=4.0)
        except asyncio.TimeoutError:
            pass

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
            try:
                await msg.edit_text(
                    f"⏳ <b>{label}</b>\n<code>{spin}</code> {elapsed:.1f} с",
                    parse_mode="HTML",
                )
            except TelegramBadRequest:
                pass
            i += 1
            try:
                await asyncio.wait_for(stop.wait(), timeout=0.6)
            except asyncio.TimeoutError:
                pass

    ticker_task = asyncio.create_task(ticker())
    typing_task = asyncio.create_task(_keep_typing(bot, msg.chat.id, stop))
    try:
        text, kb = await work
    finally:
        stop.set()
        for t in (ticker_task, typing_task):
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
    try:
        await safe_edit(msg, text, reply_markup=kb, parse_mode="HTML")
    except TelegramForbiddenError:
        pass
