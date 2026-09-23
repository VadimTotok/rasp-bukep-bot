import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from ..domain import GroupContext, SiteUnavailable
from ..services.favorites import FavoritesService
from ..services.rasp import DirectoryService, ScheduleService
from ..ui.callbacks import (
    CourseCB,
    FacultyCB,
    GroupPickCB,
    MenuCB,
    SpecialtyCB,
)
from ..ui.escape import esc
from ..ui.keyboards import (
    kb_courses,
    kb_faculties,
    kb_groups,
    kb_retry,
    kb_specialties,
    shorten,
)
from ..ui.loaders import run_with_loader, safe_delete
from .schedule import open_group

log = logging.getLogger(__name__)
router = Router(name="navigation")

@router.message(F.text == "📅 Расписание")
async def on_schedule_btn(
    message: Message, bot: Bot, directory: DirectoryService,
) -> None:
    await safe_delete(message)

    async def work():
        try:
            items = await directory.faculties()
        except SiteUnavailable:
            return ("⚠️ Сайт расписания не отвечает. Попробуйте позже.",
                    kb_retry(MenuCB().pack()))
        return "Выберите факультет:", kb_faculties(items)

    await run_with_loader(message, edit=False, work=work(),
                          label="Загрузка списка факультетов…", bot=bot)

@router.callback_query(MenuCB.filter())
async def cb_menu(
    cb: CallbackQuery, bot: Bot, directory: DirectoryService,
) -> None:
    await cb.answer()

    async def work():
        try:
            items = await directory.faculties(force=True)
        except SiteUnavailable:
            return ("⚠️ Сайт расписания не отвечает.",
                    kb_retry(MenuCB().pack()))
        return "Выберите факультет:", kb_faculties(items)

    await run_with_loader(cb.message, edit=True, work=work(),
                          label="Загрузка списка факультетов…", bot=bot)

@router.callback_query(FacultyCB.filter())
async def cb_faculty(
    cb: CallbackQuery, callback_data: FacultyCB,
    bot: Bot, directory: DirectoryService,
) -> None:
    await cb.answer()
    f = callback_data.idx

    async def work():
        facs = await directory.faculties()
        if f >= len(facs):
            return "Факультет не найден.", kb_retry(MenuCB().pack())
        try:
            items = await directory.specialties(facs[f].target)
        except SiteUnavailable:
            return ("⚠️ Не удалось загрузить специальности.",
                    kb_retry(FacultyCB(idx=f).pack()))
        text = (f"Факультет: <b>{esc(shorten(facs[f].label))}</b>\n"
                f"Выберите специальность:")
        return text, kb_specialties(f, items)

    await run_with_loader(cb.message, edit=True, work=work(),
                          label="Загрузка специальностей…", bot=bot)

@router.callback_query(SpecialtyCB.filter())
async def cb_specialty(
    cb: CallbackQuery, callback_data: SpecialtyCB,
    bot: Bot, directory: DirectoryService,
) -> None:
    await cb.answer()
    f, s = callback_data.f, callback_data.s

    async def work():
        facs = await directory.faculties()
        if f >= len(facs):
            return "Факультет не найден.", kb_retry(MenuCB().pack())
        specs = await directory.specialties(facs[f].target)
        if s >= len(specs):
            return "Специальность не найдена.",
            kb_retry(FacultyCB(idx=f).pack())
        try:
            courses = await directory.courses(facs[f].target, specs[s].target)
        except SiteUnavailable:
            return ("⚠️ Не удалось загрузить курсы.",
                    kb_retry(SpecialtyCB(f=f, s=s).pack()))
        text = (f"Специальность: <b>{esc(shorten(specs[s].label))}</b>\n"
                f"Выберите курс:")
        return text, kb_courses(f, s, courses)

    await run_with_loader(cb.message, edit=True, work=work(),
                          label="Загрузка курсов…", bot=bot)

@router.callback_query(CourseCB.filter())
async def cb_course(
    cb: CallbackQuery, callback_data: CourseCB,
    bot: Bot, directory: DirectoryService,
) -> None:
    await cb.answer()
    f, s, k = callback_data.f, callback_data.s, callback_data.k

    async def work():
        facs = await directory.faculties()
        if f >= len(facs):
            return "Факультет не найден.", kb_retry(MenuCB().pack())
        specs = await directory.specialties(facs[f].target)
        if s >= len(specs):
            return "Специальность не найдена.",
            kb_retry(FacultyCB(idx=f).pack())
        courses = await directory.courses(facs[f].target, specs[s].target)
        if k >= len(courses):
            return "Курс не найден.", kb_retry(SpecialtyCB(f=f, s=s).pack())
        try:
            groups = await directory.groups(
                facs[f].target, specs[s].target, courses[k].target,
            )
        except SiteUnavailable:
            return ("⚠️ Не удалось загрузить группы.",
                    kb_retry(CourseCB(f=f, s=s, k=k).pack()))
        text = f"Курс: <b>{esc(courses[k].label)}</b>\nВыберите группу:"
        return text, kb_groups(f, s, k, groups)

    await run_with_loader(cb.message, edit=True, work=work(), label="Загрузка групп…", bot=bot)

@router.callback_query(GroupPickCB.filter())
async def cb_group_pick(
    cb: CallbackQuery, callback_data: GroupPickCB,
    bot: Bot, directory: DirectoryService, favorites: FavoritesService,
    schedule_svc: ScheduleService,
    week_type: str | None = None,
) -> None:
    await cb.answer()
    f, s, k, g = (callback_data.f, callback_data.s,
                  callback_data.k, callback_data.g)

    facs = await directory.faculties()
    if f >= len(facs):
        await cb.message.edit_text("Факультет не найден.")
        return
    specs = await directory.specialties(facs[f].target)
    if s >= len(specs):
        await cb.message.edit_text("Специальность не найдена.")
        return
    courses = await directory.courses(facs[f].target, specs[s].target)
    if k >= len(courses):
        await cb.message.edit_text("Курс не найден.")
        return
    groups = await directory.groups(
        facs[f].target, specs[s].target, courses[k].target,
    )
    if g >= len(groups):
        await cb.message.edit_text("Группа не найдена.")
        return

    ctx = GroupContext(
        ft=facs[f].target, st=specs[s].target,
        kt=courses[k].target, gt=groups[g].target, gl=groups[g].label,
        fi=f, si=s, ki=k, gi=g,
    )
    ctx_id = await favorites.ensure_context(ctx)
    await open_group(cb, ctx, ctx_id, bot=bot,
                     schedule_svc=schedule_svc, favorites=favorites,
                     week_type=week_type)