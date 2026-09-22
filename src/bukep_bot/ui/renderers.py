from ..domain import DAY_EMOJI, DAY_ORDER, Lesson, Schedule, bell_for
from .escape import esc

def _fmt_lesson(day_name: str, l: Lesson) -> list[str]:
    prefix = l.para
    t = bell_for(day_name, l.para)
    if t:
        prefix += f" · {t}"

    line = f"<b><u>{esc(prefix)}</u></b> · {esc(l.subject)}"
    if l.week == "numerator":
        line += " <i>[Числ.]</i>"
    elif l.week == "denominator":
        line += " <i>[Знам.]</i>"

    out = [line]
    meta: list[str] = []
    if l.type:
        meta.append(esc(l.type))
    if l.room:
        meta.append(f"ауд. {esc(l.room)}")
    if l.teachers:
        meta.append(", ".join(esc(x) for x in l.teachers))
    if meta:
        out.append("   " + " · ".join(meta))
    return out

def _day_header(day: str, is_today: bool = False) -> str:
    emoji = DAY_EMOJI.get(day, "")
    label = f"{esc(day)} {emoji}".strip()
    mark = " <b>(сегодня)</b>" if is_today else ""
    return f"💢 <b>{label}</b>{mark}"

def _stale_note() -> str:
    return ("\n<i>⚠️ Сайт вуза недоступен, показаны данные из кэша. "
            "Могут быть устаревшими.</i>")

def format_schedule(
    schedule: Schedule,
    group_label: str = "",
    day: str | None = None,
    is_today: bool = False,
    stale: bool = False,
) -> str:
    head = f"📅 <b>Расписание {esc(group_label)}</b>"
    if day is not None:
        head += f"\n{_day_header(day, is_today)}"
    if stale:
        head += _stale_note()

    if day is not None:
        lessons = schedule.get(day, [])
        if not lessons:
            return head + "\n\nНа этот день занятий нет."
        out = [head, ""]
        for l in lessons:
            out.extend(_fmt_lesson(day, l))
            out.append("")
        return "\n".join(out).rstrip()

    out = [head, ""]
    any_lessons = False
    for d in DAY_ORDER:
        lessons = schedule.get(d)
        if not lessons:
            continue
        any_lessons = True
        out.append(_day_header(d))
        for l in lessons:
            out.extend(_fmt_lesson(d, l))
            out.append("")
    if not any_lessons:
        return "Расписание отсутствует."
    return "\n".join(out).rstrip()
