from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)

from ..domain import DAY_EMOJI, DAY_ORDER, Item, Schedule, today_day_name
from .callbacks import (
    BellsCB, CourseCB, FacultyCB, FavListCB, GroupPickCB,
    HelpCB, MenuCB, ScheduleCB, SpecialtyCB,
)
from ..config import GITHUB_URL, ISSUES_URL

DAY_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]

def shorten(label: str) -> str:
    return label.replace("Среднего профессионального образования", "СПО")

def kb_start_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Расписание",
                                 callback_data=MenuCB().pack()),
            InlineKeyboardButton(text="⭐ Избранное",
                                 callback_data=FavListCB(action="list").pack()),
            InlineKeyboardButton(text="🔔 Звонки",
                                 callback_data=BellsCB().pack()),
        ],
        [
            InlineKeyboardButton(text="❓ Помощь",
                                 callback_data=HelpCB().pack()),
        ],
    ])

def kb_faculties(items: list[Item]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=shorten(f.label), callback_data=FacultyCB(idx=i).pack(),
    )] for i, f in enumerate(items)]
    rows.append([InlineKeyboardButton(
        text="⭐ Избранное", callback_data=FavListCB(action="list").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_specialties(f: int, items: list[Item]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=shorten(s.label), callback_data=SpecialtyCB(f=f, s=i).pack(),
    )] for i, s in enumerate(items)]
    rows.append([InlineKeyboardButton(text="← Назад", callback_data=MenuCB().pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_courses(f: int, s: int, items: list[Item]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=c.label, callback_data=CourseCB(f=f, s=s, k=i).pack(),
    )] for i, c in enumerate(items)]
    rows.append([InlineKeyboardButton(text="← Назад",
                                      callback_data=FacultyCB(idx=f).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_groups(f: int, s: int, k: int, groups: list[Item]) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(groups), 2):
        row = [
            InlineKeyboardButton(
                text=groups[j].label[:60],
                callback_data=GroupPickCB(f=f, s=s, k=k, g=j).pack(),
            )
            for j in range(i, min(i + 2, len(groups)))
        ]
        rows.append(row)
    rows.append([InlineKeyboardButton(
        text="← Назад", callback_data=SpecialtyCB(f=f, s=s).pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _fav_btn(ctx_id: str, is_favorite: bool) -> InlineKeyboardButton:
    if is_favorite:
        return InlineKeyboardButton(
            text="★ Убрать из избранного",
            callback_data=FavListCB(action="del", ctx_id=ctx_id).pack(),
        )
    return InlineKeyboardButton(
        text="⭐ В избранное",
        callback_data=FavListCB(action="add", ctx_id=ctx_id).pack(),
    )

def kb_day_picker(
    ctx_id: str, sched: Schedule | None, is_fav: bool,
) -> InlineKeyboardMarkup:
    today = today_day_name()
    btns = []
    for i, short in enumerate(DAY_SHORT):
        full = DAY_ORDER[i]
        emoji = DAY_EMOJI.get(full, "")
        prefix = "▶ " if full == today else ""
        label = f"{prefix}{emoji} {short}".strip()
        mark = " •" if sched and sched.get(full) else ""
        btns.append(InlineKeyboardButton(
            text=f"{label}{mark}",
            callback_data=ScheduleCB(ctx_id=ctx_id, action="day", day=i).pack(),
        ))
    return InlineKeyboardMarkup(inline_keyboard=[
        btns[0:3], btns[3:6],
        [InlineKeyboardButton(
            text="📋 Все дни",
            callback_data=ScheduleCB(ctx_id=ctx_id, action="all").pack(),
        )],
        [_fav_btn(ctx_id, is_fav)],
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=ScheduleCB(ctx_id=ctx_id, action="refresh").pack(),
            ),
            InlineKeyboardButton(text="🔔 Звонки", callback_data=BellsCB().pack()),
        ],
        [InlineKeyboardButton(text="🏠 В начало", callback_data=MenuCB().pack())],
    ])

def kb_day_view(
    ctx_id: str, day_idx: int, is_fav: bool,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📅 По дням",
                callback_data=ScheduleCB(ctx_id=ctx_id, action="pick").pack(),
            ),
            InlineKeyboardButton(
                text="📋 Все дни",
                callback_data=ScheduleCB(ctx_id=ctx_id, action="all").pack(),
            ),
        ],
        [_fav_btn(ctx_id, is_fav)],
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=ScheduleCB(
                    ctx_id=ctx_id, action="refresh_day", day=day_idx,
                ).pack(),
            ),
            InlineKeyboardButton(text="🔔 Звонки", callback_data=BellsCB().pack()),
        ],
        [InlineKeyboardButton(text="🏠 В начало", callback_data=MenuCB().pack())],
    ])

def kb_all_days_view(ctx_id: str, is_fav: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📅 По дням",
            callback_data=ScheduleCB(ctx_id=ctx_id, action="pick").pack(),
        )],
        [_fav_btn(ctx_id, is_fav)],
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=ScheduleCB(ctx_id=ctx_id, action="refresh_all").pack(),
            ),
            InlineKeyboardButton(text="🔔 Звонки",
                                 callback_data=BellsCB().pack()),
        ],
        [InlineKeyboardButton(text="🏠 В начало",
                              callback_data=MenuCB().pack())],
    ])

def kb_fav_list(items: list[dict]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=it["gl"][:60],
        callback_data=FavListCB(action="open", ctx_id=it["ctx_id"]).pack(),
    )] for it in items]
    rows.append([InlineKeyboardButton(text="🏠 В начало",
                                      callback_data=MenuCB().pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_retry(callback_packed: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Повторить",
                              callback_data=callback_packed)],
        [InlineKeyboardButton(text="🏠 В начало",
                              callback_data=MenuCB().pack())],
    ])

def kb_main_reply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Расписание"),
                KeyboardButton(text="⭐ Избранное"),
                KeyboardButton(text="🔔 Звонки"),
            ],
            [
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
    )

def kb_help() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 GitHub",
                                 url=GITHUB_URL),
            InlineKeyboardButton(text="👀 Issues",
                                 url=ISSUES_URL),
        ],
        [InlineKeyboardButton(text="🏠 В начало",
                              callback_data=MenuCB().pack())],
    ])
