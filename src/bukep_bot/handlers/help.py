from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ..ui.callbacks import HelpCB
from ..ui.keyboards import kb_help
from ..ui.loaders import safe_delete

router = Router(name="help")

HELP_TEXT = (
    "❓ <b>Помощь</b>\n\n"
    "Это неофициальный бот с расписанием БУКЭП.\n\n"
    "Исходный код открыт!\n\n"
    "Если нашли баг или хотите предложить фичу: "
    "откройте <b>issue</b> на GitHub. "
    "Буду рад любой обратной связи ❤️"
)

@router.message(F.text == "❓ Помощь")
async def on_help_btn(message: Message) -> None:
    await safe_delete(message)
    await message.answer(HELP_TEXT, reply_markup=kb_help(), parse_mode="HTML")


@router.callback_query(HelpCB.filter())
async def cb_help(cb: CallbackQuery) -> None:
    await cb.answer()
    await cb.message.edit_text(HELP_TEXT, reply_markup=kb_help(), parse_mode="HTML")
