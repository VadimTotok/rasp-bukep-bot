import contextlib
import logging

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..domain import GroupContext, SiteUnavailable
from ..services.favorites import FavoritesService
from ..services.rasp import ScheduleService
from ..ui.callbacks import FavListCB, MenuCB
from ..ui.keyboards import kb_fav_list, kb_retry
from ..ui.loaders import safe_delete
from .schedule import _show_today

log = logging.getLogger(__name__)
router = Router(name="favorites")

def _empty_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В начало", callback_data=MenuCB().pack())],
    ])

def _empty_text() -> str:
    return ("⭐ <b>Избранное</b>\n\n"
            "У вас пока нет избранных групп.\n"
            "Откройте любую группу и нажмите «⭐ В избранное».")

@router.message(F.text == "⭐ Избранное")
async def on_fav_btn(message: Message, favorites: FavoritesService) -> None:
    await safe_delete(message)
    items = await favorites.list(message.from_user.id)
    if not items:
        await message.answer(_empty_text(), reply_markup=_empty_kb(),
                             parse_mode="HTML")
        return
    await message.answer("⭐ <b>Избранное</b>\n\nВыберите группу:",
                         reply_markup=kb_fav_list(items), parse_mode="HTML")

@router.callback_query(FavListCB.filter(F.action == "list"))
async def cb_fav_list(cb: CallbackQuery, favorites: FavoritesService) -> None:
    await cb.answer()
    items = await favorites.list(cb.from_user.id)
    if not items:
        await cb.message.edit_text(_empty_text(), reply_markup=_empty_kb(),
                                   parse_mode="HTML")
        return
    await cb.message.edit_text("⭐ <b>Избранное</b>\n\nВыберите группу:",
                               reply_markup=kb_fav_list(items),
                               parse_mode="HTML")

def _swap_button(markup: InlineKeyboardMarkup | None,
                 old_packed: str, new_btn: InlineKeyboardButton,
                 ) -> InlineKeyboardMarkup | None:
    if markup is None or not hasattr(markup, "inline_keyboard"):
        return None
    rows = []
    for row in markup.inline_keyboard:
        new_row = []
        for btn in row:
            if btn.callback_data == old_packed:
                new_row.append(new_btn)
            else:
                new_row.append(btn)
        rows.append(new_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.callback_query(FavListCB.filter(F.action == "add"))
async def cb_fav_add(
    cb: CallbackQuery, callback_data: FavListCB, favorites: FavoritesService,
) -> None:
    ctx = await favorites.get(callback_data.ctx_id)
    if ctx is None:
        await cb.answer("Группа не найдена", show_alert=True)
        return
    await favorites.add(cb.from_user.id, ctx)
    await cb.answer("Добавлено в избранное ⭐")
    old_packed = FavListCB(action="add", ctx_id=callback_data.ctx_id).pack()
    new_btn = InlineKeyboardButton(
        text="★ Убрать из избранного",
        callback_data=FavListCB(action="del", ctx_id=callback_data.ctx_id).pack(),
    )
    new_markup = _swap_button(cb.message.reply_markup, old_packed, new_btn)
    if new_markup is not None:
        with contextlib.suppress(Exception):
            await cb.message.edit_reply_markup(reply_markup=new_markup)

@router.callback_query(FavListCB.filter(F.action == "del"))
async def cb_fav_del(
    cb: CallbackQuery, callback_data: FavListCB, favorites: FavoritesService,
) -> None:
    ctx = await favorites.get(callback_data.ctx_id)
    if ctx is None:
        await cb.answer("Группа не найдена", show_alert=True)
        return
    await favorites.remove(cb.from_user.id, callback_data.ctx_id)
    await cb.answer("Убрано из избранного")
    old_packed = FavListCB(action="del", ctx_id=callback_data.ctx_id).pack()
    new_btn = InlineKeyboardButton(
        text="⭐ В избранное",
        callback_data=FavListCB(action="add", ctx_id=callback_data.ctx_id).pack(),
    )
    new_markup = _swap_button(cb.message.reply_markup, old_packed, new_btn)
    if new_markup is not None:
        with contextlib.suppress(Exception):
            await cb.message.edit_reply_markup(reply_markup=new_markup)

@router.callback_query(FavListCB.filter(F.action == "open"))
async def cb_fav_open(
    cb: CallbackQuery, callback_data: FavListCB, *,
    bot: Bot, schedule_svc: ScheduleService, favorites: FavoritesService,
) -> None:
    await cb.answer()
    ctx_id = callback_data.ctx_id
    ctx: GroupContext | None = await favorites.get(ctx_id)
    if ctx is None:
        await cb.message.edit_text(
            "Группа не найдена.",
            reply_markup=_empty_kb(),
        )
        return

    try:
        sched, _ = await schedule_svc.get(ctx, force=True)
    except SiteUnavailable:
        await cb.message.edit_text(
            "⚠️ Сайт недоступен, попробуйте позже.",
            reply_markup=kb_retry(
                FavListCB(action="open", ctx_id=ctx_id).pack(),
            ),
        )
        return

    if sched is None:
        new_ctx = await schedule_svc.re_resolve(ctx)
        if new_ctx is not None:
            log.info("re-resolved %s -> kt=%s gt=%s",
                     ctx.gl, new_ctx.kt, new_ctx.gt)
            await favorites.ensure_context(new_ctx)
            ctx = new_ctx

    await _show_today(cb, ctx, ctx_id, bot=bot, force=False,
                      schedule_svc=schedule_svc, favorites=favorites)
