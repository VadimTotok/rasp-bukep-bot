import logging

from aiogram import Bot, Router
from aiogram.types import CallbackQuery

from ..domain import (
    DAY_ORDER,
    GroupContext,
    SiteUnavailable,
    today_day_name,
)
from ..services.favorites import FavoritesService
from ..services.rasp import ScheduleService
from ..ui.callbacks import ScheduleCB
from ..ui.escape import esc
from ..ui.keyboards import (
    kb_all_days_view,
    kb_day_picker,
    kb_day_view,
    kb_retry,
)
from ..ui.loaders import run_with_loader
from ..ui.renderers import format_schedule

log = logging.getLogger(__name__)
router = Router(name="schedule")


async def open_group(
    cb: CallbackQuery, ctx: GroupContext, ctx_id: str, *,
    bot: Bot, schedule_svc: ScheduleService, favorites: FavoritesService,
    week_type: str | None = None,
) -> None:
    await _show_today(cb, ctx, ctx_id, bot=bot, force=False,
                      schedule_svc=schedule_svc, favorites=favorites,
                      week_type=week_type)


async def _show_today(
    cb: CallbackQuery, ctx: GroupContext, ctx_id: str, *,
    bot: Bot, force: bool,
    schedule_svc: ScheduleService, favorites: FavoritesService,
    week_type: str | None = None,
) -> None:
    today = today_day_name()
    if today is None:
        await _show_picker(cb, ctx, ctx_id, bot=bot, force=force,
                           note="Сегодня воскресенье — выходной.",
                           schedule_svc=schedule_svc, favorites=favorites,
                           week_type=week_type)
        return

    async def work():
        try:
            sched, stale = await schedule_svc.get(ctx, force=force)
        except SiteUnavailable:
            return ("⚠️ Не удалось загрузить расписание. Попробуйте позже.",
                    kb_retry(ScheduleCB(ctx_id=ctx_id, action="refresh").pack()))
        if sched is None:
            return (f"У группы <b>{esc(ctx.gl)}</b> нет расписания.",
                    kb_retry(ScheduleCB(ctx_id=ctx_id, action="pick").pack()))
        is_fav = await favorites.is_favorite(cb.from_user.id, ctx_id)
        if not sched.get(today):
            text = (f"📅 <b>Расписание {esc(ctx.gl)}</b>\n\n"
                    f"Сегодня ({esc(today)}) занятий нет.\n"
                    f"<i>▶ — сегодня, • — есть пары</i>")
            if stale:
                text += "\n<i>⚠️ Сайт недоступен, данные из кэша.</i>"
            return text, kb_day_picker(ctx_id, sched, is_fav)
        day_idx = DAY_ORDER.index(today)
        text = format_schedule(sched, group_label=ctx.gl, day=today,
                               is_today=True, stale=stale, week_type=week_type)
        return text, kb_day_view(ctx_id, day_idx, is_fav)

    await run_with_loader(cb.message, edit=True, work=work(),
                          label="Загрузка расписания…", bot=bot)


async def _show_picker(
    cb: CallbackQuery, ctx: GroupContext, ctx_id: str, *,
    bot: Bot, force: bool,
    schedule_svc: ScheduleService, favorites: FavoritesService,
    note: str | None = None,
    week_type: str | None = None,
) -> None:
    async def work():
        try:
            sched, stale = await schedule_svc.get(ctx, force=force)
        except SiteUnavailable:
            return ("⚠️ Не удалось загрузить расписание.",
                    kb_retry(ScheduleCB(ctx_id=ctx_id, action="pick").pack()))
        if sched is None:
            return (f"У группы <b>{esc(ctx.gl)}</b> нет расписания.",
                    kb_retry(ScheduleCB(ctx_id=ctx_id, action="pick").pack()))
        header = note or "Выберите день недели"
        text = (f"📅 <b>Расписание {esc(ctx.gl)}</b>\n\n"
                f"{esc(header)}\n<i>▶ — сегодня, • — есть пары</i>")
        if stale:
            text += "\n<i>⚠️ Сайт недоступен, данные из кэша.</i>"
        is_fav = await favorites.is_favorite(cb.from_user.id, ctx_id)
        return text, kb_day_picker(ctx_id, sched, is_fav)

    await run_with_loader(cb.message, edit=True, work=work(),
                          label="Загрузка расписания…", bot=bot)


