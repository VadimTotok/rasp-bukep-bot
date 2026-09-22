from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..domain import BELL_DETAILED
from ..ui.callbacks import BellsCB, MenuCB
from ..ui.loaders import safe_delete

router = Router(name="bells")

def _kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В начало", callback_data=MenuCB().pack())],
    ])

@router.message(F.text == "🔔 Звонки")
async def on_bells_btn(message: Message) -> None:
    await safe_delete(message)
    await message.answer(BELL_DETAILED, reply_markup=_kb(), parse_mode="HTML")

@router.callback_query(BellsCB.filter())
async def cb_bells(cb: CallbackQuery) -> None:
    await cb.answer()
    await cb.message.edit_text(BELL_DETAILED, reply_markup=_kb(),
                               parse_mode="HTML")
