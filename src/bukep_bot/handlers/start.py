from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..ui.keyboards import kb_main_reply, kb_start_inline

router = Router(name="start")

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 <b>Привет!</b>\n\n"
        "Этот бот показывает расписание БУКЭП.\n\n"
        "<b>Это неофициальный проект.</b> Я не связан с университетом. "
        "Данные берутся с открытого сайта <code>rasp.bukep.ru</code>.\n\n"
        "<i>Иногда бот может зависать на пару секунд при загрузке — "
        "это нормально. Сайт вуза ОЧЕНЬ СТАРЫЙ и медленно отвечает. "
        "Пока идёт загрузка, ты увидишь лоадер :3</i>",
        reply_markup=kb_start_inline(),
        parse_mode="HTML",
    )
    await message.answer(
        "Меню всегда доступно внизу 👇",
        reply_markup=kb_main_reply(),
    )