async def _show_day(
    cb: CallbackQuery, ctx: GroupContext, ctx_id: str, day_idx: int, *,
    bot: Bot, force: bool,
    schedule_svc: ScheduleService, favorites: FavoritesService,
    week_type: str | None = None,
) -> None:
    async def work():
        try:
            sched, stale = await schedule_svc.get(ctx, force=force)
        except SiteUnavailable:
            return ("⚠️ Не удалось загрузить расписание.",
                    kb_retry(ScheduleCB(
                        ctx_id=ctx_id, action="day", day=day_idx,
                    ).pack()))
        if sched is None:
            return (f"У группы <b>{esc(ctx.gl)}</b> нет расписания.",
                    kb_retry(ScheduleCB(ctx_id=ctx_id, action="pick").pack()))
        day_name = DAY_ORDER[day_idx]
        is_today = day_name == today_day_name()
        text = format_schedule(sched, group_label=ctx.gl, day=day_name,
                               is_today=is_today, stale=stale,
                               week_type=week_type)
        is_fav = await favorites.is_favorite(cb.from_user.id, ctx_id)
        return text, kb_day_view(ctx_id, day_idx, is_fav)

    await run_with_loader(cb.message, edit=True, work=work(),
                          label=f"Загрузка: {DAY_ORDER[day_idx]}…", bot=bot)


async def _show_all(
    cb: CallbackQuery, ctx: GroupContext, ctx_id: str, *,
    bot: Bot, force: bool,
    schedule_svc: ScheduleService, favorites: FavoritesService,
    week_type: str | None = None,
) -> None:
    async def work():
        try:
            sched, stale = await schedule_svc.get(ctx, force=force)
        except SiteUnavailable:
            return ("⚠️ Не удалось загрузить расписание.",
                    kb_retry(ScheduleCB(
                        ctx_id=ctx_id, action="refresh_all",
                    ).pack()))
        if sched is None:
            return (f"У группы <b>{esc(ctx.gl)}</b> нет расписания.",
                    kb_retry(ScheduleCB(ctx_id=ctx_id, action="pick").pack()))
        text = format_schedule(sched, group_label=ctx.gl, stale=stale,
                               week_type=week_type)
        is_fav = await favorites.is_favorite(cb.from_user.id, ctx_id)
        return text, kb_all_days_view(ctx_id, is_fav)

    await run_with_loader(cb.message, edit=True, work=work(),
                          label="Загрузка полного расписания…", bot=bot)


@router.callback_query(ScheduleCB.filter())
async def cb_schedule(
    cb: CallbackQuery, callback_data: ScheduleCB, *,
    bot: Bot, schedule_svc: ScheduleService, favorites: FavoritesService,
    week_type: str | None = None,
) -> None:
    await cb.answer()
    ctx_id = callback_data.ctx_id
    ctx = await favorites.get(ctx_id)
    if ctx is None:
        await cb.message.edit_text(
            "Группа не найдена. Возможно, она удалена.",
            reply_markup=kb_retry(
                ScheduleCB(ctx_id=ctx_id, action="pick").pack(),
            ),
        )
        return

    action = callback_data.action
    if action == "today":
        await _show_today(cb, ctx, ctx_id, bot=bot, force=False,
                          schedule_svc=schedule_svc, favorites=favorites,
                          week_type=week_type)
    elif action == "refresh":
        await _show_today(cb, ctx, ctx_id, bot=bot, force=True,
                          schedule_svc=schedule_svc, favorites=favorites,
                          week_type=week_type)
    elif action == "pick":
        await _show_picker(cb, ctx, ctx_id, bot=bot, force=False,
                           schedule_svc=schedule_svc, favorites=favorites,
                           week_type=week_type)
    elif action == "all":
        await _show_all(cb, ctx, ctx_id, bot=bot, force=False,
                        schedule_svc=schedule_svc, favorites=favorites,
                        week_type=week_type)
    elif action == "refresh_all":
        await _show_all(cb, ctx, ctx_id, bot=bot, force=True,
                        schedule_svc=schedule_svc, favorites=favorites,
                        week_type=week_type)
    elif action == "day":
        await _show_day(cb, ctx, ctx_id, callback_data.day, bot=bot, force=False,
                        schedule_svc=schedule_svc, favorites=favorites,
                        week_type=week_type)
    elif action == "refresh_day":
        await _show_day(cb, ctx, ctx_id, callback_data.day, bot=bot, force=True,
                        schedule_svc=schedule_svc, favorites=favorites,
                        week_type=week_type)
    else:
        log.warning("unknown ScheduleCB action: %s", action)
        await cb.answer("Неизвестное действие", show_alert=True)